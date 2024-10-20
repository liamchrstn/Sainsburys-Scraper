# Project Overview

### My Multithreaded scraper that extracts key product information from Sainsbury's and stores it in a standardized database.

## Files and their purposes:

| File             | Description                                                                                           |
|------------------|---------------------------------------------------------------------------------------------------|
| **query.py**       | **Fetches raw product data** from the Sainsbury's API based on provided category IDs and pagination. |
| **parser.py**      | **Parses the raw product data** to extract necessary information (name, price, EANs, URL) and standardizes the format.  |
| **db_handler.py** | **Handles all interactions with the database**: setting up the "products" table and saving parsed products using efficient batching.  |
| **thread_handler.py** | **Manages the threading logic** for parallel processing. Creates queues (`raw_data_queue`, `parsed_product_queue`) and worker threads to fetch, parse, and save data concurrently. |
| **logging_config.py** | **Sets up logging configuration** to output messages to both the console and a log file (`app.log`) for debugging and monitoring. |
| **main.py**        | **The application's entry point**. Orchestrates the data scraping and saving process: reads category IDs from `categoryids.txt`, starts worker threads, monitors progress, and reports final results.  |
| **categoryids.txt** | A plain text file containing a **list of Sainsbury's category IDs** to be processed.  |
| **config.toml**   | A **configuration file** holding important settings: database connection details, number of threads for each task, file names, API parameters, and other customizable options.  |




## Steps Taken

1. Scraped all product IDs by spidering the site.
2. Found each product had categories, so scraped all the categories, then searched the product search with the category name.
3. Started adding products to the database.
4. Figured out that the price for products was not saved in the same way (e.g., drinks, meat per kg, discounted items marked in different ways depending on discount type). Therefore, price and discounted price need to consider all factors before deciding which is correct for each.
5. Tried querying products one at a time per run, but it was slow. Increasing to more than 30 queries per second led to server pushback.
6. Tried bypassing the limit by doing user-agent rotations, etc.
7. Tried using proxies and VPNs but realized the method was inefficient and would be long-term expensive due to the high number of queries.
8. Found the random header that allows category searches.
9. Scraped XML for category data.
10. Scraped the tree for category data.
11. Scraped taxonomy for category data.
12. Scraped all known category IDs.
13. Performed category searches to find all products in said category, which allowed retrieving up to ~3000 products per query, making it exponentially more efficient.
14. Implemented the category searches to go from search to database.
15. Threaded it nicely - had parsing and querying on different threads.
16. Used EAN numbers to compare with other projects.
17. rewrote some of the more sloppy parts to make it more understandable
18. Fix EANs numbering
19. before searching by ids use taxonomy and tree to get up to date data
20. searches by category ids then search by category names
21. saves new category names that are now found during parse to txt file for later searches
22. wrote some analysis code to find best deals etc
23. wrote a live terminal display with speed time elapsed etc
24. changed logging to show less data unless in debug mode for simpler error finding

## To Do
1. Change how we save the databases: if there is one with the current date, do as normal; if there is none for that day, make a new one saved as ddmmyy.
2. Create a master database that has products from all searches.
3. Be able to compare prices between tables.
4. If a known product ID is not found in the category search via the master table, search for it individually and figure out why it didn't show up.
5. Inform the user of good deals/info.
6. Host and serve.

