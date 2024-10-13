"""
Parses product data to extract relevant information.
Args:
    raw api of sainsburys product json.
Returns:
    formatted json of necessary information.
"""
def parse_product_data(products):
    parsed_products = []
    
    for product in products:
        # Extract required fields with fallbacks
        product_uid = product.get('product_uid', 'N/A')
        name = product.get('name', 'N/A')
        eans = product.get('eans', [])
        full_url = product.get('full_url', 'N/A')
        
        # Ensure that eans is always a string
        if isinstance(eans, list):
            eans = ','.join(eans)
        elif eans is None:
            eans = ''

        # Default to no discount and no price if not available
        discounted_price = None
        original_price = None

        #Handle Catchweight Products
        if product['product_type'] == "CATCHWEIGHT":
            cheapest_price = float('inf')  # Initialize with a very high price
            for weight_range in product.get('catchweight', []):
                price = weight_range.get('retail_price', {}).get('price')
                if price and price < cheapest_price:
                    cheapest_price = price
            original_price = cheapest_price
            discounted_price = cheapest_price # In this case, assume no discount

        # Handle Multivariant Products
        elif product['product_type'] == "MULTIVARIANT":
            cheapest_price = float('inf')
            for variant in product.get('multivariants', []):
                price = variant.get('retail_price', {}).get('price')
                if price and price < cheapest_price:
                    cheapest_price = price
            original_price = cheapest_price
            discounted_price = cheapest_price # Assume no discount for now
        else:

            # Extract retail price (final or discounted price) only if available
            if 'retail_price' in product and isinstance(product['retail_price'], dict):
                original_price = product['retail_price'].get('price')
                discounted_price = original_price  # Default to the same as original unless overridden

            # Check for promotions and ignore meal deals
            if 'promotions' in product:
                for promotion in product['promotions']:
                    if promotion.get('promo_type') == 'MEAL_MULTI_DEAL_FOR_X':
                        continue
                    if 'original_price' in promotion and promotion['original_price'] > 0:
                        original_price = promotion['original_price']
                        discounted_price = product.get('retail_price', {}).get('price', original_price)

        product_info = {
            'id': product_uid,
            'name': name,
            'original_price': original_price,
            'discounted_price': discounted_price if discounted_price and discounted_price != original_price else None,
            'eans': eans,
            'full_url': full_url
        }

        parsed_products.append(product_info)

    return parsed_products
