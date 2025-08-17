#!/usr/bin/env python3
"""
Standalone Slack Event Listener for Intelligent Action Items Agent

This script runs independently to listen for Slack events and trigger the agent.
"""

import os
import asyncio
import logging
import subprocess
import json
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackEventListener:
    def __init__(self):
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.slack_app_token = os.getenv('SLACK_APP_TOKEN')
        
        if not all([self.slack_bot_token, self.slack_app_token]):
            raise ValueError("Slack credentials not properly configured")
        
        self.web_client = WebClient(token=self.slack_bot_token)
        self.socket_client = SocketModeClient(
            app_token=self.slack_app_token,
            web_client=self.web_client
        )
        
        # Track processed messages to prevent duplicates
        self.processed_messages = set()
        
        # Trigger keywords for action items
        self.trigger_keywords = [
            "bug", "issue", "problem", "error", "broken", "fix", "feature", 
            "request", "task", "todo", "action", "ticket", "jira", "urgent",
            "critical", "blocker", "help", "support", "review", "pr", "pull request"
        ]
    
    def should_process_message(self, event_data):
        """Determine if a message should trigger the agent"""
        event = event_data.get("event", {})
        
        # Only process message events
        if event.get("type") != "message":
            return False
        
        # Ignore bot messages to prevent loops
        if event.get("bot_id") or event.get("user", "").startswith('B'):
            logger.info(f"Ignoring bot message from {event.get('user')}")
            return False
        
        # Ignore messages from our own bot and other bots
        if event.get("user") == "U09ADLT6360" or event.get("bot_id"):  # Your bot's user ID
            logger.info(f"Ignoring bot message from {event.get('user')}")
            return False
        
        # Check for duplicate messages
        message_id = event.get("client_msg_id") or event.get("ts")
        if message_id in self.processed_messages:
            logger.info(f"Message already processed: {message_id}")
            return False
        
        # Check for @Action Agent mention specifically
        text = event.get("text", "")
        logger.info(f"Processing text: {text}")
        
        # Check for bot mention in various formats
        has_mention = (
            "@Action Agent" in text or 
            "<@U09ADLT6360>" in text or
            "U09ADLT6360" in text
        )
        
        if not has_mention:
            logger.info(f"No @Action Agent mention found in message")
            return False
        
        # Also check for trigger keywords to ensure it's an action item
        text_lower = text.lower()
        logger.info(f"Checking trigger keywords in: {text_lower}")
        
        # More lenient trigger detection - check for any action-related words
        trigger_keywords = [
            "bug", "issue", "problem", "error", "broken", "fix", "feature", 
            "request", "task", "todo", "action", "ticket", "jira", "urgent",
            "critical", "blocker", "help", "support", "review", "pr", "pull request",
            "create", "new", "build", "develop", "implement", "add", "update"
        ]
        
        has_trigger = any(keyword in text_lower for keyword in trigger_keywords)
        logger.info(f"Trigger keywords found: {[kw for kw in trigger_keywords if kw in text_lower]}")
        
        if not has_trigger:
            logger.info(f"No trigger keywords found in message")
            return False
        
        # Mark message as processed
        self.processed_messages.add(message_id)
        
        return True
    
    def call_orchestrate_agent(self, message_text: str):
        """Call the Watsonx Orchestrate agent using CLI"""
        try:
            # First, try to activate local environment
            subprocess.run(["orchestrate", "env", "activate", "local"], 
                         capture_output=True, check=False)
            
            # Call the agent with the message - fixed command syntax
            result = subprocess.run([
                "orchestrate", "chat", "action_items_agent", message_text
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Agent call failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Agent call timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling agent: {e}")
            return None
    
    def create_jira_ticket_and_repository(self, message_text: str, user: str):
        """Create Jira ticket and GitHub repository directly"""
        try:
            logger.info("Starting Jira ticket and GitHub repository creation...")
            from jira import JIRA
            import re
            
            # Extract project key from JIRA_URL
            jira_url = os.getenv('JIRA_URL')
            logger.info(f"Jira URL: {jira_url}")
            
            project_key = re.search(r'https://([^.]+)\.atlassian\.net', jira_url)
            if project_key:
                project_key = project_key.group(1).upper()
            else:
                project_key = "PROJ"  # Default project key
            
            logger.info(f"Using project key: {project_key}")
            
            # Connect to Jira
            logger.info("Connecting to Jira...")
            jira = JIRA(
                server=jira_url,
                basic_auth=(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_API_TOKEN'))
            )
            logger.info("Successfully connected to Jira")
            
            # Get available projects
            projects = jira.projects()
            logger.info(f"Available projects: {[p.key for p in projects]}")
            
            # Check if our project key exists
            project_exists = any(p.key == project_key for p in projects)
            if not project_exists:
                logger.warning(f"Project {project_key} not found, using first available project")
                if projects:
                    project_key = projects[0].key
                    logger.info(f"Using project: {project_key}")
                else:
                    logger.error("No projects available")
                    return None
            
            # Determine issue type based on keywords
            text_lower = message_text.lower()
            if any(word in text_lower for word in ['bug', 'error', 'broken', 'fix']):
                issue_type = 'Bug'
            elif any(word in text_lower for word in ['feature', 'request', 'enhancement']):
                issue_type = 'Story'
            else:
                issue_type = 'Task'
            
            logger.info(f"Using issue type: {issue_type}")
            
            # Get available issue types for the project
            project = jira.project(project_key)
            issue_types = project.issueTypes
            logger.info(f"Available issue types: {[it.name for it in issue_types]}")
            
            # Check if our issue type exists
            issue_type_exists = any(it.name == issue_type for it in issue_types)
            if not issue_type_exists:
                logger.warning(f"Issue type {issue_type} not found, using first available")
                if issue_types:
                    issue_type = issue_types[0].name
                    logger.info(f"Using issue type: {issue_type}")
                else:
                    logger.error("No issue types available")
                    return None
            
            # Create the issue
            issue_dict = {
                'project': {'key': project_key},
                'summary': f"Action Item: {message_text[:50]}...",
                'description': f"""
*Slack Message:* {message_text}
*Reported by:* {user}
*Source:* Slack Integration
                """.strip(),
                'issuetype': {'name': issue_type},
            }
            
            logger.info(f"Creating issue with data: {issue_dict}")
            new_issue = jira.create_issue(fields=issue_dict)
            logger.info(f"Successfully created issue: {new_issue.key}")
            
            # Refresh the issue to get all fields
            new_issue = jira.issue(new_issue.key)
            
            # Check if we should create a GitHub repository - more comprehensive detection
            repo_trigger_keywords = [
                'repository', 'repo', 'github', 'code', 'project', 'app', 'application',
                'website', 'api', 'service', 'feature', 'new', 'create', 'build', 'develop',
                'dashboard', 'system', 'platform', 'tool', 'module', 'component'
            ]
            
            should_create_repo = any(word in text_lower for word in repo_trigger_keywords)
            logger.info(f"Repository trigger keywords found: {[kw for kw in repo_trigger_keywords if kw in text_lower]}")
            logger.info(f"Should create repository: {should_create_repo}")
            
            repo_info = None
            if should_create_repo:
                logger.info("Creating GitHub repository...")
                try:
                    import sys
                    # Add the tools directory to the path - use absolute path
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    tools_path = os.path.join(current_dir, 'tools', 'tools', 'action_items')
                    if tools_path not in sys.path:
                        sys.path.insert(0, tools_path)
                    
                    logger.info(f"Added tools path: {tools_path}")
                    logger.info(f"Current sys.path: {sys.path[:3]}")  # Show first 3 paths
                    
                    from github_automation_simple import create_github_repository_for_task
                    
                    # Determine project type based on keywords
                    project_type = "web-application"  # default
                    if any(word in text_lower for word in ['api', 'service', 'backend']):
                        project_type = "api-service"
                    elif any(word in text_lower for word in ['mobile', 'app', 'ios', 'android']):
                        project_type = "mobile-app"
                    elif any(word in text_lower for word in ['data', 'ml', 'ai', 'machine learning']):
                        project_type = "data-science"
                    
                    repo = create_github_repository_for_task(
                        task_title=f"{new_issue.key}: {new_issue.fields.summary}",
                        task_description=f"Repository created automatically from Slack message via Jira ticket {new_issue.key}. Original message: {message_text}",
                        project_type=project_type,
                        team_members=[],
                        use_ibm_watsonx=True,
                        organization=None
                    )
                    
                    repo_info = {
                        'name': repo.name,
                        'url': repo.url,
                        'branches': repo.branches
                    }
                    
                    logger.info(f"Successfully created GitHub repository: {repo.name}")
                    
                    # Update Jira ticket with GitHub repository link
                    try:
                        updated_description = f"""
*Slack Message:* {message_text}
*Reported by:* {user}
*Source:* Slack Integration

*GitHub Repository:* {repo.url}
*Repository Name:* {repo.name}
*Branches:* {', '.join(repo.branches)}

This ticket has an associated GitHub repository with IBM Watsonx integration.
                        """.strip()
                        
                        new_issue.update(fields={'description': updated_description})
                        logger.info(f"Updated Jira ticket {new_issue.key} with GitHub repository link")
                        
                    except Exception as e:
                        logger.error(f"Error updating Jira ticket with GitHub link: {e}")
                    
                except Exception as e:
                    logger.error(f"Error creating GitHub repository: {e}")
                    repo_info = None
            
            return {
                'key': new_issue.key,
                'url': f"{jira_url}/browse/{new_issue.key}",
                'summary': new_issue.fields.summary,
                'repository': repo_info
            }
            
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    async def process_message_with_agent(self, event_data):
        """Process message using the Watsonx Orchestrate agent"""
        try:
            event = event_data.get("event", {})
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text")
            ts = event.get("ts")
            
            logger.info(f"Processing message from {user} in {channel}: {text}")
            
            # Send initial acknowledgment
            self.web_client.chat_postMessage(
                channel=channel,
                text="🤖 Processing your message and creating a Jira ticket and GitHub repository...",
                thread_ts=ts
            )
            
            # Try to call the agent first
            agent_response = self.call_orchestrate_agent(text)
            
            if agent_response:
                # Agent worked, send the response
                response_text = f"✅ {agent_response}"
            else:
                # Fallback: create ticket and repository directly
                logger.info("Agent call failed, creating ticket and repository directly...")
                ticket_info = self.create_jira_ticket_and_repository(text, user)
                
                if ticket_info:
                    response_text = f"""
✅ **Jira Ticket Created!**

📋 **Ticket:** {ticket_info['key']}
🔗 **Link:** {ticket_info['url']}
📝 **Summary:** {ticket_info['summary']}

Your action item has been automatically created in Jira!
                    """.strip()
                    
                    # Add repository information if created
                    if ticket_info.get('repository'):
                        repo = ticket_info['repository']
                        response_text += f"""

🔗 **GitHub Repository Created!**

📦 **Repository:** {repo['name']}
🔗 **URL:** {repo['url']}
🌿 **Branches:** {', '.join(repo['branches'])}

Your GitHub repository is ready for development with IBM Watsonx integration!
                    """
                else:
                    response_text = "❌ Sorry, I couldn't create a Jira ticket at the moment. Please try again later."
            
            # Send response back to Slack
            self.web_client.chat_postMessage(
                channel=channel,
                text=response_text,
                thread_ts=ts
            )
            
            logger.info(f"Sent response to {channel}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Send error response
            try:
                self.web_client.chat_postMessage(
                    channel=channel,
                    text="❌ Sorry, there was an error processing your message. Please try again.",
                    thread_ts=ts
                )
            except:
                pass
    
    def handle_socket_mode_request(self, client: SocketModeClient, req: SocketModeRequest):
        """Handle incoming Socket Mode requests"""
        try:
            logger.info(f"Received request type: {req.type}")
            
            # Check if this is an event we should process
            if req.type == "events_api":
                event_data = req.payload
                logger.info(f"Event payload: {json.dumps(event_data, indent=2)}")
                
                if self.should_process_message(event_data):
                    logger.info(f"✅ Triggered by message: {event_data.get('event', {}).get('text', '')}")
                    # Process the message synchronously to avoid async issues
                    self.process_message_sync(event_data)
                else:
                    logger.info(f"❌ Ignoring message (no triggers): {event_data.get('event', {}).get('text', '')}")
            else:
                logger.info(f"Received non-events_api request: {req.type}")
                
            # Always acknowledge the event
            client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
            
        except Exception as e:
            logger.error(f"Error handling socket mode request: {e}")
            # Still acknowledge to prevent retries
            client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
    
    def process_message_sync(self, event_data):
        """Process message synchronously (non-async version)"""
        try:
            event = event_data.get("event", {})
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text")
            ts = event.get("ts")
            
            logger.info(f"Processing message from {user} in {channel}: {text}")
            
            # Send initial acknowledgment
            self.web_client.chat_postMessage(
                channel=channel,
                text="🤖 Processing your message and creating a Jira ticket and GitHub repository...",
                thread_ts=ts
            )
            
            # Try to call the agent first
            agent_response = self.call_orchestrate_agent(text)
            
            if agent_response:
                # Agent worked, send the response
                response_text = f"✅ {agent_response}"
            else:
                # Fallback: create ticket and repository directly
                logger.info("Agent call failed, creating ticket and repository directly...")
                ticket_info = self.create_jira_ticket_and_repository(text, user)
                
                if ticket_info:
                    response_text = f"""
✅ **Jira Ticket Created!**

📋 **Ticket:** {ticket_info['key']}
🔗 **Link:** {ticket_info['url']}
📝 **Summary:** {ticket_info['summary']}

Your action item has been automatically created in Jira!
                    """.strip()
                    
                    # Add repository information if created
                    if ticket_info.get('repository'):
                        repo = ticket_info['repository']
                        response_text += f"""

🔗 **GitHub Repository Created!**

📦 **Repository:** {repo['name']}
🔗 **URL:** {repo['url']}
🌿 **Branches:** {', '.join(repo['branches'])}

Your GitHub repository is ready for development with IBM Watsonx integration!
                    """
                else:
                    response_text = "❌ Sorry, I couldn't create a Jira ticket at the moment. Please try again later."
            
            # Send response back to Slack
            self.web_client.chat_postMessage(
                channel=channel,
                text=response_text,
                thread_ts=ts
            )
            
            logger.info(f"Sent response to {channel}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Send error response
            try:
                self.web_client.chat_postMessage(
                    channel=channel,
                    text="❌ Sorry, there was an error processing your message. Please try again.",
                    thread_ts=ts
                )
            except:
                pass
    
    def start(self):
        """Start the Slack event listener"""
        logger.info("Starting Slack Event Listener...")
        
        # Set up event handler
        self.socket_client.socket_mode_request_listeners.append(self.handle_socket_mode_request)
        
        # Connect and start listening
        self.socket_client.connect()
        
        logger.info("Slack Event Listener is now running. Press Ctrl+C to stop.")
        
        try:
            # Keep the listener running
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("Shutting down Slack Event Listener...")
            self.socket_client.close()

def main():
    """Main function"""
    try:
        listener = SlackEventListener()
        listener.start()
    except Exception as e:
        logger.error(f"Failed to start listener: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
