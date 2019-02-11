# -*- coding: utf-8 -*-
#==============================================================================
#title           :search_products.py
#description     :A spider to scrape etsy.com products based on a search string.
#author          :Patrick Alves (cpatrickalves@gmail.com)
#last Update     :07-02-2019
#usage           :scrapy crawl etsy_search -a search='3d printed' -o products.csv
#python version  :3.6
#==============================================================================


# -*- coding: utf-8 -*-
import scrapy
import os
import sys
import csv
import glob
from openpyxl import Workbook
from scrapy.http import Request
from etsy.items import ProductItem
from scrapy.loader import ItemLoader

# Spider Class
class ProductsSpider(scrapy.Spider):
    # Spider name
    name = 'search_products'
    allowed_domains = ['etsy.com']
    start_urls = ['https://www.etsy.com/']

    # Max number of items 
    COUNT_MAX = 2
    custom_settings = { "CLOSESPIDER_ITEMCOUNT" : COUNT_MAX }
    # Count the number of items scraped
    COUNTER = 0

    def __init__(self, search, *args, **kwargs):
        if search:
            self.start_urls = ['https://www.etsy.com/search?q=%s' % search]
        super(ProductsSpider, self).__init__(*args, **kwargs)
      

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


    # Get the HTML from product's page and get the data
    def parse_product(self, response):
        
        # Check if the product is available
        no_available_message = response.xpath('//h2[contains(text(), "Darn")]')
        if no_available_message:
            return []

        # Create the ItemLoader object that stores each product information
        l = ItemLoader(item=ProductItem(), response=response)

        # Get the product ID (ex: 666125766)
        l.add_value('product_id',response.url.split('/')[4])
        
        # Get the produc Title
        l.add_xpath('title', '//meta[@property="og:title"]/@content')
        #l.add_xpath('title', "//h1[@data-listing-id='{}']".format(response.url.split('/')[4]))
        
        # Get the product price
        #price = response.xpath('//*[contains(@data-buy-box-region, "price")]//span/text()').extract_first().strip().replace('+','').split()[1]
        #l.add_value('price', price)
        l.add_xpath('price', '//*[contains(@data-buy-box-region, "price")]//span')
        #l.add_xpath('price', '//meta[@property="etsymarketplace:price_value"]/@content')
        #l.add_xpath('price', '//meta[@property="product:price:amount"]/@content')
        #l.add_xpath('currency', '//meta[@property="product:price:currency"]/@content')
        #l.add_xpath('currency', '//meta[@property="etsymarketplace:currency_code"]/@content')
        
        # Get the product URL (ex: www.etsy.com/listing/666125766)
        l.add_value('url', '/'.join(response.url.split('/')[2:5]))
        
        # Get the product description
        l.add_value('description', " ".join(response.xpath('//*[contains(@id, "description-text")]//text()').extract()).strip())
        #l.add_xpath('description', '//*[@id="description-text"]')
        #l.add_xpath('description', '//meta[@property="og:description"]/@content')

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

        # Separate each option with a | symbol
        l.add_value('product_options', '|'.join(product_options))                

        # Get the product rating (ex: 4.8 )
        l.add_xpath('rating', '//a[@href="#reviews"]//input[@name="rating"]/@value')
        
        # Get the number of votes (number of reviews)
        l.add_xpath('number_of_votes', '//a[@href="#reviews"]/span[last()]/text()', re='(\d+)')
        
        # Count the number of product images 
        images_sel = response.xpath('//*[@id="image-carousel"]/li')
        l.add_value('count_of_images', len(images_sel))
        
        # Get the product overview
        l.add_xpath('overview', '//*[@class="listing-page-overview-component"]//li')
        
        # Get the number of people that add the product in favorites
        #l.add_xpath('favorited_by', '//*[@id="item-overview"]//*[contains(@href, "/favoriters")]/text()', re='(\d+)')
        l.add_xpath('favorited_by', '//*[@class="listing-page-favorites-link"]/text()', re='(\d+)')
        
        # Get the name of the Store and location 
        l.add_xpath('store_name', '//span[@itemprop="title"]')
        #l.add_xpath('store_name', '//*[@id="shop-info"]//*[@class="text-title-smaller"]')        
        l.add_xpath('store_location', '//*[@id="shop-info"]/div')
        l.add_xpath('return_location', "//*[@class='js-estimated-delivery']/following-sibling::div")
        
        # Get return location
