from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    field: str
    error: str
    product_id: Optional[str] = None

class ProductValidator:
    def __init__(self):
        self.required_fields = {'id', 'title', 'price', 'url'}
        
    def validate_products(self, products):
        errors = []
        for product in products:
            errors.extend(self.validate_product(product))
        return errors
    
    def validate_product(self, product):
        errors = []

        # req. field check
        for field in self.required_fields:
            if field not in product or not product[field]:
                errors.append(ValidationError(
                    field=field,
                    error=f"Missing required field: {field}",
                    product_id=product.get('id')
                ))


        # price
        if 'price' in product and 'sales_pricees' in product:
            try:
                price = Decimal(str(product['price']))
                sales_price = Decimal(str(product['sales_price'][0])) ##bcz in code, we r taking sales prices as a list thats y.
                if sales_price > price:
                    errors.append(ValidationError(
                        field='sales_price',
                        error="Sales price cannot be greater than original price",
                        product_id=product.get('id')
                    ))
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    field='price',
                    error="Invalid price format",
                    product_id=product.get('id')
                ))



        # forurl
        if 'url' in product:
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            if not re.match(url_pattern, product['url']):
                errors.append(ValidationError(
                    field='url',
                    error="Invalid URL format",
                    product_id=product.get('id')
                ))

        return errors

def validate_scraped_data(file_path):
    try:
        with open(file_path, 'r') as f:
            products = json.load(f)
        
        validator = ProductValidator()
        errors = validator.validate_products(products)
        
        if errors:
            logger.error(f"Found {len(errors)} validation errors")
            for error in errors:
                logger.error(f"Product {error.product_id} - {error.field}: {error.error}")
        
        return errors
        
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {str(e)}")
        raise

if __name__ == "__main__":
    errors = validate_scraped_data("output/foreignfortune.json")
    print(f"Total validation errors: {len(errors)}")