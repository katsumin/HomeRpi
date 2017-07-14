#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smbus
import threading
import time
import sys
sys.path.append("/home/pi/HomeRpi")
import datetime
import commands
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')


# 初期化（38400bps）
# 0:300, 1:600, 2:1200, 3:2400, 4:4800, 5:9600, 6:19200, 7:38400, 8:57600, 9:115200
event = threading.Event()
lock = threading.Lock()
i2c_port = iniFile.get('i2c', 'port')
i2c = smbus.SMBus(int(i2c_port))
i2c.write_byte(0x40, 0x07)

ack = ""
ack += "\x02\x06\x03"
nack = ""
nack += "\x02\x15\x03"


# 受信データ数を返す
def receiveCount() :
  lock.acquire()
  try :
    count = i2c.read_byte(0x40)
  finally :
    lock.release()
  return count


# データ受信
def receiveData() :
  lock.acquire()
  try :
    data = i2c.read_byte(0x41)
  finally :
    lock.release()
  return data


# データ送信
def sendData(data) :
  lock.acquire()
  try :
    i2c.write_byte(0x41, data)
  finally :
    lock.release()


# 受信データ列を返す
def receiveMultiData(len) :
  multiData = bytearray()
  count = 0
  timeout = 10
  while event.is_set() != True :
    pre = count
    count = receiveCount()
    # 要求するデータ数を超えていたら、データ引き取り
    if count >= len :
      multiData = bytearray(len)
      for i in range(len) :
        multiData[i] = receiveData()
      return multiData
#    else :
#      print "count: {0}".format(count)

    if pre == count :
      time.sleep(0.1) # 0.1s wait
      timeout = timeout - 1
      if timeout < 1 :
        print 'receive timeout'
        return multiData
    else :
      # 受信があれば、タイムアウトカウンタをリセット
      timeout = 10
  # 終了イベントで抜ける
  print 'receive exit'
  return multiData


# データ列を送信する
def sendMultiData(multiData) :
  for i in range(multiData.__len__()) :
    sendData(ord(multiData[i]))


# 受信タスク
def rcvTask() :
  while event.is_set() != True :
    multiData = receiveMultiData(26)
    if multiData.__len__() < 26 :
      print "receive {0} less 26.".format(multiData.__len__())
      break
    print "{0} << ({1})".format(multiData,multiData.__len__())
  print 'receive exit'


# 送信タスク
def sndTask() :
  while event.is_set() != True :
    d = datetime.datetime.today()
    multiData = "{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}.{6:06d}".format(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond)
    sendMultiData(multiData)
    time.sleep(0.1) # wait
#    sendMultiData('0123456789')
#    print '>> 0123456789'
  print 'send exit'


# キー待ちタスク
def keyTask() :
  code = raw_input("")
#  code = raw_input(msg)
#  print "finish"
  event.set()


# コマンド受信
def rcv_cmd() :
  data = ""

  # STX待ち
  while event.is_set() != True :
    stx = receiveMultiData(1)
    if stx.__len__() > 0 :
      if stx == "\x02" :
        data += stx
        break
    else :
      sys.exit(1)

  # ETX待ち
  while event.is_set() != True :
    etx = receiveMultiData(1)
    if etx.__len__() > 0 :
      data += etx
      if etx == "\x03" :
        break
    else :
      sys.exit(1)
  return data


# データフレーム受信
def rcv_data() :
  data = bytearray(0)
  while event.is_set() != True :
    len = receiveMultiData(1)
    if len.__len__() > 0 :
      i_len = ord(len)
#      print i_len
      sum = i_len
      rcv_data = receiveMultiData(i_len)
      if rcv_data.__len__() > 0 :
        data = bytearray(i_len-1)
        for i in range(i_len-1) :
          data[i] = rcv_data[i]
#          data[i] = ord(rcv_data[i])
#        print data[i]
          sum += data[i]
#        sum += ord(rcv_data[i_len-1]) # bcc
        sum += rcv_data[i_len-1] # bcc
        sum &= 255
        if sum == 255 :
          sendMultiData(ack)
          break
        else :
          print sum
          sendMultiData(nack)
      else :
        sys.exit(1)
    else :
      sys.exit(1)
  return data


# influxDBサーバへ送信
def influxUp(text) :
  f = open('power_tmp.txt', 'w')
  f.write(text)
  f.close()
  commands.getoutput("curl -i -XPOST 'http://katsumin.tk:8086/write?db=smartmeter' --data-binary @power_tmp.txt")


