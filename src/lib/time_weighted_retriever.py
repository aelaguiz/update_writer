
from src.lib import lib_logging

from langchain.callbacks.manager import CallbackManagerForRetrieverRun

from prompt_toolkit.history import FileHistory
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from typing import Any, Dict, List, Optional, Tuple

from langchain.vectorstores.pgvector import PGVector
from langchain_core.documents import Document



import datetime

lib_logging.setup_logging()
logger = lib_logging.get_logger()

class EnhancedTimeWeightedRetriever(TimeWeightedVectorStoreRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _transform_document_dates(self, docs_and_scores, current_time):
        # Transform the document dates as required

        docs = []
        for i, (doc, score) in enumerate(docs_and_scores):
            if doc.metadata.get("type") == 'email':
                unix_timestamp = doc.metadata.get('send_date')

                formatted_timestamp = datetime.datetime.utcfromtimestamp(unix_timestamp)

                doc.metadata['created_at'] = formatted_timestamp
                doc.metadata['last_accessed_at'] = formatted_timestamp
            elif doc.metadata.get("source") == 'gdrive':
                doc.metadata['created_at'] = datetime.datetime.utcfromtimestamp(doc.metadata.get('created_at'))
                doc.metadata['last_accessed_at'] = datetime.datetime.utcfromtimestamp(doc.metadata.get('modified_at'))
            else:
                logger.error(f"Unknown document type: {doc.metadata.get('type')} {doc.metadata.get('source')}")
                assert(False)

            doc.metadata["buffer_idx"] = len(self.memory_stream) + i
            logger.debug(f"EnhancedTimeWeightedRetriever doc.metadata: {doc.metadata}")
            docs.append(doc)

        self.memory_stream.extend(docs)

            # doc.metadata['created_at'] = doc.metadata.get('created_at', current_time)
            # doc.metadata['last_accessed_at'] = current_time
        return docs_and_scores

    def _get_relevant_documents(self, query, *, run_manager: CallbackManagerForRetrieverRun):
        logger.debug(f"EnhancedTimeWeightedRetriever query: {query} kwargs {self.search_kwargs}")
        # Get documents from the wrapped retriever
        docs_and_scores = self.vectorstore.similarity_search_with_relevance_scores(
            query, **self.search_kwargs
        )
        logger.debug(f"EnhancedTimeWeightedRetriever docs: {len(docs_and_scores)}")

        
        # Transform documents and set in memory_stream
        current_time = datetime.datetime.now()
        self._transform_document_dates(docs_and_scores, current_time)

        logger.debug(f"Calling parent with docs {len(docs_and_scores)}")
        # Call the parent method to proceed with the usual flow

        def custom_similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Tuple[Document, float]]:
            logger.debug(f"custom_similarity_search query: {query} kwargs {kwargs}")
            return docs_and_scores

        override_relevance_score_fn = self.vectorstore.similarity_search_with_relevance_scores
        self.vectorstore.similarity_search_with_relevance_scores = custom_similarity_search.__get__(self.vectorstore, PGVector)

        res = super()._get_relevant_documents(query, run_manager=run_manager)

        for i, doc in enumerate(res):
            if doc.metadata.get('type') == 'email':
                logger.debug(f"Doc {i} {doc.metadata['buffer_idx']} {doc.metadata['type']} {doc.metadata['last_accessed_at']} {doc.metadata['created_at']} {doc.metadata['subject']}': {doc.page_content[:100]}")
            elif doc.metadata.get('source') == 'gdrive':
                logger.debug(f"Doc {i} {doc.metadata['buffer_idx']} {doc.metadata['type']} {doc.metadata['last_accessed_at']} {doc.metadata['created_at']} {doc.metadata['name']}': {doc.page_content[:100]}")

        self.vectorstore.similarity_search_with_relevance_scores = override_relevance_score_fn

        return res