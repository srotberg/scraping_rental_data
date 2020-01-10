"""
Scraping example. You will need to go to the bottom of the code and provide the url and file name you wish to have.
"""

import requests as rq
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import geopy.distance as gp
import math
from sklearn import linear_model
import statsmodels.api as sm
import seaborn as sns
from datetime import date

def scrape_data(url,\
                scrape,file_name):
    """This function take url as the website address and loops over all
    the listings in that url. It saves a DataFrame which includes: rents,
    numbers of bedrooms, location, GPS coordaintes, and distance to downtown 
    (default is Toronto)
    
    Args:
        url: the website url
        scrape: takes 0 or 1. 
                0 means that the program is using an existing DataFrame
                1 means that the program will scrape new data
        file_name: this is name of the output file or the file to read
    """
    
    if scrape==1:
    
        # creates a copy of the url in order to later call different pages
        # it takes out the part that says "/search/apa"
        url_copy=url.replace('/search/apa','')
        
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
        
        date_today=date.today()
        
        # saves as a .csv file
        master_df.to_csv(file_name+str(date_today), index=False)
        
    else:
    
        # saves as a .csv file
        master_df=pd.read_csv(file_name)
        
    # gives a full description of the data
    description=master_df.groupby("bedroom").describe()
    
    print(description)
    
    regress_rent_on_bdrms_distance(master_df)
    
def get_data_from_page(url: str, largest_rent=6000.0,smallest_rent=10.0,exclude_distance=50):
    """ Returns all the aapartments for rent on a given page in the url
    exclusing rents below smallest_rent, and if a rent is above largest_rent
    it is assumed to be a mistake that is a multiple of 10 of the true rent
    
    Args:
        url: webpage address
        largest_rent: rent above which the true rent is 10 times smaller than its value
        smallest_rent: smallest rent allowed
        exclude_distance: this excludes rentals that are located over a certain
                          distance from the initial coordainte. The default is 50
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
                    
        # checks if the title of the listing has the word "sale" in it or if the distance
        # is above exclude_distance from the initial coordinate
        # in order to get rid of apt and houses that are for sale and not for rent
        # and those that are too far to be considered as part of the city
        if ('sale' in title.text.lower() or distance>exclude_distance):
        
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
            "distance": all_distance})
    
    # returns the data frame created df
    return df

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

def get_distance(final_coordinates,initial_coordinates=[43.6536582,-79.39024]):
    """ Returns in km the distance of the property in location 
        final_coordinates from the location initial_coordinates
        
    Args:
        final_coordinates: the coordinates of the property
        initial_coordinates: the location of interest (default to downtown TO)
    """
    
    # checks if there are final coordinates
    if (len(final_coordinates)==2):
    
        slat = math.radians(initial_coordinates[0])
        slon = math.radians(initial_coordinates[1])
        elat = math.radians(final_coordinates[0])
        elon = math.radians(final_coordinates[1])

        # computing distance by longitudes and latitudes
        distance = 6371.01 * math.acos(math.sin(slat)*math.sin(elat) + \
                                       math.cos(slat)*math.cos(elat)*\
                                       math.cos(slon - elon))
     
    # if there are no final coordinates, then it saves distance as a negative
    else:
            
        distance=-1.0
                    
    # returns the computed distance
    return distance
        
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

def regress_rent_on_bdrms_distance(df):
    """ Regresses rent on bedroom and distance to understand the relationships
    between them.
    
    Args:
        df: DataFrame to use
    """
    
    # sets the regression variables
    X = df[['bedroom','distance']]
    Y = df['rent']

    # with sklearn
    regr=linear_model.LinearRegression()
    regr.fit(X, Y)
    
    print('An average studio in the initial coordinates costs:',\
          regr.intercept_, 'dollars')
    print('One additional bedroom conditional on location costs:', \
          regr.coef_[0], 'dollars')
    print('Conditional on number of bedrooms, moving one km away from the initial coordiates saves:', \
          regr.coef_[1], 'dollars')
    
    # plots rent on distance for studio apartments
    sns.scatterplot(x='distance',y='rent',data=df[df['bedroom']==0])
    
# checks if functions are run from the main page or from another script
# if it's run from another script, we want to avoid going through the whole
# code in the main script
if __name__=="__main__":  
    scrape_data('here is where you plug in your url',\
                scrape=1,file_name='your_file_name.csv')
