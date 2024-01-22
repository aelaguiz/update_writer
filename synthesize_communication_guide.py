import sys
import json
import os

import html
import html2text
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

from ai.lib import ai_defaults, lib_model, lib_doc_vectors, prompts, lc_logger
from ai.lib.loaders import wp_loader

import logging
import logging.config
import dotenv
import os

dotenv.load_dotenv()


# Define the configuration file path based on the environment
config_path = os.getenv('LOGGING_CONF_PATH')

# Use the configuration file appropriate to the environment
logging.config.fileConfig(config_path)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.connection").setLevel(logging.CRITICAL)
logging.getLogger("httpcore.http11").setLevel(logging.CRITICAL)
logging.getLogger("openai._base_client").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class Introduction(BaseModel):
    overview_of_the_author: List[str]

class GeneralWritingStyle(BaseModel):
    voice_and_tone: List[str]
    sentence_structure: List[str]
    paragraph_structure: List[str]

class VocabularyAndLanguageUse(BaseModel):
    word_choice: List[str]
    language_style: List[str]
    metaphors_and_similes: List[str]

class CharacterizationAndDialogue(BaseModel):
    character_development: List[str]
    dialogue_style: List[str]

class NarrativeElements(BaseModel):
    pacing_and_rhythm: List[str]
    story_structure: List[str]
    themes_and_motifs: List[str]

class EmotionalContext(BaseModel):
    evoking_emotions: List[str]
    atmosphere_and_setting: List[str]

class PersonalInsightsAndQuirks(BaseModel):
    authors_influences: List[str]
    personal_quirks: List[str]

class ExamplesAndAnalysis(BaseModel):
    excerpts_from_works: List[str]
    detailed_analysis: List[str]

class WritersStyleGuide(BaseModel):
    introduction: Optional[Introduction]
    general_writing_style: Optional[GeneralWritingStyle]
    vocabulary_and_language_use: Optional[VocabularyAndLanguageUse]
    characterization_and_dialogue: Optional[CharacterizationAndDialogue]
    narrative_elements: Optional[NarrativeElements]
    emotional_context: Optional[EmotionalContext]
    personal_insights_and_quirks: Optional[PersonalInsightsAndQuirks]
    examples_and_analysis: Optional[ExamplesAndAnalysis]

class RefinedObservations(BaseModel):
    refined_observations: List[str]

def combine_json_objects(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        combined_dict = {}
        for item in data:
            for key, value in item.items():
                if key in combined_dict:
                    for subkey, subvalue in value.items():
                        if subkey in combined_dict[key]:
                            combined_dict[key][subkey].extend(subvalue)
                        else:
                            combined_dict[key][subkey] = subvalue
                else:
                    combined_dict[key] = value

        return combined_dict

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

lmd = lc_logger.LlmDebugHandler()

def synthesize(section_content, section_name, subsection_name):
    llm = lib_model.get_llm()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(prompts.synthesize_comguide_section_prompt),
        HumanMessagePromptTemplate.from_template("{input}"),
    ])

    chain = (
        prompt
        | llm
        | PydanticOutputParser(pydantic_object=RefinedObservations)
    )

    for i in range(3):
        try:
            res = chain.invoke({
                "section_name": section_name,
                "subsection_name": subsection_name,
                "input": json.dumps(section_content, indent=4) 
            }, config={"callbacks": [lmd]})
            return res.refined_observations
        except:
            print(f"Error processing {section_name} - {subsection_name}")

    raise Exception("Failed to process section")

def json_to_markdown(json_data):
    """
    Convert the given JSON object to Markdown text.
    
    Args:
    json_data (dict): A dictionary representing the JSON object.
    
    Returns:
    str: The Markdown formatted string.
    """
    def process_section(title, content):
        markdown = f"## {title}\n\n"
        for key, values in content.items():
            markdown += f"### {key.replace('_', ' ').title()}\n"
            for value in values:
                markdown += f"- *{value}*\n"
            markdown += "\n"
        return markdown

    markdown_text = ""
    for section_title, section_content in json_data.items():
        markdown_text += process_section(section_title.replace('_', ' ').title(), section_content)

    return markdown_text


