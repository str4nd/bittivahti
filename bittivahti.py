#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2008, 2010 Henri Strand, Joonas Kortesalmi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.'''

from __future__ import with_statement

import getopt
import re
import readline
import sys
import time

program = 'bittivahti'
version = '$id$'

devfile = '/proc/net/dev'
sleep_seconds = 1

usage = """
Usage: bittivahti [OPTIONS]
     -c,  --colours            Show something with colours
     -d,  --dynamic            Use dynamic units (Default: Off)
     -h,  --help               Display this usage message
     -i,  --interval=SECONDS   Wait SECONDS between updates (Default: 3)
     -v,  --version            Show version information and exit
"""

device = {}
delta = {}
total = {}

class InvalidBaseException(Exception):
    pass

def pretty_unit(value, base=1000, minunit=None, format="%0.1f"):
    ''' Finds the correct unit and returns a pretty string
    
    pretty_unit(4190591051, base=1024) = "3.9 Gi"
    '''
    if not minunit:
        minunit = base
    
    # Units based on base
    if base == 1000:
        units = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    elif base == 1024:
        units = ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi']
    else:
        raise InvalidBaseException("The unit base has to be 1000 or 1024")
    
    # Divide until below threshold or base
    v = float(value)
    u = base
    for unit in units:
        if v >= base or u <= minunit:
            v = v/base
            u = u * base
        else:
            return format % v + " " + unit

def updatevalues():
    lines = None
    # Read network traffic stats to memory quickly
    with open(devfile, 'r') as f:
        lines = f.readlines()[2:]
    
    for line in lines:
        data = re.split('[ \t:]+', line.strip())
        iface = data[0]
        rx, rxp = map(long, data[1:3])
        tx, txp = map(long, data[9:11])
        trafficdata = [rx, tx, rxp, txp]
        
        if rx>0 or tx>0:
            if device.has_key(iface):
                delta[iface] = [b-a for a, b in zip(device[iface], trafficdata)]
            else:
                delta[iface] = [0L,0L,0L,0L]
                total[iface] = [0L,0L,0L,0L]
            device[iface] = trafficdata
            
            # Calculate total amount of traffic
            if True in [a<0 for a in delta[iface]]:
                pass # ignore updates where bytes or packets is negative
            else:
                total[iface] = [a+b for a, b in zip(total[iface], delta[iface])]

def printdata():
    print program, version
    print "interface   |  RX bw / pkt         |      TX bandwidth    | " + \
        "total:   RX      TX "
    
    for iface in device.keys():
        rx, tx, rxp, txp = delta[iface]
        rx_t, tx_t, rxp_t, txp_t = total[iface]
        d = {'iface' : iface,
             'rx' : pretty_unit(rx),
             'tx' : pretty_unit(tx),
             'rxp' : pretty_unit(rxp, minunit=1, format="%0.0f"),
             'txp' : pretty_unit(txp),
             'rx_t' : pretty_unit(rx_t),
             'tx_t' : pretty_unit(tx_t) }
        print ("%(iface)-12s| %(rx)7sB/s %(rxp)7sp/s| %(tx)7sB/s %(txp)7sp/s|"+ \
            "   %(rx_t)7sB %(tx_t)7sB") % d

def clear():
  sys.stdout.write("\x1b[H\x1b[2J")

def loop(sleep, dynunit, colours):
    print 'Please wait. The display is updated every %.0f seconds.' % sleep
    print 'Starting up...'
    updatevalues()
    time.sleep(sleep)
    # Main loop
    while True:
        try:
            clear()
            updatevalues()
            printdata()
            time.sleep(sleep)
        except KeyboardInterrupt:
            print '\n\nBye!'
            sys.exit()

def main(argv=None):
  colours = False
  if argv is None:
    argv = sys.argv
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:dvc", ["help", "interval=", "dynamic", "version", "colours"])
  except getopt.GetoptError, err:
    print >>sys.stderr, str(err)
    print usage
    sys.exit(2)
  interval = sleep_seconds
  dynunit = False
  for o, a in opts:
    if o in ("-h", "--help"):
      print usage
      sys.exit()
    elif o in ("-i", "--interval"):
      try:
        interval = int(a)
      except:
        print usage
        print >>sys.stderr, 'Invalid interval option.'
        sys.exit()
    elif o in ("-d", "--dynamic"):
      dynunit = True
    elif o in ("-v", "--version"):
      print program + ' v' + version
      sys.exit()
    elif o in ("-c", "--colours"):
      colours = True
    else:
      assert False, "epic fail: unhandled option"
  # Do that loop
  loop(interval, dynunit, colours)

if __name__ == "__main__":
  sys.exit(main())
