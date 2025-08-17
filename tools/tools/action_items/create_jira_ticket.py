from typing import Optional, List
import os
from enum import Enum
from pydantic import BaseModel, Field
from jira import JIRA
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class IssueType(str, Enum):
    TASK = "Task"
    BUG = "Bug"
    STORY = "Story"
    EPIC = "Epic"
    SUBTASK = "Sub-task"

class Priority(str, Enum):
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"

class JiraTicket(BaseModel):
    key: str = Field(description="The Jira ticket key (e.g., PROJ-123)")
    summary: str = Field(description="The ticket summary/title")
    description: str = Field(description="The detailed description")
    issue_type: IssueType = Field(description="The type of issue")
    priority: Priority = Field(description="The priority level")
    assignee: Optional[str] = Field(None, description="The assignee username")
    labels: List[str] = Field(default_factory=list, description="List of labels")
    components: List[str] = Field(default_factory=list, description="List of components")

@tool
def create_jira_ticket(
    summary: str,
    description: str,
    issue_type: IssueType = IssueType.TASK,
    priority: Priority = Priority.MEDIUM,
    assignee: Optional[str] = None,
    labels: List[str] = [],
    components: List[str] = [],
    project_key: str = "PROJ"
) -> JiraTicket:
    """
    Create a new Jira ticket with the specified details.
    
    Args:
        summary: A clear, concise title for the ticket
        description: Detailed description of the issue, task, or feature request
        issue_type: The type of issue (Task, Bug, Story, Epic, Sub-task)
        priority: The priority level (Highest, High, Medium, Low, Lowest)
        assignee: Username of the person to assign the ticket to (optional)
        labels: List of labels to apply to the ticket
        components: List of components to assign to the ticket
        project_key: The Jira project key (default: PROJ)
    
    Returns:
        JiraTicket object with the created ticket details
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured. Please check environment variables.")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Clean up summary - remove quotes and improve formatting
        clean_summary = summary
        if clean_summary.startswith('"') and clean_summary.endswith('"'):
            clean_summary = clean_summary[1:-1]
        if clean_summary.startswith("Action Item: "):
            clean_summary = clean_summary.replace("Action Item: ", "")
        
        # Prepare issue fields
        issue_dict = {
            'project': {'key': project_key},
            'summary': clean_summary,
            'description': description,
            'issuetype': {'name': issue_type.value if hasattr(issue_type, 'value') else str(issue_type)}
        }
        
        # Add priority field only for non-Epic issue types
        if str(issue_type).lower() != 'epic':
            issue_dict['priority'] = {'name': priority.value if hasattr(priority, 'value') else str(priority)}
        
        # Add optional fields if provided
        if assignee:
            try:
                # Verify the assignee exists in Jira
                jira.user(assignee)
                # Handle both regular usernames and Account IDs
                # Check if it's a 24-character hex string (like 63e1fbc8c3eb74ad8e9908f6) or contains colon (like 712020:...)
                if ':' in assignee or (len(assignee) == 24 and all(c in '0123456789abcdef' for c in assignee.lower())):
                    issue_dict['assignee'] = {'accountId': assignee}
                else:  # Regular username
                    issue_dict['assignee'] = {'name': assignee}
                print(f"✅ Assignee set: {assignee}")
            except Exception as e:
                print(f"Warning: Assignee {assignee} not found in Jira, creating ticket without assignee")
                # Continue without assignee if user doesn't exist
        else:
            # Fallback: automatically assign a team member if none provided
            try:
                from assign_team_member import assign_team_member
                team_member = assign_team_member(
                    issue_type=str(issue_type),
                    priority=str(priority),
                    components=[],
                    labels=[],
                    project_key=project_key
                )
                # Check if it's a 24-character hex string (like 63e1fbc8c3eb74ad8e9908f6) or contains colon (like 712020:...)
                if ':' in team_member.username or (len(team_member.username) == 24 and all(c in '0123456789abcdef' for c in team_member.username.lower())):
                    issue_dict['assignee'] = {'accountId': team_member.username}
                else:  # Regular username
                    issue_dict['assignee'] = {'name': team_member.username}
                print(f"✅ Auto-assigned team member: {team_member.name} ({team_member.username})")
            except Exception as e:
                print(f"Warning: Could not auto-assign team member: {e}")
                # Continue without assignee if auto-assignment fails
        
        if labels:
            issue_dict['labels'] = labels
            
        if components:
            issue_dict['components'] = [{'name': comp} for comp in components]
        
        # Create the issue
        new_issue = jira.create_issue(fields=issue_dict)
        
        # Return the created ticket details
        return JiraTicket(
            key=new_issue.key,
            summary=new_issue.fields.summary,
            description=new_issue.fields.description or "",
            issue_type=IssueType(new_issue.fields.issuetype.name),
            priority=Priority(new_issue.fields.priority.name) if hasattr(new_issue.fields, 'priority') and new_issue.fields.priority else Priority.MEDIUM,
            assignee=getattr(new_issue.fields.assignee, 'displayName', getattr(new_issue.fields.assignee, 'name', None)) if new_issue.fields.assignee else None,
            labels=new_issue.fields.labels,
            components=[comp.name for comp in new_issue.fields.components] if hasattr(new_issue.fields, 'components') else []
        )
        
    except Exception as e:
        raise Exception(f"Failed to create Jira ticket: {str(e)}")
