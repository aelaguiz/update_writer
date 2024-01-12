import datetime
import os

_conversation_file = None
_conversation = []

def init_conversation(company):
    global _conversation_file

    # Get current date and format it
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation_header = f"New Conversation {current_date}"

    # Find the next available file number
    num = 1
    conversation_file_name = f"conversation_{company}_{num}.txt"
    conversation_file = os.path.join("conversations", conversation_file_name)
    while os.path.exists(conversation_file):
        num += 1
        conversation_file_name = f"conversation_{company}_{num}.txt"
        conversation_file = os.path.join("conversations", conversation_file_name)

    _conversation_file = os.path.join("conversations", conversation_file_name)
    os.makedirs(os.path.dirname(_conversation_file), exist_ok=True)

    with open(_conversation_file, "w") as file:
        file.write(conversation_header)

    print(f"Conversation will be saved in: {_conversation_file}")

    return _conversation_file

def save_message(message, message_type):
    global _conversation_file
    global _conversation

    if not _conversation_file:
        raise Exception("Conversation file not initialized")

    fmted_msg = f"{message_type}: {message}\n\n"
    _conversation.append(fmted_msg)

    with open(_conversation_file, "a") as file:
        file.write(f"{fmted_msg}\n\n")


def save_conversation(input_text, memory_text):
    global _conversation_file

    if not _conversation_file:
        raise Exception("Conversation file not initialized")

    with open(_conversation_file, "a") as file:
        file.write(f"User: {input_text}\n\nAI: {memory_text}\n\n---------------------------------------------------\n\n")

def get_conversation():
    global _conversation
    return _conversation