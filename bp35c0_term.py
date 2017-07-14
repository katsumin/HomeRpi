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

echonetLiteFrame = ""
echonetLiteFrame += "\x10\x81"      # EHD (参考:EL p.3-2)
echonetLiteFrame += "\x00\x01"      # TID (参考:EL p.3-3)
# ここから EDATA
echonetLiteFrame += "\x05\xFF\x01"  # SEOJ (参考:EL p.3-3 AppH p.3-408～)
echonetLiteFrame += "\x02\x88\x01"  # DEOJ (参考:EL p.3-3 AppH p.3-274～)
echonetLiteFrame += "\x62"          # ESV(62:プロパティ値読み出し要求) (参考:EL p.3-5)
echonetLiteFrame += "\x01"          # OPC(1個)(参考:EL p.3-7)
echonetLiteFrame += "\xE1"          # EPC(参考:EL p.3-7 AppH p.3-275)
echonetLiteFrame += "\x00"          # PDC(参考:EL p.3-9)

# コマンド送信
ipv6Addr = "FE80:0000:0000:0000:021C:6400:03CE:BD79"
command = "SKTERM\r\n"
#command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} {2}".format(ipv6Addr, len(echonetLiteFrame), echonetLiteFrame)
ser.write(command)

while True:
    break
    line = ser.readline()
    print(line, end="")
    if line.startswith("ERXUDP") :
        break
