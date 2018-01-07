#!/bin/bash

# input_file is name of the file awk will parse to obtain the gage name.
# File contents must be in tab separated value format (do not include a header)

input_file=hydrocollect_gage_monitoring_stations2.csv

# The position parameter "$1" in the awk line below is the column the gage
# identifer is located in the input file.  Can be change to $2 etc to represent
# column two if the gageID in your input file is in column 2.

a="$(awk '{printf "%s ", $1}' $input_file)"

for b in $a
do
  echo
  echo "######## Start collections for $b"
  echo "python ./forecast_collector.py $b"
  python ./forecast_collector.py $b
done