#       ]return_loc =  response.xpath("//*[@class='js-estimated-delivery']/following-sibling::div//text()").extract_first().strip()
        #print('\n\n############ '+response.url.split('/')[4]+ ' --- '+return_loc+' ############\n\n')
        #l.add_value('return_location',return_loc)        
        #l.add_xpath('return_location', '//div[contains(text(), "From ")]')
        
        # If set to True, Spider will visit the page with all store reviews and get the reviews for this specific product
        # If set to False, Spider will get only the reviews in the product's page
        get_all_views = True

        if get_all_views:
            # Getting all Reviews        
            store_name = response.xpath('//span[@itemprop="title"]//text()').extract_first()
            # Build the reviews URL
            rev_url = "https://www.etsy.com/shop/{}/reviews?ref=l2-see-more-feedback".format(store_name)
            data = {'itemLoader':l, 'product_id':response.url.split('/')[4]}

            yield Request(rev_url, meta=data, callback=self.parse_reviews)        
        
        else:
            # Increment the items counter
            self.COUNTER += 1
            print('\n\n Products scraped: {}\n\n'.format(self.COUNTER))

            return l.load_item()


    # Parse the Store reviews page
    def parse_reviews(self, response):
        # Get the itemLoader object from parser_products
        l = response.meta['itemLoader']

        # Get the data from each review
        all_reviews = response.xpath("//*[@data-region='review']")
        # Dict that saves all the reviews data
        reviews_data = {}
        reviews_counter = 1

        # Process each review
        for r in all_reviews:
            
            # Get the product id of the review
            product_id = response.xpath("//*[@data-region='listing']//@href").extract_first().split('/')[4]

            # Check if the review if for the product in analysis
            if response.meta['product_id'] == product_id:
                # Get the profile URL of the reviewer
                reviewer_profile = r.xpath(".//*[@class='shop2-review-attribution']//@href").extract_first()
                if reviewer_profile:                
                    # Shorter version of the profile url
                    reviewer_profile = reviewer_profile.split('?')[0]
                else:
                    # If the profile is inactive there is no profile url
                    continue

                reviewer_rating = r.xpath('.//input[@name="rating"]/@value').extract_first()
                review_date = r.xpath(".//*[@class='shop2-review-attribution']//text()").extract()[2].replace('on ','').strip()
                review_content = " ".join(r.xpath('.//div[@class="text-gray-lighter"]//text()').extract()).strip()
                
                rev_data = {'reviewer_profile':reviewer_profile, 
                                'reviewer_rating': reviewer_rating, 
                                'review_date':review_date, 
                                'review_content':review_content}

                reviews_data[reviews_counter] = rev_data
                reviews_counter += 1
                
        # Saves the data
        l.add_value('reviews', reviews_data)
        
        # Go to the next reviews page
        next_page_url = response.xpath("//*[contains(text(),'Next page')]/parent::*/@href").extract_first()        
        # Check if there is a next page
        if next_page_url: 
            # Save the current data 
            data = {'itemLoader':l, 'product_id':product_id}
            # Build the request
            yield Request(next_page_url, meta=data, callback=self.parse_reviews)
               
        else:
            # If there is no next page, saves the data
            # Increment the items counter
            self.COUNTER += 1
            print('\nProducts scraped: {}\n'.format(self.COUNTER))

            return l.load_item()


    # Create the Excel file
    def close(self, reason):
       
        # Check if there is a CSV file in arguments
        csv_found = False
        for arg in sys.argv:
            if '.csv' in arg:
                csv_found = True

        if csv_found:            
            self.logger.info('Creating Excel file')
            #  Get the last csv file created
            csv_file = max(glob.iglob('*.csv'), key=os.path.getctime)

            wb = Workbook()
            ws = wb.active

            with open(csv_file, 'r', encoding='utf-8') as f:
                for row in csv.reader(f):
                    # Check if the row is not empty
                    if row:
                        ws.append(row)
            # Saves the file
            wb.save(csv_file.replace('.csv', '') + '.xlsx')

"""
OK - URL
OK - Listing Title 
OK - Description 
OK - Product options
OK - Price
OK - Store name
OK - Location
OK - Rating number
OK - Number of votes
OK - Return location
OK - Count of images per listing
OK - Product overview
OK - Favorited by (very important)

Reviews:
Rating
Date
Review content
Reviewer profile URL
"""

