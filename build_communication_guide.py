import sys
import json
import os

import html
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatMessagePromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import CharacterTextSplitter
from collections.abc import Iterable
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.output_parsers import PydanticOutputParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# Append the directory above 'scripts' to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
import logging.config
import dotenv
import os

dotenv.load_dotenv()


from src.lib import lib_logging, lc_logger, prompts, prompt_defaults, lib_docdb

lib_logging.setup_logging()
logger = lib_logging.get_logger()

from pydantic import BaseModel, Field
from typing import Dict, List

class Introduction(BaseModel):
    overview_of_the_author: List[str] = Field(..., alias="Overview of the Author")

class GeneralWritingStyle(BaseModel):
    voice_and_tone: List[str] = Field(..., alias="Voice and Tone")
    sentence_structure: List[str] = Field(..., alias="Sentence Structure")
    paragraph_structure: List[str] = Field(..., alias="Paragraph Structure")

class VocabularyAndLanguageUse(BaseModel):
    word_choice: List[str] = Field(..., alias="Word Choice")
    language_style: List[str] = Field(..., alias="Language Style")
    metaphors_and_similes: List[str] = Field(..., alias="Metaphors and Similes")

class CharacterizationAndDialogue(BaseModel):
    character_development: List[str] = Field(..., alias="Character Development")
    dialogue_style: List[str] = Field(..., alias="Dialogue Style")

class NarrativeElements(BaseModel):
    pacing_and_rhythm: List[str] = Field(..., alias="Pacing and Rhythm")
    story_structure: List[str] = Field(..., alias="Story Structure")
    themes_and_motifs: List[str] = Field(..., alias="Themes and Motifs")

class EmotionalContext(BaseModel):
    evoking_emotions: List[str] = Field(..., alias="Evoking Emotions")
    atmosphere_and_setting: List[str] = Field(..., alias="Atmosphere and Setting")

class PersonalInsightsAndQuirks(BaseModel):
    authors_influences: List[str] = Field(..., alias="Author's Influences")
    personal_quirks: List[str] = Field(..., alias="Personal Quirks")

class ExamplesAndAnalysis(BaseModel):
    excerpts_from_works: List[str] = Field(..., alias="Excerpts from Works")
    detailed_analysis: List[str] = Field(..., alias="Detailed Analysis")

class WritersStyleGuide(BaseModel):
    introduction: Introduction = Field(..., alias="1. Introduction")
    general_writing_style: GeneralWritingStyle = Field(..., alias="2. General Writing Style")
    vocabulary_and_language_use: VocabularyAndLanguageUse = Field(..., alias="3. Vocabulary and Language Use")
    characterization_and_dialogue: CharacterizationAndDialogue = Field(..., alias="4. Characterization and Dialogue")
    narrative_elements: NarrativeElements = Field(..., alias="5. Narrative Elements")
    emotional_context: EmotionalContext = Field(..., alias="6. Emotional Context")
    personal_insights_and_quirks: PersonalInsightsAndQuirks = Field(..., alias="7. Personal Insights and Quirks")
    examples_and_analysis: ExamplesAndAnalysis = Field(..., alias="8. Examples and Analysis")

    class Config:
        allow_population_by_field_name = True

def vectorize_texts(texts):
    """Convert a list of texts to TF-IDF vectors."""
    vectorizer = TfidfVectorizer()
    return vectorizer.fit_transform(texts)

def calculate_similarity(tfidf_matrix):
    """Calculate cosine similarity from a TF-IDF matrix."""
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])

def is_similar_with_tolerance(ai_response_text, example_text, threshold=0.5):
    """Check if AI response is similar to an example text with a given threshold."""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([ai_response_text, example_text])
    
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
    return similarity[0][0] >= threshold



def is_similar(dict1, dict2):
    logger.debug(f"Comparing {dict1}\n\n and {dict2}")
    """Recursively compare two dictionaries to determine similarity."""
    if dict1.keys() != dict2.keys():
        logger.debug(f"Keys don't match: {dict1.keys()} != {dict2.keys()}")
        return True

    for key in dict1:
        logger.debug(f"Checking key {key}")
        if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            logger.debug(f"Comparing two matching {key}...")
            if is_similar(dict1[key], dict2[key]):
                logger.debug(f"Found similar {key} - {dict1[key]} and {dict2[key]}")
                return True
        elif isinstance(dict1[key], Iterable) and isinstance(dict2[key], Iterable):
            logger.debug(f"Comparing two lists {key}...")
            for item1, item2 in zip(dict1[key], dict2[key]):
                if is_similar_with_tolerance(item1, item2):
                    logger.debug(f"Found similar items {item1} and {item2}")
                    return True

        else:
            logger.debug(f"Comparing records on {key}...")
            if is_similar_with_tolerance(dict1[key], dict2[key]):
                logger.debug(f"Similar records on {key} - {dict1[key]} and {dict2[key]}")
                return True

    return False

def check_similarity_with_examples(ai_response, example):
    if is_similar(ai_response, example):
        return True
    return False

example_data = WritersStyleGuide.model_validate(prompt_defaults.comguide_example).model_dump()

def process_document(doc, chain, lmd):
    try:
        logger.debug(f"Processing {doc.metadata['title']}")
        new_comguide = chain.invoke({
            "input": doc.page_content,
            "example": prompt_defaults.comguide_example_json,
        }, config={'callbacks': []})
        logger.debug(f"Returning {doc.metadata['title']}")
        comguide_dict = new_comguide.model_dump()

        if check_similarity_with_examples(comguide_dict, example_data):
            logger.debug(f"Found similar comguide for {doc.metadata['title']}")
            return None
        else:
            logger.debug(f"Found new comguide for {doc.metadata['title']}")
            return comguide_dict
    except Exception as e:
        # Handle the exception here
        import traceback
        traceback.print_exc()
        logger.debug(f"An error occurred: {e}")
        return None


def main():
    lmd = lc_logger.LlmDebugHandler()
    comguide_path = sys.argv[1]
    # if os.path.exists(comguide_path):
    #     default_guide = False
    #     comguide = open(comguide_path, "r").read()
    # else:
    default_guide = True
    comguide = prompt_defaults.comguide_default

    llm = lib_docdb.get_dumb_json_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(prompts.comguide_prompt),
        HumanMessagePromptTemplate.from_template("{input}"),
    ])

    chain = (
        prompt
        | llm
        | StrOutputParser()
        | PydanticOutputParser(pydantic_object=WritersStyleGuide)
    )

    # all_docs = all_docs[:1]
    guidelog = open('guidelog.txt', 'w')
    comguides = []
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_doc = {executor.submit(process_document, doc, chain, lmd): doc for doc in all_docs}
        comguides = []

        for doc, future in zip(all_docs, as_completed(future_to_doc)):
            doc_result = future.result()
            if doc_result:
                with threading.Lock():
                    guidelog.write(f"\n\n********************************************************\n")
                    guidelog.write(f"Document: {doc.metadata['title']}\n")
                    guidelog.write(f"Content: {doc.page_content}\n\n")
                    guidelog.write(f"Comguide: {json.dumps(doc_result, indent=4)}\n\n")
                    guidelog.flush()

                    comguides.append(doc_result)

                    with open(comguide_path, "w") as f:
                        json.dump(comguides, f)


if __name__ == "__main__":
    main()