#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
sys.path.append("/home/pi/HomeRpi")
import serial
import time
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

# シリアルポート初期化
serialPortDev = iniFile.get('smartmeter', 'serial_port')
baudRate = iniFile.get('smartmeter', 'serial_bps')
ser = serial.Serial(serialPortDev, int(baudRate))

# コマンド送信
command = "SKSCAN 2 FFFFFFFF 6 0\r\n"
ser.write(command)

while True:
    line = ser.readline()
    print(line, end="")
    if line.startswith("EVENT 22") :
        break
