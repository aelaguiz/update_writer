import logging
from src.lib import lib_docdb
from src.lib import lib_logging
import pprint
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
import argparse

# lib_logging.setup_logging()


# lib_logging.set_console_logging_level(logging.ERROR)
# logger = lib_logging.get_logger(logging.ERROR)

def print_doc(page_content, metadata):
    if metadata.get('type') == 'email':
        print_email_doc(page_content, metadata)
    elif metadata.get('type') == 'tweet':
        print_email_doc(page_content, metadata)
    elif metadata.get('type') == 'slack':
        print_slack_doc(page_content, metadata)

def print_slack_doc(page_content, metadata):
    # Extracting metadata
    channel = metadata.get('channel', 'N/A')
    timestamp = metadata.get('timestamp', 'N/A')
    user = metadata.get('user', 'N/A')
    avatar_hash = metadata.get('avatar_hash', 'N/A')
    image_72 = metadata.get('image_72', 'N/A')
    first_name = metadata.get('first_name', 'N/A')
    real_name = metadata.get('real_name', 'N/A')
    display_name = metadata.get('display_name', 'N/A')
    team = metadata.get('team', 'N/A')
    name = metadata.get('name', 'N/A')
    is_restricted = metadata.get('is_restricted', False)
    is_ultra_restricted = metadata.get('is_ultra_restricted', False)

    # Formatting and printing the slack document
    print("Slack Document Details")
    print("----------------------")
    print(f"Channel: {channel}")
    print(f"Timestamp: {timestamp}")
    print(f"User: {user}")
    print(f"Avatar Hash: {avatar_hash}")
    print(f"Image 72: {image_72}")
    print(f"First Name: {first_name}")
    print(f"Real Name: {real_name}")
    print(f"Display Name: {display_name}")
    print(f"Team: {team}")
    print(f"Name: {name}")
    print(f"Is Restricted: {is_restricted}")
    print(f"Is Ultra Restricted: {is_ultra_restricted}")
    print("\nContent:")
    print(page_content)
    print("----------------------")

def print_email_doc(page_content, metadata):
    # Extracting metadata
    email_id = metadata.get('email_id', 'N/A')
    from_address = metadata.get('from_address', 'N/A')
    subject = metadata.get('subject', 'N/A')
    thread_id = metadata.get('thread_id', 'N/A')
    to_address = metadata.get('to_address', 'N/A')

    # Formatting and printing the email document
    print("Email Document Details")
    print("----------------------")
    print(f"Email ID: {email_id}")
    print(f"Thread ID: {thread_id}")
    print(f"Subject: {subject}")
    print(f"From: {from_address}")
    print(f"To: {to_address}")
    print("\nContent:")
    print("----------------------")
    print(page_content)

def format_tweet_doc(doc):
    # Extracting metadata
    tweet_id = doc.metadata.get('tweet_id', 'N/A')
    tweet_text = doc.metadata.get('tweet_text', 'N/A')

    # Formatting the tweet document as a Markdown string
    tweet_details = []
    tweet_details.append("### Tweet\n")
    tweet_details.append(f"**Tweet ID:** {tweet_id}\n")
    tweet_details.append("\n**Content:**\n")
    tweet_details.append("```\n")
    tweet_details.append(tweet_text)
    tweet_details.append("```\n")

    return '\n'.join(tweet_details)

def print_tweet_doc(doc):
    print(format_tweet_doc(doc))

def process_command(input):
    print(f"Processing: {input}")
    db = lib_docdb.get_docdb()

    docs = db.similarity_search_with_relevance_scores(input, k=5)
    for doc, score in docs:
        print(f"**********DOC {score}**********")
        print(pprint.pformat(doc.metadata))
        print(f"{doc.page_content}")
        # print_doc(doc.page_content, doc.metadata)

    # res = chain.invoke(input, config={
    #     'callbacks': [lmd, oaid]
    # })

    # print(f"Result: '{res}'")
    # print(oaid)


def main():
    bindings = KeyBindings()

    while True:
        multiline = False

        while True:
            try:
                if not multiline:
                    # Single-line input mode
                    line = prompt('Enter text (""" for multiline, "quit" to exit, Ctrl-D to end): ', key_bindings=bindings)
                    if line.strip() == '"""':
                        multiline = True
                        continue
                    elif line.strip().lower() == 'quit':
                        return  # Exit the CLI
                    else:
                        process_command(line)
                        break
                else:
                    # Multiline input mode
                    line = prompt('... ', multiline=True, key_bindings=bindings)
                    process_command(line)
                    multiline = False
            except EOFError:
                return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())

main()