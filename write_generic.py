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
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.prompts import MessagesPlaceholder

lib_logging.setup_logging()

# lib_logger.set_console_logging_level(logger.ERROR)
logger = lib_logging.get_logger()

lmd = None
db = None
llm = None
retriever = None
chat_history = None
memory = None

def init():
    global lmd
    global db
    global llm
    global retriever
    global chat_history
    global memory

    lmd = LlmDebugHandler()
    db = lib_docdb.get_docdb()
    llm = lib_docdb.get_llm()
    retriever = db.as_retriever()
    chat_history = ChatMessageHistory()
    memory = ConversationBufferMemory(chat_memory=chat_history, input_key="input", output_key="output", return_messages=True)

def write_message(message_type, notes):
    global lmd
    global db
    global llm
    global retriever
    global chat_history
    global memory

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
    loaded_memory = RunnablePassthrough.assign(
        history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
    )

    chain = (
        loaded_memory
        | {
            "emails": itemgetter("notes")  | retriever | doc_formatters.retriever_format_docs,
            "message_type": lambda x: x['message_type'],
            "notes": lambda x: x['notes'],
            "history": lambda x: x['history']
        }
        | write_prompt
        | llm 
        | StrOutputParser()
    )


    res = chain.invoke({
        'message_type': message_type,
        'notes': notes
    }, config={'callbacks': [lmd]})

    memory.save_context({
        "input": message_type + ": " + notes
    }, {"output": res})

    print(f"Result: '{res}'")

def refine_message(feedback):
    global lmd
    global db
    global llm
    global retriever
    global chat_history
    global memory

    refine_prompts = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("""
        You have composed a message based on user input and retrieved documents. The user has provided feedback on the previous message. Please refine the message based on the feedback.

        **History**"""),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{feedback}")
    ])


    loaded_memory = RunnablePassthrough.assign(
        history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
    )

    logger.debug(f"Refining message: {feedback} with memory {memory.chat_memory}")

    chain = (
        loaded_memory
        | {
            "history": lambda x: x['history'],
            "feedback": lambda x: x['feedback'],
        }
        | refine_prompts
        | llm 
        | StrOutputParser()
    )


    res = chain.invoke({
        'feedback': feedback
    }, config={'callbacks': [lmd]})

    memory.save_context({
        "input": f"Refine: {feedback}"
    }, {"output": res})

    print(f"Result: '{res}'")


def main():
    bindings = KeyBindings()

    message_type = prompt('What are you writing? ("quit" to exit, Ctrl-D to end): ', key_bindings=bindings)
    # Multiline input modkwe
    notes = prompt('Enter notes: ', multiline=True, key_bindings=bindings)
    write_message(message_type.strip(), notes.strip())

    while True:
        try:
            feedback = prompt('How should we refine this? ("quit" to exit, Ctrl-D to end): ', key_bindings=bindings)
            refine_message(feedback.strip())
        except EOFError:
            return
            
if __name__ == "__main__":
    print(f"DID YOU UPDATE THE EMAIL DB?")
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    init()
    main()