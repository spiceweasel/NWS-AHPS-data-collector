import os
import re
import sys
from urllib import request
import time, datetime
import decimal
from operator import attrgetter
from collections import namedtuple

import urllib
from xml.dom.minidom import parseString

# Identifiers used for the output file names
OBSERVED_FILE_IDENT = "observed"
FORECAST_FILE_IDENT = "forecast"
RATING_FILE_IDENT = "rating"

COLLECTION_ROOT = "./nws/"                  # The directory where gage data will be stored
FILE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # The string used for datetime formatting of output values
NWS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"   # The string used for datetime formatting of input values

# The URL to the resource where data will be obtained
# NOTE: be sure to include positional parameters "{}" where the gage id can be inserted!
COLLECTION_URL = "http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage={}&output=xml"

# Headers for the various files
OBSERVATION_DATA_HEADER = "date\tstage\tflow"
FORECAST_DATA_HEADER = "date\tstage\tflow"
RATING_DATA_HEADER = "stage\tstage units\tflow\tflow units"

# Named tuples
Observation = namedtuple('Observation', ['datetime', 'stage', 'flow'])
Forecast = namedtuple('Forecast', ['datetime', 'stage', 'flow'])
Rating = namedtuple('Rating', ['stage', 'stageUnits', 'flow', 'flowUnits'])


#TODO: Issue a warning in a log if the observations are not in UTC


class IncomingDataManager:
    """Manages the collection of forecast and observations."""
    def __init__(self, gageId):
        self.observationMonths = {}
        self.forecastReport = None
        self.years = []
        self.gageId = gageId
        
    def addForecast(self, forecast):
        """Add a forecast observation to the forecast list."""
        self.forecastReport.addForecast(forecast)
    
    def addObservation(self, observation):
        """Add an observation to the observation dataset."""
        # Get the year/month from the observation
        obskey = '{0:%Y%m}'.format(observation.datetime)
        
        if obskey not in self.observationMonths:
            self.observationMonths[obskey] = ObservationMonth(self.gageId, 
                                                              observation.datetime.year, 
                                                              observation.datetime.month)
        
        # Make sure the years array has an entry for each of the years observed
        if not observation.datetime.year in self.years:
            self.years.append(observation.datetime.year)
        
        self.observationMonths[obskey].addObservation(observation)
            
    def getGageId(self):
        """Returns the gage id this manager is managing."""
        return self.gageId
    
    def getYears(self):
        """Get the years that this manager is managing."""
        return self.years
        
    def save(self):
        """Save each of the observation reports."""
        
        # Save the observation report
        for obs in (self.observationMonths[obsm].save() for obsm in self.observationMonths): pass
        
        # Save the forecastreport
        if self.forecastReport:
            self.forecastReport.save()

    def startForecast(self, datetime):
        """Begins the forecast reporing process."""
        self.forecastReport = ForecastReport(self.gageId, datetime)
       

