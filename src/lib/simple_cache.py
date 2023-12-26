import os
import pickle
import hashlib
from functools import wraps

from .lib_logging import get_logger

logger = get_logger()

def pickle_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_dir = "cache"  # Define the directory for cache files
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        hasher = hashlib.sha256()
        hasher.update(pickle.dumps((args, kwargs)))
        hash_val = hasher.hexdigest()
        
        # Create a cache file name based on the function name and the hashed arguments
        cache_file = os.path.join(cache_dir, f"{func.__name__}_{hash_val}.pkl")


        # print(f"Args {args} - Kwargs {kwargs} - Cache file {cache_file}")

        # Try to load the result from cache
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as cache:
                logger.info(f"CACHE: Hit on {func.__name__} {args, kwargs} - {cache_file}")
                return pickle.load(cache)

        # Call the function and cache the result if not found in cache
        result = func(*args, **kwargs)
        with open(cache_file, 'wb') as cache:
            logger.info(f"CACHE: Saving results from {func.__name__} {args, kwargs} - {cache_file}")
            pickle.dump(result, cache)

        return result
    return wrapper
