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
Create a spreadsheet that contains a line for each hydrological gage for which you would like to collect information.  In the spreadsheet, column 1 can be the gage identifier obtained from the NWS site for the gage you wish to obtain information from and column 2 could be the name given to that gage.  

Col 1 | Col 2
____________________________________
MACA2 | MacLaren River at Denali Hwy
MACF1 | St Marys River near Macclenney
etc.. | etc..

Save the spreadsheet as a .csv file using tab delilmited format to the directory where the collect.sh script is located.  Do not include any description header in the output file! The first line of the .csv file should be the first gage from which data should be collected.

### Step 2
Edit the collect.sh file and change the input_file to match the name of the CSV file created in the previous step.
Additionally, change the awk command to point to the column in your .csv file that contains the gage identifier (Instructions in file or search awk positional )

### Step 3
Make sure Python 3 is installed on the host machine.  

If you are using virtualenv to manage your python envornments then activate a Python 3 envornment in the bash console before executing the collect.sh script.

Alternatively, you can change the line in the collect.sh file that executes python on the forecast_collector.py file to point to your Python 3 executable (usually python3 on Linux systems). 
 