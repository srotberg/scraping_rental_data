"""
Heat map example
"""

import pandas as pd
from ast import literal_eval
import geopandas as geopd
import geoplot as gplt 
import geoplot.crs as gcrs
import matplotlib.pyplot as plt
import mplleaflet as mpl

def plotting_heat_map(file_name='toronto_data.csv',\
                      json_name='https://raw.githubusercontent.com/jasonicarter/toronto-geojson/master/toronto_crs84.geojson',\
                      max_distance=15,\
                      min_bedrooms=1,\
                      max_bedrooms=1,\
                      max_rent=5000):
    """ Plots a heat map based on the DataFrame supplied to the function.
    The function plots rents by number of bedrooms on a map
    
    Args:
        file_name: file name to be called (default='toronto_data.csv')
        json_name: file address for the map of the city on which data is superimposed 
                    (defualt='https://raw.githubusercontent.com/jasonicarter/toronto-geojson/master/toronto_crs84.geojson')
        max_distance: exclude renatal that are more than max_distance
                        away from the center (default=5)
        min_bedrooms: excludes rentals with less than min_bedrooms bedrooms
                    (default=0)
        max_bedrooms: excludes rentals with more than max_bedrooms bedrooms
                    (default=0)
        max_rent: excludes rentals that cost more than max_rent 
                    (default=5000)
    """

    # imports the .csv file and tells the data from that coordaintes are a list
    df=pd.read_csv(file_name,converters={'coordinates':literal_eval})
    
    # breaks down the coordinates to lat and long
    df[['lat','long']]=pd.DataFrame(df.coordinates.values.tolist(),index=df.index)

    # drops all the lat and long na observations
    df=df.dropna(subset=['lat'])
    df=df[df['distance']<=max_distance]
    df=df[df['rent']<=max_rent]
    
    # drops all rentals with more than max_bedrooms and less than min_bedrooms
    df=df[df['bedroom']>=min_bedrooms]
    df=df[df['bedroom']<=max_bedrooms]
    
    # creates a new column that keeps both lat and long
    gdf=geopd.GeoDataFrame(df,geometry=geopd.points_from_xy(df.long,df.lat))

    # create backgroup map with city geojson data
    city_json='https://raw.githubusercontent.com/jasonicarter/toronto-geojson/master/toronto_crs84.geojson'
    
    # loading the map for the city
    city_map=geopd.read_file(city_json)
    
    # creating the map
    ax=gplt.webmap(city_map,projection=gcrs.WebMercator())
    
    # plots rents by color on the map of the city
    gplt.pointplot(gdf,ax=ax,hue='rent',legend=True,projection=gcrs.AlbersEqualArea())
        
    # saves the plot as a .png file
    plt.savefig('heat_map_'+file_name.replace('.csv','.png'))
    
   
plotting_heat_map()
