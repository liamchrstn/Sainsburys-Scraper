import time
import toml
import threading

#initialize global variables
config = toml.load('config.toml')
threadLock = threading.Lock()
start_time = None
output_dictionary = {}
last_print_time = 0
# Global counters
category_counter = 0
product_counter = 0
#intialize how many categories there are in total
num_categories = len(open(config.get('files', {}).get('category_ids_file')).readlines())
if config.get('features', {}).get('process_category_names') == True:
    num_categories += len(open(config.get('files', {}).get('category_names_file')).readlines())

def start_and_end_time():
    global start_time
    if start_time is None:
        start_time = time.time()
        return start_time
    else:
        end_time = time.time()
        elapsed_time = end_time - start_time
        start_time = None  # Reset for the next call
        return start_time, elapsed_time, end_time

def calculate_counters(counter_type):
    with threadLock:
        global category_counter, product_counter  # Declare global counters

        if counter_type == "categories":
            category_counter += 1
            display_counters(counter_type,category_counter)
        elif counter_type == "products": 
            product_counter += 1
            display_counters(counter_type,product_counter)

def getProgressBar (iteration, counter_type, total, suffix, length = 50):
    percent = ("{0:." + "1" + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = '█' * filledLength + '-' * (length - filledLength)
    return f'\r\033[?25l{counter_type} processed Progress:|{bar}| {percent}% {suffix}'

def display_counters(counter_type, counter_value):
    global output_dictionary, last_print_time

    if counter_type == "categories":
        global num_categories
        progress_bar = f"{getProgressBar(counter_value, counter_type, num_categories, 'Complete', length=50)} || {counter_value:,} categories processed: {round(counter_value/(time.time()-start_time)):,} categories/sec"
        output_dictionary[counter_type] = progress_bar  

    elif counter_type == "products":
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        product_info = f'total products processed: {counter_value:,} || {round(counter_value/elapsed_time):,} products/sec || elapsed time: {int(minutes)}m{int(seconds)}s'
        output_dictionary[counter_type] = product_info 
      
    current_time = time.time()
    if current_time - last_print_time < 0.5:
        return  # Don't print yet
    last_print_time = current_time

    max_len = 0
    for key, value in output_dictionary.items():
        max_len = max(max_len, len(value))

    print("\033[F" * len(output_dictionary), end="")
    for key, value in output_dictionary.items():
        print(value.ljust(max_len))
