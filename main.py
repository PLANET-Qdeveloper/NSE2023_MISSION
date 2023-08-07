from machine import Pin, I2C, SPI, Timer
from utime import sleep, ticks_ms
import os

import sdcard
from bno055 import BNO055


qua_w, qua_x, qua_y, qua_z = 0

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
bno = BNO055(i2c)

cs = Pin(5, Pin.OUT)    #SDカード
spi = SPI(0, baudrate=32000000, sck=Pin(2), mosi=Pin(3), miso=Pin(4))


# Timerオブジェクト
read_timer = Timer()
record_timer = Timer()
init_sd_time =  ticks_ms()


#SDカード関連
sd = sdcard.SDCard(spi, cs)
os.mount(sd, '/sd')
file_index = 1
file_name = '/sd/NSE_2023_MISSION'+str(file_index)+'.txt'
while True:
    try:
        file = open(file_name, 'r')
    except OSError: # 新しい番号であればエラーに拾われる
        file = open(file_name, 'w')
        init_sd_time = ticks_ms()
        break
    if file:    # 同じ番号が存在する場合引っかかる
        file.close()    # 一旦古いファイルなので閉じる
        file_index += 1
        file_name = '/sd/NSE_2023_MISSION'+str(file_index)+'.txt'

file.write("gyro_x,gyro_y,gyro_z,degree,\r\n")

def read():
    global 
    try:
        qua_w, qua_x, qua_y, qua_z = bno.quaternion()
        gyro = bno.gyro()
    except:
        print('miss!')
 
read_timer.init(period=100, callback=read)

def record(t):
    global file, init_sd_time, gyro_x, gyro_y, gyro_z, degree
    file.write("%f,%f,%f,%d,"%(gyro_x, gyro_y, gyro_z, degree))
    if (ticks_ms() - init_sd_time > 10000):    # 10秒ごとにclose()して保存する
        file.close()
        file = open(file_name, "a")
        init_sd_time = ticks_ms()
record_timer.init(period=100, callback=record)

def peak_detect():
    global gyro
    count = 0
    while True:
        now_data = gyro[2]
        if triger == 0: 
            if now_data > 0:
                count += 1
                if count >= 3:
                    triger = 1
                    count = 0
            else:
                count = 0
                
        if triger == 1:
            if now_data < 0:
                count += 1
                if count >= 3:
                    triger = 2
                    barning_finish = True
                    count = 0
            else:
                count = 0
        if barning_finish:
            if now_data > 0:
                count += 1
                if count >= 3:
                    peak = True
                    break
            else:
                count = 0

def main():
    while True:
        led.value(1)
        sleep(2)
        led.value(0)
        sleep(2)

if __name__=='__main__':
    main()
