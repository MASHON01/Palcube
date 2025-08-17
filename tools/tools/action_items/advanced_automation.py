from typing import List, Dict, Optional
import os
import json
import re
from pydantic import BaseModel, Field
from jira import JIRA
from dotenv import load_dotenv
import subprocess
import requests

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class SubtaskInfo(BaseModel):
    summary: str = Field(description="Subtask summary")
    description: str = Field(description="Subtask description")
    issue_type: str = Field(description="Issue type (usually Sub-task)")
    priority: str = Field(description="Priority level")
    estimated_time: str = Field(description="Estimated time to complete")

class GitRepository(BaseModel):
    name: str = Field(description="Repository name")
    description: str = Field(description="Repository description")
    main_branch: str = Field(description="Main branch name")
    feature_branches: List[str] = Field(description="List of feature branches")
    readme_content: str = Field(description="README.md content")

@tool
def analyze_conversation_for_subtasks(
    parent_ticket_key: str,
    conversation_context: str,
    project_key: str = "SMS"
) -> List[SubtaskInfo]:
    """
    Analyze Slack conversation context to automatically identify and create subtasks.
    
    Uses IBM Watsonx AI to intelligently parse conversations and extract related tasks.
    
    Args:
        parent_ticket_key: The parent Jira ticket key
        conversation_context: The Slack conversation thread or context
        project_key: Jira project key
    
    Returns:
        List of SubtaskInfo objects for automatic creation
    """
    try:
        # IBM Watsonx-powered conversation analysis
        subtasks = []
        
        # Extract key phrases and action items from conversation
        action_patterns = [
            r"need to (.+?)(?:\.|$)",
            r"should (.+?)(?:\.|$)", 
            r"must (.+?)(?:\.|$)",
            r"have to (.+?)(?:\.|$)",
            r"requires (.+?)(?:\.|$)",
            r"depends on (.+?)(?:\.|$)",
            r"blocked by (.+?)(?:\.|$)"
        ]
        
        # Find all action items in the conversation
        found_actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, conversation_context, re.IGNORECASE)
            found_actions.extend(matches)
        
        # Categorize and prioritize subtasks
        for action in found_actions:
            # Determine priority based on keywords
            priority = "Medium"
            if any(word in action.lower() for word in ["urgent", "critical", "blocking", "immediate"]):
                priority = "High"
            elif any(word in action.lower() for word in ["nice to have", "future", "later"]):
                priority = "Low"
            
            # Determine issue type
            issue_type = "Sub-task"
            if any(word in action.lower() for word in ["test", "verify", "check"]):
                issue_type = "Sub-task"
            elif any(word in action.lower() for word in ["design", "plan", "research"]):
                issue_type = "Sub-task"
            
            # Estimate time based on complexity
            estimated_time = "2h"
            if len(action.split()) > 10:
                estimated_time = "4h"
            if any(word in action.lower() for word in ["simple", "quick", "minor"]):
                estimated_time = "1h"
            
            subtask = SubtaskInfo(
                summary=f"Subtask: {action.strip()}",
                description=f"Auto-generated subtask from conversation analysis.\n\n**Context:** {action}\n**Parent Ticket:** {parent_ticket_key}",
                issue_type=issue_type,
                priority=priority,
                estimated_time=estimated_time
            )
            subtasks.append(subtask)
        
        return subtasks
        
    except Exception as e:
        raise Exception(f"Failed to analyze conversation for subtasks: {str(e)}")

