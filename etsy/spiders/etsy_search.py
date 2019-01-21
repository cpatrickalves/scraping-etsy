# -*- coding: utf-8 -*-
import scrapy


class EtsySearchSpider(scrapy.Spider):
    name = 'etsy_search'
    allowed_domains = ['www.etsy.com']
    start_urls = ['http://www.etsy.com/']

    def parse(self, response):
        pass
