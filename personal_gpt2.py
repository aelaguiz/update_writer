import argparse
import uuid
import os
from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from src.lib import lib_docdb, lib_logging, lc_logger, lib_retrievers, lib_tools
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationBufferWindowMemory, ConversationBufferMemory

from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.memory import ConversationSummaryMemory, ChatMessageHistory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.runnables import RunnableLambda

from prompt_toolkit.history import FileHistory
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from typing import Any, Dict, List, Optional, Tuple

from langchain.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain.agents import AgentExecutor

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools.retriever import create_retriever_tool



from langchain.agents import OpenAIFunctionsAgent



from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from operator import itemgetter
from src.util import doc_formatters
from src.util import prompts
from src.lib import lib_conversation
import datetime
import dateutil

lib_logging.setup_logging()
logger = lib_logging.get_logger()


lmd = None
db = None
llm = None
retriever = None
chat_history = None
memory = None
conversation_file = None
tw_retriever = None
main_agent = None

agent_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=[], template=prompts.personal_gpt_agent_prompt)), 
    MessagesPlaceholder(variable_name='chat_history'),
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
    MessagesPlaceholder(variable_name='agent_scratchpad')
])

def init(company):
    global lmd, db, llm, retriever, chat_history, memory, conversation_file, tw_retriever, main_agent

    lmd = lc_logger.LlmDebugHandler()  
    db = lib_docdb.get_docdb()
    llm = lib_docdb.get_smart_llm()

    chat_history = ChatMessageHistory()
    memory = ConversationBufferMemory(chat_memory=chat_history, input_key="input", memory_key="history", return_messages=True)

    gdrive_tool = lib_tools.create_retriever_tool(
        lib_retrievers.get_self_query(llm, db, "Company google drige docs", 5, "gdrive"),
        "doc_search",
        "Search company google drive documents",
    )
    email_tool = lib_tools.create_retriever_tool(
        lib_retrievers.get_self_query(llm, db, "Company e-mails", 5, "gmail"),
        "email_search",
        "Search company emails",
    )
    book_tool = lib_tools.create_retriever_tool(
        lib_retrievers.get_retriever(db, 10, source_filter="epub"),
        "book_search",
        "Search books",
    )

    tools = [book_tool, gdrive_tool, email_tool, lib_tools.save_gdoc_tool, lib_tools.update_gdoc_tool, lib_tools.change_title_gdoc_tool]
    agent = OpenAIFunctionsAgent(
        llm= llm,
        prompt= agent_prompt,
        tools=tools
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, callbacks=[lmd])

    main_agent = RunnableWithMessageHistory(
        agent_executor,
        # This is needed because in most real world scenarios, a session id is needed
        # It isn't really used here because we are using a simple in memory ChatMessageHistory
        lambda session_id: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    lib_conversation.init_conversation(company)

def show_obj(input_obj):
    # print("\n\n")
    # print("OBJ: ", input_obj)
    # print("\n\n")

    return input_obj

def initialize_spinner():
    return Halo(text='Thinking...', spinner='dots')

def process_input(input):
    lib_conversation.save_message(input, "HUMAN")

    spinner = initialize_spinner()

    spinner.start()

    res = main_agent.invoke(
        {"input": input},
        config={"configurable": {"session_id": "<foo>"}, 'callbacks': [lmd]}
    )

    spinner.stop()
    output = res['output']

    # # fmted_prompt = personal_gpt_prompt.format(**{
    # #     "emails": doc_formatters.retriever_format_docs(retriever.get_relevant_documents(input)),
    # #     "history": memory.load_memory_variables(None)["history"]
    # # })
    # # print(fmted_prompt)
    # memory.save_context({"input": input}, {"history": res})

    print(f"AI: {output}\n\n")
    lib_conversation.save_message(output, "AI")

def main():
    bindings = KeyBindings()
    history = FileHistory('./gpt_prompt_history.txt')  # specify the path to your history file


    print('quit to exit, Ctrl-D to end, """ for multiline')
    print("AI: How can I help?")
    while True:
        try:
            line = prompt('HUMAN: ', key_bindings=bindings, history=history).strip()
            if line == '"""':
                line = prompt('... ', multiline=True, key_bindings=bindings, history=history).strip()
            if line.lower() == 'quit':
                return
            process_input(line)
        except EOFError:
            return
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Your personal business advisor.')
    parser.add_argument('company', choices=['cj', 'fc', 'mb'], help='Specify the company environment ("cj" or "fc" or "mb").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())
    lib_tools.set_company_environment(args.company.upper())
    init(args.company)
    main()