import toml
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import logging
import time

logger = logging.getLogger(__name__)

# Load configuration from config.toml
with open('config.toml', 'r') as f:
    config = toml.load(f)

db_config = config['database'] #gets db config from config.toml


connection_pool = MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config)

def get_connection():
    try:
        connection = connection_pool.get_connection()
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
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
        logger.info("No products to save.")
        return 0, 0
    try:
        with get_connection() as connection:
            if connection is None: raise Error("No connection available")
            with connection.cursor() as cursor:
                start_time = time.time()
                for product in product_infos:
                    logger.debug(f"EANs before saving: {product['eans']}")  # Add logging for debugging
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