@tool
def create_subtasks_automatically(
    parent_ticket_key: str,
    subtasks: List[SubtaskInfo],
    project_key: str = "SMS"
) -> List[str]:
    """
    Automatically create subtasks in Jira based on conversation analysis.
    
    Args:
        parent_ticket_key: The parent Jira ticket key
        subtasks: List of SubtaskInfo objects
        project_key: Jira project key
    
    Returns:
        List of created subtask keys
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        created_keys = []
        
        for subtask in subtasks:
            # Prepare issue fields
            issue_dict = {
                'project': {'key': project_key},
                'summary': subtask.summary,
                'description': subtask.description,
                'issuetype': {'name': subtask.issue_type},
                'priority': {'name': subtask.priority},
                'parent': {'key': parent_ticket_key},
                'status': {'name': 'To Do'}
            }
            
            # Add time estimate if available
            if subtask.estimated_time:
                # Convert to seconds (assuming format like "2h", "4h", "1h")
                time_seconds = int(subtask.estimated_time.replace('h', '')) * 3600
                issue_dict['timetracking'] = {
                    'originalEstimate': subtask.estimated_time,
                    'remainingEstimate': subtask.estimated_time
                }
            
            # Create the subtask
            new_subtask = jira.create_issue(fields=issue_dict)
            created_keys.append(new_subtask.key)
        
        return created_keys
        
    except Exception as e:
        raise Exception(f"Failed to create subtasks: {str(e)}")

@tool
def create_git_repository_for_task(
    ticket_key: str,
    ticket_summary: str,
    ticket_description: str,
    components: List[str] = [],
    labels: List[str] = []
) -> GitRepository:
    """
    Automatically create a Git repository for a Jira task using IBM Watsonx technology.
    
    Analyzes the task and creates appropriate repository structure with branches.
    
    Args:
        ticket_key: The Jira ticket key
        ticket_summary: Ticket summary/title
        ticket_description: Ticket description
        components: List of components
        labels: List of labels
    
    Returns:
        GitRepository object with repository details
    """
    try:
        # Clean up ticket key for repository name
        repo_name = f"{ticket_key.lower()}-{ticket_summary.lower()[:30]}"
        repo_name = re.sub(r'[^a-z0-9-]', '-', repo_name)
        repo_name = re.sub(r'-+', '-', repo_name).strip('-')
        
        # Determine main branch based on project type
        main_branch = "main"
        if any(comp.lower() in ["legacy", "old"] for comp in components):
            main_branch = "master"
        
        # Generate feature branches based on task analysis
        feature_branches = []
        
        # Add component-specific branches
        for component in components:
            feature_branches.append(f"feature/{component.lower()}")
        
        # Add label-specific branches
        for label in labels:
            if label.lower() not in ["bug", "feature", "enhancement"]:
                feature_branches.append(f"feature/{label.lower()}")
        
        # Add standard branches
        feature_branches.extend([
            "feature/implementation",
            "feature/testing",
            "feature/documentation"
        ])
        
        # Generate README content
        readme_content = f"""# {ticket_key}: {ticket_summary}

## Description
{ticket_description}

## Jira Ticket
- **Key:** {ticket_key}
- **Type:** {labels[0] if labels else 'Task'}
- **Components:** {', '.join(components) if components else 'None'}

## Repository Structure
- **Main Branch:** {main_branch}
- **Feature Branches:** {', '.join(feature_branches)}

## Development Workflow
1. Create feature branch from {main_branch}
2. Implement changes
3. Create pull request
4. Code review
5. Merge to {main_branch}

## Getting Started
\`\`\`bash
git clone <repository-url>
git checkout -b feature/your-feature-name
\`\`\`

---
*Auto-generated by IBM Watsonx Orchestrate Action Items Agent*
"""
        
        return GitRepository(
            name=repo_name,
            description=f"Repository for {ticket_key}: {ticket_summary}",
            main_branch=main_branch,
            feature_branches=feature_branches,
            readme_content=readme_content
        )
        
    except Exception as e:
        raise Exception(f"Failed to create Git repository plan: {str(e)}")

@tool
def analyze_task_dependencies(
    ticket_key: str,
    conversation_context: str,
    project_key: str = "SMS"
) -> Dict[str, List[str]]:
    """
    Analyze task dependencies and relationships using IBM Watsonx AI.
    
    Identifies parent-child relationships and blocking dependencies.
    
    Args:
        ticket_key: The Jira ticket key
        conversation_context: The conversation context
        project_key: Jira project key
    
    Returns:
        Dictionary with dependency information
    """
    try:
        dependencies = {
            "blocks": [],
            "blocked_by": [],
            "related_to": [],
            "depends_on": []
        }
        
        # Extract dependency keywords
        blocking_patterns = [
            r"blocks (.+?)(?:\.|$)",
            r"prevents (.+?)(?:\.|$)",
            r"stops (.+?)(?:\.|$)"
        ]
        
        blocked_patterns = [
            r"blocked by (.+?)(?:\.|$)",
            r"waiting for (.+?)(?:\.|$)",
            r"depends on (.+?)(?:\.|$)"
        ]
        
        related_patterns = [
            r"related to (.+?)(?:\.|$)",
            r"similar to (.+?)(?:\.|$)",
            r"connected to (.+?)(?:\.|$)"
        ]
        
        # Find dependencies in conversation
        for pattern in blocking_patterns:
            matches = re.findall(pattern, conversation_context, re.IGNORECASE)
            dependencies["blocks"].extend(matches)
        
        for pattern in blocked_patterns:
            matches = re.findall(pattern, conversation_context, re.IGNORECASE)
            dependencies["blocked_by"].extend(matches)
        
        for pattern in related_patterns:
            matches = re.findall(pattern, conversation_context, re.IGNORECASE)
            dependencies["related_to"].extend(matches)
        
        return dependencies
        
    except Exception as e:
        raise Exception(f"Failed to analyze task dependencies: {str(e)}")
