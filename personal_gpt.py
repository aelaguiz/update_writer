import argparse
import uuid
import os
from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from src.lib import lib_docdb, lib_logging, lc_logger
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory

from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.memory import ConversationSummaryMemory, ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.runnables import RunnableLambda

from prompt_toolkit.history import FileHistory
from langchain.retrievers import TimeWeightedVectorStoreRetriever



from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter
from src.util import doc_formatters
from src.util import prompts
import datetime

lib_logging.setup_logging()
logger = lib_logging.get_logger()

class EnhancedTimeWeightedRetriever(TimeWeightedVectorStoreRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _transform_document_dates(self, documents, current_time):
        # Transform the document dates as required

        for i, doc in enumerate(documents):
            if doc.metadata.get("type") == 'email':
                doc.metadata['created_at'] = doc.metadata.get('send_date')
                doc.metadata['last_access_date'] = doc.metadata.get('send_date')
            elif doc.metadata.get("source") == 'gdrive':
                doc.metadata['created_at'] = doc.metadata.get('created_time')
                doc.metadata['last_access_date'] = doc.metadata.get('modified_time')
            else:
                logger.error(f"Unknown document type: {doc.metadata.get('type')} {doc.metadata.get('source')}")
                assert(False)

            doc.metadata["buffer_idx"] = len(self.memory_stream) + i
            logger.debug(f"EnhancedTimeWeightedRetriever doc.metadata: {doc.metadata}")

        self.memory_stream.extend(documents)

            # doc.metadata['created_at'] = doc.metadata.get('created_at', current_time)
            # doc.metadata['last_accessed_at'] = current_time
        return documents

    def _get_relevant_documents(self, query, *, run_manager: CallbackManagerForRetrieverRun):
        logger.debug(f"EnhancedTimeWeightedRetriever query: {query} kwargs {self.search_kwargs}")
        # Get documents from the wrapped retriever
        docs = self.vectorstore.similarity_search(
            query, **self.search_kwargs
        )
        logger.debug(f"EnhancedTimeWeightedRetriever docs: {docs}")

        
        # Transform documents and set in memory_stream
        current_time = datetime.datetime.now()
        self._transform_document_dates(docs, current_time)

        # Call the parent method to proceed with the usual flow
        return super()._get_relevant_documents(query, run_manager=run_manager)


lmd = None
db = None
llm = None
retriever = None
chat_history = None
memory = None
conversation_file = None
time_weighted_retriever = None

def init(company):
    global lmd, db, llm, retriever, chat_history, memory, conversation_file, time_weighted_retriever

    lmd = lc_logger.LlmDebugHandler()  
    db = lib_docdb.get_docdb()
    llm = lib_docdb.get_llm()
    retriever = db.as_retriever()

    time_weighted_retriever = EnhancedTimeWeightedRetriever(
        vectorstore=db, decay_rate=0.0000000000000000000000001, k=3
    )

    chat_history = ChatMessageHistory()
    memory = ConversationBufferMemory(chat_memory=chat_history, input_key="input", memory_key="history", return_messages=True)

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

    conversation_file = os.path.join("conversations", conversation_file_name)
    os.makedirs(os.path.dirname(conversation_file), exist_ok=True)

    with open(conversation_file, "w") as file:
        file.write(conversation_header)

    print(f"Conversation will be saved in: {conversation_file}")

def save_conversation(input_text, memory_text):
    with open(conversation_file, "a") as file:
        file.write(f"User: {input_text}\n\nAI: {memory_text}\n\n---------------------------------------------------\n\n")

def show_obj(input_obj):
    # print("\n\n")
    # print("OBJ: ", input_obj)
    # print("\n\n")

    return input_obj

def create_chain(prompt_template, input_obj):
    loaded_memory = RunnablePassthrough.assign(history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"))

    return (
        loaded_memory
        | input_obj 
        | show_obj
        | prompt_template
        | llm 
        | StrOutputParser()
    )

def initialize_spinner():
    return Halo(text='Thinking...', spinner='dots')

def process_input(input):
    personal_gpt_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(prompts.personal_gpt_prompt),
        HumanMessagePromptTemplate.from_template("{input}")
    ])

    def _compose_retriever_input(input, history):
        ret_input = "\n".join(h.content for h in history)  + "\n\n" + input + "\n\n"
        print(f"Retriever input: {ret_input}")

        return ret_input


    def compose_retriever_input(_dict):
        return _compose_retriever_input(_dict["input"], _dict["history"])

    retriever

    chain = create_chain(

        personal_gpt_prompt, 
        {
            # "emails": itemgetter("history")  | retriever | doc_formatters.retriever_format_docs,
            "input": lambda x: x['input'],
            "history": lambda x: x['history'],
            "emails": {"input": itemgetter("input"), "history": itemgetter("history")} | RunnableLambda(compose_retriever_input) | time_weighted_retriever | doc_formatters.retriever_format_docs,
        }
    )
    spinner = initialize_spinner()

    spinner.start()
    res = chain.invoke({
        'input': input,
    }, config={'callbacks': [lmd]})
    spinner.stop()

    # fmted_prompt = personal_gpt_prompt.format(**{
    #     "emails": doc_formatters.retriever_format_docs(retriever.get_relevant_documents(input)),
    #     "history": memory.load_memory_variables(None)["history"]
    # })
    # print(fmted_prompt)
    memory.save_context({"input": input}, {"history": res})

    save_conversation(input, res)
    print(f"AI: {res}\n\n")

def main():
    bindings = KeyBindings()
    history = FileHistory('./gpt_prompt_history.txt')  # specify the path to your history file


    print('quit to exit, Ctrl-D to end, """ for multiline')
    while True:
        try:
            line = prompt('How can I help? ', key_bindings=bindings, history=history).strip()
            if line == '"""':
                line = prompt('... ', multiline=True, key_bindings=bindings, history=history).strip()
            if line.lower() == 'quit':
                return
            process_input(line)
        except EOFError:
            return
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Your personal business advisor.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    init(args.company)
    main()
    print(f"Reminder: Your conversation has been saved in {conversation_file}")