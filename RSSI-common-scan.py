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

# Library Functions
#-=-=-=-=-=-=-=-=-=-
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

def alarm():
  '''Makes 12 beeps by writing "\a" 12 times on the same line'''
  print "\n."
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
      write.write("'Set','Clock','antennaSTR','clientRSSI'\n")
      
    for i in lines_found[-lines:]:
      write.write(i)
  except:
    alarm()
    print "ERROR HAPPENED WHEN SAVING FILE!!"

  return lines_found[-lines:]

class Sample:
  def __init__(self, rssi,dbm,time):
    self.clientRSSI,self.dbm,self.timestamp =rssi,dbm,time
    
class RunConfiguration:
  def CreateTempFolder(self):
    self.temp = mkdtemp(prefix='research')
    if not self.temp.endswith(os.sep):
      self.temp += os.sep
      
def rm(file):
  try:
    os.remove(file)
  except OSError:
    pass
    
def setAntennaStrength(dbm):
  b = Popen(["ifconfig",args.prom,"down;","iw","reg","set","B0;","ifconfig",args.prom,"up;","iwconfig",args.prom,"txpower",str(dbm)], stdout=DN, stderr=DN)
  b.wait()
  
def signal_handler(sig, frame):
  flush_input()
  print "Exited, successfully"
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#~=~=~=~=~=~=~=~=~=~

# Main Functionality
#-=-=-=-=-=-=-=-=-=-
def learnDBm():
  ''' Generate what dBm levels are appropiate for this particular environment '''
  pass

def scanAndWait(file,current,airo_pre,dbm,counter=0):
  count = 0
  if counter > 2:
    return "debug"
  while True:
    if os.path.exists(file):
      if len(open(file).readlines()) >= 7:
        print "*"
        stdout.flush()
        return file
      else:
        print "+",
        if count < 50:
          count = 50
        else:
          count += 1
        stdout.flush()
        time.sleep(0.4)
    else:
      print ".",
      count += 1
      stdout.flush()
      time.sleep(0.5)
    if count == 45 or count == 80:
      k = Popen(["rfkill","unblock","wifi;", "sudo","rfkill","unblock","all;","ifconfig",ifaceNonMon,"up"], stdout=DN, stderr=DN)
      k.wait()
      setAntennaStrength(dbm)
      current += 1
      d = Popen(['airodump-ng', '-a','--write-interval', '1', '--bssid', args.bssid, '-c', str(args.channel), '-w', airo_pre, args.prom], stdout=DN, stderr=DN)
      return scanAndWait(airo_pre + '-'+"%02d" % (current,) +'.csv',current,airo_pre,dbm,counter+1)
      

