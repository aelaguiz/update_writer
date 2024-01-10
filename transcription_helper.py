
import pprint
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
from langchain_core.runnables.history import RunnableWithMessageHistory
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
        file.write(f"{output_text}\n\n---------------------------------------------------")

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

chunk_size = 5000
def write_initial_memo(transcription_chunk):
    
    def _write_initial_memo(_transcription_chunk):
        write_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(prompts.transcription_initial_prompt),
            MessagesPlaceholder(variable_name='chat_history'),
            HumanMessagePromptTemplate.from_template("Transcript chunk: \"\"\"{transcription_chunk}\"\"\""),
        ])

        chain = create_chain(
            write_prompt, 
            {
                "transcription_chunk": lambda x: x['transcription_chunk'],
                "chat_history": lambda x: x['chat_history']
            }
        )
        spinner = initialize_spinner()

        spinner.start()
        chain_with_chat_history = RunnableWithMessageHistory(
            chain,
            # This is needed because in most real world scenarios, a session id is needed
            # It isn't really used here because we are using a simple in memory ChatMessageHistory
            lambda session_id: chat_history,
            input_messages_key="transcription_chunk",
            history_messages_key="chat_history",
        )
        res = chain_with_chat_history.invoke({
            'transcription_chunk': _transcription_chunk,
        }, config={'callbacks': [lmd], "configurable": {"session_id": "<foo>"}})
        spinner.stop()


        print(f"AI: {res}")
        save_conversation(transcription_chunk, res)

    chunks = [transcription_chunk[i:i+chunk_size] for i in range(0, len(transcription_chunk), chunk_size)]
    
    for idx, chunk in enumerate(chunks):
        if idx == 0:
            _write_initial_memo(chunk)
        else:
            refine(chunk)



def refine(feedback):
    def _refine(_feedback):
        refine_prompts = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(prompts.transcription_continuation_prompt),
            MessagesPlaceholder(variable_name='chat_history'),
            HumanMessagePromptTemplate.from_template("{feedback}"),
        ])

        chain = create_chain(
            refine_prompts,
            {
                "feedback": lambda x: x['feedback'],
                "chat_history": lambda x: x['chat_history']
            }
        )
        spinner = initialize_spinner()

        spinner.start()
        chain_with_chat_history = RunnableWithMessageHistory(
            chain,
            # This is needed because in most real world scenarios, a session id is needed
            # It isn't really used here because we are using a simple in memory ChatMessageHistory
            lambda session_id: chat_history,
            input_messages_key="feedback",
            history_messages_key="chat_history",
        )
        res = chain_with_chat_history.invoke({
            'feedback': _feedback,
        }, config={'callbacks': [lmd], "configurable": {"session_id": "<foo>"}})
        spinner.stop()


        print(f"AI: {res}")
        # print(pprint.pformat(chat_history.messages))

        save_conversation(feedback, res)

    chunks = [feedback[i:i+chunk_size] for i in range(0, len(feedback), chunk_size)]
    
    for chunk in chunks:
        _refine(chunk)


def main():
    bindings = KeyBindings()
    print("Welcome to the transcription helper!")
    print('quit to exit, Ctrl-D to end, Escape then Enter to submit')

    transcription_chunk = prompt('Paste in your transcript ', multiline=True, key_bindings=bindings).strip()
    write_initial_memo(transcription_chunk)

    while True:
        try:
            line = prompt('What is your feedback? (or """ to paste in more transcript, or summarize to summarize)', key_bindings=bindings).strip()
            line = line.strip()
            if line == '"""':
                line = prompt('... ', multiline=True, key_bindings=bindings).strip()
            if line.lower() == 'quit':
                return
            if line.lower() == 'summarize':
                summarize(line)
            else:
                refine(line)
        except EOFError:
            return
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    init(args.company)
    main()
    print(f"Reminder: Your conversation has been saved in {conversation_file}")