class ObservationMonth:
    """Temporarly holds data from NWS gage observations and can save/append to a file."""
    months = [str(n) for n in range(1, 13)]
     
    def __init__(self, gageId, year, month):
        # Set the month and year to valid times
        self.gageId = gageId
        self.month = str(month) if str(month) in self.months else None
        self.year = str(year) or '1800'
        self.observations = []
                
        month_path = os.path.join(COLLECTION_ROOT, self.gageId, str(year))
        
        self.monthFile = os.path.join(month_path, OBSERVED_FILE_IDENT + "." + str(year) + "%02d" % month)
                                  
        if not os.path.exists(month_path):
            os.makedirs(month_path)
        
        # Establish a last saved point from an existing file.
        if os.path.exists(self.monthFile):
            sp = self._getLastSavedPointFromFile(self.monthFile)
            if sp: self.lastSavedPoint = sp
        else:
            # Set the saved point to the beginning of time
            self.lastSavedPoint = datetime.datetime(datetime.MINYEAR, 1, 1)
        
    def _getLastSavedPointFromFile(self, filename):
        """Used to return the last time that was saved to an existing file."""
        mfile = open(filename, "rb")
        mfile.seek(-2, os.SEEK_END)
        while mfile.read(1) != b"\n":
            mfile.seek(-2, os.SEEK_CUR)
        last = mfile.readline()
        mfile.close()
        if last:
            last = last.decode("utf-8")
            #print("Last is: " + last)
            tab_patt = re.compile("[^\t]+")
            last_datetime = tab_patt.findall(last)[0]
            return datetime.datetime.strptime(last_datetime, FILE_DATETIME_FORMAT)
        return None
        
    def addObservation(self, observation):
        """Add an observed data point to the list."""
        # TODO: Is the datum part of the month else return false
        
        # Since an existing file for the month in question can exist,
        # do not add any times that before the last saved point in the 
        # existing file.  Otherwise last saved point should represent  
        # the earliest time possible so that all added times get saved.  
        if observation.datetime > self.lastSavedPoint:
            self.observations.append(observation)
        
    def getObservations(self):
        """ Returns a list sorted time ascending of the observations. """
        return sorted(self.observations, key=attrgetter('datetime'))

    def save(self):
        """ Write the new observations to the output file. """
        # No need to try to save if there are no observations
        if not len(self.observations):
            return
        
        file_exists = os.path.exists(self.monthFile)
        #print("Observations count %d" % len(self.observations))
        with open(self.monthFile, "a") as mfile:
            if not file_exists:
                mfile.write(OBSERVATION_DATA_HEADER + "\t" + self.gageId)
            for ob in self.getObservations():
                mfile.write("\n%s\t%s\t%s" % (ob.datetime, ob.stage, ob.flow))
        

class ForecastReport:
    """ Temporarily holds data from a NWS forecast and after collection can save 
    the data to an output file."""
    def __init__(self, gageId, datetime_issued):
        self.collectionTime = datetime.datetime.now() 
        self.forecasts = []
        self.gageId = gageId
        self.datetime_issued = datetime_issued
    
    def addForecast(self, forecast):
        """ Add a forecast to the list."""
        self.forecasts.append(forecast)
    
    def save(self):
        """ Save the accumulated forecast data to an output file."""
        if not len(self.forecasts):
            return
        
        save_path = os.path.join(COLLECTION_ROOT, self.gageId, str(self.datetime_issued.year))
        save_name = FORECAST_FILE_IDENT + "." + '{0:%Y%m%d%H%M}'.format(self.datetime_issued)
        save_file_name = os.path.join(save_path, save_name)
        
        if os.path.exists(save_file_name):
            # forecast already exists
            print("Forecast report already exists %s" % save_file_name)
            return
            
        with open(save_file_name, "w") as ffile:
            ffile.write(FORECAST_DATA_HEADER + "\t" + self.gageId)
            for fc in self.forecasts:
                ffile.write("\n%s\t%s\t%s" % (fc.datetime, fc.stage, fc.flow))


class RatingReport:
    """ Temporarly Holds data from an NWS gage rating and can save the data to
    a file."""
    
    def __init__(self, gageId, year):
        self.ratings = []
        self.gageId = gageId
        self.year = year
        
        self.saveFileName = os.path.join(COLLECTION_ROOT, self.gageId, str(self.year), RATING_FILE_IDENT + "." + str(self.year))
    
    def addRating(self, rating):
        """ Add a rating to the list."""
        self.ratings.append(rating)
        
    def ratingFileExists(self):
        """Checks to see if a rating file exists for the year of this report."""
        return os.path.exists(self.saveFileName)
        
    def save(self):
        """Save the rating report to a file."""
        if not len(self.ratings):
            return
        with open(self.saveFileName, "w") as ffile:
            ffile.write(RATING_DATA_HEADER + "\t" + self.gageId)
            for ra in self.ratings:
                #print("\n%s\t%s\t%s\t%s" % (ra.stage, ra.stageUnits, ra.flow, ra.flowUnits))
                ffile.write("\n%s\t%s\t%s\t%s" % (ra.stage, ra.stageUnits, ra.flow, ra.flowUnits))
        


def get_flood_data_from_NWS(site):
    """ Opens a http connection and retrieves the flood mapper data."""
    
    site = COLLECTION_URL.format(site)
    print("url to open: " + site)
    
    try:
        g = urllib.request.urlopen(site)
    except: 
        return None
    
    dat = g.read()
    g.close()
    return dat



