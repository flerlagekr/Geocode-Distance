#  This code will take an input csv file containing IDs and addresses then:
#  1) Geocode the addressess (obtain latitude and longitude)
#  2) Find the distance, in miles, from a central point as defined in the global variables.
#  3) Output a new csv with all the same original fields plus latitude, longitude, and distance.
#
#  Written by Ken Flerlage, January, 2023
#----------------------------------------------------------------------------------------------------------------------------------------

from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from tkinter import filedialog
from tkinter import Tk
import datetime
import os
import pandas

# Global variables.
coordsCentralPoint = (55.8668, -4.2500)                              # Lat/Long of our central point.
userid = "flerlagekr@gmail.com"                                      # User ID needed when using the Nominatim package.

#---------------------------------------------------------------------------------------------------------------------------------------- 
# Prompt for the input csv file.
#---------------------------------------------------------------------------------------------------------------------------------------- 
def get_csv_file():
    root = Tk()
    root.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select CSV File",filetypes = (("Comma-Separated Values","*.csv"),("All Files","*.*")))
    root.withdraw()

    return root.filename 

#-------------------------------------------------------------------------------------
# Log a message.
#-------------------------------------------------------------------------------------
def log(msg):
    timeStamp = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    print(timeStamp + ': ' + msg)

#-------------------------------------------------------------------------------------
# Return the geodesic distance, in miles, between two coordinates.
#-------------------------------------------------------------------------------------
def distance(coords1, coords2):
    # If you want kilometers, change "mi" to "km"
    return geodesic(coords1, coords2).mi

#-------------------------------------------------------------------------------------
# Geocode based on an address.
# We're using a function so we can capture errors when using "apply" on the dataframe.
#-------------------------------------------------------------------------------------
def geocoder(geo):
    geolocator = Nominatim(user_agent=userid)

    try:
        coords = geolocator.geocode(geo)
    except:
        coords = None

    return coords

#----------------------------------------------------------------------------------------------------------------------------------------
# Process the data, geocoding each location and finding the distance from our central point.
#----------------------------------------------------------------------------------------------------------------------------------------
def process_data(fullAddress):
    # Prompt for the input file.
    inFilename = get_csv_file()
    
    if inFilename == "":
        log("No file selected. Exiting program.")
        return

    # Open the input file, loading it into a dataframe.
    dfData = pandas.read_csv(inFilename, index_col='id', dtype={'postalcode': str})

    # Change NaN to ""
    dfData = dfData.fillna("")

    # Create address fields
    if fullAddress == True:
        # Use full version of the address.
        dfData["address"] = dfData.street1 + " " + dfData.street2 + " " + dfData.street3 + " " + dfData.city + " " + dfData.state + " " + dfData.postalcode + " " + dfData.country

        # Change any double spaces to single spaces. Do multiple times to account for concatenation.
        for i in range(1, 7):
            dfData.replace({'  ': ' '}, regex=True, inplace=True)
    
    else:
        # Just use city, state, and country.
        dfData["address"] = dfData.city + " " + dfData.state + " " + dfData.country

        # Change any double spaces to single spaces. Do multiple times to account for concatenation.
        for i in range(1, 3):
            dfData.replace({'  ': ' '}, regex=True, inplace=True)


    # Now geocode the address by applying to the dataframe.
    dfData["geocode"] = dfData.address.apply(geocoder)

    # Get the actual coordinates from the geocode field.
    # Lambda function will handle those rows that couldn't be geocoded, using 0,0.
    # We're using 0,0 as a temporary value, which we'll then change to null.
    dfData["coordinates"] = dfData["geocode"].apply(lambda geo: (0,0) if geo is None else (geo.latitude, geo.longitude))
    dfData["latitude"] = dfData["geocode"].apply(lambda geo: 0 if geo is None else geo.latitude)
    dfData["longitude"] = dfData["geocode"].apply(lambda geo: 0 if geo is None else geo.longitude)

    # Find the distance in miles from the central point.
    dfData["distance"] = dfData.coordinates.apply(distance, coords2=coordsCentralPoint)

    # For invalid geocoding, null the individual coordinates and distance.
    dfData.loc[dfData["coordinates"] == (0,0), ["latitude", "longitude", "distance"]] = None

    # Remove temporary columns.
    dfData.drop(['coordinates','geocode','address'], axis=1, inplace=True)

    # Write an ouput file to the same folder, concatenating "geocode" to the file name.
    outFilename = inFilename[0:-4] + "_geocode.csv"
    dfData.to_csv(outFilename, encoding='utf-8')


#----------------------------------------------------------------------------------------------------------------------------------------
# Main processing routine.
#----------------------------------------------------------------------------------------------------------------------------------------
# Get the time so we can track total runime, then log the start.
startTime = datetime.datetime.now()
log("Code is running locally")

# Process the data using the short address (city, state, country)
process_data(False)

# Determine runtime, then log it.
checkTime = datetime.datetime.now()
dateDiff = checkTime - startTime
secondsRunning = dateDiff.seconds
log("Code completed in " + str(secondsRunning) + " seconds")
