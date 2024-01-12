from src.lib import lib_docdb, lib_logging, lc_logger
from langchain import hub
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder, PromptTemplate
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
import argparse

lib_logging.setup_logging()
logger = lib_logging.get_logger()

agent_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate(prompt=PromptTemplate(input_variables=[], template="""You are an AI assistant designed to provide high-level support to a CEO with extensive expertise and a top-secret clearance. Your task is to understand and assist in achieving specific business and personal objectives, utilizing various tools and capabilities at your disposal.

**Your Goals:**
1. **Clarify and Achieve Objectives:** Accurately understand the user's goals and business needs. If unclear, ask questions to clarify. Then, actively work towards achieving these objectives.
2. **Document and Email Analysis:** When directed, locate specific documents or emails. Otherwise, use judgment to decide if and which documents to reference for a task.
3. **Autonomous Decision-Making:** Operate with the discretion expected of a high-functioning executive assistant. Make independent decisions within this scope but seek confirmation in situations of uncertainty or significant impact.

**Guidelines on How to Work:**
1. **Concise Communication:** Keep all responses short, direct, and free from unnecessary detail.
2. **Handling Ambiguity:** In cases of ambiguity, promptly seek clarification from the user.
3. **Confidentiality and Trust:** Maintain the highest level of confidentiality with all information, respecting the trust granted by the user.
4. **Conversation History Utilization:** Leverage past conversations to enhance understanding of current context and requirements.
                                                      
**Chat History:**""")), 
    MessagesPlaceholder(variable_name='chat_history'),
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
    MessagesPlaceholder(variable_name='agent_scratchpad')
])


from langchain.agents import AgentExecutor

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.tools.retriever import create_retriever_tool



from langchain.agents import OpenAIFunctionsAgent

lmd = lc_logger.LlmDebugHandler()  


def process_command(agent, input):
    res = agent.invoke(
        {"input": input},
        config={"configurable": {"session_id": "<foo>", 'callbacks': [lmd]}}
    )
    print(res['output'])

def main():
    llm = lib_docdb.get_llm()

    doc_db = lib_docdb.get_docdb()
    retriever = doc_db.as_retriever()

    retriever_tool = create_retriever_tool(
        retriever,
        "doc_search",
        "Search company documents",
    )



    tools = [retriever_tool]
    agent = OpenAIFunctionsAgent(
        llm= llm,
        prompt= agent_prompt,
        tools=tools
    )
    message_history = ChatMessageHistory()
    agent_executor = AgentExecutor(agent=agent, tools=tools, callbacks=[lmd])

    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        # This is needed because in most real world scenarios, a session id is needed
        # It isn't really used here because we are using a simple in memory ChatMessageHistory
        lambda session_id: message_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
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
                        process_command(agent_with_chat_history, line)
                        break
                else:
                    # Multiline input mode
                    line = prompt('... ', multiline=True, key_bindings=bindings)
                    process_command(agent_with_chat_history, line)
                    multiline = False
            except EOFError:
                return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    args = parser.parse_args()

    lib_docdb.set_company_environment(args.company.upper())


    main()