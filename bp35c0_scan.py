#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import serial
import time

# シリアルポート初期化
serialPortDev = '/dev/ttyAMA0'
ser = serial.Serial(serialPortDev, 115200)

# コマンド送信
command = "SKSCAN 2 FFFFFFFF 6 0\r\n"
ser.write(command)

while True:
    line = ser.readline()
    print(line, end="")
    if line.startswith("EVENT 22") :
        break