def parse_NWS_data(data, manager):
    """ Parses the data from the NWS into multiple parts and saves it.
        - Observations - observed gage readings
        - Forecasts - a stage forecast (if available)
        - Ratings - gage ratings of flow per stage
    """
    
    # Get the observed and forecast data from the document
    try:
        doc = parseString(data)
    except:
        observed = []
        forecast = []
        print('Could not get observed or forecast for ' + manager.getGageId())
        return
        
    try:
        observed = doc.getElementsByTagName("observed")  # returns a list of elements in the xml taht have the tag name observed.
    except:
        observed = []
    try:        
        forecast = doc.getElementsByTagName("forecast")
    except:
        forecast = []
    
    # Parse the observed data.
    for o in observed:
        if o.hasChildNodes():
            print("Has observations: %s" % True)
            for datum in o.childNodes:
                ddate = datetime.datetime.strptime(datum.childNodes[0].childNodes[0].nodeValue[:-6], NWS_DATETIME_FORMAT)
                dstage = datum.childNodes[1].childNodes[0].nodeValue
                dflow = datum.childNodes[2].childNodes[0].nodeValue
                #print("%s\t%s\t%s" %(ddate, dstage, dflow))
                manager.addObservation(Observation(ddate, dstage, dflow))
        else:
            print("Has observations: %s" % False)
        
    
    try:
        manager.startForecast(datetime.datetime.strptime(forecast[0].attributes["issued"].value[:-6] ,NWS_DATETIME_FORMAT))
    except:
        pass
     
    # Parse the forecast data.
    for fct in forecast:
        
        #manager.startForecast(datetime.datetime.now())
        if fct.hasChildNodes():
            print("Has forecasts: %s" % True)
            for datum in fct.childNodes:
                # Add a new forecast to the manager
                if len(datum.childNodes):
                    ddate = datetime.datetime.strptime(datum.childNodes[0].childNodes[0].nodeValue[:-6], NWS_DATETIME_FORMAT)
                    dstage = datum.childNodes[1].childNodes[0].nodeValue
                    dflow = datum.childNodes[2].childNodes[0].nodeValue
                    #print("%s\t%s\t%s" %(ddate, dstage, dflow))
                    manager.addForecast(Forecast(ddate, dstage, dflow))
        else:
            print("Has forecasts: %s" % False)
        
    
    # Save the manager.  We will no longer need to add data to it.
    manager.save()
    
    # Parse the ratings if necessary
    try:
        ratings = doc.getElementsByTagName("rating")
    except:
        ratings = []
        
    
    for year in manager.getYears():    
        rreport = RatingReport(manager.getGageId(), year)
        
        if rreport.ratingFileExists():
            continue
        
        for r in ratings:
            if r.hasChildNodes():
                for rat in r.childNodes:
                    rreport.addRating(Rating(rat.getAttribute("stage"), rat.getAttribute("stageUnits"), rat.getAttribute("flow"), rat.getAttribute("flowUnits")))    
        
        rreport.save()
    

def main():
    if len(sys.argv) < 2: 
        print("\n Usage: forecast_collector.py <nws_gage_identifier>\n")
        print("The gage identifier is the abbreviation used by the National Weather Service for identifying hydrolic gages.\n See readme.txt for more details.")
        sys.exit("Error: no gage identifier parameter found.")
    
    #print("\n\nStarting Parse for gage " + sys.argv[1])
    #print("GageID: " + sys.argv[1])
    
    gagename = sys.argv[1]
    
    if not os.path.exists(os.path.join(COLLECTION_ROOT, gagename)):
        os.makedirs(os.path.join(COLLECTION_ROOT, gagename))
    
    # Get the data from the NWS.
    data = get_flood_data_from_NWS(gagename)
    
    if not data:
        print("Failed to retrieve data for %s.  Exiting." % gagename)
        sys.exit("ERROR 1")
    
    # Start a manager for the incoming data.
    manager = IncomingDataManager(gagename)
    
    # Parse the incoming data into the manager.
    parse_NWS_data(data, manager)


if __name__ == "__main__":
  main()
