import streamlit as st
import pandas as pd
import json
import validators
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="ChatGPT Product Feed Validator",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load specifications from the CSV
@st.cache_data
def load_specifications():
    """Load the ChatGPT Product Feed specifications"""
    specs = {
        'enable_search': {'type': 'Enum', 'values': ['true', 'false'], 'required': True, 'description': 'Controls whether the product can be surfaced in ChatGPT search results. '},
        'enable_checkout':  {'type': 'Enum', 'values': ['true', 'false'], 'required': True, 'description': 'Allows direct purchase inside ChatGPT.'},
        'id': {'type': 'String', 'max_length': 100, 'required': True, 'description': 'Merchant product ID (unique)'},
        'gtin': {'type': 'String', 'pattern': r'^\d{8,14}$', 'required': False, 'recommended': True, 'description': 'Universal product identifier'},
        'mpn': {'type': 'String', 'max_length': 70, 'required': 'conditional', 'description': 'Manufacturer part number'},
        'title': {'type': 'String', 'max_length': 150, 'required': True, 'description': 'Product title'},
        'description': {'type':  'String', 'max_length': 5000, 'required': True, 'description': 'Full product description'},
        'link': {'type': 'URL', 'required': True, 'description': 'Product detail page URL'},
        'condition': {'type': 'Enum', 'values': ['new', 'refurbished', 'used'], 'required': 'conditional', 'description': 'Condition of product'},
        'product_category': {'type': 'String', 'required': True, 'description': 'Category path'},
        'brand': {'type':  'String', 'max_length': 70, 'required': 'conditional', 'description': 'Product brand'},
        'material': {'type':  'String', 'max_length': 100, 'required': True, 'description': 'Primary material(s)'},
        'weight': {'type': 'Number', 'required': True, 'description': 'Product weight with unit'},
        'image_link': {'type': 'URL', 'required': True, 'description': 'Main product image URL'},
        'price': {'type': 'Number', 'required': True, 'description': 'Regular price with currency code'},
        'availability': {'type': 'Enum', 'values': ['in_stock', 'out_of_stock', 'preorder'], 'required': True, 'description': 'Product availability'},
        'inventory_quantity': {'type': 'Integer', 'required': True, 'description': 'Stock count'},
        'seller_name': {'type': 'String', 'max_length': 70, 'required': True, 'description': 'Seller name'},
        'seller_url': {'type': 'URL', 'required': True, 'description': 'Seller page'},
        'return_policy': {'type': 'URL', 'required': True, 'description': 'Return policy URL'},
        'return_window': {'type': 'Integer', 'required': True, 'description':  'Days allowed for return'},
    }
    return specs

def validate_field(field_name, value, spec):
    """Validate a single field against its specification"""
    errors = []
    warnings = []
    
    if pd.isna(value) or value == '' or value is None:
        if spec. get('required') == True:
            errors.append(f"Required field '{field_name}' is missing")
        elif spec.get('recommended'):
            warnings.append(f"Recommended field '{field_name}' is missing")
        return errors, warnings
    
    # Type validation
    if spec.get('type') == 'String':
        value = str(value)
        if 'max_length' in spec and len(value) > spec['max_length']:
            errors.append(f"'{field_name}' exceeds max length of {spec['max_length']} characters")
    
    elif spec.get('type') == 'URL':
        if not validators.url(str(value)):
            errors.append(f"'{field_name}' is not a valid URL")
    
    elif spec.get('type') == 'Enum':
        if str(value).lower() not in [v.lower() for v in spec. get('values', [])]:
            errors.append(f"'{field_name}' must be one of:  {', '.join(spec['values'])}")
    
    elif spec.get('type') == 'Integer':
        try:
            int_val = int(float(value))
            if int_val < 0:
                errors.append(f"'{field_name}' must be non-negative")
        except:
            errors.append(f"'{field_name}' must be an integer")
    
    elif spec.get('type') == 'Number':
        try:
            float(str(value).split()[0])
        except:
            errors.append(f"'{field_name}' must be a number")
    
    # Pattern validation
    if 'pattern' in spec:
        if not re.match(spec['pattern'], str(value)):
            errors.append(f"'{field_name}' does not match required pattern")
    
    return errors, warnings

