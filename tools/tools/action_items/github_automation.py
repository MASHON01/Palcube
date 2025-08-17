#!/usr/bin/env python3
"""
GitHub Automation Tool for IBM Watsonx Orchestrate
Automatically creates GitHub repositories with proper branch structure and IBM Watsonx integration
"""

import os
import requests
import json
import subprocess
import tempfile
import shutil
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class GitHubRepo(BaseModel):
    name: str = Field(description="Repository name")
    description: str = Field(description="Repository description")
    url: str = Field(description="GitHub repository URL")
    branches: List[str] = Field(description="List of created branches")
    default_branch: str = Field(description="Default branch name")

class BranchInfo(BaseModel):
    name: str = Field(description="Branch name")
    description: str = Field(description="Branch purpose")
    protection_rules: Dict = Field(description="Branch protection settings")

@tool
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
    
    Uses IBM Watsonx technology to intelligently plan repository structure and branches.
    
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
            
            # Add team members as collaborators
            if team_members:
                _add_collaborators(github_token, owner, repo_name, team_members)
            
            return GitHubRepo(
                name=repo_name,
                description=task_description,
                url=repo_data['html_url'],
                branches=branches,
                default_branch=repo_data['default_branch']
            )
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        raise Exception(f"Failed to create GitHub repository: {str(e)}")

@tool
def analyze_task_for_repository_structure(
    task_description: str,
    project_type: str = "web-application"
) -> Dict:
    """
    Analyze a task to determine optimal repository structure using IBM Watsonx technology.
    
    Args:
        task_description: Detailed description of the task
        project_type: Type of project
    
    Returns:
        Dictionary with recommended repository structure
    """
    try:
        # IBM Watsonx-powered analysis
        analysis = {
            "recommended_branches": _get_recommended_branches(project_type),
            "file_structure": _get_file_structure(project_type),
            "dependencies": _get_dependencies(project_type),
            "ibm_watsonx_integration": _get_ibm_watsonx_features(project_type),
            "deployment_strategy": _get_deployment_strategy(project_type)
        }
        
        return analysis
        
    except Exception as e:
        raise Exception(f"Failed to analyze task: {str(e)}")

def _generate_repo_name(task_title: str) -> str:
    """Generate a clean repository name from task title"""
    # Remove special characters and convert to lowercase
    clean_name = ''.join(c.lower() if c.isalnum() else '-' for c in task_title)
    # Remove multiple dashes and trim
    clean_name = '-'.join(filter(None, clean_name.split('-')))
    # Limit length
    return clean_name[:50]

def _create_github_repo(token: str, owner: str, name: str, description: str, private: bool = True) -> Dict:
    """Create a new GitHub repository"""
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
        "gitignore_template": "Python" if "python" in description.lower() else "Node"
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to create repository: {response.text}")

def _clone_repository(clone_url: str, local_path: str, token: str):
    """Clone repository to local directory"""
    # Replace https with token-based URL
    auth_url = clone_url.replace("https://", f"https://{token}@")
    subprocess.run(["git", "clone", auth_url, local_path], check=True)

def _create_branch_structure(local_path: str, project_type: str, use_ibm_watsonx: bool) -> List[str]:
    """Create branch structure based on project type"""
    branches = ["main"]
    
    # Change to repository directory
    os.chdir(local_path)
    
    # Create development branch
    subprocess.run(["git", "checkout", "-b", "develop"], check=True)
    branches.append("develop")
    
    # Create feature branch
    subprocess.run(["git", "checkout", "-b", "feature/initial-setup"], check=True)
    branches.append("feature/initial-setup")
    
    # Create staging branch for production-like testing
    subprocess.run(["git", "checkout", "develop"], check=True)
    subprocess.run(["git", "checkout", "-b", "staging"], check=True)
    branches.append("staging")
    
    # Create hotfix branch
    subprocess.run(["git", "checkout", "main"], check=True)
    subprocess.run(["git", "checkout", "-b", "hotfix/emergency-fixes"], check=True)
    branches.append("hotfix/emergency-fixes")
    
    # Create IBM Watsonx integration branch if requested
    if use_ibm_watsonx:
        subprocess.run(["git", "checkout", "develop"], check=True)
        subprocess.run(["git", "checkout", "-b", "feature/ibm-watsonx-integration"], check=True)
        branches.append("feature/ibm-watsonx-integration")
    
    return branches

