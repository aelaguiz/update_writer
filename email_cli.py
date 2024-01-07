import logging
from src.lib import lib_docdb
from src.lib import lib_logging
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

# lib_logging.setup_logging()


# lib_logging.set_console_logging_level(logging.ERROR)
# logger = lib_logging.get_logger(logging.ERROR)

db = lib_docdb.get_docdb()

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


def process_command(input):
    print(f"Processing: {input}")

    docs = db.similarity_search(input, k=5)
    for doc in docs:
        print_email_doc(doc.page_content, doc.metadata)

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
    main()
