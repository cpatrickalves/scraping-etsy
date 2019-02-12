# Scraping Etsy

This project was built using [Scrapy](https://scrapy.org/) (Scraping and Web Crawling Framework).

It contains a set of Spiders to gather product's data from [Etsy Website](www.etsy.com).

## Prerequisites

To run the Spiders, download Python 3 from [Python.org](https://www.python.org/). 
After install, you need to install some Python packages:
```
pip install -r requirements.txt

```
## Usage

### Spider: search_products.py

This Spider access the Etsy website and search for products based on a given search string.

Supported parameters:
* *search* - set the search string
* *reviews_option* - set the method to get the product's reviews

For example, to search for '3d printed' products go to the project's folder and run:
```
scrapy crawl search_products -a search='3d printed' 
```
To save the results, use -o parameter:
```
scrapy crawl search_products -a search='3d printed' -o products.csv
```
The Spider will create a CSV and Excel files.

The *product reviews* data can be obtained in three ways:
* 1 - Spider will get only the reviews in the product's page, the default value is 4 reviews. This is the default and fastest option for scraping.
* 2 - Spider will produce an Ajax request to get all reviews in the product's page (simulate the click in the *+More* button to load more reviews). In this option, the Spider will get a maximum of 10 reviews.
* 3 - Spider will visit the page with all store reviews (click in the *Read All Reviews* button) and get all the reviews for this specific product. As the Spider will visit several pages to get the reviews, this is the slower scraping option and there is a chance to get temporarily blocked by Etsy because of the high number of requests.

To choose the option to scraping the reviews use the *-a reviews_option* parameter:
```
scrapy crawl search_products -a search='3d printed' -a reviews_option=3 -o products.csv
```

