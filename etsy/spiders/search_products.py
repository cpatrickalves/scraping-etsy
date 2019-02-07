# -*- coding: utf-8 -*-
#==============================================================================
#title           :search_products.py
#description     :A spider to scrape etsy.com products based on a search string.
#author          :Patrick Alves (cpatrickalves@gmail.com)
#date            :21-01-2019
#usage           :scrapy crawl etsy_search -a search='3d printed' -o products.csv
#python_version  :3.6
#==============================================================================


# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from etsy.items import ProductItem
from scrapy.loader import ItemLoader
from urllib.parse import urlparse


# Spider Class
class ProductsSpider(scrapy.Spider):
    # Spider name
    name = 'search_products'
    allowed_domains = ['etsy.com']
    start_urls = ['https://www.etsy.com/']

    # Max number of items 
    COUNT_MAX = 20
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

            if self.COUNTER <= self.COUNT_MAX:                    
                # Go to the product's page to get the data
                yield scrapy.Request(product_url, callback=self.parse_product)

        # Pagination - Go to the next page 
        if self.COUNTER <= self.COUNT_MAX:    
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
        l.add_value('product_id',response.url.split('/')[4])
        l.add_xpath('title', '//meta[@property="og:title"]/@content')
        l.add_xpath('title', "//h1[@data-listing-id='{}']".format(response.url.split('/')[4]))
        #l.add_value('price', response.xpath('//*[contains(@data-buy-box-region, "price")]//span/text()').extract_first().strip().replace('$','').replace('+',''))
        l.add_xpath('price', '//meta[@property="etsymarketplace:price_value"]/@content')
        l.add_xpath('price', '//meta[@property="product:price:amount"]/@content')
        #l.add_xpath('currency', '//meta[@property="product:price:currency"]/@content')
        #l.add_xpath('currency', '//meta[@property="etsymarketplace:currency_code"]/@content')
        l.add_value('url', '/'.join(response.url.split('/')[2:5]))
        l.add_value('description', " ".join(response.xpath('//*[contains(@id, "description-text")]//text()').extract()).strip())
        #l.add_xpath('description', '//*[@id="description-text"]')
        #l.add_xpath('description', '//meta[@property="og:description"]/@content')
        l.add_xpath('variations', '//*[@data-buy-box-region="variation"]/label')                
        l.add_xpath('rating', '//a[@href="#reviews"]//input[@name="rating"]/@value')
        l.add_xpath('number_of_votes', '//a[@href="#reviews"]/span[last()]/text()', re='(\d+)')
        
        images_sel = response.xpath('//*[@id="image-carousel"]/li')
        l.add_value('count_of_images', len(images_sel))
        l.add_xpath('overview', '//*[@class="listing-page-overview-component"]//li')
        l.add_xpath('favorited_by', '//*[@id="item-overview"]//*[contains(@href, "/favoriters")]/text()', re='(\d+)')
        l.add_xpath('favorited_by', '//*[@class="listing-page-favorites-link"]/text()', re='(\d+)')
        l.add_xpath('store_name', '//span[@itemprop="title"]')
        l.add_xpath('store_name', '//*[@id="shop-info"]//*[@class="text-title-smaller"]')        
        l.add_xpath('store_location', '//*[@id="shop-info"]/div')
        l.add_xpath('return_location',"//*[@class='js-estimated-delivery']/following-sibling::div")
        
        # Increment the counter
        self.COUNTER += 1
        print('\n\n Products scraped: {}\n\n'.format(self.COUNTER))

        return l.load_item()

"""
OK - Name
OK - ID
OK - URL
OK - Listing Title 
OK - Description 
Product options
OK - Price
OK - Store name
OK - Location
OK - Rating number
OK - Number of votes
Return location
OK - Count of images per listing
Product overview
??? - Favorited by (very important)

Reviews:
Rating
Date
Review content
Reviewer profile URL

Item nao existe!!
GERAR CSV
"""

