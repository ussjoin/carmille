#!/usr/bin/env bash

CONFIGPATH=/home/ussjoin/carmille-cron/carmille-s3cfg

now=$(date "+%s")
beforetime=$(expr $now - 3600)

s3cmd -c $CONFIGPATH ls s3://carmille | while IFS= read -r line; do
  datestr=$(echo $line | cut -f 1,2 -d' ')
  filename=$(echo $line | cut -f 4 -d' ')
  lineepoch=$(date --date="$datestr" "+%s")
  if [ $lineepoch -ge $beforetime ]
  then
    echo "Not deleting $filename"
  else
    s3cmd -c $CONFIGPATH rm $filename
  fi
done
