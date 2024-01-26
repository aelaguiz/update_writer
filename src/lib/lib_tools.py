from langchain.tools import BaseTool, StructuredTool, tool

from . import lib_gdrive
import datetime
from . import lib_tools
from . import lib_gdrive
from . import lib_conversation

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.retrievers import BaseRetriever

from langchain.tools import Tool

import logging
logger = logging.getLogger(__name__)

COMPANY_ENV = None

def set_company_environment(company_env):
    global COMPANY_ENV
    global EMAILDB_PATH

    COMPANY_ENV = company_env

def _save_gdoc_fn(title: str, overwrite: bool) -> str:
    lib_gdrive.gmail_authenticate(COMPANY_ENV)

    conversation = "\n\n".join(lib_conversation.get_conversation())

    logger.debug(f"Saving conversation to gdoc {title}:\n{conversation}")


    doc_id = lib_gdrive.publish_google_doc(title, conversation)

    return f"sucessfully saved gdoc id: {doc_id} with title {title} url: https://docs.google.com/document/d/{doc_id}/edit"

def save_gdoc_fn(title: str) -> str:
    try:
        return _save_gdoc_fn(title, overwrite=False)
    except:
        return "DOCUMENT ALREADY EXISTS, OVERWRITE EXCPLICITLY REQUIRED"

def update_gdoc_fn(doc_id: str) -> str:
    lib_gdrive.gmail_authenticate(COMPANY_ENV)

    conversation = "\n\n".join(lib_conversation.get_conversation())

    lib_gdrive.update_google_doc_content(doc_id, conversation)

    return f"sucessfully saved gdoc id: {doc_id}  url: https://docs.google.com/document/d/{doc_id}/edit"

def change_title_gdoc_fn(doc_id: str, new_title: str) -> str:
    lib_gdrive.gmail_authenticate(COMPANY_ENV)

    lib_gdrive.update_google_doc_title(doc_id, new_title)

    return f"Successfully changed title of gdoc id: {doc_id} to {new_title}"


save_gdoc_tool = StructuredTool.from_function(
    func=save_gdoc_fn,
    name="save_gdoc",
    description="Saves this conversation to a google drive document"
)


update_gdoc_tool = StructuredTool.from_function(
    func=update_gdoc_fn,
    name="update_gdoc",
    description="updates an existing google doc"
)

change_title_gdoc_tool = StructuredTool.from_function(
    func=change_title_gdoc_fn,
    name="change_gdoc_title",
    description="changes the title of an existing google doc"
)


class RetrieverInput(BaseModel):
    """Input to the retriever."""

    query: str = Field(description="query to look up in retriever")


def create_retriever_tool(
    retriever: BaseRetriever, name: str, description: str
) -> Tool:
    """Create a tool to do retrieval of documents.

    Args:
        retriever: The retriever to use for the retrieval
        name: The name for the tool. This will be passed to the language model,
            so should be unique and somewhat descriptive.
        description: The description for the tool. This will be passed to the language
            model, so should be descriptive.

    Returns:
        Tool class to pass to an agent
    """

    def _get_relevant_documents(query: str) -> str:
        # print(f"Getting relevant documents for query: {query}")
        docs = retriever.get_relevant_documents(query)

        logger.debug(f"Getting relevant documents: {docs}")

        for doc in docs:
            # created_at = doc.metadata['created_at']
            # # Convert current time to datetime for comparison
            # now = datetime.datetime.now(created_at.tzinfo)  # Preserving timezone of created_at if it has one
            # # Calculate the difference in hours
            # hours_ago = int((now - created_at).total_seconds() / 3600)

            created_at_timestamp = doc.metadata['created_at']
            created_at = datetime.datetime.fromtimestamp(created_at_timestamp)

            # Get the current time
            # If created_at is timezone-aware, use the same timezone for 'now'
            if created_at.tzinfo:
                now = datetime.datetime.now(created_at.tzinfo)
            else:
                now = datetime.datetime.now()

            # Calculate the difference
            time_difference = now - created_at
            hours_difference = int(time_difference.total_seconds() / 3600)
            doc.page_content = f"CREATED {hours_difference} HOURS AGO\n\n{doc.page_content}"
            logger.debug(f"DOC {doc.metadata['name']} {doc.metadata['created_at']} {doc.metadata['source']} {doc.metadata['type']} {doc.page_content[:100]}\n\n")
            # logger.debug(f"DOC {doc.metadata['name']} {doc.metadata['created_at']} {doc.metadata['last_accessed_at']} {doc.metadata['source']} {doc.metadata['type']} {doc.metadata['buffer_idx']} {doc.page_content[:100]}\n\n")

        return docs

    return Tool(
        name=name,
        description=description,
        func=_get_relevant_documents,
        coroutine=retriever.aget_relevant_documents,
        args_schema=RetrieverInput,
    )
