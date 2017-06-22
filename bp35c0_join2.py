#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import serial
import time
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

args = sys.argv

# シリアルポート初期化
serialPortDev = '/dev/ttyAMA0'
ser = serial.Serial(serialPortDev, 115200)

# 関数
def waitOk() :
    while True :
        line = ser.readline()
        print(line, end="")
        if line.startswith("OK") :
            break

# コマンド送信
while True :
    ser.write("SKVER\r\n")
    line = ser.readline()
    if line.startswith("OK") :
        break

#pwd = args[1]
pwd = iniFile.get('smartmeter', 'pwd')
ser.write("SKSETPWD C {0}\r\n".format(pwd))
waitOk()

#bid = args[2]
bid = iniFile.get('smartmeter', 'bid')
ser.write("SKSETRBID {0}\r\n".format(bid))
waitOk()

scanRes = {}
ser.write("SKSCAN 2 FFFFFFFF 6 0\r\n")
while True :
    line = ser.readline()
    print(line, end="")
    if line.startswith("EVENT 22") :
        break
    elif line.startswith("  ") :
        cols = line.strip().split(':')
        scanRes[cols[0]] = cols[1]

ser.write("SKSREG S2 " + scanRes["Channel"] + "\r\n")
waitOk()

ser.write("SKSREG S3 " + scanRes["Pan ID"] + "\r\n")
waitOk()

ser.write("SKLL64 " + scanRes["Addr"] + "\r\n")
while True :
    line = ser.readline()
    print(line, end="")
    if not line.startswith("SKLL64") :
        ipv6Addr = line.strip()
        break
print(ipv6Addr)

iniFile.set('smartmeter','address',ipv6Addr)
fp=open('./config.ini','w')
iniFile.write(fp)
fp.close()

#ipv6Addr = "FE80:0000:0000:0000:021C:6400:03CE:BD79"
command = "SKJOIN {0}\r\n".format(ipv6Addr)
ser.write(command)

while True:
    line = ser.readline()
    print(line, end="")
    if line.startswith("EVENT 24") :
        break
    elif line.startswith("EVENT 25") :
        break
