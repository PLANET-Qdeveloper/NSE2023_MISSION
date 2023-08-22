from machine import Pin, I2C, SPI, Timer
from utime import sleep, ticks_ms
import os

import sdcard
from bno055 import BNO055


i2c_0 =  I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
i2c_1 =  I2C(1, scl=Pin(27), sda=Pin(26),freq=100000)

bno = BNO055(i2c_0)
eeprom = i2c_0
adc = i2c_1

#I2Cアドレス表示（デバック用）
print("---address of bno and eeproms---")
for i in i2c_0.scan():
    d = hex(i)
    print("I2C_address; ",d)
print("-----------------------------")

print("---address of adc---")
for i in i2c_1.scan():
    d = hex(i)
    print("I2C_address; ",d)
print("-----------------------------")

flight_pin = Pin(0, Pin.IN, Pin.PULL_DOWN)
led = Pin(15, Pin.OUT)

cs = Pin(17, Pin.OUT)    #SDカード
spi = SPI(0, baudrate=32000000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))

#定数宣言
addr = 0x0000 #書き込みを開始するメモリアドレス
device_address = 84 #スレーブアドレス（EEPROM）
count = 682 #書き込みメインループの繰り返し回数
inter = 0.1 #データサンプリング周期（s）
dot_posi = 0 #小数点の位置を表す変数

#変数宣言
qua_w, qua_x, qua_y, qua_z = 0, 0, 0, 0
gyro_x, gyro_y, gyro_z = 0, 0, 0
difpres = 0



# Timerオブジェクト
read_timer = Timer()
record_timer = Timer()
init_sd_time =  ticks_ms()
init_mission_time = ticks_ms()

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

file.write("mission_time,flight_pin,gyro_x,gyro_y,gyro_z,quaternion_w,quaternion_x,quaternion_y,quaternion_z,differential pressure\r\n")

sleep(0.1)

def read(t):
    global qua_w, qua_x, qua_y, qua_z, gyro_x, gyro_y, gyro_z, FP
    try:
        qua_w, qua_x, qua_y, qua_z = bno.quaternion()
        gyro_x, gyro_y, gyro_z = bno.gyro()
        FP = flight_pin.value()
        print(FP)  
    except:
        print('miss!')
read_timer.init(period=100, callback=read)

def record(t):
    global file, init_sd_time, qua_w, qua_x, qua_y, qua_z, gyro_x, gyro_y, gyro_z, FP, difpres
    try:
        mission_time = (ticks_ms() - init_mission_time)/1000
        file.write("%f,%d,%f,%f,%f,%f,%f,%f,%f,%f\r\n"%(mission_time, FP, gyro_x, gyro_y, gyro_z, qua_w, qua_x, qua_y, qua_z, difpres))
        if (ticks_ms() - init_sd_time > 10000):    # 10秒ごとにclose()して保存する
            file.close()
            file = open(file_name, "a")
            init_sd_time = ticks_ms()
           
    except:
        print('record error')
        pass
    
record_timer.init(period=1000, callback=record)
  
                
def read_adc():
    global difpres, inter
    try:
        i2c_1.writeto(0x68,b'\x98')  
        sleep(inter)
        data = i2c_1.readfrom(0x68, 3)
        data1 = (data[0] << 8) | data[1]
         
        voltage = data1 * 2.047 /  32767
        difpres = ( voltage / 5  - 0.04) / 0.0012858
        
        if difpres < 0:
            difpres = 0
        
        print(difpres)
            
    except (ValueError , OSError) :
        print("!Error!")
        difpres = 99999999
        sleep(inter)
        
    return difpres


def writeData(buff):
    i2c_0.writeto_mem(device_address[k], addr, bytes([buff & 0xFF]), addrsize=16)
    sleep(0.01)
    

def format_decimal(num):
    num_str = str(num)
    if '.' in num_str:
        int_part, dec_part = num_str.split('.')
    else:
        int_part, dec_part = num_str, ''

    if len(int_part) > 8:
        return ['9'] * 9

    dec_part_len = 8 - len(int_part)
    if len(dec_part) > dec_part_len:
        dec_part = dec_part[:dec_part_len]
    else:
        dec_part += '0' * (dec_part_len - len(dec_part))

    num_str = int_part + '.' + dec_part
    return list(num_str)


def detect_dot(lst):
    global dot_posi
    try:
        dot_posi = lst.index('.')
    except ValueError:
        dot_posi = 99   
    return dot_posi


def exclude_dot(lst):
    if lst.count('9') == len(lst):
        return [9] * 8
    dot_index = lst.index('.')
    int_lst = lst[:dot_index] + lst[dot_index+1:]
    int_lst = [int(x) for x in int_lst]
    if len(int_lst) < 8:
        int_lst += [0] * (8 - len(int_lst))
    elif len(int_lst) > 8:
        int_lst = int_lst[:8]
    return [str(i) for i in int_lst] 


def split_list(lst):
    if len(lst) != 8:
        return [99]*4

    return [int(lst[i] + lst[i+1]) for i in range(0, 8, 2)]


def write_to_eeprom(lis):
    global addr
    for i in range (len(lis)):
        intdata = lis[i]
        writeData(intdata)
        addr += 1
    writeData(int(dot_posi))    
    addr += 1
    sleep(0.1)


def main():
    while True:
        if flight_pin.value() == 1:
            print('start')
            break
              
    for i in range(count):
        
        list1 = format_decimal(read_adc())
        detect_dot(list1) 
        list2 = exclude_dot(list1)
        list3 = split_list(list2)
        write_to_eeprom(list3)


if __name__=='__main__':
    main()