class RunEngine:
  def __init__(self, rc):
    self.RC = rc
    self.RC.RE = self

  def Start(self):
  
    # Create files if not present
    #-=-=-=-
    if not os.path.exists('files'): os.makedirs('files')
    if not os.path.exists('files/scan-30.csv'): 
      with open('files/scan-30.csv','w') as csvfile:
        w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        w.writerow(["Set","Clock","antennaSTR","clientRSSI"])
    if not os.path.exists('files/scan-total.csv'): 
      with open('files/scan-total.csv','w') as csvfile:
        w = csv.writer(csvfile,delimiter=',',quotechar='\'',quoting=csv.QUOTE_MINIMAL)
        w.writerow(["Set","Clock","antennaSTR","clientRSSI"])
    #~=~=~=~
    
    count=0
    x = sorted(set(args.dbm))
    print(x)
    
    while 1:
      while True:
      
        # Begin going through each Antenna Gain Strength
        for dbm in x:
          clientArray, current = [], []
          client = 999
          airo_pre = os.path.join('./', 'files','tmp',str(count),str(dbm),"empty")
          if not os.path.exists(airo_pre): os.makedirs(airo_pre)      
          
          print "Starting collection at: "+str(dbm)+" dbi (Iteration: "+str(count)+"):\n"
          setAntennaStrength(dbm)

          d = Popen(['airodump-ng', '-a','--write-interval', '1', '--bssid', args.bssid, '-c', str(args.channel), '-w', airo_pre, args.prom], stdout=DN, stderr=DN)
          
          file = airo_pre + '-'+"%02d" % (current,) +'.csv'
          
          file = scanAndWait(airo_pre+'-'+"%02d"%(current,)+'.csv',current,airo_pre,dbm)
          
          if file == "debug": continue
          
          while client==999:
            if client == 999:
              c = Popen(["ifconfig",args.prom,"up"], stdout=DN, stderr=DN)

            if not os.path.exists(file): 
              print "OH NO!!\n-=-=-=-=-=-=-=-=-=-=-\n"
              
            # clients = []
            hit_clients = False
            with open(file, 'rb') as csvfile:
              targetreader = csv.reader((line.replace('\0', '') for line in csvfile), delimiter=',')
              for row in targetreader:
                if len(row) < 2: continue
                if (row[0] == args.bssid): continue
                if not hit_clients:
                  if row[0].strip() == 'Station MAC':
                    hit_clients = True
                    continue
                else:
                  if len(row) >= 6 and re.sub(r'[^a-zA-Z0-9:]', '', row[5].strip()) != 'notassociated':
                    client = int(row[3].strip())
                  
          sp = Sample(client,dbm,timer()-start)
          flush_input()
          
          # Less efficient to keep two seperate files, but this is to ensure that
          #   all the data is kept. (Data Retainment Ensurance)
          with open('files/scan-30.csv','a+') as csvf:
            w = csv.writer(csvf,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
            w.writerow([str(count),sp.timestamp, sp.dbm, sp.clientRSSI])
          with open('files/scan-total.csv','a+') as csvf:
            w = csv.writer(csvf,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
            w.writerow([str(count),sp.timestamp, sp.dbm, sp.clientRSSI])
          
          # Keep only the last 30 lines of this file
          tail('files/scan-30.csv')
          
          print "RSSI collection sample collected. Trying to stop spawned process."
          kill(d.pid)
          
        # Garbage Collection
        try:
          Popen(["sudo","rm","-rf", "files/tmp/"+str(count)], stdout=DN, stderr=DN)
        except:
          print "File not deleted"
          
        count += 1
        
        flush_input()

    flush_input()
    
#~=~=~=~=~=~=~=~=~=~

if __name__ == '__main__':

  # All of the parser stuff
  parser = argparse.ArgumentParser(description='ALT-RSSI: Alternating Strength to Detect MAC Spoof\n[Common Scan Script]\n\nThis program should be started with the wireless adapter of your choice started into monitor mode. Additionally, your monior station must be in a location where multiple disjoint RSSI pockets intersecting at differing levels of atenna gain strength.Additionally, please keep this python script running for both the learning and detection phase\n-=-=-=-=-=-=-\nNOTE: Although this is supposed to detect MAC spoofing attacks, to make testing easier all clients are considered to be the same device [will be changed before final release]',formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('-b','--bssid', metavar='00:11:22:33:44:55', help='The access point\'s MAC address', type=str,required=True)
  parser.add_argument('-c','--channel', metavar='#', help='The access point\'s channel', type=int, default=1)
  parser.add_argument('-m','--client', metavar='00:11:22:33:44:55', help='This is the client\'s MAC address', type=str)
  parser.add_argument('-d','--dbm', metavar='# # #', help='All of the antenna gain strengths scaned', type=int, nargs='+',required=True)
  parser.add_argument('-i','--interface', metavar='wlan0', help='raw (un-promiscuous) interface', type=str, default="wlan1")
  parser.add_argument('-p','--promiscuous', dest='prom', metavar='wlan0mon', help='promiscuous interface', type=str, default="wlan1")

  global args, DN, start
  args = parser.parse_args()
  DN = open(os.devnull, 'w')
  start = timer()
  
  
  RC = RunConfiguration()
  RunEngine(RC).Start()

