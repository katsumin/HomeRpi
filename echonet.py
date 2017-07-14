#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("/home/pi/HomeRpi")
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

ipv6Addr = iniFile.get('smartmeter', 'address')

# 送信コマンド生成
def generateSmartMeterCommand(EPC) :
    echonetLiteFrame = ""
    echonetLiteFrame += "\x10\x81"      # EHD
    echonetLiteFrame += "\x00\x01"      # TID
    # EDATA
    echonetLiteFrame += "\x05\xFF\x01"  # SEOJ
    echonetLiteFrame += "\x02\x88\x01"  # DEOJ
    echonetLiteFrame += "\x62"          # ESV(62:プロパティ値読み出し要求) 
    echonetLiteFrame += "\x01"          # OPC(1個)
    echonetLiteFrame += EPC
    echonetLiteFrame += "\x00"          # PDC
    command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} {2}".format(ipv6Addr, len(echonetLiteFrame), echonetLiteFrame)
    return command
