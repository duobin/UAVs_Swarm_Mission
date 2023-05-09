#!/bin/bash
# IMPORTANT: Path has to be absolute path.

path="/home/iris1/Log/";
if [ ! -d $path ]; then mkdir $path; fi;

today=`date '+%Y%m%d_%H-%M-%S'`;
filename="stderr_FlightLog_iris1_$today.txt";
path_filename=$path$filename;
python /home/iris1/iris_code/balloon_finder_leader.py > $path_filename 2>&1;



