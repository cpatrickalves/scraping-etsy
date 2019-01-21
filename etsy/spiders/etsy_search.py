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


class EtsySearchSpider(scrapy.Spider):
    name = 'etsy_search'
    allowed_domains = ['www.etsy.com']
    start_urls = ['http://www.etsy.com/']

    # Defining the search string
    def __init__(self, search=None):
        search_url = "https://www.etsy.com/search?q="

        if search:
            search_url += search

        self.start_urls = [search_url]


    # Parse the first page result and go to the next page
    def parse(self, response):
        scrapy.utils.response.open_in_browser(response)