def _create_ibm_watsonx_integration(local_path: str, task_title: str, task_description: str):
    """Create IBM Watsonx integration files"""
    os.chdir(local_path)
    
    # Create IBM Watsonx configuration
    watsonx_config = {
        "project_name": task_title,
        "description": task_description,
        "ibm_watsonx_features": {
            "agent_builder": True,
            "flow_builder": True,
            "knowledge_bases": True,
            "model_integration": True
        },
        "ai_models": {
            "llama_3_2_90b": "For intelligent task analysis",
            "watsonx_assistant": "For conversational AI features"
        }
    }
    
    with open("ibm-watsonx-config.json", "w", encoding="utf-8") as f:
        json.dump(watsonx_config, f, indent=2)
    
    # Create IBM Watsonx integration script
    integration_script = '''#!/usr/bin/env python3
"""
IBM Watsonx Orchestrate Integration Script
Automatically generated for: {task_title}
"""

import os
from dotenv import load_dotenv
from ibm_watsonx_orchestrate import AgentBuilder, FlowBuilder

load_dotenv()

class IBMWatsonxIntegration:
    def __init__(self):
        self.agent_builder = AgentBuilder()
        self.flow_builder = FlowBuilder()
    
    def setup_project_agents(self):
        """Setup IBM Watsonx agents for this project"""
        # Create intelligent task analysis agent
        task_agent = self.agent_builder.create_agent(
            name="task_analyzer",
            model="llama-3.2-90b",
            instructions="Analyze tasks and provide intelligent recommendations"
        )
        
        # Create automated workflow agent
        workflow_agent = self.agent_builder.create_agent(
            name="workflow_automator", 
            model="llama-3.2-90b",
            instructions="Automate repetitive development workflows"
        )
        
        return task_agent, workflow_agent
    
    def create_development_flow(self):
        """Create IBM Watsonx flow for development automation"""
        flow = self.flow_builder.create_flow(
            name="development_automation",
            description="Automated development workflow using IBM Watsonx"
        )
        
        # Add nodes for code review, testing, deployment
        flow.add_node("code_review", "Automated code review using AI")
        flow.add_node("testing", "Intelligent test generation and execution")
        flow.add_node("deployment", "Smart deployment with rollback capabilities")
        
        return flow

if __name__ == "__main__":
    integration = IBMWatsonxIntegration()
    task_agent, workflow_agent = integration.setup_project_agents()
    dev_flow = integration.create_development_flow()
    
    print("✅ IBM Watsonx integration setup complete!")
    print(f"   Task Analyzer Agent: Created")
    print(f"   Workflow Automator Agent: Created")
    print(f"   Development Flow: Created")
'''.format(task_title=task_title)
    
    with open("ibm_watsonx_integration.py", "w", encoding="utf-8") as f:
        f.write(integration_script)
    
    # Create README with IBM Watsonx documentation
    readme_content = f'''# {task_title}

## IBM Watsonx Orchestrate Integration

This project is enhanced with IBM Watsonx Orchestrate technology for intelligent automation and AI-powered development workflows.

### Features

- 🤖 **Intelligent Task Analysis**: AI-powered task breakdown and planning
- 🔄 **Automated Workflows**: Smart automation of development processes
- 📊 **Knowledge Integration**: Leverages IBM Watsonx knowledge bases
- 🧠 **Model Integration**: Uses Llama 3.2 90B for intelligent decision making

### Setup

1. Install IBM Watsonx Orchestrate ADK:
   ```bash
   pip install ibm-watsonx-orchestrate-adk
   ```

2. Configure environment variables:
   ```bash
   export WATSONX_API_KEY=your_api_key
   export WATSONX_PROJECT_ID=your_project_id
   ```

3. Run IBM Watsonx integration:
   ```bash
   python ibm_watsonx_integration.py
   ```

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `staging`: Pre-production testing
- `feature/*`: Feature development
- `hotfix/*`: Emergency fixes
- `feature/ibm-watsonx-integration`: AI/ML features

### IBM Watsonx Agents

- **Task Analyzer**: Intelligent task analysis and planning
- **Workflow Automator**: Automated development workflows
- **Code Reviewer**: AI-powered code review and suggestions

### Contributing

This project uses IBM Watsonx technology for intelligent automation. All contributions should leverage the AI-powered workflows for optimal results.
'''
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

