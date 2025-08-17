from typing import Optional, List
import os
from pydantic import BaseModel, Field
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

load_dotenv()

class SlackMessageResponse(BaseModel):
    success: bool = Field(description="Whether the message was sent successfully")
    channel: str = Field(description="The channel where the message was sent")
    message_ts: Optional[str] = Field(None, description="The timestamp of the sent message")
    error: Optional[str] = Field(None, description="Error message if sending failed")

@tool
def send_slack_message(
    channel: str,
    message: str,
    thread_ts: Optional[str] = None,
    attachments: Optional[List[dict]] = None
) -> SlackMessageResponse:
    """
    Send a message to a Slack channel or thread.
    
    Args:
        channel: The Slack channel ID or name (e.g., #general, C1234567890)
        message: The message text to send
        thread_ts: The timestamp of the parent message to reply in a thread (optional)
        attachments: List of attachment objects for rich formatting (optional)
    
    Returns:
        SlackMessageResponse object with the result of the operation
    """
    try:
        # Initialize Slack client
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        
        if not slack_token:
            raise ValueError("Slack bot token not properly configured. Please check SLACK_BOT_TOKEN environment variable.")
        
        client = WebClient(token=slack_token)
        
        # Prepare message parameters
        message_params = {
            'channel': channel,
            'text': message
        }
        
        if thread_ts:
            message_params['thread_ts'] = thread_ts
            
        if attachments:
            message_params['attachments'] = attachments
        
        # Send the message
        response = client.chat_postMessage(**message_params)
        
        return SlackMessageResponse(
            success=True,
            channel=channel,
            message_ts=response['ts'],
            error=None
        )
        
    except SlackApiError as e:
        return SlackMessageResponse(
            success=False,
            channel=channel,
            message_ts=None,
            error=f"Slack API error: {e.response['error']}"
        )
    except Exception as e:
        return SlackMessageResponse(
            success=False,
            channel=channel,
            message_ts=None,
            error=f"Failed to send Slack message: {str(e)}"
        )
