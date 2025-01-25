# foreignfortune.py
from typing import List, Dict, Any
from parsel import Selector
from pyppeteer import launch
import asyncio
import json
import os
import aiohttp
import re
from jsonpath_ng import parse

class ForeignFortuneScraper:
    """Scraperr for foreignfortune.com website"""
    
    def __init__(self):
        self.base_url = "https://foreignfortune.com"



    async def get_page_content(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
    
    def extract_json_data(self, text):
        pattern = r'publish\("collection_viewed",\s*(.*?)\s*\);}'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1) if match else None

    def extract_prod_json(self, text):
        pattern = r'isMerchantRequest: false,initData:\s*(.*?)\s*,\},function pageEvents'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1) if match else None


    def extract_models(self, data):
        data = json.loads(data)
        variants = data.get('productVariants', [])
        
        color_groups = {}
        
        for variant in variants:
            if ' / ' in variant['title']:
                size, color = variant['title'].split(' / ')
            else:
                color = variant['title']
                size = 'ONE SIZE'

            
            if color not in color_groups:
                color_groups[color] = []
                
            variant_obj = {
                'id': variant['id'],
                'image': f"https:{variant['image']['src']}" if variant['image']['src'].startswith('//') else variant['image']['src'],
                'price': variant['price']['amount'],
                'size': size
            }
            
            color_groups[color].append(variant_obj)
        
        models = [
            {
                'color': color,
                'variants': variants
            }
            for color, variants in color_groups.items()
        ]
        
        return models

        

    def parse_product(self, selector: Selector, meta) -> Dict[str, Any]:

        prod_data = selector.xpath("//script[@id='web-pixels-manager-setup']/text()").get()
        prod_data = self.extract_prod_json(prod_data)
        id = meta['id']

        variants_data = self.extract_models(prod_data)

        product = {
            "id": id,
            "title": meta['title'],
            "image" : meta['image'],
            "price": meta['price'],
            "description": meta["title"],
            "sales_prices": meta['sales_prices'],
            "prices": meta["prices"],
            "images": meta['images'],
            "url": meta['url'],
            "brand": meta['brand'],
            "models": variants_data
        }
        
          
        return product
    


    async def scrape(self) -> List[Dict[str, Any]]:
        base_collection_url = "https://foreignfortune.com/collections/all"
        products = []
        page = 1
        
        while True:
            collection_url = f"{base_collection_url}?page={page}" if page > 1 else base_collection_url
            print(f"Scraping page {page}: {collection_url}")
            
            content = await self.get_page_content(collection_url)
            selector = Selector(text=content)
            
            product_urls = selector.xpath("//script[@id='web-pixels-manager-setup']/text()").get()
            
            if not product_urls:
                print(f"No products found on page {page}. Stopping pagination.")
                break
                
            try:
                data = self.extract_json_data(product_urls)
                data = json.loads(data)
                collection = data["collection"]["productVariants"]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing data on page {page}: {e}")
                break
                

            for item in collection:
                try:
                    url = item['product']['url']
                    title = item['product']['title']
                    id = item['id']
                    image = item['image']['src']
                    price = item['price']['amount']
                    sales_prices = [item['price']['amount']]
                    prices = [item['price']['amount']]
                    images = [item['image']['src']]
                    brand = item['product']['vendor']
                    
                    url = f"https://foreignfortune.com{url}"
                    meta_info = {
                        "url": url,
                        "title": title,
                        "id": id,
                        "image": image,
                        "price": price,
                        "sales_prices": sales_prices,
                        "prices": prices,
                        "images": images,
                        "brand": brand,
                    }


                    prod_content = await self.get_page_content(url)
                    prod_selector = Selector(text=prod_content)
                    
                    product = self.parse_product(prod_selector, meta=meta_info)
                    products.append(product)
                    
                except Exception as e:
                    print(f"Error processing product on page {page}: {e}")
                    continue
            

            next_page = selector.xpath("//ul[@class='list--inline pagination']/li[last()]/a/@href").get()
            if not next_page or f"page={page + 1}" not in next_page:
                print(f"No more pages found after page {page}")
                break
                
            await asyncio.sleep(2)
            page += 1
        
        print(f"Total products scraped: {len(products)}")
        return products     
        


def save_output(products: List[Dict[str, Any]]):
        os.makedirs("output", exist_ok=True)
        with open("output/foreignfortune.json", "a") as f:
            json.dump(products, f, indent=2)


async def main():
    ff_scraper = ForeignFortuneScraper()
    ff_products = await ff_scraper.scrape()
    # print(ff_products)
    save_output(ff_products)
    print("Output saved")


if __name__ == "__main__":
    asyncio.run(main())
