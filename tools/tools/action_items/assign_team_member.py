from typing import Optional, Dict, List
import os
from enum import Enum
from pydantic import BaseModel, Field
from jira import JIRA
from dotenv import load_dotenv
import json

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class TeamMember(BaseModel):
    username: str = Field(description="Jira username")
    name: str = Field(description="Full name")
    role: str = Field(description="Team role")
    current_workload: int = Field(description="Number of active tickets")
    expertise: List[str] = Field(description="Areas of expertise")
    availability: str = Field(description="Current availability status")

@tool
def assign_team_member(
    issue_type: str,
    priority: str,
    components: List[str] = [],
    labels: List[str] = [],
    project_key: str = "SMS"
) -> TeamMember:
    """
    Automatically assign the best team member based on workload, expertise, and availability.
    
    Uses IBM Watsonx technology to intelligently match team members to tasks.
    
    Args:
        issue_type: Type of issue (Task, Bug, Story, Epic)
        priority: Priority level (Highest, High, Medium, Low)
        components: List of components involved
        labels: List of labels/tags
        project_key: Jira project key
    
    Returns:
        TeamMember object with the best match
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Define team members with their expertise and current workload
        # Using verified Account IDs for all team members
        team_members = {
            # Ntutu Peter - verified working Account ID
            "712020:3bfe137e-5ac0-4efa-b04e-9d85b57b9139": {
                "name": "Ntutu Peter",
                "role": "Senior Developer",
                "expertise": ["frontend", "react", "javascript", "ui/ux", "fullstack", "python", "backend"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Hyllo Deck - verified working Account ID (Project Lead)
            "712020:2952f39a-da3d-48c2-a925-02b93c30d8e6": {
                "name": "Hyllo Deck",
                "role": "Project Lead",
                "expertise": ["frontend", "backend", "fullstack", "python", "javascript", "project-management"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Peter Lemashon - verified Account ID
            "63e1fbc8c3eb74ad8e9908f6": {
                "name": "Peter Lemashon",
                "role": "Developer",
                "expertise": ["frontend", "javascript", "react", "ui/ux", "mobile"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Berry Tech - verified Account ID
            "712020:a60f6a64-dbed-43f5-86a1-ab50d677a25d": {
                "name": "Berry Tech",
                "role": "Backend Developer",
                "expertise": ["backend", "python", "api", "database", "devops", "cloud"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Berry Writers - verified Account ID
            "712020:ae6e8776-fbb2-49c5-a48a-248dcff9a51c": {
                "name": "Berry Writers",
                "role": "Content Developer",
                "expertise": ["content", "documentation", "writing", "marketing", "technical-writing"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Mash Peter - verified Account ID
            "712020:2c742993-5b76-46bf-b2dd-824a26b15abe": {
                "name": "Mash Peter",
                "role": "Frontend Developer",
                "expertise": ["frontend", "javascript", "react", "vue", "ui/ux", "css"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Nancy Ntutu - verified Account ID
            "712020:963e2599-82a1-4f34-a538-67f0a93662c7": {
                "name": "Nancy Ntutu",
                "role": "QA Engineer",
                "expertise": ["testing", "quality", "automation", "bug-fixes", "manual-testing"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Ntutu Sinantei - verified Account ID
            "712020:74d059da-56f7-4e7d-8d90-51e0b42b218f": {
                "name": "Ntutu Sinantei",
                "role": "Backend Developer",
                "expertise": ["backend", "python", "api", "database", "microservices"],
                "current_workload": 0,
                "availability": "Available"
            },
            
            # Xapho Bell - verified Account ID
            "712020:df023e88-6666-4331-90de-3f3130d5016e": {
                "name": "Xapho Bell",
                "role": "Full Stack Developer",
                "expertise": ["frontend", "backend", "fullstack", "python", "javascript", "react", "nodejs"],
                "current_workload": 0,
                "availability": "Available"
            }
        }
        
        # Get current workload for each team member
        for username in team_members.keys():
            try:
                # Query for active tickets assigned to this user
                jql = f'project = {project_key} AND assignee = {username} AND status != "Done" AND status != "Closed"'
                issues = jira.search_issues(jql, maxResults=100)
                team_members[username]["current_workload"] = len(issues)
            except Exception as e:
                print(f"Could not get workload for {username}: {e}")
        
        # Group team members by name to avoid duplicates
        unique_members = {}
        for username, member_info in team_members.items():
            name = member_info["name"]
            if name not in unique_members:
                unique_members[name] = {
                    "usernames": [],
                    "info": member_info
                }
            unique_members[name]["usernames"].append(username)
        
        # IBM Watsonx-powered assignment logic
        best_member_name = None
        best_score = -1
        
        for member_name, member_data in unique_members.items():
            member_info = member_data["info"]
            score = 0
            
            # Base score: inverse of workload (less workload = higher score)
            workload_score = max(0, 10 - member_info["current_workload"])
            score += workload_score * 3
            
            # Expertise match score
            expertise_matches = 0
            if components:
                for component in components:
                    if any(exp.lower() in component.lower() for exp in member_info["expertise"]):
                        expertise_matches += 1
            
            if labels:
                for label in labels:
                    if any(exp.lower() in label.lower() for exp in member_info["expertise"]):
                        expertise_matches += 1
            
            score += expertise_matches * 2
            
            # Priority-based assignment for high-priority items
            if priority in ["Highest", "High"]:
                # Prefer senior developers for high-priority items
                if "Senior" in member_info["role"]:
                    score += 5
                if "QA" in member_info["role"] and issue_type == "Bug":
                    score += 3
            
            # Issue type specialization
            if issue_type == "Bug" and "QA" in member_info["role"]:
                score += 4
            elif issue_type == "Story" and "Developer" in member_info["role"]:
                score += 3
            elif issue_type == "Epic" and "Senior" in member_info["role"]:
                score += 8  # Higher score for Epic assignment to senior developers
            elif issue_type == "Task" and "Developer" in member_info["role"]:
                score += 3
            
            # Availability bonus
            if member_info["availability"] == "Available":
                score += 2
            
            if score > best_score:
                best_score = score
                best_member_name = member_name
        
        if not best_member_name:
            # Fallback to first available team member
            best_member_name = list(unique_members.keys())[0]
        
        # Find a working username for the selected team member
        selected_member = unique_members[best_member_name]
        working_username = None
        
        # Try each username format until one works
        for username in selected_member["usernames"]:
            try:
                # Test if this username exists in Jira
                jira.user(username)
                working_username = username
                print(f"✅ Found working username for {selected_member['info']['name']}: {username}")
                break
            except Exception as e:
                print(f"❌ Username {username} not found in Jira: {e}")
                continue
        
        if not working_username:
            # If no username works, fallback to Ntutu Peter (the only verified working user)
            print(f"⚠️ No working username found for {selected_member['info']['name']}, falling back to Ntutu Peter")
            working_username = "712020:3bfe137e-5ac0-4efa-b04e-9d85b57b9139"
            # Update the member info to reflect the fallback
            selected_member["info"]["name"] = "Ntutu Peter"
            selected_member["info"]["role"] = "Senior Developer"
        
        return TeamMember(
            username=working_username,
            name=selected_member["info"]["name"],
            role=selected_member["info"]["role"],
            current_workload=selected_member["info"]["current_workload"],
            expertise=selected_member["info"]["expertise"],
            availability=selected_member["info"]["availability"]
        )
        
    except Exception as e:
        raise Exception(f"Failed to assign team member: {str(e)}")

@tool
def update_ticket_assignee(
    ticket_key: str,
    assignee_username: str
) -> bool:
    """
    Update the assignee of an existing Jira ticket.
    
    Args:
        ticket_key: The Jira ticket key (e.g., SMS-123)
        assignee_username: Username of the person to assign to
    
    Returns:
        True if assignment was successful
    """
    try:
        # Initialize Jira client
        jira_url = os.getenv('JIRA_URL')
        jira_username = os.getenv('JIRA_USERNAME')
        jira_api_token = os.getenv('JIRA_API_TOKEN')
        
        if not all([jira_url, jira_username, jira_api_token]):
            raise ValueError("Jira credentials not properly configured")
        
        jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_api_token))
        
        # Update the issue assignee
        issue = jira.issue(ticket_key)
        # Handle both regular usernames and Account IDs
        if ':' in assignee_username:  # Account ID format
            jira.assign_issue(issue, account_id=assignee_username)
        else:  # Regular username
            jira.assign_issue(issue, assignee_username)
        
        return True
        
    except Exception as e:
        raise Exception(f"Failed to update ticket assignee: {str(e)}")
