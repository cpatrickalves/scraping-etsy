# Scraping Etsy

This project was built using * [Scrapy](https://scrapy.org/) (Scraping and Web Crawling Framework).

It contains a set of Spiders to gather data for products in [Etsy Website](www.etsy.com).

### Prerequisites

To run this code, download Python 3 from [Python.org](https://www.python.org/). 
After install, you need to install some Python packages:
```
pip install -r requirements.txt

```
### Usage

Inside the project's folder, run:
```
scrapy crawl search_products -a search='3d printed' -o products.csv
```
To save the results, use -o parameter:
```
scrapy crawl search_products -a search='3d printed' -o products.csv
```
The Spider will create a CSV and Excel files.
