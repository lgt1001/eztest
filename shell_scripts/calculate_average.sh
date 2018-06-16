#!/bin/bash

if [[ "$#" > 0 ]]; then
        file_path=$1
else
        echo "Please provide file path"
        exit
fi
pattern='"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3,6}","[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{3,6}","([0-9.]+)"'
total=0.0
count=0
while read line
do
        [[ $line =~ $pattern ]]
        new=${BASH_REMATCH[1]}
        if [ ! -z "$new" ]; then
                total=$(echo "$new + $total" | bc)
                count=$((count+1))
        fi
done < $file_path
if [[ $count == 0 ]]; then
    count=1
fi
avg=$(echo "scale=6;$total/$count" | bc)
echo "$avg"