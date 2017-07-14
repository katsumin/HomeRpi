#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("/home/pi/HomeRpi")
import socket
from contextlib import closing

# 送信コマンド生成
def generateEcocuteCommand(EPC) :
    echonetLiteFrame = ""
    echonetLiteFrame += "\x10\x81"      # EHD
    echonetLiteFrame += "\x00\x01"      # TID
    # EDATA
    echonetLiteFrame += "\x05\xFF\x01"  # SEOJ
    echonetLiteFrame += "\x02\x6b\x01"  # DEOJ
    echonetLiteFrame += "\x62"          # ESV(62:プロパティ値読み出し要求) 
    echonetLiteFrame += "\x03"          # OPC(3個)
    echonetLiteFrame += "\x84"
#    echonetLiteFrame += EPC
    echonetLiteFrame += "\x00"          # PDC
    echonetLiteFrame += "\x85"
    echonetLiteFrame += "\x00"          # PDC
    echonetLiteFrame += "\xE1"
    echonetLiteFrame += "\x00"          # PDC
#    command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} {2}".format(ipv6Addr, len(echonetLiteFrame), echonetLiteFrame)
#    return command
    return echonetLiteFrame


host = '192.168.1.155'
port = 3610
bufsize = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
with closing(sock) :
  sock.sendto(generateEcocuteCommand("\x84"), (host, port))

