import requests
import toml
import logging

logger = logging.getLogger(__name__)

def get_category_ids():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://www.sainsburys.co.uk/',
        'X-Requested-With': 'XMLHttpRequest',
    }
    api_urls = [
        "https://www.sainsburys.co.uk/groceries-api/gol-services/product/categories/tree",
        "https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product/taxonomy"
    ]
    category_ids = set()

    def extract_ids(data):
        if isinstance(data, dict):
            # Expert 1's change: Check if ID exists before adding
            if data.get('id') is not None: 
                category_ids.add(str(data.get('id')))
            # Expert 2's change: Check if 'c:' exists before splitting
            if 's' in data and 'c:' in data['s']:
                category_ids.add(data['s'].split('c:')[-1])
            for value in data.values():
                extract_ids(value)
        elif isinstance(data, list):
            for item in data:
                extract_ids(item)

    for url in api_urls:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            extract_ids(response.json())
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {url}: {e}")

    config = toml.load("config.toml")
    file_path = config["files"]["category_ids_file"]

    existing_ids = set()
    try:
        with open(file_path, 'r') as f:
            existing_ids.update(line.strip() for line in f)
    except FileNotFoundError:
        pass

    all_ids = sorted([id for id in category_ids | existing_ids if id is not None])

    with open(file_path, 'w') as f:
        f.writelines(f"{id}\n" for id in all_ids)
    total_ids = len(all_ids)
    added_ids = total_ids - len(existing_ids)
    logging.info(f"Category IDs written to {file_path} \n {total_ids} total IDs, {added_ids} new IDs added.")