import argparse
import src.pipeline.twitter_pipeline as twitter_pipeline
import src.lib.lib_logging as lib_logging
import logging
import dotenv

googleapiclient_logger = logging.getLogger('googleapiclient.discovery_cache')
googleapiclient_logger.setLevel(logging.WARNING)

dotenv.load_dotenv()
lib_logging.setup_logging()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process tweets from a file.")
    parser.add_argument("file_path", help="Path to the file containing tweets.")
    args = parser.parse_args()

    twitter_pipeline.process_tweets(args.file_path)