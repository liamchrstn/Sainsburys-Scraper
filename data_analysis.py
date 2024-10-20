import toml
import mysql.connector


# Load config 
config = toml.load("config.toml")
db_config = config["database"]

# Remove mysqltablename from connection parameters
connection_params = db_config.copy() # Create a copy to modify
table_name = connection_params.pop("mysqltablename")  # Remove and store the table name


def establish_connection(connection_params):
    try:
        mydb = mysql.connector.connect(**connection_params)
        mycursor = mydb.cursor(dictionary=True)
        return mydb, mycursor
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None, None

def find_max_original_price_item(mycursor, table_name):
    try:
        mycursor.execute(f"SELECT * FROM {table_name} ORDER BY original_price DESC LIMIT 1")
        return mycursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def find_max_discounted_price_item(mycursor, table_name):
    try:
        mycursor.execute(f"SELECT * FROM {table_name} ORDER BY discounted_price DESC LIMIT 1")
        return mycursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def find_top_discount_percentage_items(mycursor, table_name):
    try:
        mycursor.execute(f"SELECT *, (original_price - discounted_price) / original_price AS discount_percentage FROM {table_name} ORDER BY discount_percentage DESC LIMIT 5")
        return mycursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

def print_top_discount_percentage_items(items):
    for item in items:
        name = item.get("name", "N/A")
        original_price = item.get("original_price", "N/A")
        discounted_price = item.get("discounted_price", "N/A")
        discount_percentage = item.get("discount_percentage", "N/A")
        url = item.get("full_url", "N/A")
        print(f"Name: {name}, Original Price: {original_price}, Discounted Price: {discounted_price}, Discount Percentage: {discount_percentage:.2%}, URL: {url}")


def get_table_size(mycursor, table_name):
    try:
        mycursor.execute(f"SELECT table_name AS `Table`, round(((data_length + index_length) / 1024 / 1024), 2) `Size in MB` FROM information_schema.TABLES WHERE table_name = '{table_name}'")
        result = mycursor.fetchone()
        return result["Size in MB"] if result else None
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None

def main():
    mydb, mycursor = establish_connection(connection_params)
    if mydb is None or mycursor is None:
        return

    max_original_price_item = find_max_original_price_item(mycursor, table_name)
    max_discounted_price_item = find_max_discounted_price_item(mycursor, table_name)
    top_discount_percentage_items = find_top_discount_percentage_items(mycursor, table_name)
    print(f"Table size: {get_table_size(mycursor, table_name)} MB")
    print_top_discount_percentage_items(top_discount_percentage_items)

    if mydb.is_connected():
        mycursor.close()
        mydb.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()