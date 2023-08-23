from machine import Pin,I2C 
import time, bme280

#ピン初期化
sda_pin=machine.Pin(10)
scl_pin=machine.Pin(11)
i2c=machine.I2C(1,sda = sda_pin, scl = scl_pin, freq = 100000)

#bme = bme280.BME280(i2c=i2c)



#=============================================================================
#I2Cアドレス表示（デバック用）
print("---address of eeproms and sensors---")
for i in i2c.scan():
    d = int(i)
    print("I2C_address; ",d)
print("-----------------------------")
#=============================================================================




'''定数設定・各変数初期設定'''
addr = 0x0000 #開始するメモリアドレス
device_address = 84 #スレーブアドレス（EEPROM）
count = 682 #メインループの繰り返し回数
dot_posi = 0 #小数点の位置を表す変数

time.sleep(0.1)



'''------------関数の定義-------------------------------'''




'''
#eeprom読み書きの基本関数定義
'''
def writeData(buff):
    #print("buff>>",buff)
    i2c.writeto_mem(device_address, addr, bytes(1), addrsize=16)
    time.sleep(0.01)
    
def readData():
    data = i2c.readfrom_mem(device_address, addr,1, addrsize = 16)
    time.sleep(0.01)
    return data
'''
lis = [0]*8

def write_to_eeprom(lis):
    global addr
    for i in range (len(lis)):
        intdata = lis[i]
        #print(intdata)
        writeData(intdata)
        addr += 1
        print("dataADDRESS=",addr)
    writeData(int(dot_posi))    
    addr += 1
    print("dotADDRESS=",addr)
'''
def read_eeprom():
    lis_readData = []
    global addr
    for i in range(4):
        intData = int.from_bytes(readData(), 'big') #readDataで得られたbytes型のデータを整数型に変換している
        lis_readData.append(intData)
        #print("ADDRESS=",addr)
        addr += 1
        #print("reading!!")
    decorded_posi = int.from_bytes(readData(), 'big')
    lis_readData.append(decorded_posi)    
    #print("lis_readData ",lis_readData)
    addr += 1
    #print(addr)
    return lis_readData 


    
    
time.sleep(0.1)
for i in range (count):
    result = convert_list(read_eeprom())
    data = create_decimal(result[0], result[1])
    #data = create_decimal( convert_list(read_eeprom())[0], convert_list(read_eeprom())[1] )
    print("decorded_press:",data)
    #print("address",addr)
    
    
    
    
print("reading is over !")    
    
