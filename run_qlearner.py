#!/usr/bin/env python
import subprocess as sub
import sys
# Loop qlearner, feeding in a new game number each iteration.
num_games = 50
command = "python qlearner.py"
dir = 'bot4'
if len(sys.argv) > 1:
    num_games = int(sys.argv[1])
if len(sys.argv) > 2:
    dir = str(sys.argv[2])
    
for i in range(num_games):

    # Try to run one game and capture standard out/err. 
    current_command = command + " " + str(i) + " " + str(num_games) + ' ' + dir
    print 'Executing ' + current_command + " ..."
    process = sub.Popen(current_command, shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    output, errors = process.communicate()
    #print output
    #print errors