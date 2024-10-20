import logging
import sys
import threading
import time
from queue import Queue
import toml
from logging_config import setup_logging
from db_handler import setup_database, get_row_count
from thread_handler import (start_fetcher_threads, start_parser_threads, start_db_consumer, start_category_name_saver_thread, raw_data_queue, parsed_product_queue, category_names_process_queue)
from obtain_recent_categories import get_category_ids
from display_live_info import start_time, start_and_end_time


logger = logging.getLogger(__name__)

with open('config.toml', 'r') as f:
    config = toml.load(f)

#set scraping options    
fetch_new_ids = config.get('features', {}).get('fetch_new_category_ids')  # Default to True if not specified
save_names = config.get('features', {}).get('save_category_names')
process_names = config.get('features', {}).get('process_category_names') 


def read_category_ids(file_path):
    if fetch_new_ids:
        get_category_ids() #get the new updated category ids
    category_queue = Queue()
    try:
        with open(file_path, 'r') as file:
            for line in file:
                category_queue.put(int(line.strip()))
    except FileNotFoundError:
        logger.error(f"Category file {file_path} not found.")
        sys.exit(1)
    except ValueError:
        logger.error(f"Invalid category ID format in {file_path}.")
        sys.exit(1)
    return category_queue

def main():
    setup_logging()
    setup_database()
    print("\033[38;5;208mWelcome to the Sainsbury's Scraper\033[0m")
    start_time = start_and_end_time()
    print('Start time:', time.strftime('%H:%M:%S', time.gmtime(start_time)),'\n\n')


    category_ids_file = config.get('files', {}).get('category_ids_file')
    category_queue = read_category_ids(category_ids_file)

    num_fetcher_threads = config.get('processing',{}).get('num_fetcher_threads')
    num_parser_threads = config.get('processing',{}).get('num_parser_threads')


    fetcher_threads = start_fetcher_threads(category_queue, category_names_process_queue, num_fetcher_threads) # Pass the new queue
    parser_threads = start_parser_threads(num_parser_threads)
    if save_names:
        category_saver_thread = start_category_name_saver_thread()
    db_consumer_thread = threading.Thread(target=start_db_consumer, daemon=True, name="DB-Consumer")
    db_consumer_thread.start()


    # Populate category_names_process_queue *after* starting fetcher threads and *before* they finish
    if process_names:
        category_names_file = config.get('files', {}).get('category_names_file')
        try:
            with open(category_names_file, 'r') as f:
                for line in f:
                    category_names_process_queue.put(line.strip())
        except FileNotFoundError:
            logger.warning(f"Category names file {category_names_file} not found.")  # Warning instead of sys.exit


    # Wait for all fetcher threads (both ID and name processing)
    for thread in fetcher_threads:
        thread.join()

    # Signal parser threads to stop *after* all fetching is done
    for _ in range(num_parser_threads):
        raw_data_queue.put(None)
    
    for thread in parser_threads:
        thread.join()


    # Wait for any remaining items in parsed_product_queue to be processed
    while not parsed_product_queue.empty():
        time.sleep(1)

    # Now it's safe to save the category names because all processing is finished.
    category_saver_thread.join()  # Wait for the category saver thread to finish

    row_count = get_row_count()
    if row_count is not None:
        logger.info(f"Table 'products' has {row_count} rows.")
    else:
        logger.warning("Could not retrieve row count.")
    _, elapsed_time, end_time = start_and_end_time()
    print(f"Application Summary: \n Time taken: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}\n Unique Products Saved: {row_count}\n Goodbye!")
    logger.info("All products processed. Application finished.")

if __name__ == "__main__":
    main()