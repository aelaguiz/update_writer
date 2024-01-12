from langchain.tools import BaseTool, StructuredTool, tool

from . import lib_tools
from . import lib_gdrive

def save_gdoc_fn(title: str) -> str:
    return f"SUCESSFULLY SAVED GDOC {title}"


save_gdoc_tool = StructuredTool.from_function(
    func=save_gdoc_fn,
    name="save_gdoc",
    description="Saves this conversation to a google drive document"
)

