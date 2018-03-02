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
import threading
import echonet

# 送信タスク
event = threading.Event()
def sndTask() :
    print('sndTask start')
    event.clear()
    while not event.wait(60) :
        # コマンド送信
        command = echonet.generateSmartMeterCommand("\xE7")
        ser.write(command)
        time.sleep(60) # wait
    print('sndTask end')

def term(ser):
    command = "SKTERM\r\n"
    ser.write(command)
    return

def waitOk() :
    while True :
        line = ser.readline()
        print(line, end="")
        if line.startswith("OK") :
            break

def join(ser,pwd,bid,iniFile):
    # コマンド送信
    while True :
        ser.write("SKVER\r\n")
        line = ser.readline()
        if line.startswith("OK") :
            break
    
    ser.write("SKSETPWD C {0}\r\n".format(pwd))
    waitOk()
    
    ser.write("SKSETRBID {0}\r\n".format(bid))
    waitOk()

    scanRes = {}
    ser.write("SKSCAN 2 FFFFFFFF 6 0\r\n")
    scaned = False
    while True :
        line = ser.readline()
        print(line, end="")
        if line.startswith("EVENT 22") :
            # アクティブスキャンが完了
            if scaned == True :
                break
            else :
                # SKSCANを再送
                ser.write("SKSCAN 2 FFFFFFFF 6 0\r\n")
        elif line.startswith("EPANDESC") :
            scaned = True
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

    command = "SKJOIN {0}\r\n".format(ipv6Addr)
    ser.write(command)

    return

def influxUp(text,url) :
    d = datetime.datetime.today()
    f = open('power_tmp.txt', 'w')
    f.write(text)
    f.close()
    commands.getoutput("curl -i XPOST '{0}:8086/write?db=smartmeter' --data-binary @power_tmp.txt".format(url))
    commands.getoutput("cat power_tmp.txt >> power{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day))

k = 0.1
def rcv_e1(res) :
    if len(res) < 2+1*2 :
        return 0
#    PDC = res[0:0+2] 
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

def rcv_e7(res,url) :
    # 内容が瞬時電力計測値(E7)だったら
    if len(res) < 2+4*2 :
        return 0
#    PDC = res[0:0+2]
    hexPower = res[2:2+8] # 最後の4バイト（16進数で8文字）が瞬時電力計測値
    intPower = int(hexPower, 16)
#    print(hexPower)
    if intPower > 0x80000000 :
#        print("{0:08x}".format(intPower))
        intPower = intPower - 0x100000000
    print("瞬時電力計測値:{0}[W]".format(intPower))
    timestamp = int(time.mktime(d.timetuple())) * 1000000000
    influxUp("power value={0} {1}\n".format(intPower,timestamp),url)
    return 10

def rcv_eaeb(res,prefix,url) :
    if len(res) < 2+11*2 :
        return 0
#    PDC = res[0:0+2]
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
    print("定時積算電力量: {0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d} {6:.1f}[kWh]".format(intYear,intMonth,intDay,intHour,intMin,intSec,float(intValue)*k))
    influxUp("{0}power value={1} {2}\n".format(prefix,float(intValue)*k,timestamp),url)
    return 24

def smartmeter_rcv(EDATA,url):
    OPC = EDATA[14:14+2]
    iOPC = int(OPC, 16)
    offset = 16
    step = 0
    for index in range(iOPC) :
        EPC = EDATA[offset:offset+2]
        offset = offset + 2
        if EPC == "E7" :
            # 内容が瞬時電力計測値(E7)だったら
            step = rcv_e7(EDATA[offset:],url)
        elif EPC == "E1" :
            step = rcv_e1(EDATA[offset:])
        elif EPC == "EA" :
            step = rcv_eaeb(EDATA[offset:],"+",url)
        elif EPC == "EB" :
            step = rcv_eaeb(EDATA[offset:],"-",url)
        else :
            print(u"Other EPC: {0}".format(EPC))
        if step == 0 :
            break
        offset = offset + step
    return

def rejoin(ser,pwd,bid,iniFile):
    # 送信タスク終了
    event.set()
    # 送信タスクの終了を待つ
    thread.join()
    # 再接続
    term(ser)
    join(ser,pwd,bid,iniFile)
    return

if __name__ == '__main__' :
    iniFile = ConfigParser.SafeConfigParser()
    iniFile.read('./config.ini')
    serialPortDev = iniFile.get('smartmeter', 'serial_port')
    baudRate = iniFile.get('smartmeter', 'serial_bps')
    url = iniFile.get('server', 'url')
    pwd = iniFile.get('smartmeter', 'pwd')
    bid = iniFile.get('smartmeter', 'bid')

    # initialize(seral)
    ser = serial.Serial(serialPortDev, int(baudRate))
    
    # term
    term(ser)
    
    # join
    join(ser,pwd,bid,iniFile)
    
    # receive loop
    while True:
        line = ser.readline()         # ERXUDPが来るはず
        print(line, end="")
        d = datetime.datetime.today()

        if line.startswith("OK") :
            continue;
        elif line.startswith("SKSEND") :
            # UDP送信エコーバック
            continue;
        elif line.startswith("EVENT 21") :
            # UDP送信完了
            continue;
        elif line.startswith("ERXUDP") :
            # スマートメーターからの電文受信
            cols = line.strip().split(' ')
            res = cols[9]   # UDP受信データ部分
            ehd1 = res[0:0+2]
            ehd2 = res[2:2+2]
            tid = res[4:4+4]
            EDATA = res[8:]
            seoj = EDATA[0:0+6]
            deoj = EDATA[6:6+6]
            if seoj == "028801" :
                ESV = EDATA[12:12+2]
                if ESV == "72" or ESV == "73" :
                    # スマートメーター(028801)から来た応答(72)なら
                    # スマートメーター(028801)から来たプロパティ通知(73)なら
                    smartmeter_rcv(EDATA,url)
                else :
                    print(u"Other ESV: {0}".format(ESV))
            else :
                print(u"Other SEOJ: {0}".format(seoj))
        elif line.startswith("EVENT 25") :
            # 要求コマンドを開始
            print(u"RCV EVENT 25")
            thread = threading.Thread(target=sndTask)
            thread.start()
        elif line.startswith("EVENT 26") :
            # セッション切断要求 → 再接続開始
            print(u"RCV EVENT 26")
            rejoin(ser,pwd,bid,iniFile)
        elif line.startswith("EVENT 27") :
            # PANA セッションの終了に成功 → 再接続開始
            print(u"RCV EVENT 27")
            rejoin(ser,pwd,bid,iniFile)
        elif line.startswith("EVENT 28") :
            # PANA セッションの終了要求に対する応答がなくタイムアウトした (セッションは終了) → 再接続開始
            print(u"RCV EVENT 28")
            rejoin(ser,pwd,bid,iniFile)
        elif line.startswith("EVENT 29") :
            # セッション期限切れ → 送信を止め、'EVENT 25'を待つ
            print(u"RCV EVENT 29")
            event.set()
            # 送信タスクの終了を待つ
            thread.join()
        else :
            print(u"Not ERXUDP/EVENT")