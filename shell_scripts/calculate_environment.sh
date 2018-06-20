#!/bin/bash
#######################################################################################################################
# Calculate following average from $file_path.
#   Load Average,CPU Usage,Memory Info,TCP Connection Count,File Opened Count
#######################################################################################################################

if [[ "$#" > 0 ]]; then
        file_path=$1
else
        echo "Please provide file path"
        exit
fi

# Load Average,CPU Usage,Memory Info,TCP Connection Count,File Opened Count,Current Datetime
load_pattern='^"([0-9.]+), ([0-9.]+), ([0-9.]+)"'
cpu_pattern='"([0-9.]+)%us"'
memory_free_pattern='([0-9]+)k free'
tcp_file_pattern='free","([0-9]+)","([0-9]+)"'
total_load_1=0.0
total_load_2=0.0
total_load_3=0.0
total_cpu=0.0
total_memory=0.0
total_tcp_conn=0.0
total_file_opened=0.0
count=0
while read line
do
        [[ $line =~ $load_pattern ]]
        if [ ! -z "${BASH_REMATCH[1]}" ]; then
            total_load_1=$(echo "${BASH_REMATCH[1]} + $total_load_1" | bc)
            total_load_2=$(echo "${BASH_REMATCH[2]} + $total_load_2" | bc)
            total_load_3=$(echo "${BASH_REMATCH[3]} + $total_load_3" | bc)

            [[ $line =~ $cpu_pattern ]]
            total_cpu=$(echo "${BASH_REMATCH[1]} + $total_cpu" | bc)

            [[ $line =~ $memory_free_pattern ]]
            total_memory=$(echo "${BASH_REMATCH[1]} + $total_memory" | bc)

            [[ $line =~ tcp_file_pattern ]]
            total_tcp_conn=$(echo "${BASH_REMATCH[1]} + $total_tcp_conn" | bc)
            total_file_opened=$(echo "${BASH_REMATCH[2]} + $total_file_opened" | bc)

            count=$((count+1))
        fi
done < $file_path

if [[ $count == 0 ]]; then
    count=1
fi

avg_load_1=$(echo "scale=6;$total_load_1/$count" | bc)
avg_load_2=$(echo "scale=6;$total_load_2/$count" | bc)
avg_load_3=$(echo "scale=6;$total_load_3/$count" | bc)

avg_cpu=$(echo "scale=6;$total_cpu/$count" | bc)
avg_memory=$(echo "scale=6;$total_memory/$count" | bc)
avg_tcp_conn=$(echo "scale=6;$total_tcp_conn/$count" | bc)
avg_file_opened=$(echo "scale=6;$total_file_opened/$count" | bc)

echo "Load Average,CPU Usage,Memory Info,TCP Connection Count,File Opened Count"
echo "\"$avg_load_1,$avg_load_2,$avg_load_3\",\"$avg_cpu\",\"$avg_memory\",\"$avg_tcp_conn\",\"$avg_file_opened\""