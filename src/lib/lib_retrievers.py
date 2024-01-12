from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .time_weighted_retriever import EnhancedTimeWeightedRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo


document_metadata_attributes = [
    AttributeInfo(name="type", type="string", description="Type of the document"),
    AttributeInfo(name="source", type="string", description="Source of the document"),
    AttributeInfo(name="created_at", type="int", description="Creation timestamp of the document"),
    AttributeInfo(name="name", type="string", description="Name of the document")
]


def get_retriever(vectorstore, k, source_filter=None, type_filter=None):
    skw = get_search_kwargs(k, source_filter, type_filter)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs=skw)
    return retriever

def get_time_weighted(vectorstore, k, source_filter=None, type_filter=None):
    tw_retriever = EnhancedTimeWeightedRetriever(
        vectorstore=vectorstore, decay_rate=0.80, k=k, search_kwargs=get_search_kwargs(k, source_filter, type_filter)
    )

    return tw_retriever


def get_self_query(llm, vectorstore, doc_content_description, k, source_filter=None, type_filter=None):
    skw = get_search_kwargs(k, source_filter, type_filter)
    sq = SelfQueryRetriever.from_llm(
        llm,
        vectorstore,
        doc_content_description,
        document_metadata_attributes,
        search_kwargs=skw)

    return sq


def get_search_kwargs(k, source_filter, type_filter):
    search_kwargs = {
        "k": k
    }

    if source_filter and type_filter:
        raise Exception("Not Implemented: Cannot filter by both source and type")

    if source_filter:
        ## This syntax was neeeded for chroma, but I don't think needed for pgvector
        # search_kwargs["filter"] = {"source": {"$eq": source_filter}}
        search_kwargs["filter"] = {"source": source_filter}
    if type_filter:
        search_kwargs["filter"] = {"type": type_filter}

    return search_kwargs