# データ・ダンプ
def dump() :
  d = datetime.datetime.today()
  f = open("kyocera_{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day), 'w')
  idx = 0
#  while True :
  count = total_data.__len__()
  count /=  32
  for i in range(count) :
    text = "{0:04X}: ".format(idx)
    for j in range(32) :
      text += "{0:02X}".format(total_data[idx])
      idx += 1
    text += "\n"
    f.write(text)

  count = total_data.__len__()
  count -= idx
  print count
  print "{0:04X}".format(idx)
  text = "{0:04X}: ".format(idx)
  for i in range(count) :
    print i
    text += "{0:02X}".format(total_data[idx])
    idx += 1
  text += "\n"
  f.write(text)
  f.close()


# ３０分データの抽出
def generate_txt(day) :
  day_pos = int("007C",16)
  hatuden_pos = int("00E5",16) # 発電
  baiden_pos = int("0E05",16) # 買電ー売電
  txt = ""
  date = "20{0:02X}/{1:02X}/{2:02X}".format(total_data[day * 3 + day_pos], total_data[day * 3 + day_pos+1], total_data[day * 3 + day_pos+2])

  # 発電
  pos = hatuden_pos
  for idx in range(48) :
    d1 = total_data[pos + day * 96 + idx * 2 + 0]
    d2 = total_data[pos + day * 96 + idx * 2 + 1]
    if d1 != 0x75 or d2 != 0x30 :
#    upper = total_data[pos + day * 96 + idx * 2 + 0] * 10
#    upper += total_data[pos + day * 96 + idx * 2 + 1] / 10
#    lower = total_data[pos + day * 96 + idx * 2 + 1] % 10
#    print("{0} -> {1}.{2}".format(dt,upper,lower))
      upper = d1 * 256
      upper += d2
      if upper > 32767 :
        upper -= 65536
      upper /= 10.0
      dt = "{0} {1:02d}:{2:02d}:00".format(date,idx/2,idx%2*30)
      print("{0} -> {1}".format(dt,upper))
      d = time.strptime(dt, "%Y/%m/%d %H:%M:%S")
      timestamp = int(time.mktime(d)) * 1000000000
#      txt = txt + "hatuden value={0}.{1} {2}\n".format(upper,lower,timestamp)
      txt = txt + "hatuden value={0} {1}\n".format(upper,timestamp)
  # 買電ー売電
  pos = baiden_pos
  for idx in range(48) :
    d1 = total_data[pos + day * 96 + idx * 2 + 0]
    d2 = total_data[pos + day * 96 + idx * 2 + 1]
    if d1 != 0x75 or d2 != 0x30 :
#    upper = total_data[pos + day * 96 + idx * 2 + 0] * 10
#    upper += total_data[pos + day * 96 + idx * 2 + 1] / 10
#    lower = total_data[pos + day * 96 + idx * 2 + 1] % 10
#    print("{0} -> {1}.{2}".format(dt,upper,lower))
      upper = d1 * 256
      upper += d2
      if upper > 32767 :
        upper -= 65536
      upper /= 10.0
      dt = "{0} {1:02d}:{2:02d}:00".format(date,idx/2,idx%2*30)
      print("{0} -> {1}".format(dt,upper))
      d = time.strptime(dt, "%Y/%m/%d %H:%M:%S")
      timestamp = int(time.mktime(d)) * 1000000000
#      txt = txt + "baiden_diff value={0}.{1} {2}\n".format(upper,lower,timestamp)
      txt = txt + "baiden_diff value={0} {1}\n".format(upper,timestamp)
  return txt


# 受信バッファ・クリア
for i in range(receiveCount()) :
  receiveData()

# 要求コマンド
time.sleep(1)
cmd = ""
cmd += "\x02CMD1000FFFF50\x03"
sendMultiData(cmd)
#print "request command"

# ACK
#print "ack wait"
data = rcv_cmd()
#print "{0} << ({1})".format(data, data.__len__())

# 受信開始コマンド
#print "rcv_start wait"
data = rcv_cmd()
print data
# +0+1+2+3+4+5+6+7+8+9+A+B+C+D+E+F+0+1+2
# 02434D44303130303030303032313446434203
# st C M D 0 1 0 0 0 0 0 0 2 1 4 F C B etx
total = int(data[12:12+4].decode(),16)
#print total
total_data = bytearray(total)

# ACK
sendMultiData(ack)
#print "ack"

# データ受信
count = 0
len = 0
while event.is_set() != True and len < total :
  data = rcv_data()
  total_data[len:len+data.__len__()] = data
  count = count + 1
  len += data.__len__()
  print("{0}, {1}, {2}".format(count, data.__len__(), len))
#  if data.__len__() == 32 :
#    print("{0:02X},{1:02X},{2:02X},{3:02X},{4:02X},{5:02X},{6:02X},{7:02X},{8:02X},{9:02X},{10:02X},{11:02X},{12:02X},{13:02X},{14:02X},{15:02X},{16:02X},{17:02X},{18:02X},{19:02X},{20:02X},{21:02X},{22:02X},{23:02X},{24:02X},{25:02X},{26:02X},{27:02X},{28:02X},{29:02X},{30:02X},{31:02X}".format(data[ 0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13],data[14],data[15],data[16],data[17],data[18],data[19],data[20],data[21],data[22],data[23],data[24],data[25],data[26],data[27],data[28],data[29],data[30],data[31]))

# 受信終了コマンド
data = rcv_cmd()
#print data

# ACK
sendMultiData(ack)
#print "ack"

dump()

pow_txt = generate_txt(0)
pow_txt += generate_txt(1)
print pow_txt

influxUp(pow_txt)


#thread1 = threading.Thread(target=rcvTask, args=(,))
#thread1 = threading.Thread(target=rcvTask)
#thread2 = threading.Thread(target=sndTask)
#thread3 = threading.Thread(target=keyTask)
#thread1.start()
#thread2.start()
#thread3.start()
#thread1.join()
#thread2.join()
#thread3.join()

