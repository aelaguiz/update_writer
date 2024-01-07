import sys
from ..lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level

from concurrent.futures import ThreadPoolExecutor, as_completed, wait



import json
import zipfile
import pprint
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from langchain_core.documents import Document
from .conversation_splitter import split_conversations, format_message_for_prompt
from typing import Dict, List, Optional
import hashlib
import logging

non_chat_subtypes = [
    "bot_message",
    "channel_join",
    "channel_leave",
    "channel_topic",
    "channel_purpose",
    "channel_name",
    "channel_archive",
    "channel_unarchive",
    "file_comment",
    "file_mention",
    "pinned_item",
    "unpinned_item",
    "me_message",
    "thread_broadcast",
    "reply_broadcast"
]

class SlackDirectoryLoader:
    """Load from a Slack directory dump."""

    def __init__(self, zip_path: str, workspace_url: Optional[str] = None):
        self.zip_path = Path(zip_path)
        self.workspace_url = workspace_url
        self.channel_id_map = self._get_channel_id_map(self.zip_path)

    @staticmethod
    def _get_channel_id_map(zip_path: Path) -> Dict[str, str]:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            with zip_file.open("channels.json", "r") as f:
                channels = json.load(f)
            return {channel["name"]: channel["id"] for channel in channels}

    def _get_message_metadata(self, message: dict, channel_name: str) -> dict:
        timestamp = message.get("ts", "")
        user = message.get("user", "")

        user_profile = message.get("user_profile", {})
        avatar_hash = user_profile.get("avatar_hash", "")
        image_72 = user_profile.get("image_72", "")
        first_name = user_profile.get("first_name", "")
        real_name = user_profile.get("real_name", "")
        display_name = user_profile.get("display_name", "")
        team = user_profile.get("team", "")
        name = user_profile.get("name", "")

        is_restricted = user_profile.get("is_restricted", False)
        is_ultra_restricted = user_profile.get("is_ultra_restricted", False)

        source = self._get_message_source(channel_name, user, timestamp)
        return {
            "source": source,
            "slack_id": message.get("client_msg_id", ""),
            "channel": channel_name,
            "timestamp": timestamp,
            "user": user,
            "avatar_hash": avatar_hash,
            "image_72": image_72,
            "first_name": first_name,
            "real_name": real_name,
            "display_name": display_name,
            "team": team,
            "name": name,
            "is_restricted": is_restricted,
            "is_ultra_restricted": is_ultra_restricted,
            'type': 'slack'
        }

    def _get_message_source(self, channel_name: str, user: str, timestamp: str) -> str:
        if self.workspace_url:
            channel_id = self.channel_id_map.get(channel_name, "")
            return f"{self.workspace_url}/archives/{channel_id}/p{timestamp.replace('.', '')}"
        else:
            return f"{channel_name} - {user} - {timestamp}"

    def load_messages(self, zip_file, channel_name) -> List[Dict]:
        logger = get_logger()
        messages = []

        # List all files in the channel directory
        channel_files = [f for f in zip_file.namelist() if f.startswith(f"{channel_name}/") and f.endswith(".json")]

        for channel_path in channel_files:
            with zip_file.open(channel_path, "r") as f:
                channel_name = Path(channel_path).parent.name
                channel_messages = json.load(f)
                for msg in channel_messages:
                    if msg.get('type') != "message":
                        # logger.info(f"Slack non-message: {pprint.pformat(msg)}")
                        continue
                    elif msg.get('type') == 'message':
                        if msg.get('subtype') in non_chat_subtypes:
                            # logger.info(f"Skipping message with subtype {msg.get('subtype')} - {pprint.pformat(msg)}")
                            continue

                    # logger.info(f"Slack message {msg.get('type')} and subtype {msg.get('subtype')}: {pprint.pformat(msg)}")
                    timestamp = datetime.fromtimestamp(float(msg['ts']))
                    metadata = self._get_message_metadata(msg, channel_name)
                    metadata['channel'] = channel_name  # Set channel name in metadata

                    new_message = {
                        "number": len(messages) + 1,
                        "timestamp": timestamp,
                        "user": metadata['real_name'],
                        "message": msg.get("text", "")
                    }
                    # logger.info(pprint.pformat(new_message))
                    messages.append(new_message)
        return messages

    def load(self) -> List[Document]:
        logger = logging.getLogger(__name__)
        with zipfile.ZipFile(self.zip_path, "r") as zip_file:
            channel_dirs = set(Path(f).parent.name for f in zip_file.namelist() if '/' in f and f.endswith(".json"))

            for channel_name in channel_dirs:
                messages = self.load_messages(zip_file, channel_name)
                logger.debug(f"Loaded {len(messages)} messages from #{channel_name}")

                conversations = split_conversations(messages=messages)
                for conversation in conversations:
                    logger.debug(conversation)
                    if not conversation['messages']:
                        logger.warning(f"Skipping conversation with no messages: {conversation}")
                        continue

                    timestamp = conversation['messages'][0]['timestamp'].strftime("%d/%m/%Y, %I:%M %p")
                    doc = Document(page_content="\n".join(format_message_for_prompt(c) for c in conversation['messages']), metadata={
                        "title": conversation['topic'],
                        "timestamp": timestamp,
                        "participants": conversation['participants'],
                        "type": "slack",
                        "source": f"#{channel_name}",
                        "filename": str(self.zip_path),
                        "author": json.dumps(conversation['participants'])
                    })

                    content_hash = hashlib.sha256(doc.page_content.encode()).hexdigest()
                    metadata_hash = hashlib.sha256(json.dumps(doc.metadata).encode()).hexdigest()
                    guid = f"{content_hash}-{metadata_hash}"
                    doc.metadata['guid'] = guid

                    yield doc