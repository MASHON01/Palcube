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

class JiraTicketUpdate(BaseModel):
    key: str = Field(description="The Jira ticket key")
    summary: str = Field(description="The updated ticket summary/title")
    description: str = Field(description="The updated description")
    status: str = Field(description="The current status")
    issue_type: IssueType = Field(description="The type of issue")
    priority: Priority = Field(description="The priority level")
    assignee: Optional[str] = Field(None, description="The assignee username")
    labels: List[str] = Field(default_factory=list, description="List of labels")
    components: List[str] = Field(default_factory=list, description="List of components")

@tool
def update_jira_ticket(
    ticket_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    issue_type: Optional[IssueType] = None,
    priority: Optional[Priority] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    components: Optional[List[str]] = None,
    status: Optional[str] = None
) -> JiraTicketUpdate:
    """
    Update an existing Jira ticket with new information.
    
    Args:
        ticket_key: The Jira ticket key to update (e.g., PROJ-123)
        summary: New summary/title for the ticket (optional)
        description: New description for the ticket (optional)
        issue_type: New issue type (optional)
        priority: New priority level (optional)
        assignee: New assignee username (optional)
        labels: New list of labels (optional)
        components: New list of components (optional)
        status: New status (optional)
    
    Returns:
        JiraTicketUpdate object with the updated ticket details
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured. Please check environment variables.")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Get the existing issue
        issue = jira.issue(ticket_key)
        
        # Prepare update fields
        update_fields = {}
        
        if summary is not None:
            update_fields['summary'] = summary
            
        if description is not None:
            update_fields['description'] = description
            
        if issue_type is not None:
            update_fields['issuetype'] = {'name': issue_type.value}
            
        if priority is not None:
            update_fields['priority'] = {'name': priority.value}
            
        if assignee is not None:
            update_fields['assignee'] = {'name': assignee}
            
        if labels is not None:
            update_fields['labels'] = labels
            
        if components is not None:
            update_fields['components'] = [{'name': comp} for comp in components]
        
        # Update the issue
        if update_fields:
            issue.update(fields=update_fields)
        
        # Update status if provided
        if status is not None:
            jira.transition_issue(issue, status)
        
        # Refresh the issue to get updated data
        issue = jira.issue(ticket_key)
        
        # Handle assignee - could be Account ID or username
        assignee_value = None
        if issue.fields.assignee:
            # Check if it's an Account ID (contains colon) or regular username
            if hasattr(issue.fields.assignee, 'accountId'):
                assignee_value = issue.fields.assignee.accountId
            elif hasattr(issue.fields.assignee, 'name'):
                assignee_value = issue.fields.assignee.name
            else:
                # Fallback to string representation
                assignee_value = str(issue.fields.assignee)
        
        # Return the updated ticket details
        return JiraTicketUpdate(
            key=issue.key,
            summary=issue.fields.summary,
            description=issue.fields.description or "",
            status=issue.fields.status.name,
            issue_type=IssueType(issue.fields.issuetype.name),
            priority=Priority(issue.fields.priority.name),
            assignee=assignee_value,
            labels=issue.fields.labels,
            components=[comp.name for comp in issue.fields.components]
        )
        
    except Exception as e:
        raise Exception(f"Failed to update Jira ticket {ticket_key}: {str(e)}")
