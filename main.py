import logging
import sys
import threading
import time
from queue import Queue
import toml
from logging_config import setup_logging
from db_handler import setup_database, get_row_count
from thread_handler import (
    start_fetcher_threads,
    start_parser_threads,
    start_db_consumer,
    raw_data_queue,
    parsed_product_queue
)
logger = logging.getLogger(__name__)

with open('config.toml', 'r') as f:
    config = toml.load(f)

def read_category_ids(file_path):
    category_queue = Queue()
    try:
        with open(file_path, 'r') as file:
            for line in file:
                category_queue.put(int(line.strip()))
    except FileNotFoundError:
        logging.error(f"Category file {file_path} not found.")
        sys.exit(1)
    except ValueError:
        logging.error(f"Invalid category ID format in {file_path}.")
        sys.exit(1)
    return category_queue


def main():
    setup_logging()
    setup_database()

    category_ids_file = config.get('files', {}).get('category_ids_file')
    category_queue = read_category_ids(category_ids_file)

    num_fetcher_threads = config.get('processing',{}).get('num_fetcher_threads')
    fetcher_threads = start_fetcher_threads(category_queue, num_fetcher_threads)

    num_parser_threads = config.get('processing',{}).get('num_parser_threads')
    parser_threads = start_parser_threads(num_parser_threads)

    # Start DB consumer thread
    db_consumer_thread = threading.Thread(target=start_db_consumer, daemon=True, name="DB-Consumer")
    db_consumer_thread.start()
    logger.info("all threads started")
    # Wait for all fetcher threads to complete
    for thread in fetcher_threads:
        thread.join()

    # Signal parser threads to stop
    for _ in range(num_parser_threads):
        raw_data_queue.put(None)

    # Wait for parser threads to complete
    for thread in parser_threads:
        thread.join()

    while not parsed_product_queue.empty():
        time.sleep(1)

    row_count = get_row_count() # Get the row count
    if row_count is not None:
        logging.info(f"Table 'products' has {row_count} rows.")
    else:
        logging.warning("Could not retrieve row count.")

    logging.info("All products processed. Application finished.")


if __name__ == "__main__":
    main()
