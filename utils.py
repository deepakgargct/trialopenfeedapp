"""
Utility functions for the ChatGPT Product Feed Validator
"""

import re
import validators
from datetime import datetime

def validate_url(url):
    """Validate if a string is a valid URL"""
    return validators.url(url)

def validate_gtin(gtin):
    """Validate GTIN format (8-14 digits)"""
    if not gtin or pd.isna(gtin):
        return False
    gtin_str = str(gtin).replace('-', '').replace(' ', '')
    return bool(re.match(r'^\d{8,14}$', gtin_str))

def validate_iso_date(date_str):
    """Validate ISO 8601 date format"""
    try:
        datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        return True
    except: 
        return False

def parse_price(price_str):
    """Parse price string to extract amount and currency"""
    if not price_str or pd.isna(price_str):
        return None, None
    
    parts = str(price_str).split()
    if len(parts) >= 2:
        try:
            amount = float(parts[0])
            currency = parts[1]
            return amount, currency
        except:
            return None, None
    return None, None

def validate_currency_code(currency):
    """Validate ISO 4217 currency code"""
    # Common currency codes
    valid_currencies = [
        'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 
        'SEK', 'NZD', 'MXN', 'SGD', 'HKD', 'NOK', 'KRW', 'TRY',
        'INR', 'RUB', 'BRL', 'ZAR'
    ]
    return currency and currency.upper() in valid_currencies

def clean_html(html_text):
    """Remove HTML tags from text"""
    if not html_text or pd.isna(html_text):
        return ''
    clean = re.compile('<.*?>')
    return re.sub(clean, '', str(html_text))

def truncate_text(text, max_length):
    """Truncate text to maximum length"""
    if not text or pd.isna(text):
        return ''
    text_str = str(text)
    return text_str[:max_length] + '...' if len(text_str) > max_length else text_str