def validate_product_feed(df, specs):
    """Validate entire product feed"""
    results = {
        'total_products': len(df),
        'products_with_errors': 0,
        'products_with_warnings': 0,
        'field_coverage': {},
        'all_errors': [],
        'all_warnings': [],
        'missing_required_fields': set(),
        'missing_recommended_fields': set()
    }
    
    # Check field coverage
    for field_name, spec in specs.items():
        if field_name in df.columns:
            non_empty = df[field_name].notna().sum()
            results['field_coverage'][field_name] = {
                'present': True,
                'filled': non_empty,
                'percentage': (non_empty / len(df)) * 100
            }
        else:
            results['field_coverage'][field_name] = {
                'present': False,
                'filled': 0,
                'percentage': 0
            }
            if spec.get('required') == True:
                results['missing_required_fields'].add(field_name)
            elif spec.get('recommended'):
                results['missing_recommended_fields'].add(field_name)
    
    # Validate each product
    for idx, row in df.iterrows():
        product_errors = []
        product_warnings = []
        
        for field_name, spec in specs. items():
            if field_name in df.columns:
                errors, warnings = validate_field(field_name, row[field_name], spec)
                product_errors.extend(errors)
                product_warnings.extend(warnings)
        
        if product_errors:
            results['products_with_errors'] += 1
            results['all_errors'].append({
                'product_id': row. get('id', f'Row {idx}'),
                'errors': product_errors
            })
        
        if product_warnings:
            results['products_with_warnings'] += 1
            results['all_warnings'].append({
                'product_id': row.get('id', f'Row {idx}'),
                'warnings': product_warnings
            })
    
    return results

def generate_schema_markup(product_data):
    """Generate schema. org Product markup"""
    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
    }
    
    # Map fields to schema.org properties
    field_mapping = {
        'id': 'sku',
        'title': 'name',
        'description':  'description',
        'link': 'url',
        'brand': 'brand',
        'gtin': 'gtin',
        'mpn': 'mpn',
        'image_link': 'image',
        'material': 'material',
        'weight': 'weight',
    }
    
    for csv_field, schema_field in field_mapping.items():
        if csv_field in product_data and pd.notna(product_data[csv_field]):
            value = product_data[csv_field]
            if schema_field == 'brand':
                schema[schema_field] = {"@type": "Brand", "name": str(value)}
            elif schema_field == 'image': 
                schema[schema_field] = str(value)
            else:
                schema[schema_field] = str(value)
    
    # Add offers
    if 'price' in product_data and pd.notna(product_data['price']):
        price_str = str(product_data['price'])
        price_parts = price_str.split()
        
        offer = {
            "@type": "Offer",
            "price": price_parts[0] if price_parts else price_str,
            "priceCurrency": price_parts[1] if len(price_parts) > 1 else "USD",
        }
        
        if 'availability' in product_data and pd.notna(product_data['availability']):
            availability_map = {
                'in_stock': 'https://schema.org/InStock',
                'out_of_stock': 'https://schema.org/OutOfStock',
                'preorder': 'https://schema.org/PreOrder'
            }
            offer['availability'] = availability_map. get(str(product_data['availability']).lower(), 'https://schema.org/InStock')
        
        if 'link' in product_data and pd. notna(product_data['link']):
            offer['url'] = str(product_data['link'])
        
        if 'seller_name' in product_data and pd.notna(product_data['seller_name']):
            offer['seller'] = {
                "@type": "Organization",
                "name": str(product_data['seller_name'])
            }
        
        schema['offers'] = offer
    
    # Add aggregateRating if available
    if 'product_review_rating' in product_data and pd. notna(product_data['product_review_rating']):
        rating = {
            "@type": "AggregateRating",
            "ratingValue": str(product_data['product_review_rating']),
        }
        if 'product_review_count' in product_data and pd.notna(product_data['product_review_count']):
            rating['reviewCount'] = str(product_data['product_review_count'])
        schema['aggregateRating'] = rating
    
    return schema

