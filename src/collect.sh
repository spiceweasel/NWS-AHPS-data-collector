#!/bin/bash

# input_file is name of the file awk will parse to obtain the gage name.
# File contents must be in tab separated value format (do not include a header)

input_file=ahps_stations.csv

# The line variable "$1" in the awk command below is the column the gage
# identifer is located in the input .csv file.  This can be change to $2 etc.
# to represent column 2 if the gage identifier in your input file the second column.

a="$(awk '{printf "%s ", $1}' $input_file)"

for b in $a
do
  echo
  echo "######## Start collections for $b"
  echo "python ./forecast_collector.py $b"
  python ./forecast_collector.py $b
done