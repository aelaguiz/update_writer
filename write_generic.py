import argparse
import uuid
import os
from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from src.lib import lib_docdb, lib_logging, lc_logger
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter
from src.util import doc_formatters
from src.util import prompts

lib_logging.setup_logging()
logger = lib_logging.get_logger()

lmd = None
db = None
llm = None
retriever = None
chat_history = None
memory = None
conversation_file = None

def init(company):
    global lmd, db, llm, retriever, chat_history, memory, conversation_file

    lmd = lc_logger.LlmDebugHandler()  
    db = lib_docdb.get_docdb()
    llm = lib_docdb.get_llm()
    retriever = db.as_retriever()
    chat_history = ChatMessageHistory()
    memory = ConversationBufferMemory(chat_memory=chat_history, input_key="input", output_key="output", return_messages=True)

    # Unique file name for conversation history
    conversation_file_name = f"conversation_{company}_{uuid.uuid4()}.txt"
    conversation_file = os.path.join("conversations", conversation_file_name)
    os.makedirs(os.path.dirname(conversation_file), exist_ok=True)
    print(f"Conversation will be saved in: {conversation_file}")

def save_conversation(input_text, output_text):
    with open(conversation_file, "a") as file:
        file.write(f"User: {input_text}\n\nAI: {output_text}\n\n---------------------------------------------------")

def create_chain(prompt_template, input_obj):
    loaded_memory = RunnablePassthrough.assign(history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"))

    return (
        loaded_memory
        | input_obj 
        | prompt_template
        | llm 
        | StrOutputParser()
    )

def initialize_spinner():
    return Halo(text='Thinking...', spinner='dots')

def write_message(message_type, notes):
    write_prompt = ChatPromptTemplate.from_template(prompts.write_generic_message_prompt)
    chain = create_chain(
        write_prompt, 
        {
            "emails": itemgetter("notes")  | retriever | doc_formatters.retriever_format_docs,
            "message_type": lambda x: x['message_type'],
            "notes": lambda x: x['notes'],
            "history": lambda x: x['history']
        }
    )
    spinner = initialize_spinner()

    spinner.start()
    res = chain.invoke({'message_type': message_type, 'notes': notes}, config={'callbacks': [lmd]})
    spinner.stop()

    fmted_prompt = write_prompt.format(**{
        "emails": doc_formatters.retriever_format_docs(retriever.get_relevant_documents(notes)),
        "message_type": message_type,
        "notes": notes,
        "history": memory.load_memory_variables(None)["history"]
    })
    print(fmted_prompt)
    memory.save_context({"input": fmted_prompt}, {"output": res})
    save_conversation(fmted_prompt, res)

    print(f"AI: {res}")

def refine_message(feedback):
    refine_prompts = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(prompts.refine_generic_message_prompt), 
        MessagesPlaceholder(variable_name="history"), 
        HumanMessagePromptTemplate.from_template("{feedback}")])  # Simplified for brevity

    chain = create_chain(
        refine_prompts,
        {
            "history": lambda x: x['history'],
            "feedback": lambda x: x['feedback']
        }
    )
    spinner = initialize_spinner()

    spinner.start()
    res = chain.invoke({'feedback': feedback}, config={'callbacks': [lmd]})
    spinner.stop()

    fmted_prompt = refine_prompts.format(**{
        "history": memory.load_memory_variables(None)["history"],
        "feedback": feedback
    })
    memory.save_context({"input": fmted_prompt}, {"output": res})
    save_conversation(fmted_prompt, res)

    print(f"AI: {res}")

def main():
    bindings = KeyBindings()
    print('quit to exit, Ctrl-D to end, """ for multiline')
    message_type = prompt('What are you writing? ', key_bindings=bindings).strip()
    if message_type.lower() == 'quit':
        return
    notes = prompt('Provide any notes or context: ', multiline=True, key_bindings=bindings).strip()
    write_message(message_type, notes)

    while True:
        try:
            line = prompt('What is your feedback? ', key_bindings=bindings).strip()
            if line == '"""':
                line = prompt('... ', multiline=True, key_bindings=bindings).strip()
            if line.lower() == 'quit':
                return
            refine_message(line)
        except EOFError:
            return
            
if __name__ == "__main__":
    print(f"DID YOU UPDATE THE EMAIL DB?")
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    init(args.company)
    main()
    print(f"Reminder: Your conversation has been saved in {conversation_file}")
