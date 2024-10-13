import requests
import logging
import time
import toml

with open('config.toml', 'r') as f:
    config = toml.load(f)

# Moved to config.toml under api settings
max_retries = config.get("api", {}).get("max_retries")
retry_delay = config.get("api", {}).get("retry_delay")


logger = logging.getLogger(__name__)

def fetch_sainsburys_products(category_id, page_number, page_size):
    url = 'https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product'
    params = {
        'filter[keyword]': '',
        'filter[category]': category_id,
        'browse': 'true',
        'page_number': str(page_number),
        'page_size': str(page_size)
    }
    headers = {
        'authority': 'www.sainsburys.co.uk',
        'method': 'GET',
        'accept': 'application/json',
        'enabled-feature-flags': 'findability_search',
        'referer': 'https://www.sainsburys.co.uk/gol-ui/groceries/halloween/all-halloween/c:1043380',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response  
        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out for category {category_id}, page {page_number}. Attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for category {category_id}, page {page_number}. Attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                return None

    return None 