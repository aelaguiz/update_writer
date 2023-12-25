import logging
from src.lib import lib_twitterdb
from src.lib import lib_logging
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

# lib_logging.setup_logging()


# lib_logging.set_console_logging_level(logging.ERROR)
# logger = lib_logging.get_logger(logging.ERROR)

lib_twitterdb.set_company_environment('TWITTER')
db = lib_twitterdb.get_docdb()
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

    docs = db.similarity_search(input, k=5)
    for doc in docs:
        print_tweet_doc(doc)

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
