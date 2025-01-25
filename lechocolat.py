from typing import List, Dict, Any
from parsel import Selector
import asyncio
import aiohttp
import json
import os
import logging
from urllib.parse import urljoin
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChocolateScraper:
    def __init__(self):
        self.base_url = "https://www.lechocolat-alainducasse.com"
        self.categories = {
            'christmas': "/uk/christmas",
            "boxes": "/uk/chocolates",
            "gifts": "/uk/chocolate-gift",
            "bars":"/uk/chocolate-bar",
            "simple pleasures": "/uk/simple-pleasures",
            "Specialty Coffee Beans": "/uk/specialty-coffee-beans",
            "Specialty Coffee Capsules": "/uk/specialty-coffee-capsules"
        }
        self.headers = {
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7',

            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        }

    async def get_page_content(self, url: str):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                return await response.text()

    def parse_product(self, selector: Selector, url: str):
        try:

            images= selector.xpath("//ul[contains(@class, 'productImages__')]/li/a/@href").getall()
            title_list = selector.xpath("//div[contains(@class, 'productCard__name')]//text()").getall()
            title = " ".join([t.strip() for t in title_list if t.strip()])

            desc_list = selector.xpath("//div[contains(@class, 'productDescription__text')]//text()").getall()
            desc = " ".join([d.strip() for d in desc_list if d.strip()])
            model_list = selector.xpath("//ul[@class='linkedProducts__list']/li")
            models = []
            for m in model_list:
                title = m.xpath("./a/@title").get()
                if not title:
                   title = m.xpath("./span[contains(@class, 'linkedProducts__bullet')]/span/text()").get()
                #    title = " ".join([t.strip() for t in title if t.strip()])
                
                link = m.xpath("./a/@href").get()
                if not link:
                    link = url

                model = {
                "title" : title,
                "link" : link
                }
                models.append(model)

            prod_jsson = selector.xpath("//article[@id='product-details']/@data-product").get()

            prod_json= json.loads(prod_jsson)
            available= prod_json['availability_message']
            price = prod_json['price']
            price = float(re.sub(r"[^\d.]", "", price.replace(",", "")))

            id = prod_json['id_product']
            url = prod_json["link"]

            product = {
                "id": id,
                "title": title,
                "image":images[0],
                "price": price,
                "description": desc,
                "availability": available,
                "sales_prices": [price],
                "prices": [price],
                "images":images,
                "url": url,
                "brand": "LE CHOCOLAT",
                "models": models,
               
            }
            return product
        except Exception as e:
            logger.error(f"Error parsing product {url}: {e}")
            return None


    async def scrape_category(self, category_url):
        products = []
    
        url = category_url
        content = await self.get_page_content(url)
        selector = Selector(text=content)
        
        product_data_str = selector.xpath("//script[@type='application/ld+json'][contains(text(), 'ItemList')]/text()").get()
        if product_data_str:
            product_data = json.loads(product_data_str)

        product_links = product_data["itemListElement"]
        
        print("yaha tk aaya ")
        for d in product_links:
            product_url = d['url']
            product_content= await self.get_page_content(product_url)
            product_selector = Selector(text=product_content)
            
            product = self.parse_product(product_selector, product_url)
            if product:
                products.append(product)
            await asyncio.sleep(1)
        
            
        return products


    async def scrape(self):
        results = {}
        all_products = []

        for category_name, category_path in self.categories.items():
            category_url = urljoin(self.base_url, category_path)

            print(f"Scraping category: {category_name}")

            results= await self.scrape_category(category_url)
            all_products.extend(results)
        return all_products

def save_output(data):
    os.makedirs("output", exist_ok=True)
    with open("output/chocolate_test.json", "w") as f:
        json.dump(data, f, indent=4)

async def main():
    scraper = ChocolateScraper()
    results = await scraper.scrape()
    save_output(results)
    print("Scraping done")

if __name__ == "__main__":
    asyncio.run(main())