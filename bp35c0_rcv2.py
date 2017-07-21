#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
sys.path.append("/home/pi/HomeRpi")
import serial
import datetime
import locale
import time
import commands
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

# シリアルポート初期化
serialPortDev = iniFile.get('smartmeter', 'serial_port')
baudRate = iniFile.get('smartmeter', 'serial_bps')
ser = serial.Serial(serialPortDev, int(baudRate))

k = 0.1

url = iniFile.get('server', 'url')
def influxUp(text) :
    d = datetime.datetime.today()
    f = open('power_tmp.txt', 'w')
    f.write(text)
    f.close()
    commands.getoutput("curl -i XPOST '{0}:8086/write?db=smartmeter' --data-binary @power_tmp.txt".format(url))
    commands.getoutput("cat power_tmp.txt >> power{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day))

def rcv_e1(res) :
    if len(res) < 2+1*2 :
        return 0
    PDC = res[0:0+2] 
    EDT = res[2:2+2]    # 最後の1バイト（16進数で2文字）が積算電力量単位
    if EDT == "00" :
        k = 1
        print("1kWh")
    elif EDT == "01" :
        k = 0.1
        print("0.1kWh")
    elif EDT == "02" :
        k = 0.01
        print("0.01kWh")
    elif EDT == "03" :
        k = 0.001
        print("0.001kWh")
    elif EDT == "04" :
        k = 0.0001
        print("0.0001kWh")
    elif EDT == "0A" :
        k = 10
        print("10kWh")
    elif EDT == "0B" :
        k = 100
        print("100kWh")
    elif EDT == "0C" :
        k = 1000
        print("1000kWh")
    elif EDT == "0D" :
        k = 10000
        print("10000kWh")
    else :
        print(u"unknown: {0}".format(hex))
    return 4

def rcv_e7(res) :
    # 内容が瞬時電力計測値(E7)だったら
    if len(res) < 2+4*2 :
        return 0
    PDC = res[0:0+2] 
    hexPower = res[2:2+8] # 最後の4バイト（16進数で8文字）が瞬時電力計測値
    intPower = int(hexPower, 16)
#    print(hexPower)
    if intPower > 0x80000000 :
#        print("{0:08x}".format(intPower))
        intPower = intPower - 0x100000000
    print("瞬時電力計測値:{0}[W]".format(intPower))
    timestamp = int(time.mktime(d.timetuple())) * 1000000000
    influxUp("power value={0} {1}\n".format(intPower,timestamp))
    return 10

def rcv_eaeb(res,prefix) :
    if len(res) < 2+11*2 :
        return 0
    PDC = res[0:0+2]
    EDT = res[2:]
    intYear = int(EDT[0:0+4],16)
    intMonth = int(EDT[4:4+2],16)
    intDay = int(EDT[6:6+2],16)
    intHour = int(EDT[8:8+2],16)
    intMin = int(EDT[10:10+2],16)
    intSec = int(EDT[12:12+2],16)
    intValue = int(EDT[14:14+8],16)
    d = time.strptime("{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}".format(intYear,intMonth,intDay,intHour,intMin,intSec), "%Y/%m/%d %H:%M:%S")
    timestamp = int(time.mktime(d)) * 1000000000
    print("正方向定時積算電力量: {0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d} {6:.1f}[kWh]".format(intYear,intMonth,intDay,intHour,intMin,intSec,float(intValue)*k))
    influxUp("{0}power value={1} {2}\n".format(prefix,float(intValue)*k,timestamp))
    return 24

while True:
    line = ser.readline()         # ERXUDPが来るはず
    print(line, end="")
    d = datetime.datetime.today()

    if line.startswith("ERXUDP") :
        cols = line.strip().split(' ')
        res = cols[9]   # UDP受信データ部分
        ehd1 = res[0:0+2]
        ehd2 = res[2:2+2]
        tid = res[4:4+4]
        EDATA = res[8:]
        seoj = EDATA[0:0+6]
        deoj = EDATA[6:6+6]
        offset = 24
        if seoj == "028801" :
            ESV = EDATA[12:12+2]
            if ESV == "72" or ESV == "73" :
                # スマートメーター(028801)から来た応答(72)なら
                # スマートメーター(028801)から来たプロパティ通知(73)なら
                OPC = EDATA[14:14+2]
                iOPC = int(OPC, 16)
                offset = 16
                step = 0
                for index in range(iOPC) :
                    EPC = EDATA[offset:offset+2]
                    offset = offset + 2
                    if EPC == "E7" :
                        # 内容が瞬時電力計測値(E7)だったら
                        step = rcv_e7(EDATA[offset:])
                    elif EPC == "E1" :
                        step = rcv_e1(EDATA[offset:])
                    elif EPC == "EA" :
                        step = rcv_eaeb(EDATA[offset:],"+")
                    elif EPC == "EB" :
                        step = rcv_eaeb(EDATA[offset:],"-")
                    else :
                        print(u"Other EPC: {0}".format(EPC))
                    if step == 0 :
                        break
                    offset = offset + step
            else :
                print(u"Other ESV: {0}".format(ESV))
        else :
            print(u"Other SEOJ: {0}".format(seoj))
    else :
        print(u"Not ERXUDP")
