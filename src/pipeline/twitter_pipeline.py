import dotenv
import json
import argparse
from ..lib.lib_logging import get_logger, setup_logging
from ..lib import lib_twitterdb  # Importing the lib_twitterdb module

dotenv.load_dotenv()
setup_logging()
logger = get_logger()

def load_tweets_from_file(file_path):
    """
    Load tweets from a file. Each line in the file is a JSON object with 'id' and 'text' keys.
    """
    tweets = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                tweet = json.loads(line)
                tweets.append(tweet)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
    return tweets

def process_tweet(tweet):
    """
    Process an individual tweet. Placeholder for further processing logic.
    """
    logger.debug(f"Processing tweet {tweet['id']}: {tweet['text']}")
    # Add processing logic here if needed
    return tweet

def tweet_exists(tweet_id):
    """
    Check if a tweet already exists in the DocDB.
    """
    existing_tweet_ids = set(lib_twitterdb.get_tweet_ids())
    return tweet_id in existing_tweet_ids

def process_tweets(file_path):
    lib_twitterdb.set_company_environment('TWITTER')
    # lib_twitterdb.get_docdb()


    """
    Main function to process tweets from a file.
    """
    tweets = load_tweets_from_file(file_path)
    for tweet in tweets:
        if not tweet_exists(tweet['id']):
            processed_tweet = process_tweet(tweet)
            lib_twitterdb.add_tweet(processed_tweet)
        else:
            logger.info(f"Tweet {tweet['id']} already exists in the database.")

