### **Sainsbury's Product Scraper**

A Python scraper that downloads product data from Sainsbury's and saves it into a MySQL database.

Sainsbury's doesn't offer an easy way to track price history, so this tool was built to handle that. It runs as part of a daily pipeline to monitor for price drops and automatically find the best deals.

#### **Features**

*   Fetches product data by category.
*   Normalizes different price types (standard, promotional, by weight).
*   Saves or updates products in a MySQL table (no duplicates).
*   Prints its progress as it runs.

#### **Getting Started**

**Prerequisites:** Python 3.10+, MySQL

1.  **Install dependencies:**
    ```
    pip install requests mysql-connector-python toml
    ```
2.  **Configure:**
    Edit `config.toml` with your MySQL details.

3.  **Run:**
    ```
    python main.py
    ```

#### **Configuration**

read `config.toml` to toggle features like finding new categories or to adjust the scraper's speed and batch sizes.


> **Disclaimer:** This tool is for educational and research use. Please be respectful of Sainsbury's terms and policies.