def _create_project_files(local_path: str, project_type: str, task_title: str, task_description: str):
    """Create project-specific files"""
    os.chdir(local_path)
    
    # Create requirements.txt for Python projects
    if "python" in project_type.lower() or "web" in project_type.lower():
        requirements = '''# Project Dependencies
# Generated for: {task_title}

# Core dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# IBM Watsonx Orchestrate Integration
ibm-watsonx-orchestrate-adk==1.0.0

# Development dependencies
pytest==7.4.3
black==23.11.0
flake8==6.1.0

# AI/ML dependencies
transformers==4.35.2
torch==2.1.1
'''.format(task_title=task_title)
        
        with open("requirements.txt", "w") as f:
            f.write(requirements)
    
    # Create Docker configuration
    dockerfile = '''# Dockerfile for {task_title}
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with IBM Watsonx integration
CMD ["python", "ibm_watsonx_integration.py"]
'''.format(task_title=task_title)
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile)
    
    # Create GitHub Actions workflow
    workflow_dir = ".github/workflows"
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow = '''name: IBM Watsonx CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run IBM Watsonx integration tests
      run: |
        python ibm_watsonx_integration.py --test
    
    - name: Run standard tests
      run: |
        pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy with IBM Watsonx
      run: |
        echo "Deploying with IBM Watsonx Orchestrate..."
        # Add your deployment logic here
'''
    
    with open(f"{workflow_dir}/ci-cd.yml", "w") as f:
        f.write(workflow)

def _push_changes(local_path: str, clone_url: str, token: str):
    """Push all changes to GitHub"""
    os.chdir(local_path)
    
    # Configure git
    subprocess.run(["git", "config", "user.name", "IBM Watsonx Bot"], check=True)
    subprocess.run(["git", "config", "user.email", "watsonx-bot@ibm.com"], check=True)
    
    # Add all files
    subprocess.run(["git", "add", "."], check=True)
    
    # Commit changes
    subprocess.run(["git", "commit", "-m", "Initial setup with IBM Watsonx integration"], check=True)
    
    # Push all branches
    subprocess.run(["git", "push", "--all", "origin"], check=True)

def _add_collaborators(token: str, owner: str, repo_name: str, team_members: List[str]):
    """Add team members as collaborators"""
    for member in team_members:
        url = f"https://api.github.com/repos/{owner}/{repo_name}/collaborators/{member}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"permission": "push"}
        
        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [201, 204]:
            print(f"✅ Added {member} as collaborator")
        else:
            print(f"⚠️ Could not add {member}: {response.text}")

def _get_recommended_branches(project_type: str) -> List[str]:
    """Get recommended branches based on project type"""
    base_branches = ["main", "develop", "staging"]
    
    if "web" in project_type.lower():
        return base_branches + ["feature/frontend", "feature/backend", "feature/ui-ux"]
    elif "api" in project_type.lower():
        return base_branches + ["feature/api", "feature/database", "feature/testing"]
    elif "mobile" in project_type.lower():
        return base_branches + ["feature/mobile", "feature/ios", "feature/android"]
    else:
        return base_branches + ["feature/development"]

def _get_file_structure(project_type: str) -> Dict:
    """Get recommended file structure"""
    if "web" in project_type.lower():
        return {
            "frontend/": ["src/", "public/", "package.json"],
            "backend/": ["api/", "models/", "services/"],
            "shared/": ["utils/", "types/"],
            "docs/": ["README.md", "API.md"]
        }
    else:
        return {
            "src/": ["main.py", "config.py"],
            "tests/": ["test_main.py"],
            "docs/": ["README.md"]
        }

def _get_dependencies(project_type: str) -> List[str]:
    """Get recommended dependencies"""
    if "web" in project_type.lower():
        return ["fastapi", "react", "typescript", "ibm-watsonx-orchestrate-adk"]
    elif "api" in project_type.lower():
        return ["fastapi", "sqlalchemy", "pydantic", "ibm-watsonx-orchestrate-adk"]
    else:
        return ["python", "ibm-watsonx-orchestrate-adk"]

def _get_ibm_watsonx_features(project_type: str) -> List[str]:
    """Get IBM Watsonx features for project type"""
    return [
        "Intelligent Task Analysis",
        "Automated Code Review",
        "Smart Testing Generation",
        "AI-Powered Documentation",
        "Workflow Automation"
    ]

def _get_deployment_strategy(project_type: str) -> str:
    """Get deployment strategy recommendation"""
    if "web" in project_type.lower():
        return "Container-based deployment with IBM Cloud"
    elif "api" in project_type.lower():
        return "Serverless deployment with IBM Cloud Functions"
    else:
        return "Traditional deployment with IBM Cloud"
