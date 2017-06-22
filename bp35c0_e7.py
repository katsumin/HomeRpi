#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
sys.path.append("/home/pi")
import serial
import time
import echonet

# シリアルポート初期化
serialPortDev = '/dev/ttyAMA0'
ser = serial.Serial(serialPortDev, 115200)

# コマンド送信
command = echonet.generateSmartMeterCommand("\xE7")
ser.write(command)