def main():
    lmd = lc_logger.LlmDebugHandler()
    comguide_path = sys.argv[1]
    out_path = sys.argv[2]
    md_out_path = sys.argv[3]
    
    lib_model.init(os.getenv("OPENAI_MODEL"), os.getenv("OPENAI_API_KEY"), os.getenv("PGVECTOR_CONNECTION_STRING"), os.getenv("RECORDMANAGER_CONNECTION_STRING"), temp=os.getenv("OPENAI_TEMPERATURE"))

    _comguide = combine_json_objects(comguide_path)
    print(_comguide.keys())
    big_comguide = WritersStyleGuide.model_validate(_comguide)

    # print(big_comguide.introduction.overview_of_the_author)
    # print(WritersStyleGuide.introduction.alias)

    big_comguide.introduction.overview_of_the_author = synthesize(big_comguide.introduction.overview_of_the_author, "Introduction", "Overview of the Author")

    big_comguide.general_writing_style.voice_and_tone = synthesize(big_comguide.general_writing_style.voice_and_tone, "General Writing Style", "Voice and Tone")

    big_comguide.general_writing_style.sentence_structure = synthesize(big_comguide.general_writing_style.sentence_structure, "General Writing Style", "Sentence Structure")
    big_comguide.general_writing_style.paragraph_structure = synthesize(big_comguide.general_writing_style.paragraph_structure, "General Writing Style", "Paragraph Structure")

    big_comguide.vocabulary_and_language_use.word_choice = synthesize(big_comguide.general_writing_style.paragraph_structure, "Vocabulary and Language Use", "Word Choice")
    big_comguide.vocabulary_and_language_use.language_style = synthesize(big_comguide.general_writing_style.paragraph_structure, "Vocabulary and Language Use", "Language Style")
    big_comguide.vocabulary_and_language_use.metaphors_and_similes = synthesize(big_comguide.general_writing_style.paragraph_structure, "Vocabulary and Language Use", "Metaphors and Similes")

    big_comguide.characterization_and_dialogue.character_development = synthesize(big_comguide.general_writing_style.paragraph_structure, "Characterization and Dialogue", "Character Development")
    big_comguide.characterization_and_dialogue.dialogue_style = synthesize(big_comguide.general_writing_style.paragraph_structure, "Characterization and Dialogue", "Dialogue Style")

    big_comguide.narrative_elements.pacing_and_rhythm = synthesize(big_comguide.general_writing_style.paragraph_structure, "Narrative Elements", "Pacing and Rhythm")
    big_comguide.narrative_elements.story_structure = synthesize(big_comguide.general_writing_style.paragraph_structure, "Narrative Elements", "Story Structure")
    big_comguide.narrative_elements.themes_and_motifs = synthesize(big_comguide.general_writing_style.paragraph_structure, "Narrative Elements", "Themes and Motifs")

    big_comguide.emotional_context.evoking_emotions = synthesize(big_comguide.general_writing_style.paragraph_structure, "Emotional Context", "Evoking Emotions")
    big_comguide.emotional_context.atmosphere_and_setting = synthesize(big_comguide.general_writing_style.paragraph_structure, "Emotional Context", "Atmosphere and Setting")

    big_comguide.personal_insights_and_quirks.authors_influences = synthesize(big_comguide.general_writing_style.paragraph_structure, "Personal Insights and Quirks", "Author's Influences")
    big_comguide.personal_insights_and_quirks.personal_quirks = synthesize(big_comguide.general_writing_style.paragraph_structure, "Personal Insights and Quirks", "Personal Quirks")

    big_comguide.examples_and_analysis.excerpts_from_works = synthesize(big_comguide.general_writing_style.paragraph_structure, "Examples and Analysis", "Excerpts from Works")
    big_comguide.examples_and_analysis.detailed_analysis = synthesize(big_comguide.general_writing_style.paragraph_structure, "Examples and Analysis", "Detailed Analysis")

    print(json.dumps(big_comguide.dict(), indent=4))

    with open(out_path, "w") as f:
        json.dump(big_comguide.model_dump(), f, indent=4)

    md_str = json_to_markdown(big_comguide.model_dump())

    with(open(md_out_path, "w")) as f:
        f.write(md_str)

    # "2. General Writing Style": {
    #   "Voice and Tone": ["Employs a conversational and engaging tone, as seen in: 'Talking to her was like sipping the most expensive wine — smooth and refreshing.'"],
    #   "Sentence Structure": ["Uses a mix of complex and simple sentence structures, exemplified by: 'The morning sun peeked through the curtains, casting a dance of shadows across the room, whispering secrets of the day to come.'"],
    #   "Paragraph Structure": ["Prefers short, impactful paragraphs for dramatic effect, as in: 'Darkness fell. The world held its breath.'"]
    # },




    # # if os.path.exists(comguide_path):
    # #     default_guide = False
    # #     comguide = open(comguide_path, "r").read()
    # # else:
    # default_guide = True
    # comguide = ai_defaults.comguide_default

    # logger.debug("Loading model")

    # lib_model.init(os.getenv("OPENAI_MODEL"), os.getenv("OPENAI_API_KEY"), os.getenv("PGVECTOR_CONNECTION_STRING"), os.getenv("RECORDMANAGER_CONNECTION_STRING"), temp=os.getenv("OPENAI_TEMPERATURE"))

    # logger.debug("Done loading")

    # vectordb = lib_doc_vectors.get_vectordb()
    # logger.debug(vectordb)

    # loader = wp_loader.WPLoader('documents/innerconfidence.WordPress.2023-12-29.xml')
    # docs = loader.load()
    # logger.debug(len(docs))

    # # text_splitter = RecursiveCharacterTextSplitter(chunk_size=int(2000), chunk_overlap=200, add_start_index=True)
    # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=3000, chunk_overlap=0)
    # all_docs = text_splitter.split_documents(docs)

    # llm = lib_model.get_json_llm()
    # prompt = ChatPromptTemplate.from_messages([
    #     SystemMessagePromptTemplate.from_template(prompts.comguide_prompt),
    #     HumanMessagePromptTemplate.from_template("{input}"),
    # ])

    # chain = (
    #     prompt
    #     | llm
    #     | StrOutputParser()
    #     | PydanticOutputParser(pydantic_object=WritersStyleGuide)
    # )

    # # all_docs = all_docs[:1]
    # guidelog = open('guidelog.txt', 'w')
    # comguides = []
    # num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    # with ThreadPoolExecutor(max_workers=num_threads) as executor:
    #     future_to_doc = {executor.submit(process_document, doc, chain, lmd): doc for doc in all_docs}
    #     comguides = []

    #     for doc, future in zip(all_docs, as_completed(future_to_doc)):
    #         doc_result = future.result()
    #         if doc_result:
    #             with threading.Lock():
    #                 guidelog.write(f"\n\n********************************************************\n")
    #                 guidelog.write(f"Document: {doc.metadata['title']}\n")
    #                 guidelog.write(f"Content: {doc.page_content}\n\n")
    #                 guidelog.write(f"Comguide: {json.dumps(doc_result, indent=4)}\n\n")
    #                 guidelog.flush()

    #                 comguides.append(doc_result)

    #                 with open(comguide_path, "w") as f:
    #                     json.dump(comguides, f)


if __name__ == "__main__":
    main()