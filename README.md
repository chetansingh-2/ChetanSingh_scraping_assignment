# ChetanSingh_scraping_assignment

I have made this scraping project for adeptmind.ai company.
There are 3 websites to be scraped. Foreign fortune, traderjoes, le chocolat.

I have made scraper for all 3 sites and along with It I have also created a validation class to check for some data validations.

Now I will explain for each sites.

## 1. Foreign Fortune
   In this code, I have used 3 major functions, scrape, parse_product and extract_models.  
All the information is scraped from source page only and I have avoided any API calls for it.

I am passing my base URL to scrape functions which is getting all the info (meta) about product available on category page, then calling each product URL for further parsing in parse_product function.
Similary after parsing it, parse_product function is further calling extract_model function to scrape the models of the product.

### I have made sure to make it modular. Following the project structure shared I have adhered to it and wrote all functions in code itself.


## 2. TraderJoes
This site was little tricky as no data was available on source page , API was available but it was not be used as per guidelines, So I use pypetteer for it.
It had similar structure as previous one, Scrape and parse_product function.




## 3. Le Chocolat
 This site has multiple category URLs  whhich I have listed in a dict inside code itself. Although during automation I can store all these in a db and pull directly from there. 

Since it had many cat URLs, so I have 3 functions for it, one is scrape which loops over all the cat URLs, then it sends each cat URLs to scrape_category function and similary as in earlier code, it sends again each prod URL to parse_product function.


## 4. Validation pipeline
I have also made a basic validation.py file which checks for ID, price, title, url pattern etc.

I have also tested it on my json, I achieved over 99% accuracy on my scraped product.




## Notes:
1. I have followed the exact json structure as provided to me, so I have made prices and sales_prices as list. Although no sites has sales going on so I have filled same price in it. Also , It will be easy to handle  it if sale comes with little tweak in code.

2. Pypeeteer is little slow than other code, but multiple strategies can be applied to quick it up.

3. I have not used any PROXY service for this project. I have requirements.txt file in this code. By chance if some are missing, I am sorry for that I have checked it while uploading the project, it is running. I did not dockerize it to make it easy to run without much setup





Thanks for reading and evaluating my project.
I would love to hear any improvements or suggestions in this.

thanks again :)


 
