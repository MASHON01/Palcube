from typing import Optional, Dict, Any
import os
import json
import asyncio
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class SlackEvent(BaseModel):
    type: str = Field(description="Type of Slack event")
    channel: str = Field(description="Channel where the event occurred")
    user: str = Field(description="User who triggered the event")
    text: str = Field(description="Message text content")
    ts: str = Field(description="Timestamp of the event")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if in a thread")

class SlackEventHandler(BaseModel):
    success: bool = Field(description="Whether the event was processed successfully")
    action_taken: str = Field(description="Description of the action taken")
    agent_response: Optional[str] = Field(None, description="Response from the agent")

@tool
def process_slack_event(event_data: Dict[str, Any]) -> SlackEventHandler:
    """
    Process incoming Slack events and trigger the action items agent.
    
    Args:
        event_data: Raw Slack event data from the Events API
    
    Returns:
        SlackEventHandler object with processing results
    """
    try:
        # Parse the event
        event = SlackEvent(**event_data)
        
        # Only process message events (not reactions, etc.)
        if event.type != "message" or not event.text:
            return SlackEventHandler(
                success=False,
                action_taken="Ignored non-message event"
            )
        
        # Check if this is a bot message (ignore to prevent loops)
        if event.user.startswith('B'):
            return SlackEventHandler(
                success=False,
                action_taken="Ignored bot message"
            )
        
        # Check for trigger keywords or patterns
        trigger_keywords = [
            "bug", "issue", "problem", "error", "broken", "fix", "feature", 
            "request", "task", "todo", "action", "ticket", "jira"
        ]
        
        message_lower = event.text.lower()
        has_trigger = any(keyword in message_lower for keyword in trigger_keywords)
        
        if not has_trigger:
            return SlackEventHandler(
                success=False,
                action_taken="No action items detected in message"
            )
        
        # Here we would trigger the agent
        # For now, we'll simulate the agent call
        # In a real implementation, you would call the agent here
        
        return SlackEventHandler(
            success=True,
            action_taken=f"Processed message from {event.user} in {event.channel}",
            agent_response="Agent would analyze and create Jira ticket here"
        )
        
    except Exception as e:
        return SlackEventHandler(
            success=False,
            action_taken=f"Error processing event: {str(e)}"
        )

@tool
def start_slack_event_listener() -> str:
    """
    Start listening for Slack events using Socket Mode.
    
    Returns:
        Status message about the listener
    """
    try:
        # Get Slack credentials
        slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        slack_app_token = os.getenv('SLACK_APP_TOKEN')
        
        if not all([slack_bot_token, slack_app_token]):
            raise ValueError("Slack credentials not properly configured")
        
        # Initialize Socket Mode client
        client = SocketModeClient(
            app_token=slack_app_token,
            web_client=WebClient(token=slack_bot_token)
        )
        
        def process_event(client: SocketModeClient, req: SocketModeRequest):
            """Process incoming events"""
            try:
                # Parse the event
                event_data = req.payload.get("event", {})
                
                # Process the event
                result = process_slack_event(event_data)
                
                # Send response
                client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
                
                # Log the result
                print(f"Processed event: {result.action_taken}")
                
            except Exception as e:
                print(f"Error processing event: {e}")
                client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
        
        # Set up event handler
        client.socket_mode_request_listeners.append(process_event)
        
        # Start the client
        client.connect()
        
        return "Slack event listener started successfully"
        
    except Exception as e:
        return f"Failed to start Slack event listener: {str(e)}"
