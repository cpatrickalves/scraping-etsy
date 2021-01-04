# -*- coding: utf-8 -*-
#==============================================================================
#title           :search_products.py
#description     :A spider to scrape etsy.com products based on a search string.
#author          :Patrick Alves (cpatrickalves@gmail.com)
#last Update     :12-02-2019
#usage           :scrapy crawl search_products -a search='3d printed' -o products.csv
#python version  :3.6
#==============================================================================


import scrapy
import os
import sys
import csv
import glob
import json
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
    COUNT_MAX = 10**100
    # Count the number of items scraped
    COUNTER = 0

    # Set the method to get the product reviews
    # If set to 1 (default), Spider will get only the reviews in the product's page, the default value is 4 reviews [FAST SCRAPING]
    # If set to 2, Spider will produce a Ajax request to get all reviews in the product's page, that is, a maximum of 10 reviews
    # If set to 3, Spider will visit the page with all store reviews and get all the reviews for this specific product [SLOWER SCRAPING]
    reviews_opt = None

    def __init__(self, search, reviews_option=1, count_max=None,*args, **kwargs):
        if search:
            # Build the search URL
            self.start_urls = ['https://www.etsy.com/search?q={}&ref=pagination&page=1'.format(search)]
            # Set the maximum number of items to be scraped
            if count_max:
                self.COUNT_MAX = int(count_max)

            # Set the chosen review option
            self.reviews_opt = int(reviews_option)

        super(ProductsSpider, self).__init__(*args, **kwargs)


    # Parse the first page result and go to the next page
    def parse(self, response):

        # Get the list of products from html response
        products_list = response.xpath('//*[contains(@class, "organic-impression")]')

        # Stops if there is no product to scrape
        if len(products_list) == 0:
            raise scrapy.exceptions.CloseSpider(reason='All products scraped - {} items'.format(self.COUNTER))

        # For each product extracts the product URL
        for product in products_list:
            product_url = product.xpath("./@href").extract_first()

            # Stops if the COUNTER reaches the maximum set value
            if self.COUNTER < self.COUNT_MAX:
                # Go to the product's page to get the data
                yield scrapy.Request(product_url, callback=self.parse_product)

        # Pagination - Go to the next page
        current_page_number = int(response.url.split('=')[-1])
        next_page_number = current_page_number + 1
        # Build the next page URL
        next_page_url = '='.join(response.url.split('=')[:-1]) + '=' + str(next_page_number)
        yield scrapy.Request(next_page_url)


    # Get the HTML from product's page and get the data
    def parse_product(self, response):

        # Stops if the COUNTER reaches the maximum set value
        if self.COUNTER >= self.COUNT_MAX:
            raise scrapy.exceptions.CloseSpider(reason='COUNT_MAX value reached - {} items'.format(self.COUNT_MAX))

        # Check if the product is available
        no_available_message = response.xpath('//h2[contains(text(), "Darn")]')
        if no_available_message:
            return []

        # Create the ItemLoader object that stores each product information
        l = ItemLoader(item=ProductItem(), response=response)

        # Get the product ID (ex: 666125766)
        product_id = response.url.split('/')[4]
        l.add_value('product_id', product_id)

        # Get the produc Title
        #l.add_xpath('title', '//meta[@property="og:title"]/@content')
        l.add_xpath('title', '//div[@data-component="listing-page-title-component"]/h1/text()')
        #l.add_xpath('title', "//h1[@data-listing-id='{}']".format(response.url.split('/')[4]))

        # Get the product price
        l.add_xpath('price', '//*[contains(@data-buy-box-region, "price")]//p')

        # Get the product URL (ex: www.etsy.com/listing/666125766)
        l.add_value('url', '/'.join(response.url.split('/')[2:5]))

        # Get the product description
        l.add_value('description', " ".join(response.xpath('//*[contains(@id, "description-text")]//text()').extract()).strip().replace(' + More - Less',''))

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

        # Separate each option with a | (pipe) symbol
        l.add_value('product_options', '|'.join(product_options))

        # Get the product rating (ex: 4.8 )
        l.add_xpath('rating', '//a[@href="#reviews"]//input[@name="rating"]/@value')

        # Get the number of votes (number of reviews)
        l.add_xpath('number_of_reviews', '//button[@id="same-listing-reviews-tab"]/span/text()')

        # Count the number of product images
        images_sel = response.xpath('//ul[@data-carousel-pagination-list=""]/li/img/@data-src-delay').extract()
        l.add_value('count_of_images', len(images_sel))
        l.add_value('images_urls', images_sel)

        # Get the product overview
        l.add_xpath('overview', '//*[@class="listing-page-overview-component"]//li')

        # Get the number of people that add the product in favorites
        l.add_xpath('favorited_by', '//*[@id="item-overview"]//*[contains(@href, "/favoriters")]/text()', re='(\d+)')
        l.add_xpath('favorited_by', '//*[@class="listing-page-favorites-link"]/text()', re='(\d+)')
        l.add_xpath('favorited_by', '//a[contains(text(), " favorites")]/text()', re='(\d+)')

        # Get the name of the Store and location
        l.add_xpath('store_name', '//div[@id="listing-page-cart"]//span/text()')
        #l.add_xpath('store_location', '//*[@id="shop-info"]/div')
        #l.add_xpath('return_location', "//*[@class='js-estimated-delivery']/following-sibling::div")

        # Use the chosen method to get the reviews
        self.logger.info('Reviews scraping option: ' + str(self.reviews_opt))

        # Option 3 - All reviews
        if self.reviews_opt == 3:
            # Getting all Reviews
            store_name = response.xpath('//span[@itemprop="title"]//text()').extract_first()
            # Build the reviews URL
            rev_url = "https://www.etsy.com/shop/{}/reviews?ref=l2-see-more-feedback".format(store_name)
            data = {'itemLoader':l, 'product_id':product_id}

            # Go to the all reviews page
            yield Request(rev_url, meta=data, callback=self.parse_reviews)

        # Option 2 - Ajax request
        elif self.reviews_opt == 2:
            # Creating the Ajax request
            # Getting the session cookie
            get_cookie = response.request.headers['Cookie'].split(b';')[0].split(b'=')
            cookies = {get_cookie[0].decode("utf-8"):get_cookie[1].decode("utf-8")}

            # Getting the x-csrf-token
            headers = {'x-csrf-token': response.xpath("//*[@name='_nnc']/@value").extract_first()}

            # Shop Id
            shop_id = response.xpath("//*[@property='og:image']/@content").extract_first().split('/')[3]

            formdata = {
            'stats_sample_rate': '',
            'specs[reviews][]': 'Listzilla_ApiSpecs_Reviews',
            'specs[reviews][1][listing_id]': product_id,
            'specs[reviews][1][shop_id]': shop_id,
            'specs[reviews][1][render_complete]': 'true'
            }

            data = {'itemLoader':l, 'product_id':product_id}
            ajax_url = "https://www.etsy.com/api/v3/ajax/bespoke/member/neu/specs/reviews"

            yield scrapy.FormRequest(ajax_url, headers=headers, cookies=cookies,
                                    meta=data, formdata=formdata,
                                    callback=self.parse_ajax_response)
        # Option 1
        else:
            # Dict that saves all the reviews data
            reviews_data = []
            reviews_counter = 1

            # Get the data from each review
            all_reviews = response.xpath('//*[@class="listing-page__review col-group pl-xs-0 pr-xs-0"]')
            # Process each review
            for r in all_reviews:

                # Get the profile URL of the reviewer
                reviewer_profile = r.xpath(".//*[@class='display-block']/parent::*//@href").extract_first()
                if reviewer_profile:
                    # Build the full profile url
                    reviewer_profile = 'www.etsy.com' + reviewer_profile
                else:
                    # If the profile is inactive there is no profile url
                    continue

                review_date = r.xpath(".//*[@class='text-link-underline display-inline-block mr-xs-1']/parent::*//text()").extract()[2].strip()
                reviewer_rating = r.xpath('.//input[@name="rating"]/@value').extract_first()
                review_content = " ".join(r.xpath('.//div[@class="overflow-hidden"]//text()').extract()).strip()

                # Build the review string
                rev_data = "Review number: {} \nProfile: {} \nRating: {} \nDate: {} \nContent: {}".format(reviews_counter, reviewer_profile, reviewer_rating, review_date, review_content)

                # Save into the list
                reviews_data.append(rev_data)
                reviews_counter += 1

            # Saves all reviews data
            l.add_value('reviews', "\n\n".join(reviews_data))

            # Increment the items counter
            self.COUNTER += 1
            print('\nProducts scraped: {}\n'.format(self.COUNTER))

            yield l.load_item()


    # Parse the Ajax response (Json) and extract reviews data
    def parse_ajax_response(self, response):
        # Get the itemLoader object from parser_products
        l = response.meta['itemLoader']

        # Dict that saves all the reviews data
        reviews_data = []
        reviews_counter = 1

        # Loads the Json data
        j = json.loads(response.text)
        html = j["output"]["reviews"]
        # Create the Selector
        sel = scrapy.Selector(text=html)

        # Get the data from each review
        all_reviews = sel.xpath('//*[@class="listing-page__review col-group pl-xs-0 pr-xs-0"]')
        # Process each review
        for r in all_reviews:

            # Get the profile URL of the reviewer
            reviewer_profile = r.xpath(".//*[@class='display-block']/parent::*//@href").extract_first()
            if reviewer_profile:
                # Build the full profile url
                reviewer_profile = 'www.etsy.com' + reviewer_profile
            else:
                # If the profile is inactive there is no profile url
                continue

            review_date = r.xpath(".//*[@class='text-link-underline display-inline-block mr-xs-1']/parent::*//text()").extract()[2].strip()
            reviewer_rating = r.xpath('.//input[@name="rating"]/@value').extract_first()
            review_content = " ".join(r.xpath('.//div[@class="overflow-hidden"]//text()').extract()).strip()

            # Build the string
            rev_data = "Review number: {} \nProfile: {} \nRating: {} \nDate: {} \nContent: {}".format(reviews_counter, reviewer_profile, reviewer_rating, review_date, review_content)

            # Saves the string in a list
            reviews_data.append(rev_data)
            reviews_counter += 1

        # aves all reviews data
        l.add_value('reviews', "\n\n".join(reviews_data))

        # Increment the items counter
        self.COUNTER += 1
        print('\nProducts scraped: {}\n'.format(self.COUNTER))

        yield l.load_item()


    # Parse the Store reviews page
    def parse_reviews(self, response):
        # Get the itemLoader object from parser_products
        l = response.meta['itemLoader']

        # Dict that saves all the reviews data
        # Check if this is the first access or if there is data from another reviews page
        if 'reviews_data' in response.meta.keys():
            reviews_data = response.meta['reviews_data']
            reviews_counter = response.meta['reviews_counter']
        else:
            reviews_data = []
            reviews_counter = 1

        # Get the data from each review
        all_reviews = response.xpath("//*[@data-region='review']")

        # Process each review
        for r in all_reviews:

            # Get the product id of the review
            product_id = response.xpath("//*[@data-region='listing']//@href").extract_first().split('/')[4]

            # Check if this is the product in analysis
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

                # Build the string
                rev_data = "Review number: {} \nProfile: {} \nRating: {} \nDate: {} \nContent: {}".format(reviews_counter, reviewer_profile, reviewer_rating, review_date, review_content)

                # Saves the string in a list
                reviews_data.append(rev_data)
                reviews_counter += 1

        # Go to the next reviews page
        next_page_url = response.xpath("//*[contains(text(),'Next page')]/parent::*/@href").extract_first()
        # Check if there is a next page
        if next_page_url:
            # Save the current data
            data = {'itemLoader':l, 'product_id':product_id, 'reviews_data':reviews_data, 'reviews_counter':reviews_counter}
            # Build the request
            yield Request(next_page_url, meta=data, callback=self.parse_reviews)

        else:
            # If there is no next page, saves the data
             # Saves the data
            l.add_value('reviews', "\n\n".join(reviews_data))
            # Increment the items counter
            self.COUNTER += 1
            print('\nProducts scraped: {}\n'.format(self.COUNTER))

            yield l.load_item()


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
