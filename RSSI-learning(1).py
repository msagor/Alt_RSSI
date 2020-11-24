#!/usr/bin/python

# -*- coding: utf-8 -*-
# Written to work for Python 2.7
import csv, os, time, random, errno, re, argparse, urllib, abc
import sys, stat, signal, psutil, termios
from sys import stdout, stderr
from shutil import copy
from subprocess import Popen, call, PIPE
from signal import SIGINT, SIGTERM
from tempfile import mkdtemp
from random import shuffle
from shutil import rmtree
from timeit import default_timer as timer
from itertools import combinations as com
from itertools import product as prod


# Library Functions
#-=-=-=-=-=-=-=-=-=-

#https://stackoverflow.com/questions/45926230/how-to-calculate-1st-and-3rd-quartiles#answer-53551756
def find_median(sorted_list):
  indices = []

  list_size = len(sorted_list)
  median = 0

  if list_size % 2 == 0:
    indices.append(int(list_size / 2) - 1)  # -1 because index starts from 0
    indices.append(int(list_size / 2))

    median = (sorted_list[indices[0]] + sorted_list[indices[1]]) / 2
    pass
  else:
    indices.append(int(list_size / 2))

    median = sorted_list[indices[0]]
    pass

  return median, indices
  pass

def find_quarts(samples):  
  median, median_indices = find_median(samples)
  Q1, Q1_indices = find_median(samples[:median_indices[0]])
  Q2, Q2_indices = find_median(samples[median_indices[-1] + 1:])

  return [Q1, median, Q2]


# https://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true
def kill(proc_pid):
  process = psutil.Process(proc_pid)
  for proc in process.children(recursive=True):
    proc.kill()
  process.kill()
    
# https://stackoverflow.com/questions/2520893/how-to-flush-the-input-stream-in-python
def flush_input(): # only works on LINUX
  termios.tcflush(sys.stdin, termios.TCIOFLUSH)
  stdout.flush()

def alarm(message=""):
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n."
  print (message)
  print ("\n")
  for i in range(0,12):
    time.sleep(0.3)
    print "\x1b[1A.",  
    print "\r           \n",
    
# https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
def tail(file, lines=30, _buffer=4098):
  f = open(file, "r");
  """Tail a file and get X lines from the end"""
  lines_found = []
  block_counter = -1

  while len(lines_found) <= lines:
    try:
      f.seek(block_counter * _buffer, os.SEEK_END)
    except IOError:  # either file is too small, or too many lines requested
      f.seek(0)
      lines_found = f.readlines()
      break

    lines_found = f.readlines()
    block_counter -= 1
  
  try:
    write = open(file, "w");
    if len(lines_found[-lines:]) > lines:
      write.write("'antennaSTR','clientRSSI','bssidRSSI','bssidArray','clientArray'\n")
    for i in lines_found[-lines:]:
      write.write(i)
  except:
    alarm("[ERROR] Tail has not properly saved file")

  return lines_found[-lines:]
      
def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass
    
def findFile():
  wait = True
  
  while True:
    if not os.path.exists('files/scan-30.csv'):
      if wait:
        print "This script is supposed to be run after the first 30 inputs from the scan.py script have been generated\nPlease wait while the system finds the file.\nWaiting"
        wait = False
      else: print ".",
      time.sleep(0.5)
    else:
      if sum(1 for line in open('files/scan-30.csv')) >= 30: return
      else:
        if wait:
          print "This script is supposed to be run after the first 30 inputs from the scan.py script have been generated\nPlease wait while the system finds the file.\nWaiting"
          wait = False
        else: print "*",
        time.sleep(0.5)

#~=~=~=~=~=~=~=~=~=~

# Global Variables
#-=-=-=-=-=-=-=-=-=-
global normalProfile
normalProfile = dict()

#~=~=~=~=~=~=~=~=~=~

# Common Functionality
#-=-=-=-=-=-=-=-=-=-
def InitializeIntraTimestamp(timestamp):  # Fast learning / detection
  ''' Generate Intra-timestamp Correlation  '''
  ''' Investigates patterns associated with samples from within a single time group   '''
  
  # Get the differences between each sample with a timestamp
  diff = [i[1] - i[0] for i in com(timestamp, 2)]
  
  # print timestamp
  # print diff
  
  # initialize/store all timestamps 
  for i in range(len(timestamp)):
    if len(normalProfile["Intra"]["hist"]) < len(timestamp):
      normalProfile["Intra"]["hist"][i] = [timestamp[i]]
      normalProfile["Intra"]["diff"][i] = [diff[i]]
      normalProfile["Intra"]["score"][i] = 0
    else:
      normalProfile["Intra"]["hist"][i].append(timestamp[i])
      normalProfile["Intra"]["diff"][i].append(diff[i])
  
  return
  
