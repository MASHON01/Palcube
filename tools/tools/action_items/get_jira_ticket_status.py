from typing import Optional, List
import os
from pydantic import BaseModel, Field
from jira import JIRA
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class JiraTicketStatus(BaseModel):
    key: str = Field(description="The Jira ticket key")
    summary: str = Field(description="The ticket summary/title")
    status: str = Field(description="The current status of the ticket")
    issue_type: str = Field(description="The type of issue")
    priority: str = Field(description="The priority level")
    assignee: Optional[str] = Field(None, description="The assignee username")
    reporter: str = Field(description="The person who created the ticket")
    created: str = Field(description="Creation date")
    updated: str = Field(description="Last updated date")
    url: str = Field(description="Direct link to the ticket")
    description: str = Field(description="The ticket description")

@tool
def get_jira_ticket_status(ticket_key: str) -> JiraTicketStatus:
    """
    Get the current status and details of a specific Jira ticket.
    
    Args:
        ticket_key: The Jira ticket key (e.g., PROJ-123)
    
    Returns:
        JiraTicketStatus object with the ticket details
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured. Please check environment variables.")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Get the issue
        issue = jira.issue(ticket_key)
        
        # Return the ticket status details
        return JiraTicketStatus(
            key=issue.key,
            summary=issue.fields.summary,
            status=issue.fields.status.name,
            issue_type=issue.fields.issuetype.name,
            priority=issue.fields.priority.name,
            assignee=issue.fields.assignee.name if issue.fields.assignee else None,
            reporter=issue.fields.reporter.name,
            created=issue.fields.created,
            updated=issue.fields.updated,
            url=f"{jira_url}/browse/{issue.key}",
            description=issue.fields.description or ""
        )
        
    except Exception as e:
        raise Exception(f"Failed to get status for Jira ticket {ticket_key}: {str(e)}")