def scrape_website_products(url):
    """Scrape basic product information from a website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract schema.org data first
        schema_scripts = soup.find_all('script', type='application/ld+json')
        products = []
        
        for script in schema_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    products.append(extract_product_from_schema(data))
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            products.append(extract_product_from_schema(item))
            except:
                continue
        
        if not products:
            # Fallback:  basic scraping
            product = {
                'title': soup.find('title').text if soup.find('title') else '',
                'description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else '',
                'link': url,
            }
            
            # Try to find images
            og_image = soup.find('meta', attrs={'property': 'og:image'})
            if og_image:
                product['image_link'] = og_image.get('content', '')
            
            products.append(product)
        
        return products
    except Exception as e:
        st.error(f"Error scraping website: {str(e)}")
        return []

def extract_product_from_schema(schema_data):
    """Extract product data from schema.org markup"""
    product = {}
    
    mapping = {
        'name': 'title',
        'description': 'description',
        'url': 'link',
        'image': 'image_link',
        'sku': 'id',
        'gtin': 'gtin',
        'mpn': 'mpn',
        'material': 'material',
    }
    
    for schema_key, csv_key in mapping.items():
        if schema_key in schema_data: 
            value = schema_data[schema_key]
            if isinstance(value, dict):
                product[csv_key] = value.get('name', str(value))
            elif isinstance(value, list) and value:
                product[csv_key] = value[0]
            else:
                product[csv_key] = value
    
    # Extract brand
    if 'brand' in schema_data:
        brand = schema_data['brand']
        product['brand'] = brand.get('name', brand) if isinstance(brand, dict) else brand
    
    # Extract offers
    if 'offers' in schema_data:
        offers = schema_data['offers']
        if isinstance(offers, list):
            offers = offers[0]
        
        if isinstance(offers, dict):
            if 'price' in offers: 
                currency = offers. get('priceCurrency', 'USD')
                product['price'] = f"{offers['price']} {currency}"
            
            if 'availability' in offers:
                avail = offers['availability']. lower()
                if 'instock' in avail:
                    product['availability'] = 'in_stock'
                elif 'outofstock' in avail: 
                    product['availability'] = 'out_of_stock'
                elif 'preorder' in avail:
                    product['availability'] = 'preorder'
    
    # Extract ratings
    if 'aggregateRating' in schema_data: 
        rating = schema_data['aggregateRating']
        if isinstance(rating, dict):
            product['product_review_rating'] = rating.get('ratingValue', '')
            product['product_review_count'] = rating.get('reviewCount', '')
    
    return product

# Main App
def main():
    st.title("🛍�� ChatGPT Product Feed Validator & Schema Generator")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st. header("📋 About")
        st.info(
            "This tool validates product feeds against ChatGPT Product Feed specifications "
            "and generates schema markup recommendations."
        )
        
        st.header("🔧 Options")
        input_method = st.radio(
            "Choose input method:",
            ["Upload CSV File", "Enter Website URL"]
        )
    
    # Load specifications
    specs = load_specifications()
    
    # Main content
    if input_method == "Upload CSV File":
        st.header("📤 Upload Product Feed")
        uploaded_file = st.file_uploader(
            "Upload your product feed CSV file",
            type=['csv'],
            help="Upload a CSV file containing your product data"
        )
        
        if uploaded_file is not None: 
            try:
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} products from CSV")
                
                # Display preview
                with st.expander("📊 Data Preview"):
                    st.dataframe(df.head(10))
                
                process_product_feed(df, specs)
                
            except Exception as e: 
                st.error(f"Error reading CSV file: {str(e)}")
    
    else:  # Website URL
        st.header("🌐 Enter Website URL")
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com/product-page",
            help="Enter the URL of a product page or website to scrape"
        )
        
        if st.button("🔍 Scrape & Analyze", type="primary"):
            if url and validators.url(url):
                with st.spinner("Scraping website..."):
                    products = scrape_website_products(url)
                    
                    if products:
                        df = pd.DataFrame(products)
                        st.success(f"✅ Extracted {len(products)} product(s)")
                        
                        with st.expander("📊 Extracted Data"):
                            st.dataframe(df)
                        
                        process_product_feed(df, specs)
                    else:
                        st.warning("No product data found on this page")
            else:
                st. error("Please enter a valid URL")

def process_product_feed(df, specs):
    """Process and validate product feed"""
    st. header("🔍 Validation Results")
    
    # Run validation
    with st.spinner("Validating product feed..."):
        results = validate_product_feed(df, specs)
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", results['total_products'])
    with col2:
        st.metric("Products with Errors", results['products_with_errors'])
    with col3:
        st. metric("Products with Warnings", results['products_with_warnings'])
    with col4:
        success_rate = ((results['total_products'] - results['products_with_errors']) / results['total_products'] * 100) if results['total_products'] > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Missing fields
    st.subheader("📋 Field Analysis")
    
    col1, col2 = st. columns(2)
    
    with col1:
        if results['missing_required_fields']: 
            st.error("❌ Missing Required Fields")
            for field in results['missing_required_fields']:
                st.write(f"- **{field}**: {specs[field]['description']}")
        else:
            st.success("✅ All required fields present")
    
    with col2:
        if results['missing_recommended_fields']:
            st.warning("⚠️ Missing Recommended Fields")
            for field in results['missing_recommended_fields']: 
                st.write(f"- **{field}**: {specs[field]['description']}")
        else:
            st.success("✅ All recommended fields present")
    
    # Field coverage chart
    with st.expander("📊 Field Coverage Details"):
        coverage_data = []
        for field, data in results['field_coverage'].items():
            if data['present']:
                coverage_data.append({
                    'Field': field,
                    'Filled': data['filled'],
                    'Coverage %': f"{data['percentage']:.1f}%",
                    'Required': '✓' if specs[field]. get('required') == True else ('⭐' if specs[field].get('recommended') else '')
                })
        
        if coverage_data:
            coverage_df = pd.DataFrame(coverage_data)
            st.dataframe(coverage_df, use_container_width=True)
    
    # Detailed errors
    if results['all_errors']:
        with st.expander(f"❌ Detailed Errors ({len(results['all_errors'])} products)"):
            for error_data in results['all_errors'][:50]:  # Limit to first 50
                st.write(f"**Product:  {error_data['product_id']}**")
                for error in error_data['errors']: 
                    st.write(f"  - {error}")
                st.markdown("---")
    
    # Detailed warnings
    if results['all_warnings']:
        with st.expander(f"⚠️ Detailed Warnings ({len(results['all_warnings'])} products)"):
            for warning_data in results['all_warnings'][: 50]:  # Limit to first 50
                st.write(f"**Product: {warning_data['product_id']}**")
                for warning in warning_data['warnings']:
                    st.write(f"  - {warning}")
                st.markdown("---")
    
    # Schema Markup Generation
    st.header("📝 Schema Markup Generation")
    
    product_options = [f"{row. get('id', f'Row {idx}')} - {row.get('title', 'Untitled')}" 
                      for idx, row in df.iterrows()]
    
    selected_product = st.selectbox(
        "Select a product to generate schema markup:",
        range(len(product_options)),
        format_func=lambda x:  product_options[x]
    )
    
    if st.button("🎯 Generate Schema Markup", type="primary"):
        product_data = df.iloc[selected_product]
        schema = generate_schema_markup(product_data)
        
        st.subheader("Generated Schema. org Markup")
        schema_json = json.dumps(schema, indent=2)
        st.code(schema_json, language='json')
        
        # Download button
        st.download_button(
            label="⬇️ Download Schema JSON",
            data=schema_json,
            file_name=f"schema_{product_data.get('id', 'product')}.json",
            mime="application/json"
        )
        
        # Validation
        st.subheader("✅ Schema Validation")
        missing_fields = []
        for field in ['name', 'image', 'description']: 
            if field not in schema: 
                missing_fields.append(field)
        
        if not missing_fields:
            st. success("Schema markup includes all core required fields!")
        else:
            st. warning(f"Missing recommended fields: {', '.join(missing_fields)}")
        
        # HTML implementation
        st.subheader("🔧 HTML Implementation")
        html_code = f'''<script type="application/ld+json">
{schema_json}
</script>'''
        st.code(html_code, language='html')
    
    # Export options
    st.header("💾 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export validation report
        report = {
            'summary': {
                'total_products': results['total_products'],
                'products_with_errors':  results['products_with_errors'],
                'products_with_warnings': results['products_with_warnings'],
            },
            'missing_required_fields': list(results['missing_required_fields']),
            'missing_recommended_fields': list(results['missing_recommended_fields']),
            'errors': results['all_errors'][:100],
            'warnings': results['all_warnings'][:100]
        }
        
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="📥 Download Validation Report (JSON)",
            data=report_json,
            file_name=f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        # Export enriched CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        st.download_button(
            label="📥 Download Product Feed (CSV)",
            data=output,
            file_name=f"product_feed_{datetime. now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
