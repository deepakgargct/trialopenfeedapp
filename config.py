"""
Configuration file for the ChatGPT Product Feed Validator
"""

# ChatGPT Product Feed Specifications
PRODUCT_FEED_SPECS = {
    'enable_search': {
        'type': 'Enum',
        'values': ['true', 'false'],
        'required': True,
        'description': 'Controls whether the product can be surfaced in ChatGPT search results.',
        'example': 'true'
    },
    'enable_checkout': {
        'type': 'Enum',
        'values': ['true', 'false'],
        'required': True,
        'description': 'Allows direct purchase inside ChatGPT.',
        'example': 'true',
        'dependencies': ['enable_search']
    },
    'id': {
        'type': 'String',
        'max_length': 100,
        'required': True,
        'description':  'Merchant product ID (unique)',
        'example': 'SKU12345'
    },
    'gtin': {
        'type':  'String',
        'pattern': r'^\d{8,14}$',
        'required': False,
        'recommended': True,
        'description':  'Universal product identifier (GTIN, UPC, ISBN)',
        'example': '123456789012'
    },
    'mpn': {
        'type': 'String',
        'max_length': 70,
        'required': 'conditional',
        'description': 'Manufacturer part number (required if gtin missing)',
        'example': 'GPT5'
    },
    'title': {
        'type': 'String',
        'max_length': 150,
        'required': True,
        'description': 'Product title',
        'example': "Men's Trail Running Shoes Black"
    },
    'description': {
        'type': 'String',
        'max_length': 5000,
        'required': True,
        'description': 'Full product description',
        'example':  'Waterproof trail shoe with cushioned sole'
    },
    'link': {
        'type': 'URL',
        'required': True,
        'description': 'Product detail page URL (HTTPS preferred)',
        'example': 'https://example.com/product/SKU12345'
    },
    'condition': {
        'type': 'Enum',
        'values': ['new', 'refurbished', 'used'],
        'required': 'conditional',
        'description':  'Condition of product',
        'example': 'new'
    },
    'product_category': {
        'type': 'String',
        'required': True,
        'description': 'Category path (use > separator)',
        'example': 'Apparel & Accessories > Shoes'
    },
    'brand': {
        'type': 'String',
        'max_length': 70,
        'required': 'conditional',
        'description': 'Product brand',
        'example': 'OpenAI'
    },
    'material': {
        'type': 'String',
        'max_length': 100,
        'required': True,
        'description': 'Primary material(s)',
        'example': 'Leather'
    },
    'weight': {
        'type': 'Number',
        'required': True,
        'description': 'Product weight with unit',
        'example': '1.5 lb'
    },
    'image_link': {
        'type': 'URL',
        'required': True,
        'description': 'Main product image URL (JPEG/PNG, HTTPS preferred)',
        'example': 'https://example.com/image1.jpg'
    },
    'price': {
        'type': 'Number',
        'required':  True,
        'description': 'Regular price with ISO 4217 currency code',
        'example': '79.99 USD'
    },
    'availability': {
        'type':  'Enum',
        'values': ['in_stock', 'out_of_stock', 'preorder'],
        'required': True,
        'description': 'Product availability',
        'example': 'in_stock'
    },
    'inventory_quantity': {
        'type': 'Integer',
        'required': True,
        'description': 'Stock count (non-negative)',
        'example': '25'
    },
    'seller_name': {
        'type': 'String',
        'max_length': 70,
        'required': True,
        'description': 'Seller name',
        'example': 'Example Store'
    },
    'seller_url': {
        'type': 'URL',
        'required':  True,
        'description': 'Seller page (HTTPS preferred)',
        'example': 'https://example.com/store'
    },
    'seller_privacy_policy': {
        'type':  'URL',
        'required': 'conditional',
        'description':  'Seller privacy policy (required if enable_checkout is true)',
        'example': 'https://example.com/privacy'
    },
    'seller_tos': {
        'type':  'URL',
        'required': 'conditional',
        'description': 'Seller terms of service (required if enable_checkout is true)',
        'example':  'https://example.com/terms'
    },
    'return_policy': {
        'type': 'URL',
        'required': True,
        'description': 'Return policy URL (HTTPS preferred)',
        'example': 'https://example.com/returns'
    },
    'return_window': {
        'type': 'Integer',
        'required':  True,
        'description': 'Days allowed for return (positive integer)',
        'example': '30'
    },
}

# Schema. org mapping
SCHEMA_ORG_MAPPING = {
    'id': 'sku',
    'title': 'name',
    'description': 'description',
    'link': 'url',
    'brand': 'brand',
    'gtin': 'gtin',
    'mpn': 'mpn',
    'image_link': 'image',
    'material': 'material',
    'weight': 'weight',
}
