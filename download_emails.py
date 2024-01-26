import argparse
import src.pipeline.gmail_pipeline as gmail_pipeline
import src.lib.lib_logging as lib_logging
import logging

googleapiclient_logger = logging.getLogger('googleapiclient.discovery_cache')
googleapiclient_logger.setLevel(logging.WARNING)

lib_logging.setup_logging()

def main():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    parser.add_argument('max_documents', type=int, help='Maximum number of documents to load.')
    parser.add_argument('output_file', type=str, help='Ouput file name.')
    args = parser.parse_args()

    gmail_pipeline.run_pipeline(args.company.upper(), args.max_documents, True, args.output_file)