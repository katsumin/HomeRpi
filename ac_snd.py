#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("/home/pi/HomeRpi")
import socket
from contextlib import closing

# 送信コマンド生成
def generateAirConCommand() :
    echonetLiteFrame = ""
    echonetLiteFrame += "\x10\x81"      # EHD
    echonetLiteFrame += "\x00\x01"      # TID
    # EDATA
    echonetLiteFrame += "\x05\xFF\x01"  # SEOJ
    echonetLiteFrame += "\x01\x30\x01"  # DEOJ
    echonetLiteFrame += "\x62"          # ESV(62:プロパティ値読み出し要求)
    echonetLiteFrame += "\x03"          # OPC(3個)
    echonetLiteFrame += "\x84"          # power
    echonetLiteFrame += "\x00"          # PDC
    echonetLiteFrame += "\xBE"          # temp. out
    echonetLiteFrame += "\x00"          # PDC
    echonetLiteFrame += "\xBB"          # temp. room
    echonetLiteFrame += "\x00"          # PDC
#    return command
    return echonetLiteFrame


host = '192.168.1.158'
port = 3610
bufsize = 4096

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
with closing(sock) :
  sock.sendto(generateAirConCommand(), (host, port))
