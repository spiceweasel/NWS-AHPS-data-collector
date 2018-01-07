# NWS-AHPS-data-collector
A data collection mechanism for hydrologic information retrieved from the National Weather Service AHPS site.

## Introduction
The National Weather Service (NWS) collects hydrologica data for rivers and waterways across the United States http://water.weather.gov/ahps2/.  The observation and prediction data for each waterway is available via xml through an HTTP service.  This script retrieves data from from the NWS for a list of hydrologic gages and saves the data into a csv file on the host computer.

## What it Collects
This set of scripts collects observational, forecast, and gage rating data for a given list of NWS hydrologic gages.  The information is stored in flat text files in a yearly folders for each gage in the input list.

Observational data is saved in a file that will

The collection script is intended to be ran as often as necessary. New information from observations will be appended to any existing file for a given month where observations are found. Forecast data is saved in a separate file for each forecast that is issued.  Ratings will be saved once per year.

## Setup
### Step 1
Edit the ahps_stations.csv and ahps_stations2.csv files to inclue only the hydrologic gages of interest.  Data will be retrieved for each gage in the file.  

NOTE: There are two separate collection scripts and station files to accomodate parallell downloading of the information.  Both collect.sh and collect2.sh scripts can be executed at the same time to roughly cut in half the download time of the entire set.  These can easly be combined into one stations file if only a smaller subset of these stations are of interest to you.   

### Step 2
If you have your own files that have station information, edit the collect.sh and collect2.sh files and change the input_file to match the name of the CSV files you wish them to use for collection purposes.  

### Step 3
If necessary, change the awk command in the collect.sh and collect2.sh files to point to the column in your .csv file that contains the gage identifier. By default the $1 points to the first column in the CSV file as the one that contains the gage identifier.  Thange the $1 to $2 or $3 if the 2nd or 3rd column of your file is the one that contains the gage identifier.

### Step 4
Make sure Python 3 is installed on the host machine.

### Step 5
If you are using virtualenv to manage your python envornments then activate a Python 3 envornment in the bash console before executing the collect.sh script. 
Alternatively, you can change the line in the collect.sh file that executes python on the forecast_collector.py file to point to your Python 3 executable (usually python3 on Linux systems).
If your Python 3 executable is "python3" then change the line that executes the forecast_collector.py script to "python3 ./forecast_collector.py $b" 

Enjoy