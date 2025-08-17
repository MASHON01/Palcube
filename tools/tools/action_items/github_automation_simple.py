#!/usr/bin/env python3
"""
GitHub Automation Tool - Simplified Version
Automatically creates GitHub repositories with proper branch structure
"""

import os
import requests
import json
import subprocess
import tempfile
import shutil
import re
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class GitHubRepo(BaseModel):
    name: str = Field(description="Repository name")
    description: str = Field(description="Repository description")
    url: str = Field(description="GitHub repository URL")
    branches: List[str] = Field(description="List of created branches")
    default_branch: str = Field(description="Default branch name")

def _generate_repo_name(task_title: str) -> str:
    """Generate a valid GitHub repository name from task title"""
    # Remove special characters and convert to lowercase
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', task_title.lower())
    # Replace spaces with hyphens
    name = re.sub(r'\s+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    # Limit length
    if len(name) > 50:
        name = name[:50].rstrip('-')
    # Ensure it starts with a letter
    if name and not name[0].isalpha():
        name = 'repo-' + name
    return name or 'new-project'

def _create_github_repo(token: str, owner: str, name: str, description: str, private: bool = True) -> Dict:
    """Create a GitHub repository using the GitHub API"""
    # Always create user repository for now (can be extended for organizations later)
    url = "https://api.github.com/user/repos"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": True,
        "gitignore_template": "Python"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create GitHub repository: {response.status_code} - {response.text}")

def _clone_repository(clone_url: str, local_path: str, token: str):
    """Clone the repository to a local directory"""
    # Replace https:// with https://token@ for authentication
    auth_url = clone_url.replace("https://", f"https://{token}@")
    
    try:
        subprocess.run(
            ["git", "clone", auth_url, local_path],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to clone repository: {e.stderr}")

def _create_branch_structure(local_path: str, project_type: str, use_ibm_watsonx: bool) -> List[str]:
    """Create branch structure for the project"""
    branches = ["main", "develop"]
    
    # Create develop branch
    try:
        subprocess.run(
            ["git", "checkout", "-b", "develop"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create feature branch
        subprocess.run(
            ["git", "checkout", "-b", "feature/initial-setup"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        branches.append("feature/initial-setup")
        
        # Switch back to main
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not create branches: {e}")
    
    return branches

def _create_ibm_watsonx_integration(local_path: str, task_title: str, task_description: str):
    """Create IBM Watsonx integration files"""
    # Create README with IBM Watsonx integration info
    readme_content = f"""# {task_title}

{task_description}

## IBM Watsonx Integration

This project is set up with IBM Watsonx integration capabilities.

### Features
- AI-powered code generation
- Intelligent project structure
- Automated testing with AI assistance
- Smart documentation generation

### Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Set up IBM Watsonx credentials
3. Run the application: `python main.py`

### IBM Watsonx Configuration
Add your IBM Watsonx credentials to `.env`:
```
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
```
"""
    
    with open(os.path.join(local_path, "README.md"), "w") as f:
        f.write(readme_content)

def _create_project_files(local_path: str, project_type: str, task_title: str, task_description: str):
    """Create project-specific files"""
    # Create requirements.txt
    requirements_content = """# Core dependencies
python-dotenv==1.0.0
requests==2.31.0
pydantic==2.5.0

# IBM Watsonx Integration
ibm-watsonx-orchestrate

# Development
pytest==7.4.3
black==23.0.0
flake8==6.0.0
"""
    
    with open(os.path.join(local_path, "requirements.txt"), "w") as f:
        f.write(requirements_content)
    
    # Create main.py
    main_content = f'''#!/usr/bin/env python3
"""
{task_title}

{task_description}
"""

import os
from dotenv import load_dotenv

def main():
    """Main application entry point"""
    load_dotenv()
    print("Application started successfully!")
    print("IBM Watsonx integration ready.")

if __name__ == "__main__":
    main()
'''
    
    with open(os.path.join(local_path, "main.py"), "w") as f:
        f.write(main_content)
    
    # Create .env.example
    env_content = """# IBM Watsonx Configuration
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
"""
    
    with open(os.path.join(local_path, ".env.example"), "w") as f:
        f.write(env_content)

def _push_changes(local_path: str, clone_url: str, token: str):
    """Push all changes to the repository"""
    try:
        # Configure git
        subprocess.run(
            ["git", "config", "user.name", "Action Agent"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "config", "user.email", "action-agent@example.com"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Add all files
        subprocess.run(
            ["git", "add", "."],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Commit changes
        subprocess.run(
            ["git", "commit", "-m", "Initial setup with IBM Watsonx integration"],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Push all branches
        auth_url = clone_url.replace("https://", f"https://{token}@")
        subprocess.run(
            ["git", "push", "--all", auth_url],
            cwd=local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to push changes: {e.stderr}")

def create_github_repository_for_task(
    task_title: str,
    task_description: str,
    project_type: str = "web-application",
    team_members: List[str] = [],
    use_ibm_watsonx: bool = True,
    organization: Optional[str] = None
) -> GitHubRepo:
    """
    Automatically create a GitHub repository for a specific task with IBM Watsonx integration.
    
    Args:
        task_title: Title of the task (used to generate repo name)
        task_description: Detailed description of the task
        project_type: Type of project (web-application, api, mobile-app, data-science, etc.)
        team_members: List of team member usernames to add as collaborators
        use_ibm_watsonx: Whether to include IBM Watsonx integration features
        organization: GitHub organization name (optional)
    
    Returns:
        GitHubRepo object with repository details
    """
    try:
        # Get GitHub credentials
        github_token = os.getenv('GITHUB_TOKEN')
        github_username = os.getenv('GITHUB_USERNAME')
        
        if not github_token:
            raise ValueError("GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
        
        # Generate repository name from task title
        repo_name = _generate_repo_name(task_title)
        
        # Determine repository owner
        owner = organization if organization else github_username
        
        # Create repository using GitHub API
        repo_data = _create_github_repo(
            token=github_token,
            owner=owner,
            name=repo_name,
            description=task_description,
            private=True  # Start as private for security
        )
        
        # Clone repository locally for setup
        temp_dir = tempfile.mkdtemp()
        try:
            _clone_repository(repo_data['clone_url'], temp_dir, github_token)
            
            # Create branch structure based on project type
            branches = _create_branch_structure(temp_dir, project_type, use_ibm_watsonx)
            
            # Create IBM Watsonx integration files if requested
            if use_ibm_watsonx:
                _create_ibm_watsonx_integration(temp_dir, task_title, task_description)
            
            # Create project-specific files
            _create_project_files(temp_dir, project_type, task_title, task_description)
            
            # Push all changes
            _push_changes(temp_dir, repo_data['clone_url'], github_token)
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return GitHubRepo(
            name=repo_data['name'],
            description=repo_data['description'],
            url=repo_data['html_url'],
            branches=branches,
            default_branch=repo_data['default_branch']
        )
        
    except Exception as e:
        raise Exception(f"Failed to create GitHub repository: {str(e)}")
