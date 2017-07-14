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

# ユーティリティ
def s16(v) :
    if v & 0x8000 :
        return v - 65536
    else :
        return v

def u16(v) :
    return v

def s12(v) :
    if v & 0x800 :
        return v - 4096
    else :
        return v

def s8(v) :
    if v & 0x80 :
        return v - 256
    else :
        return v

def u8(v) :
    return v


# i2c初期化
i2c_port = iniFile.get('i2c', 'port')
i2c = smbus.SMBus(int(i2c_port))

# LCD初期化
def init_lcd(addr) :
    time.sleep(0.040)
    i2c.write_byte_data(addr, 0x00, 0x38)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x39)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x14)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x70)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x56)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x6c)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x38)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x0c)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x01)
    time.sleep(0.001)
    i2c.write_byte_data(addr, 0x00, 0x80)
    time.sleep(0.002)

# LCD初期化
#init_lcd(0x3e)

# 温度・湿度・気圧計初期化
bme280_addr = 0x76
dig_T1 = u16(i2c.read_word_data(bme280_addr, 0x88))
dig_T2 = s16(i2c.read_word_data(bme280_addr, 0x8a))
dig_T3 = s16(i2c.read_word_data(bme280_addr, 0x8c))
dig_P1 = u16(i2c.read_word_data(bme280_addr, 0x8e))
dig_P2 = s16(i2c.read_word_data(bme280_addr, 0x90))
dig_P3 = s16(i2c.read_word_data(bme280_addr, 0x92))
dig_P4 = s16(i2c.read_word_data(bme280_addr, 0x94))
dig_P5 = s16(i2c.read_word_data(bme280_addr, 0x96))
dig_P6 = s16(i2c.read_word_data(bme280_addr, 0x98))
dig_P7 = s16(i2c.read_word_data(bme280_addr, 0x9a))
dig_P8 = s16(i2c.read_word_data(bme280_addr, 0x9c))
dig_P9 = s16(i2c.read_word_data(bme280_addr, 0x9e))
dig_H1 =  u8(i2c.read_byte_data(bme280_addr, 0xa1))
dig_H2 = s16(i2c.read_word_data(bme280_addr, 0xe1))
dig_H3 =  u8(i2c.read_byte_data(bme280_addr, 0xe3))
dig_H4 = s12(i2c.read_byte_data(bme280_addr, 0xe4) << 4 \
       | i2c.read_byte_data(bme280_addr, 0xe5) & 0x0f)
dig_H5 = s12(i2c.read_byte_data(bme280_addr, 0xe6) << 4 \
       | (i2c.read_byte_data(bme280_addr, 0xe5) & 0xf0) >> 4)
dig_H6 =  s8(i2c.read_byte_data(bme280_addr, 0xe7))

def init_temp(addr) :
#    i2c.write_byte_data(addr, 0xf5, 0x00)
#    i2c.write_byte_data(addr, 0xf2, 0x01)
    i2c.write_byte_data(addr, 0xf5, 0x10)
    i2c.write_byte_data(addr, 0xf2, 0x05)

def get_TFine(adc_T) :
    var1 = (adc_T / 16384.0 - dig_T1 / 1024.0) \
         * dig_T2
    var2 = (adc_T / 131072.0 - dig_T1 / 8192.0) \
         * (adc_T / 131072.0 - dig_T1 / 8192.0) \
         * dig_T3
    t_fine = var1 + var2
    return t_fine

def compensate_T(t_fine) :
    T = t_fine / 5120.0
    return T

def compensate_P(adc_P, t_fine) :
    var1 = (t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * dig_P6 / 32768.0
    var2 = var2 + (var1 * dig_P5 * 2.0)
    var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
    var1 = ((dig_P3 * var1 * var1 / 524288.0) + (dig_P2 * var1)) / 524288.0
    var1 = (1.0 + (var1 / 32768.0)) * dig_P1
    if var1 == 0.0 :
        return 0
    p = 1048576.0 - adc_P
    p = (p - (var2 / 4096.0)) * 6250.0 / var1;
    var1 = dig_P9 * p * p / 2147483648.0
    var2 = p * dig_P8 / 32768.0
    p = p + (var1 + var2 + dig_P7) / 16.0
    return p / 100.0

def compensate_H(adc_H, t_fine) :
    var_H = t_fine - 76800.0;
    var_H = (adc_H - (dig_H4 * 64.0 + dig_H5 / 16384.0 * var_H)) \
          * (dig_H2 / 65536.0 \
          * (1.0 + dig_H6 / 67108864.0 * var_H \
          * (1.0 + dig_H3 / 67108864.0 * var_H)))
    var_H = var_H * (1.0 - dig_H1 * var_H / 524288.0)
    if var_H > 100.0 :
        var_H = 100.0
    elif var_H < 0.0 :
        var_H = 0.0
    return var_H  

#temp = 0
sensor_addr = 0x76
init_temp(sensor_addr)
while True :
    i2c.write_byte_data(sensor_addr, 0xf4, 0xb5)
#    i2c.write_byte_data(sensor_addr, 0xf4, 0x25)
    status = i2c.read_byte_data(sensor_addr, 0xf3)
    c = 0
    while status & 0x08 == 0x08 :
        time.sleep(0.1)
        status = i2c.read_byte_data(sensor_addr, 0xf3)
        c = c + 1
#    print c

    press = i2c.read_byte_data(sensor_addr, 0xf7) << 12 \
          | i2c.read_byte_data(sensor_addr, 0xf8) << 4 \
          | i2c.read_byte_data(sensor_addr, 0xf9) >> 4
    temp  = i2c.read_byte_data(sensor_addr, 0xfa) << 12 \
          | i2c.read_byte_data(sensor_addr, 0xfb) << 4 \
          | i2c.read_byte_data(sensor_addr, 0xfc) >> 4
    hum   = i2c.read_byte_data(sensor_addr, 0xfd) << 8 \
          | i2c.read_byte_data(sensor_addr, 0xfe)
    t_fine = get_TFine(temp)
    temp  = compensate_T(t_fine)
    press = compensate_P(press, t_fine)
    hum   = compensate_H(hum, t_fine)
    print "press:{0:.2f}hPa, temp:{1:.2f}C, hum:{2:.2f}%".format(press, temp, hum)
    time.sleep(10)

#  temp = temp + 1
#  temp /= 128.0
#  str = "{0:2.2f}, {1:2.1f}".format(temp, temp)
#  str = "{0:2.1f}".format(temp)
#  print str
#  i2c.write_byte_data(0x3e, 0x00, 0x02)
#  for i in range(str.__len__()) :
#    i2c.write_byte_data(0x3e, 0x40, ord(str[i])) 
#  time.sleep(1)

#  d = datetime.datetime.today()
#  timestamp = int(time.mktime(d.timetuple())) * 1000000000
#  text = "room temp={0} {1}\n".format(str,timestamp)
#  influxUp(text)
  
