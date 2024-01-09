import logging
from src.lib import lib_docdb
from src.lib import lib_logging
import argparse
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.lib.lc_logger import LlmDebugHandler
from operator import itemgetter
from src.util import doc_formatters

lib_logging.setup_logging()

# lib_logger.set_console_logging_level(logger.ERROR)
logger = lib_logging.get_logger()


def write_email(message_type, notes):
    lmd = LlmDebugHandler()
    db = lib_docdb.get_docdb()
    llm = lib_docdb.get_llm()
    retriever = db.as_retriever()

    print(f"Message type: {message_type} notes: {notes}")
    write_prompt = ChatPromptTemplate.from_template("""# Write a {message_type}

## Instructions
- Create a {message_type} focused on the provided content.
- Use a style and tone consistent with the medium of the {message_type}.
- Maintain a candid and casual tone, avoiding expressions of exaggerated enthusiasm (e.g., 'thrilled', 'excited').
- Minimize the use of exclamations.
- Avoid statements that imply grandiosity or hype, such as 'we're onto something big.'
- Do not include motivational or team-building statements, especially in the closing.
- Notes for content can be transcribed audio, a collection of random notes, or any combination thereof, not necessarily in a specific order.

## Section 1: Tone and Style Examples
{emails}

## Section 2: Content
{notes}
""")

    chain = (
        {
            "emails": itemgetter("notes")  | retriever | doc_formatters.retriever_format_docs,
            "message_type": lambda x: x['message_type'],
            "notes": lambda x: x['notes']
        }
        | write_prompt
        | llm 
        | StrOutputParser()
    )


    res = chain.invoke({
        'message_type': message_type,
        'notes': notes
    }, config={'callbacks': [lmd]})

    print(f"Result: '{res}'")


def main():
    bindings = KeyBindings()

    while True:
        try:
            message_type = prompt('What are you writing? ("quit" to exit, Ctrl-D to end): ', key_bindings=bindings)
            # Multiline input modkwe
            notes = prompt('Enter notes: ', multiline=True, key_bindings=bindings)
            write_email(message_type.strip(), notes.strip())
        except EOFError:
            return
            
if __name__ == "__main__":
    print(f"DID YOU UPDATE THE EMAIL DB?")
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    main()