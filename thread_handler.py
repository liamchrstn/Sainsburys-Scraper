import logging
import time
from queue import Queue
import threading
from query import fetch_sainsburys_products
from parser import parse_product_data
from db_handler import save_products_to_db
import toml

logger = logging.getLogger(__name__)
with open('config.toml', 'r') as f:
    config = toml.load(f)


parsing_complete = threading.Event()

# Global queues
raw_data_queue = Queue()
parsed_product_queue = Queue()

# Constants (moved to config.toml)
BATCH_SIZE = config.get('processing', {}).get('batch_size')
PAGE_SIZE = config.get('api', {}).get('page_size')

def fetch_data(category_id, page_size):
    page_number = 1
    while True:
        response = fetch_sainsburys_products(category_id, page_number, page_size)
        if response and response.ok:
            data = response.json()
            raw_data_queue.put(data)
            pagination_info = data.get('controls', {}).get('page', {})
            current_page = pagination_info.get('active', page_number)
            last_page = pagination_info.get('last', page_number)       
            if current_page >= last_page:
                if last_page == 1:
                    logger.info(f"Fetched all of category: {category_id}")
                else:
                    logger.info(f"Fetched all of category: {category_id} -  that had {last_page} pages.")
                break
            page_number += 1
        else:
            logger.error(f"Failed to fetch page {page_number} for category {category_id}.")
            break

def parse_data():
    thread_name = threading.current_thread().name
    while True:
        raw_data = raw_data_queue.get()
        if raw_data is None:
            break 
        products = raw_data.get('products', [])
        parsed_products = parse_product_data(products)
        for product in parsed_products:
            parsed_product_queue.put(product)
        raw_data_queue.task_done()
    logger.info(f"Parser thread {thread_name} finished.")
    parsing_complete.set()

      
def start_db_consumer():
    thread_name = threading.current_thread().name
    batch = []
    while True:
        # Consume entire queue
        while not parsed_product_queue.empty():  # Loop until queue is empty
            try:
                item = parsed_product_queue.get_nowait()
                batch.append(item)
                if len(batch) == BATCH_SIZE:
                    if batch:  # Avoid saving an empty batch
                        save_products_to_db(batch)
                        for p in batch:
                             parsed_product_queue.task_done()
                        logger.info(f"[{thread_name}] Saved {len(batch)} products to db.")  # Log after saving
                    batch.clear() # reset the batch list
            except Queue.Empty:
                time.sleep(0.1) #give a small amount of time to avoid using unnecessary resources
        #Only check for parsing complete once we have confirmed queue is empty
        if parsing_complete.is_set():  # Exit after processing and parsing complete
            break
        if batch:  # Save any remaining items
            save_products_to_db(batch)
            for p in batch:
                parsed_product_queue.task_done()
            logger.info(f"[{thread_name}] Saved remaining {len(batch)} products to db.") # Log after saving
            batch.clear()  # Important: Clear the batch after saving

    

def fetcher_worker(category_queue):  # <--- Added back the missing function
    thread_name = threading.current_thread().name
    while not category_queue.empty():
        try:
            category_id = category_queue.get(timeout=5)
            fetch_data(category_id, PAGE_SIZE)
            category_queue.task_done()
        except Queue.Empty:
            break
    logger.info(f"{thread_name}: finished all tasks.")

def start_fetcher_threads(category_queue, num_threads):
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=fetcher_worker, args=(category_queue,), daemon=True, name=f"Fetcher-{i+1}")
        thread.start()
        threads.append(thread)
    return threads

def start_parser_threads(num_threads):
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=parse_data, daemon=True, name=f"Parser-{i+1}")
        thread.start()
        threads.append(thread)
    return threads
