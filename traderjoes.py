from typing import List, Dict, Any
from parsel import Selector
from pyppeteer import launch
import asyncio
import json
import os
import re
from urllib.parse import urljoin

class TraderJoesScraper:
    """ trader joes scrapper"""
    def __init__(self):
        self.base_url = "https://www.traderjoes.com/home/products/category/products-2"
        self.browser = None
        self.page = None
        
    async def init_browser(self):
        try:
            self.browser = await launch(
                headless=True,  
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-gpu'  
                ]
            )
            self.page = await self.browser.newPage()
           
            await self.page.setViewport({'width': 1920, 'height': 1080})
            await self.page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        except Exception as e:
            print(f"Browser initialization error: {e}")
            if self.browser:
                await self.browser.close()
            raise
        
    async def close_browser(self):
        if self.browser:
            await self.browser.close()
            
    async def get_page_content(self, url: str) -> str:
        try:
            response = await self.page.goto(
                url, 
                {'waitUntil': 'networkidle0', 'timeout': 30000}
            )
            if not response:
                print(f"Failed to get response for {url}")
                return None
                
            content = await self.page.content()
            return content
                
        except Exception as e:
            print(f"Error getting page content for {url}: {e}")
            return None
             
    def clean_price(self, price_str: str) -> float:
        try:
            return float(price_str.replace('$', '').strip())
        except (ValueError, AttributeError):
            return 0.0
        
    async def auto_scroll(self):
        try:
            await self.page.evaluate('''
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            ''')
        except Exception as e:
            print(f"Error during scrolling: {e}")
            
    def parse_product(self, selector: Selector, meta) -> Dict[str, Any]:
       
        try: 

            description= selector.xpath("//div[@class='Expand_expand__container__3COzO']/div/p/text()").getall()
            cleaned_description = " ".join(text.strip() for text in description)
            ingredients= selector.xpath("(//div[@class='Container_defaultContainer__yz3tT defaultContainer'])[7]//text()").getall()
            cleaned_ingredients = " ".join(text.strip() for text in ingredients)

            id = meta['url'].split("-")[-1]

            product = {
                "id": id,
                "title": selector.xpath("//h1[@class='ProductDetails_main__title__14Cnm']/text()").get(),
                "image": meta['image'],
                "price":meta['price'],
                "description": cleaned_description,
                "ingredients section": cleaned_ingredients,
                "sales_prices":[meta['price']],
                "prices":[meta['price']],
                "images": [meta["images"]],
                "url": meta['url'],
                "brand": meta['brand'],
                "models": []
            }
            
            
            
            return product
            
        except Exception as e:
            print(f"Error parsing product: {e}")
            return {}

    async def scrape(self) -> List[Dict[str, Any]]:
        try:
            await self.init_browser()
            if not self.browser or not self.page:
                raise Exception("Failed to initialize browser")
            products = []
            page = 1
            
            while True:
                url = f"{self.base_url}?filters=%7B%22page%22%3A{page}%7D" if page > 1 else self.base_url
                print(f"Scraping page {page}: {url}")
                
                content = await self.get_page_content(url)
                selector = Selector(text=content)

                
                product_list = selector.xpath("//ul[@class='ProductList_productList__list__3-dGs']/li").getall()
                
                if not product_list:
                    print(f"No products found on page {page}. Stopping pagination.")
                    break
                
                for element in product_list:
                    sel = Selector(text=element)
                    try:
                        url = sel.xpath("//section/a/@href").get()
                        image = sel.xpath("//section/a/div//source/@srcset").get()
                        price = sel.xpath("//section/div/div[@class='ProductPrice_productPrice__1Rq1r ProductCard_card__productPrice__1W4Le']/div/span[@class='ProductPrice_productPrice__price__3-50j']/text()").get()
                        unit = sel.xpath("//section/div/div[@class='ProductPrice_productPrice__1Rq1r ProductCard_card__productPrice__1W4Le']/div/span[@class='ProductPrice_productPrice__unit__2jvkA']/text()").get()
                        
                        if not all([url, image, price]):
                            print(f"Skipping product due to missing required fields")
                            continue
                        
                        meta_info = {
                            "url": f"https://www.traderjoes.com{url}",
                            "image": f"https://www.traderjoes.com{image}",
                            "price": self.clean_price(price),
                            "sales_prices": [price],
                            "prices": [price],
                            "images": f"https://www.traderjoes.com{image}",
                            "brand": "TRADERJOES",
                        }
                        
                        product_content = await self.get_page_content(meta_info['url'])
                        product_selector = Selector(text=product_content)
                        product = self.parse_product(product_selector, meta=meta_info)
                        
                        if product:
                            products.append(product)
                            print(f"Successfully scraped product: {meta_info['url']}")
                        
                    except Exception as e:
                        print(f"Error processing product: {e}")
                        continue
                
                print(f"Completed page {page}. Products so far: {len(products)}")
                page += 1
                
                
                
            return products
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        
        finally:
            await self.close_browser()


def save_output(products: List[Dict[str, Any]]):
    """Save scraped data to JSON file"""
    os.makedirs("output", exist_ok=True)
    with open("output/traderjoes.json", "w") as f:
        json.dump(products, f, indent=2)

async def main():
    try:
        tj_scraper = TraderJoesScraper()
        products = await tj_scraper.scrape()
        save_output(products)
        print(f"Total products scraped: {len(products)}")
        print("Output saved")
    except Exception as e:
        print(f"Main error: {e}")
    finally:
        if tj_scraper and tj_scraper.browser:
            await tj_scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(main())