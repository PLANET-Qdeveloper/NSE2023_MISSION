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


'''
関数 convert_list
list(int型) >>> list(str型), int値
与えられた1桁or2桁非負整数からなる長さ５のリスト（関数read_eepromが返すリスト）を受け、
前半4つの整数を順番に取り出し、2文字の要素4つを持つstr型リスト(new_list)の要素とし
て格納し、5番目の整数をint型のままfifth_numとして出力する関数。与えられたリストの前半
４つの要素に1桁の整数がある場合、2 >> '02'のように適宜0で埋めて2文字に調節する。0も
同様に'00'とする。fifth_numは気圧データの小数点位置を特定する情報である。

例:
num_list = [10, 4, 0, 23, 4]
new_list >>> ['10', '04', '00', '23']
fifth_num = 4

'''
def convert_list(num_list):
    new_list = []
    for num in num_list[:4]:
        if num < 10:
            new_list.append('0' + str(num))
        else:
            new_list.append(str(num))
    fifth_num = num_list[4]
    #print("new_list, fifth_num: ",new_list, fifth_num)
    return new_list, fifth_num




'''
関数 create_decimal
list（str型） ,int値　>>>　float値
convert_listから出力されるリストと整数を受けて、もとの気圧データを完全に復元する関数。
出力decorded_dataは8桁の小数となる。

例:
new_list = ['10', '04', '00', '23']
fifth_num = 4
 decorded_data >>> 1004.0023

引数を2つとることに注意
'''
def create_decimal(new_list, fifth_num):
    # 1文字ごとに分割した新しいリストを作成
    new_list_split = []
    for string in new_list:
        for char in string:
            new_list_split.append(char)
    
    # 5番目の文字の前に'.'を追加して、リストを長さ9にする
    new_list_split.insert(fifth_num, '.')
    new_list_split = new_list_split[:9]
    
    # 文字列に変換して小数値に変換
    decimal_str = ''.join(new_list_split)
    return float(decimal_str)



    
    
time.sleep(0.1)
for i in range (count):
    result = convert_list(read_eeprom())
    data = create_decimal(result[0], result[1])
    #data = create_decimal( convert_list(read_eeprom())[0], convert_list(read_eeprom())[1] )
    print("decorded_press:",data)
    #print("address",addr)
    
    
    
    
print("reading is over !")    
    
