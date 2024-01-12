from langchain.tools import BaseTool, StructuredTool, tool

from . import lib_gdrive
from . import lib_tools
from . import lib_gdrive
from . import lib_conversation

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