def InitializeInterTimestamp(timestamp):  # Fast learning / detection
  ''' Generate Inter-timestamp Correlation  '''
  ''' Investigates patterns associated with samples from one time group to the next   '''
  
  # Initialize Inter's Timestamp History list
  if len (normalProfile["Inter"]["hist"]) ==0:
    # need two timestamps, so return on only one
    normalProfile["Inter"]["hist"] = [timestamp]    
    return
  
  # Generate the differences between all dbm samples from one timestamp to the next
  diff = [a-b for a,b in prod(normalProfile["Inter"]["hist"][-1], timestamp)]
  
  # hold the history of all differences in indecies
  for i in range(len(diff)):
    if len(normalProfile["Inter"]["diff"]) < len(diff):
      normalProfile["Inter"]["diff"][i] = [diff[i]]
      normalProfile["Inter"]["score"][i] = 0
    else:
      normalProfile["Inter"]["diff"][i].append(diff[i])
    
  # Store timestamp for next iteration (and other model uses)
  normalProfile["Inter"]["hist"].append(timestamp)
  
  return

def DBmCorrelation(numberOfDBms):  # Slow learning / detection
  ''' Generate dBm Correlation  '''
  ''' Investigates patterns associated with samples' spread across lots of timestamps '''
  
  for i in range(numberOfDBms):
    normalProfile["Corr"]["score"][i] = find_quarts(sorted(normalProfile["Intra"]["hist"][i]))
  
  
  pass
  
def DBmClusterization(numberOfDBms): # Slow learning / detection
  ''' Generate dBm Correlation  '''
  ''' Investigates how samples cluster across lots of timestamps '''
  
  for i in range(numberOfDBms):
  
    normalProfile["Clust"]["hist"][i] = normalProfile["Intra"]["hist"][i]
  
    
  print normalProfile["Clust"]["hist"]
  
  pass

#~=~=~=~=~=~=~=~=~=~

# Main Functionality
#-=-=-=-=-=-=-=-=-=-

def learningPhase():  
  if not os.path.exists('files'): os.makedirs('files')
  
  findFile()
  
  print "\x1b[1A\r                                                  \a"
  print "File has been found. Please keep RSSI-common-scan.py running. This will take about 5 minutes to complete:\n\n"
  
  latestClock=0
  
  while len(normalProfile["Inter"]["hist"]) < 120 : # Gather 120 timestamps
  
    with open('files/scan-30.csv') as csv_file:
      r = csv.reader(csv_file,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
      next(csv_file) #Skip headers
      set="0"
      switch=False
      timestamp=[]
      
      for sample in r:
        ''' sample[0] := Set, [1] := Clock, [2] := Antenna Strength, [3] := Client RSSI ''' 
        
        # If you have seen this value before, then don't look at it anymore
        if latestClock > float(sample[1]):
          continue
        
        if sample[0] == set:
          timestamp += [abs(int(sample[3]))]
          switch = False
        elif switch == False: # First in set
        
          # Currently have a full timestamp
          InitializeIntraTimestamp(timestamp)
          InitializeInterTimestamp(timestamp)
        
          switch = True
          set = sample[0]
          timestamp = [abs(int(sample[3]))]
        else:
          alarm("[ERROR] scan-30.csv does not have consistent sets")
        
  # IntraTimestamp Functionality
    # How much should samples within the same timestamp change?
  for i in range(len(timestamp)):
    normalProfile["Intra"]["score"][i] = find_quarts(sorted(normalProfile["Intra"]["diff"][i]))
  
  # InterTimestamp Functionality
    # How much should samples change from timestamp to the next?
  for i in range(len(normalProfile["Inter"]["diff"])):
    normalProfile["Inter"]["score"][i] = find_quarts(sorted(normalProfile["Inter"]["diff"][i]))
  
  DBmCorrelation(len(timestamp))
  DBmClusterization(len(timestamp))
  
  print normalProfile["Intra"]["score"]
  print normalProfile["Inter"]["score"]
  print normalProfile["Corr"]["score"]
  
  # len(timestamp)
    
#~=~=~=~=~=~=~=~=~=~

if __name__ == '__main__':

  # All of the parser stuff
  parser = argparse.ArgumentParser(description='ALT-RSSI: Alternating Strength to Detect MAC Spoof\n[Learning Script]\n\nThis is the program meant for specifically learning a new enviornment',formatter_class=argparse.RawTextHelpFormatter)

  global args, DN
  args = parser.parse_args()
  DN = open(os.devnull, 'w')
  
  # global variables for models
  normalProfile["Intra"] = dict()
  normalProfile["Inter"] = dict()
  normalProfile["Corr"] = dict()
  normalProfile["Clust"] = dict()
  
  # Holds data specifically for Intra
  normalProfile["Intra"]["hist"] = dict() # All samples (stored in i^th idexes)
  normalProfile["Intra"]["score"] = dict()
  normalProfile["Intra"]["diff"] = dict()
  
  # Holds data specifically for Inter
  normalProfile["Inter"]["hist"] = [] # All samples (stored in whole timestamps)
  normalProfile["Inter"]["diff"] = dict() 
  normalProfile["Inter"]["score"] = dict() 
  
  # Holds data specifically for dBmCorrelation
  normalProfile["Corr"]["score"] = dict() 
  
  # Holds data specifically for dBmCorrelation
  normalProfile["Clust"]["score"] = dict() 
  normalProfile["Clust"]["hist"] = dict() 
  
  learningPhase()
  
  

