#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Bittivahti – display bandwidth and packets on interfaces
    Copyright (C) 2008  Henri Strand

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time, readline, re, time, sys, getopt

program = 'bittivahti-python'
version = '0.01'

devfile = '/proc/net/dev'
sleep_seconds = 3;
regexp = re.compile(r"^\s*([a-z0-9]+):\s*(\d+)\s*(\d+)(\s+\d+){6}\s+(\d+)\s*(\d+)")

usage = """
Usage: bittivahti [OPTIONS]
     -c,  --colours            Show something with colours
     -d,  --dynamic            Use dynamic units (Default: Off)
     -h,  --help               Display this usage message
     -i,  --interval=SECONDS   Wait SECONDS between updates (Default: 3)
     -v,  --version            Show version information and exit
"""

device = {}
device_new = {}
device_total = {}

def calcb(value, dynunit):
  if value < 1024 and dynunit == True:
    byte = value
    unit = 'B'
  elif value < 1024*1024 or dynunit == False:
    byte = value / 1024
    unit = 'KiB'
  elif value < 1024*1024*1024:
    byte = value / 1024 / 1024
    unit = 'MiB'
  elif value < 1024*1024*1024*1024:
    byte = value / 1024 / 1024 / 1024
    unit = 'GiB'
  else:
    byte = value / 1024 / 1024 / 1024 / 1024
    unit = 'TiB'
  return [float(byte), unit]

def calcp(value, dynunit):
  if value < 1000 or dynunit == False:
    pack = value
    unit = 'p'
  elif value < 1000*1000:
    pack = value / 1000
    unit = 'kp'
  elif value < 1000*1000*1000:
    pack = value / 1000 / 1000
    unit = 'Mp'
  elif value < 1000*1000*1000*1000:
    pack = value / 1000 / 1000 / 1000
    unit = 'Gp'
  else:
    pack = value / 1000 / 1000 / 1000 / 1000
    unit = 'Tp'
  return [float(pack), unit]

def updatevalues(sleep, dynunit, colours):
  if colours == True:
    bytecolours = '\033[32m'
    packetcolours = '\033[33m'
    coloursoff = '\033[0m'
  else:
    packetcolours = ''
    bytecolours = ''
    coloursoff = ''
  f = open(devfile, 'r')
  for line in f:
    b = regexp.match(line)
    if b is not None and b.group(2) is not '0' and b.group(5) is not '0':
      rx = float(b.group(2))
      tx = float(b.group(5))
      rxp = float(b.group(3))
      txp = float(b.group(6))
      if device.has_key(b.group(1)):

        rx_delta = rx-device[b.group(1)][0]
	tx_delta = tx-device[b.group(1)][1]
	rxp_delta = rxp-device[b.group(1)][2]
	txp_delta = txp-device[b.group(1)][3]

        device[b.group(1)] = [rx, tx, rxp, txp]

	if rx_delta > 0 and tx_delta > 0 and rxp_delta > 0 and txp_delta > 0:
	  device_total[b.group(1)][0] += rx_delta
	  device_total[b.group(1)][1] += tx_delta
	  device_total[b.group(1)][2] += rxp_delta
	  device_total[b.group(1)][3] += txp_delta

        print bytecolours + "%12s |%9.1f %3s/s |%9.1f %3s/s | %10.1f %3s |%10.1f %3s\n" % (
	  b.group(1),
	  calcb(rx_delta / sleep, dynunit)[0],
          calcb(rx_delta / sleep, dynunit)[1],
	  calcb(tx_delta / sleep, dynunit)[0],
	  calcb(tx_delta / sleep, dynunit)[1],
	  calcb(device_total[b.group(1)][0], dynunit)[0],
	  calcb(device_total[b.group(1)][0], dynunit)[1],
	  calcb(device_total[b.group(1)][1], dynunit)[0],
	  calcb(device_total[b.group(1)][1], dynunit)[1]
	) + packetcolours + "             |%9.1f  %2s/s |%9.1f  %2s/s | %10.1f  %2s |%10.1f  %2s" % (
	  calcp(rxp_delta / sleep, dynunit)[0],
	  calcp(rxp_delta / sleep, dynunit)[1],
	  calcp(txp_delta / sleep, dynunit)[0],
	  calcp(txp_delta / sleep, dynunit)[1],
	  calcp(device_total[b.group(1)][2], dynunit)[0],
	  calcp(device_total[b.group(1)][2], dynunit)[1],
	  calcp(device_total[b.group(1)][3], dynunit)[0],
	  calcp(device_total[b.group(1)][3], dynunit)[1]
	) + coloursoff
      elif b.group(2) is not '0' and b.group(5) is not '0':
	device[b.group(1)] = [rx, tx, rxp, txp]
	device_new[b.group(1)] = [0, 0, 0, 0]
	device_total[b.group(1)] = [0, 0, 0, 0]
  f.close()

def clear():
  sys.stdout.write("\x1b[H\x1b[2J")

def loop(sleep, dynunit, colours):
  print 'Please wait. The display is updated every %.0f seconds.' % sleep
  print 'Starting up...'
  updatevalues(sleep, dynunit, colours)
  time.sleep(sleep)
  # Main loop
  while True:
    try:
      clear()
      print program + ' ' + version
      print "%12s |  %s  |  %s  |    %s  |   %s" % (
            "interface", "RX bandwidth", "TX bandwidth",
            "RX traffic", "TX traffic")
      updatevalues(sleep, dynunit, colours)
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
