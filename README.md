# Scraping Rental Data From Craigslist

This [code](scraping_example.py) scrapes rental data from Craigslist. For a given url, it scrapes all the listings of that area and produces a .csv file with rents, number of bedrooms, location, GPS coordinates, and distance to downtown.

Then, it generates various statistics by the number of bedrooms as well as regresses rent on bedrooms and distance to downtown. 

You will need these packages:
* requests
* BeautifulSoup
* pandas
* numpy
* geopy
* sklearn
* statsmodels
* seaborn
