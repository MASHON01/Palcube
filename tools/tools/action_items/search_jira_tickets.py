from typing import List, Optional
import os
from pydantic import BaseModel, Field
from jira import JIRA
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class JiraTicketSearchResult(BaseModel):
    key: str = Field(description="The Jira ticket key")
    summary: str = Field(description="The ticket summary/title")
    status: str = Field(description="The current status of the ticket")
    issue_type: str = Field(description="The type of issue")
    priority: str = Field(description="The priority level")
    assignee: Optional[str] = Field(None, description="The assignee username")
    created: str = Field(description="Creation date")
    updated: str = Field(description="Last updated date")
    url: str = Field(description="Direct link to the ticket")

@tool
def search_jira_tickets(
    query: str,
    project_key: Optional[str] = None,
    issue_type: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    max_results: int = 10
) -> List[JiraTicketSearchResult]:
    """
    Search for existing Jira tickets based on various criteria to avoid duplicates.
    
    Args:
        query: Text to search for in ticket summary and description
        project_key: Filter by specific project key (optional)
        issue_type: Filter by issue type (optional)
        status: Filter by status (optional)
        assignee: Filter by assignee (optional)
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        List of matching Jira tickets
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured. Please check environment variables.")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Build JQL query
        jql_parts = []
        
        # Add text search
        if query:
            jql_parts.append(f'text ~ "{query}"')
        
        # Add project filter
        if project_key:
            jql_parts.append(f'project = {project_key}')
        
        # Add issue type filter
        if issue_type:
            jql_parts.append(f'issuetype = "{issue_type}"')
        
        # Add status filter
        if status:
            jql_parts.append(f'status = "{status}"')
        
        # Add assignee filter
        if assignee:
            jql_parts.append(f'assignee = {assignee}')
        
        # Combine all parts
        jql = ' AND '.join(jql_parts) if jql_parts else 'ORDER BY created DESC'
        
        # Search for issues
        issues = jira.search_issues(jql, maxResults=max_results)
        
        # Convert to result objects
        results = []
        for issue in issues:
            results.append(JiraTicketSearchResult(
                key=issue.key,
                summary=issue.fields.summary,
                status=issue.fields.status.name,
                issue_type=issue.fields.issuetype.name,
                priority=issue.fields.priority.name,
                assignee=issue.fields.assignee.name if issue.fields.assignee else None,
                created=issue.fields.created,
                updated=issue.fields.updated,
                url=f"{jira_url}/browse/{issue.key}"
            ))
        
        return results
        
    except Exception as e:
        raise Exception(f"Failed to search Jira tickets: {str(e)}")
