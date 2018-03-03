#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import sys
sys.path.append("/home/pi/HomeRpi")
import socket
import datetime
import time
import commands
from contextlib import closing
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

url = iniFile.get('server', 'url')
def influxUp(text,type) :
    d = datetime.datetime.today()
    f = open('{0}_tmp.txt'.format(type), 'w')
    f.write(text)
    f.close()
    commands.getoutput("curl -i XPOST '{0}:8086/write?db=smartmeter' --data-binary @{1}_tmp.txt".format(url,type))
    commands.getoutput("cat {3}_tmp.txt >> {3}{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day,type))


host = '127.0.0.1'
port = 3610
bufsize = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
with closing(sock) :
  sock.bind(('', port))
  while True :
    p = sock.recv(bufsize)
    print("{0}: {1}".format(len(p),[p]))
#    for i in range(len(p)) :
#      print(ord(p[i]))
    tuple = struct.unpack('!BHBHBB',p[4:12])
    seoj = tuple[0] * 0x10000 + tuple[1]
    deoj = tuple[2] * 0x10000 + tuple[3]
    esv = tuple[4]
    opc = tuple[5]
    if seoj == 0x026b01 and deoj == 0x05ff01 and opc == 3 :
      tuple = struct.unpack('!BBHBBIBBH',p[12:])
      epc1 = tuple[0]
      pdc1 = tuple[1]
      edt1 = tuple[2] # power
      epc2 = tuple[3]
      pdc2 = tuple[4]
      edt2 = tuple[5] # powerSum
      epc3 = tuple[6]
      pdc3 = tuple[7]
      edt3 = tuple[8] # tank
#    print("{0:06X}->{1:06X}: {2}(W), {3}(W), {4}(L)".format(seoj,deoj,edt1,edt2,edt3))
      d = datetime.datetime.today()
      timestamp = int(time.mktime(d.timetuple())) * 1000000000
      text = "ecocute power={0},powerSum={1},tank={2} {3}\n".format(edt1,edt2,edt3,timestamp)
      print(text)
      influxUp(text,'ec')
    elif seoj == 0x013001 and deoj == 0x05ff01 and opc == 3 :
      tuple = struct.unpack('!BBHBBbBBb',p[12:])
      epc1 = tuple[0]
      pdc1 = tuple[1]
      edt1 = tuple[2] # power
      epc2 = tuple[3]
      pdc2 = tuple[4]
      edt2 = tuple[5] # temp. out
      epc3 = tuple[6]
      pdc3 = tuple[7]
      edt3 = tuple[8] # temp. room
#    print("{0:06X}->{1:06X}: {2}(W), {3}(W), {4}(L)".format(seoj,deoj,edt1,edt2,edt3))
      d = datetime.datetime.today()
      timestamp = int(time.mktime(d.timetuple())) * 1000000000
      text = "aircon power={0},tempOut={1},tempRoom={2} {3}\n".format(edt1,edt2,edt3,timestamp)
      print(text)
      influxUp(text,'ac')
