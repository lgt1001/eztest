#!/bin/bash
#######################################################################################################################
# Collect following info from system commands per 10 seconds and save to $file_path
#   Load Average, CPU Usage, Memory Info from "top" command,
#   TCP Connection Count from "netstat" command,
#   File Opened Count from "/proc/sys/fs/file-nr" file,
#######################################################################################################################

if [[ "$#" > 0 ]]; then
        file_path=$1
else
        echo "please provide target file path."
        exit 0
fi

pattern_load='load average: ([0-9\.]*, [0-9\.]*, [0-9\.]*)'
pattern_cpu='Cpu.* ([0-9\.]*%us)'
pattern_mem='([0-9]+k free)'
echo "Load Average,CPU Usage,Memory Info,TCP Connection Count,File Opened Count,Current Datetime" > $file_path
while true;
do
    env=$(top -bn1)
    [[ $env =~ $pattern_load ]]
    load_averge=${BASH_REMATCH[1]}
    [[ $env =~ $pattern_cpu ]]
    cpu_usage=${BASH_REMATCH[1]}
    [[ $env =~ $pattern_mem ]]
    mem_info=${BASH_REMATCH[1]}
    tcp_conn_count=$(netstat | grep "^tcp" -c)
    file_opened_count=$(cat /proc/sys/fs/file-nr | awk '{ print $1 }')
    curdate=$(date +"%Y-%m-%d %H:%M:%S")
    echo "\"$load_averge\",\"$cpu_usage\",\"$mem_info\",\"$tcp_conn_count\",\"$file_opened_count\",\"$curdate\"" >> $file_path

    sleep 10;
done
