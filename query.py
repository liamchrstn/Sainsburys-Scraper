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

def fetch_sainsburys_products(search_term, page_number, page_size, search_by="id"):
    url = 'https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product'

    if search_by == "id":
        params = {
            'filter[keyword]': '',
            'filter[category]': search_term,
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
    elif search_by == "name":
        params = {
            'filter[keyword]': search_term,
            'page_number': page_number,
            'page_size': page_size,
            'include[CANNED]': 'true'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://www.sainsburys.co.uk/',
            'X-Requested-With': 'XMLHttpRequest',
        }
    else:
        raise ValueError("Invalid search_by argument. Must be 'id' or 'name'.")

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logger.debug(f"Request timed out for search term {search_term}, page {page_number}. Attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                time.sleep(retry_delay*attempt)
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for search term {search_term}, page {page_number}. Attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries reached for search term {search_term}, page {page_number} NO SEARCH MADE.")
                return None

    return None