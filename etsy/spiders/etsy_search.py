# -*- coding: utf-8 -*-
#==============================================================================
#title           :etsy_search.py
#description     :A spider to scrape etsy.com products based on a search string.
#author          :Patrick Alves (cpatrickalves@gmail.com)
#date            :21-01-2019
#usage           :scrapy crawl etsy_search -a search='3d printed' -o products.csv
#python_version  :3.6
#==============================================================================

import scrapy


# Spider Class
class EtsySearchSpider(scrapy.Spider):
    name = 'etsy_search'                    
    allowed_domains = ['www.etsy.com']      
    start_urls = ['http://www.etsy.com/']   

    # Setting the search string
    def __init__(self, search=None):
        search_url = "https://www.etsy.com/search?q="

        if search:
            search_url += search
        else:
            search = input("Please, type the search string:")
            search_url += search

        self.start_urls = [search_url]


    # Parse the first page result and go to the next page
    def parse(self, response):
        
        # Get the list of products from html response
        products_list = response.xpath('//*[contains(@class, "organic-impression")]')
        # For each product extracts the product URL
        for product in products_list:
            product_url = product.xpath("./@href").extract_first()
            
            # Go to the product's page to get the data
            yield scrapy.Request(product_url, callback=self.parse_product)

        # Pagination - Go to the next page 
        next_page_url = response.xpath('//*[contains(@role, "navigation")]//@href').extract()[-1]
        self.logger.info('NEXT PAGE')
        yield scrapy.Request(next_page_url)


    def parse_product(self, response):

        # Check if the product is available
        no_available_message = response.xpath('//h2[contains(text(), "Darn")]')
        if no_available_message:
            return []

        # Getting product's data
        product_url = '/'.join(response.url.split('/')[2:5])
        product_id = response.url.split('/')[4]
        product_name = response.xpath("//h1[@data-listing-id='{}']//text()".format(product_id)).extract_first()
        product_description = " ".join(response.xpath('//*[contains(@id, "description-text")]//text()').extract()).strip()
        product_price = response.xpath('//*[contains(@data-buy-box-region, "price")]//span/text()').extract_first().strip().replace('$','').replace('+','')
        
        # Get each product option and save in a list
        product_options = []
        product_options_list = response.xpath('//*[contains(@id, "inventory-variation-select")]')
        for options in product_options_list:
            # Get list of options
            temp_list = options.xpath('.//text()').extract()
            # Remove '\n' strings
            temp_list = list(map(lambda s: s.strip(), temp_list))
            # Remove empty strings ('')
            temp_list = list(filter(lambda s: s != '', temp_list))

            # Filter the 'Quantity' option
            if temp_list[0] != '1':
                # Create the final string:
                # example: "Select a color: White, Black, Red, Silver"
                product_options.append(temp_list[0] +': ' + ', '.join(temp_list[1:]))

        yield{
            'Title': product_name,
            'Description': product_description,
            'Price': product_price,
            'Product_Options': product_options,
            'product_id': product_id,
            'URL' : product_url
        }



"""
OK - URL
OK - Listing Title 
OK - Description 
OK - Product options
OK - Price
Store name
Location
Rating number
Number of votes
Return location
Count of images per listing
Product overview
Favorited by (very important)

Reviews:
Rating
Date
Review content
Reviewer profile URL
"""

