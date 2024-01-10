import argparse
import src.pipeline.gdrive_pipeline as gdrive_pipeline
import src.lib.lib_logging as lib_logging
import logging

googleapiclient_logger = logging.getLogger('googleapiclient.discovery_cache')
googleapiclient_logger.setLevel(logging.WARNING)

lib_logging.setup_logging()

def main(max_documents):
    gdrive_pipeline.run_pipeline(args.company.upper(), max_documents)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the gdrive pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    parser.add_argument('max_documents', type=int, help='Maximum number of documents to load.')
    args = parser.parse_args()
    main(args.max_documents)