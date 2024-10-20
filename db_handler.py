import toml
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import logging
import time
import re
from display_live_info import calculate_counters

logger = logging.getLogger(__name__)

# Load configuration from config.toml
with open('config.toml', 'r') as f:
    config = toml.load(f)

db_config = config['database']  # gets db config from config.toml

# Remove unsupported arguments from db_config
unsupported_keys = ['mysqltablename']
for key in unsupported_keys:
    db_config.pop(key, None)

connection_pool = MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

def get_connection():
    try:
        connection = connection_pool.get_connection()
        if connection.is_connected():
            return connection
    except Error as e:
        logger.warn(f"Error connecting to MySQL: {e}")
    return None

def setup_database():
    try:
        with get_connection() as connection:
            if connection is None: raise Error("No connection available") # Explicit raise for cleaner handling
            with connection.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id VARCHAR(255) PRIMARY KEY,
                        name TEXT,
                        original_price DECIMAL(10, 2),
                        discounted_price DECIMAL(10, 2),
                        eans TEXT,
                        full_url TEXT
                    )
                ''')
                connection.commit() # Commit moved inside the outer with block
    except Error as e:
        logger.error(f"Error setting up database: {e}")

def save_products_to_db(product_infos):
    if not product_infos:
        logger.error("No products to save.")
        return 0, 0
    try:
        with get_connection() as connection:
            if connection is None: raise Error("No connection available")
            with connection.cursor() as cursor:
                start_time = time.time()
                for product in product_infos:
                    calculate_counters("products")
                 #   logger.debug(f"EANs before saving: {product['eans']}") 
                placeholders = ', '.join(['%s'] * len(product_infos[0]))
                query = f"""INSERT INTO products (id, name, original_price, discounted_price, eans, full_url)
                           VALUES ({placeholders}) ON DUPLICATE KEY UPDATE name=VALUES(name), original_price=VALUES(original_price),
                                   discounted_price=VALUES(discounted_price), eans=VALUES(eans), full_url=VALUES(full_url)"""
                cursor.executemany(query, [tuple(product.values()) for product in product_infos])
                connection.commit()
                return len(product_infos), time.time() - start_time
    except Error as e:
        logger.error(f"Error saving products: {e}")
        return 0, 0
    
def save_category_names(category_names_save_queue): 
    all_category_names = set()
    logger.info("Category name saver thread started.")

    # Load existing category names from file
    file_path = config.get('files', {}).get('category_names_file')
    try:
        with open(file_path, 'r') as f:
            existing_names = set(line.strip() for line in f)
            all_category_names.update(existing_names) 
    except FileNotFoundError:
        pass # If the file doesn't exist, it's okay, we'll create it

    while True:
        category_name = category_names_save_queue.get()
        if category_name is None:  # Signal to stop
            logger.info("Category name saver thread finished.")
            break

        # Allow only ASCII characters (0-127) and replace others with spaces
        sanitized_name = re.sub(r'[^\x00-\x7F]', ' ', category_name)
        all_category_names.add(sanitized_name) # Add the sanitized name to the set

        category_names_save_queue.task_done()

    # Sort the unique category names
    sorted_category_names = sorted(list(all_category_names))

    # Save sorted and unique category names to file
    with open(file_path, 'w') as f:
        for category_name in sorted_category_names:
            f.write(category_name + '\n') # Use category_name instead of sanitized_name
    logger.info(f"Saved {len(sorted_category_names)} category names to file.")

def get_row_count():
    try:
        with get_connection() as connection:
            if connection is None: raise Error("No connection available")
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
                return count
    except Error as e:
        logger.error(f"Error getting row count: {e}")
        return None  # Return None to indicate failure