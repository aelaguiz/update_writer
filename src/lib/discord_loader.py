import re
from typing import List, Dict
from datetime import datetime
from langchain.document_loaders import UnstructuredFileLoader
import json
from langchain_core.documents import Document

import ai.lib.conversation_splitter

import logging
import hashlib
import traceback

class DiscordChatLoader(UnstructuredFileLoader):
    def __init__(self, file_path):
        super().__init__(file_path)

    def load_messages(self) -> List[Dict]:
        logger = logging.getLogger(__name__)
        # Open the file
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()

        logger.info(f"Loading file {self.file_path}")

        # Define a regular expression to match the Discord chat structure
        pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2})\] (.*?): (.*)')

        current_msg = None
        message_number = 1

        for line in content:
            match = pattern.match(line)
            if match:
                # If there's a current message being built, add it to messages
                if current_msg:
                    yield current_msg
                    message_number += 1

                timestamp_str, user, message = match.groups()
                parsed_timestamp = datetime.fromisoformat(timestamp_str)
                current_msg = {
                    "number": message_number,
                    "timestamp": parsed_timestamp,
                    "user": user,
                    "message": message
                }
            elif current_msg:
                # If the line doesn't match and there's a current message, append the line to the current message
                current_msg["message"] += "\n" + line.strip()
            else:
                print(f"Failed to match line: {line}")
                raise Exception(f"Failed to match line: {line}")

        # Add the last message if there is one
        if current_msg:
            current_msg["number"] = message_number
            yield current_msg




    def load(self) -> List[Document]:

        logger = logging.getLogger(__name__)
        
        messages = self.load_messages()
        logger.debug(f"Loaded {len(messages)} messages")
        # try:
        #     logger.debug(f"Loaded {len(messages)} messages")
        #     return ai.lib.conversation_splitter.split_conversations(messages=messages)
        # except Exception as e:
        #     logger.error(f"Failed to split conversations: {traceback.format_exc()}")
        conversations = ai.lib.conversation_splitter.split_conversations(messages=messages)
        for conversation in conversations:
            logger.debug(conversation)
            if not conversation['messages']:
                logger.warning(f"Skipping conversation with no messages: {conversation}")
                continue

            timestamp = conversation['messages'][0]['timestamp'].strftime("%d/%m/%Y, %I:%M %p")

            doc = Document(page_content="\n".join(ai.lib.conversation_splitter.format_message_for_prompt(c) for c in conversation['messages']), metadata={
                "title": conversation['topic'],
                "timestamp": timestamp,
                "participants": conversation['participants'],
                "type": "discord",
                "source": f"Discord Chat Export {self.file_path}",
                "filename": self.file_path,
                "author": json.dumps(conversation['participants'])
            })

            content_hash = hashlib.sha256(doc.page_content.encode()).hexdigest()
            metadata_hash = hashlib.sha256(json.dumps(doc.metadata).encode()).hexdigest()
            guid = f"{content_hash}-{metadata_hash}"
            doc.metadata['guid'] = guid
            # docs.append(doc)
            yield doc