import logging
import time
import queue
from queue import Queue
import threading
from query import fetch_sainsburys_products
from parser import parse_product_data
from db_handler import save_products_to_db, save_category_names
import toml
from display_live_info import calculate_counters

logger = logging.getLogger(__name__)
with open('config.toml', 'r') as f:
    config = toml.load(f)

parsing_complete = threading.Event()

# Global queues and events
raw_data_queue = Queue()
parsed_product_queue = Queue()
category_names_save_queue = Queue()
category_names_process_queue = Queue()
name_processing_complete = threading.Event()
name_processing_threads_finished = 0
name_processing_lock = threading.Lock()

# Constants (moved to config.toml)
BATCH_SIZE = config.get('processing', {}).get('batch_size')
PAGE_SIZE = config.get('api', {}).get('page_size')

def fetch_data(search_term, page_size, search_by): #added search_by
    page_number = 1
    while True:
        response = fetch_sainsburys_products(search_term, page_number, page_size, search_by)
        if response and response.ok:
            data = response.json()
            raw_data_queue.put(data)
            calculate_counters("categories")
            pagination_info = data.get('controls', {}).get('page', {})
            current_page = pagination_info.get('active', page_number)
            last_page = pagination_info.get('last', page_number)
            if current_page >= last_page:
                if last_page == 1:
                    logger.debug(f"Fetched all of category: {search_term}.")
                else:
                    logger.debug(f"Fetched all of category: {search_term} -  that had {last_page} pages.")
                break
            page_number += 1
            break
        break

def parse_data():
    thread_name = threading.current_thread().name
    while True:
        raw_data = raw_data_queue.get()
        if raw_data is None:
            break 
        products = raw_data.get('products', [])
        parsed_products, category_names = parse_product_data(products) # Unpack both return values
        for product in parsed_products:
            parsed_product_queue.put(product)
        for category_name in category_names:
            category_names_save_queue.put(category_name)# Add category names to the queue
        raw_data_queue.task_done()
    logger.debug(f"Parser thread {thread_name} finished.")
    parsing_complete.set()

def start_db_consumer():
    thread_name = threading.current_thread().name
    batch = []
    while True:
        try:
            item = parsed_product_queue.get(timeout=1)  # Use a timeout to avoid indefinite blocking
            batch.append(item)
            if len(batch) == BATCH_SIZE:
                save_products_to_db(batch)
                parsed_product_queue.task_done()  # Mark tasks as done after processing
                logger.debug(f"[{thread_name}] Saved {len(batch)} products to db.")
                batch.clear()
        except queue.Empty:
            if parsing_complete.is_set() and name_processing_threads_finished == config.get('processing', {}).get('num_fetcher_threads'):
                break  # Exit only when parsing is complete and all fetcher threads are done
            else:
                continue  # Continue checking for items or completion

    # Save any remaining items in the batch after the loop finishes
    if batch:
        save_products_to_db(batch)
        parsed_product_queue.task_done()
        logger.debug(f"[{thread_name}] Saved remaining {len(batch)} products to db.")
        batch.clear()

    category_names_save_queue.put(None)  # Signal category saver to stop after all products are processed

def fetcher_worker(category_queue, category_names_process_queue):
    thread_name = threading.current_thread().name
    search_by = "id"  # Default search type
    while True:
        if search_by == "id":
            try:
                category_id = category_queue.get(timeout=5)
                fetch_data(category_id, PAGE_SIZE, search_by)
                category_queue.task_done()
            except queue.Empty:  # Corrected exception handling
                if category_names_process_queue.empty():
                    break
                else:
                    search_by = "name"
                    continue
        elif search_by == "name":  # we're now doing names
            if config.get('features', {}).get('process_category_names') ==  True:
                with name_processing_lock:  # thread safety
                    if not name_processing_complete.is_set():
                        name_processing_complete.set()

                while True:
                    try:
                        category_name = category_names_process_queue.get(timeout=5)
                        fetch_data(category_name, PAGE_SIZE, search_by)
                        category_names_process_queue.task_done()
                    except queue.Empty:  # Corrected exception handling HERE as well
                        with name_processing_lock:  # increment when done a full search
                            global name_processing_threads_finished  # global declaration
                            name_processing_threads_finished += 1
                        break
            break  # fetcher has done both category name and id searching
    logger.debug(f"{thread_name}: finished all tasks.")

def start_fetcher_threads(category_queue, category_names_process_queue, num_threads): #add new parameter
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=fetcher_worker, args=(category_queue, category_names_process_queue), daemon=True, name=f"Fetcher-{i+1}") #add as arg here
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


def start_category_name_saver_thread():
    thread = threading.Thread(target=save_category_names, args=(category_names_save_queue,), daemon=True, name="Category-Saver")
    thread.start()
    return thread
    