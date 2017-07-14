#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smbus
import time
import datetime
import sys
sys.path.append("/home/pi/HomeRpi")
import commands
import ConfigParser

iniFile = ConfigParser.SafeConfigParser()
iniFile.read('./config.ini')

# influxDBサーバへ送信
url = iniFile.get('server', 'url')
def influxUp(text) :
    d = datetime.datetime.today()
    f = open('temp_tmp.txt', 'w')
    f.write(text)
    f.close()
    commands.getoutput("curl -i XPOST '{0}:8086/write?db=smartmeter' --data-binary @temp_tmp.txt".format(url))
    commands.getoutput("cat temp_tmp.txt >> temp{0:04d}{1:02d}{2:02d}.txt".format(d.year,d.month,d.day))

# i2c初期化
i2c_port = iniFile.get('i2c', 'port')
i2c = smbus.SMBus(int(i2c_port))

# LCD初期化
time.sleep(0.040)
i2c.write_byte_data(0x3e, 0x00, 0x38)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x39)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x14)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x70)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x56)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x6c)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x38)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x0c)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x01)
time.sleep(0.001)
i2c.write_byte_data(0x3e, 0x00, 0x80)
time.sleep(0.002)

# 温度計初期化
i2c.write_byte_data(0x48, 0x03, 0xc0)

while True :
  temp = i2c.read_word_data(0x48, 0x00)
  temp_l = (temp & 0xff00) >> 8
  temp_h = (temp & 0x00ff) << 8
  temp = temp_h | temp_l
  temp /= 128.0
#  str = "{0:2.2f}, {1:2.1f}".format(temp, temp)
  str = "{0:2.1f}".format(temp, temp)
#  print str
  i2c.write_byte_data(0x3e, 0x00, 0x02)
  for i in range(str.__len__()) :
    i2c.write_byte_data(0x3e, 0x40, ord(str[i])) 
  time.sleep(60)

  d = datetime.datetime.today()
  timestamp = int(time.mktime(d.timetuple())) * 1000000000
  text = "room temp={0} {1}\n".format(str,timestamp)
  influxUp(text)
  