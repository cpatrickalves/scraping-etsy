# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from w3lib.html import remove_tags
from scrapy.loader.processors import MapCompose, TakeFirst, Join

# Remove extras spaces in strings
def strip_space(value):
    return value.strip()

# Put only one space between strings
def normalize_space(value):
    return " ".join(value.split())

# This class defines the fields that will be created
class ProductItem(scrapy.Item):

    # Each item may have a input and output processor
    # Each processor performs a series of transformations on the data before saving it
    
    product_id = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    description = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
    					       output_processor=TakeFirst())

    product_options = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                              output_processor=Join(','))

    price = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                         output_processor=TakeFirst())

    currency = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                            output_processor=TakeFirst())

    rating = scrapy.Field(output_processor=TakeFirst())

    number_of_votes = scrapy.Field(output_processor=TakeFirst())
    count_of_images = scrapy.Field(output_processor=TakeFirst())
    overview = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                            output_processor=Join(','))

    favorited_by = scrapy.Field(output_processor=TakeFirst())
    store_name = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                              output_processor=TakeFirst())
                              
    store_location = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                                  output_processor=TakeFirst())

    return_location = scrapy.Field(input_processor=MapCompose(normalize_space, remove_tags, strip_space),
                                    output_processor=TakeFirst())
