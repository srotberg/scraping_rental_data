"""
Scraping example
"""

import requests as rq
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import geopy.distance as gp

def get_distance(final_coordinates,initial_coordinates=[43.6536582,-79.39024]):
    """ Returns in km the distance of the property in location 
        final_coordinates from the location initial_coordinates
        
    Args:
        final_coordinates: the coordinates of the property
        initial_coordinates: the location of interest (default to downtown TO)
    """
    
    slat = radians(initial_coordinates[0])
    slon = radians(initial_coordinates[1])
    elat = radians(final_coordinates[0])
    elon = radians(final_coordinates[1])

    # computing distance by longitudes and latitudes
    distance = 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slon - elon))
        
    # returns the computed distance
    return distance

def get_coordinates(url: str):
    """ Returns the longitude and latitude coordinates of the property
        that is listed in web address url
    
    Args:
        url: web address
    """
    
    # command to request the page based on the url
    page=rq.get(url)
        
    # command to parse the page by html
    soup=BeautifulSoup(page.content, 'html.parser')
        
    # gets the results that maps the address to coordaintes 
    results=soup.find('p', class_='mapaddress')
    
    coordinates_url=''
    
    # starts a coordinates list
    coordinates=[]
    
    # checks if there is an map address
    if results:
                
        # gets the full webaddress with the coordinates
        coordinates_url=results.find('a')['href']
            
        # since the coordaintes always appear after the "@" sign, 
        # and are split by a "," x saves the part that comes after the  
        # "@" sign and parses out the string by ","
        x=coordinates_url.split('@')[-1].split(',')
        
        # saves coordinates based on the first and second elements of the split
        coordinates=[float(x[0]),float(x[1])]
        
    # returns the coordinates
    return coordinates
        
def get_data_from_page(url: str, largest_rent=6000.0,smallest_rent=10.0):
    """ Returns all the aapartments for rent on a given page on Craigslist
    exclusing rents below smallest_rent, and if a rent is above largest_rent
    it is assumed to be a mistake that is a multiple of 10 of the true rent
    
    Args:
        url: webpage address
        largest_rent: rent above which the true rent is 10 times smaller than its value
        smallest_rent: smallest rent allowed
    """
    
    # saves the page in the url
    page=rq.get(url)

    # parses the page by html
    soup=BeautifulSoup(page.content, 'html.parser')

    # gets all the listings
    results=soup.find_all('li', class_='result-row')

    #initializes lists for rents, bedrooms,cities,coordinates,and distance
    all_rents=[]
    all_bedrooms=[]
    all_cities=[]
    all_coordinates=[]
    all_distance=[]
    
    # loops over all listings
    for info in results:
    
        # obtains the title info
        title=info.find('p', class_='result-info')  
        
        # obtains the rent
        rent=info.find('span', class_='result-price')
        
        # obtains the rent requested
        bdrms=info.find('span', class_='housing')
        
        # obtains the neighborhood data
        city=info.find('span', class_='result-hood')
        
        # saves the coordinates by calling a function that uses the 
        # webpage of the actual listing
        coordinates=get_coordinates(info.find('a')['href'])
        
        # saves the distance by calling a function that computes
        # distance based on the final coordaintes (the function default is 
        # that the city center is Nathan Phillips Square)
        distance=get_distance(final_coordinates=coordinates)
        
        # initializes city name
        cities = ''
        
        # checks if city is not non
        if city:
            
            # saves the city name by clearing blanks and "(" ")" and then
            # splitting by "," so that only the first part of the text is
            # saved (sometimes there is more text after that is not the city)
            cities=city.text.strip().strip('()').split(',')[0]
                    .
        # saves the rent as a float by taking out the "$" sign from rent
        rnt=float(rent.text.replace('$',''))
                        
        # checks if bdrms is not non
        if bdrms:
            
            # checks if the word "br" is the bdrms 
            if 'br' in bdrms.text.lower():
            
                bdrm=int(bdrms.text.strip()[0])
                
            # if the word "br" is not in bdrms, it is assumed that the 
            # apartment is a studio apartment
            else:
                
                bdrm=0
                
        # if bdrms does not exist it is also assumed that the apartment is
        # a studio
        else:
            
            bdrm=0
                    
        # checks if the title of the listing has the word "sale" in it
        # in order to get rid of apt and houses that are for sale and not for rent
        if ('sale' in title.text.lower()):
        
            pass
        
        # checks if rnt is in the acceptable range
        elif (rnt>=smallest_rent and rnt<largest_rent):
            
            # appaends all the acquired data to the lists we are interested in
            all_rents.append(rnt)
            all_bedrooms.append(bdrm)
            all_cities.append(cities)
            all_coordinates.append(coordinates)
            all_distance.append(distance)
            
        # if rent is above largest_rent, then it is assumed that the true 
        # rent is 10 times smaller than the rnt
        elif (rnt>=largest_rent):
            
            # reduces rnt
            rnt=rnt/10.0
            
            # appaends all the acquired data to the lists we are interested in
            all_rents.append(rnt)
            all_bedrooms.append(bdrm)
            all_cities.append(cities)
            all_coordinates.append(coordinates)
            all_distance.append(distance)
          
    # creating data frame with a dictionary in which the key is the variable name
    # and the value is the extracted value from the website
    df=pd.DataFrame({
            "rent": all_rents,
            "bedroom": all_bedrooms,
            "city": all_cities,
            "coordinates": all_coordinates,
            "distance": distance})

    # returns the data frame created df
    return df

def get_next_url(url: str):
    """ Returns the reference of the next page of listings
    
    Args:
        url: webpage address
    """
    
    # saves the data in the url in page
    page=rq.get(url)

    # parses the page by html
    soup=BeautifulSoup(page.content, 'html.parser')

    # finds the next url by looking at the button "next" at the end of the
    # listing page
    next_url=soup.find('span', class_='buttons')
    
    # returns the url of the next page
    return next_url.find('a', class_='button next')['href']
            
# starts out with this url
url='https://toronto.craigslist.org/d/apts-housing-for-rent/search/apa'
    
# creates a copy of the url in order to later call different pages
url_copy='https://toronto.craigslist.org/d/apts-housing-for-rent'

# initializes the all_data which will be used to produce the final output
all_data=[]

# checks if the url is not empty
while url!='':

    # calls a function that gets all the data from the url page
    # and appends it to all_data
    all_data.append(get_data_from_page(url=url)) 
    
    # calls a function that finds the next page url using the button for next page
    next_url=get_next_url(url)
        
    # checks if there is a next page button
    if next_url!='':
        
        # updaes the url page based on the url_copy and the next_url
        url=url_copy+next_url
       
    else:
        
        # if there is no next page button the url is ''
        url=''
        
# adds up all the data
master_df = pd.concat(all_data)

# saves as a .csv file
master_df.to_csv("toronto_craigslist_data.csv", index=False)
