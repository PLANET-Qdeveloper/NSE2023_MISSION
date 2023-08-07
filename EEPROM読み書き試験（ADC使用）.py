from machine import Pin, I2C
import time
import utime

#ピン初期化

#0x50(eeprom)
sda_pin2 = Pin(12) 
scl_pin2 = Pin(13)
i2c_eeprom = I2C(0,sda = sda_pin2, scl = scl_pin2, freq = 100000)

#0x68(adc)
sda_pin1 = Pin(26) 
scl_pin1 = Pin(27)
i2c_adc = I2C(1,sda = sda_pin1, scl = scl_pin1, freq = 100000)

#フライトピン
FP = Pin(0, Pin.IN, Pin.PULL_DOWN)

#=============================================================================
#I2Cアドレス表示（デバック用）
print("---address of eeproms and adc---")
for i in i2c_eeprom.scan():
    d = hex(i)
    print("I2C_address; ",d)
print("-----------------------------")
#=============================================================================




'''定数設定・各変数初期設定'''
addr = 0x0000 #書き込みを開始するメモリアドレス
device_address = [80,84] #スレーブアドレス（EEPROM）
k = 0 #スレーブアドレスリストの要素番号
count = 10922 #書き込みメインループの繰り返し回数
t = 5000 #データサンプリング周期（ms）
dot_posi = 0 #小数点の位置を表す変数
'''------------------'''



time.sleep(0.1)



'''------------関数の定義-------------------------------'''

def read_adc():
    try:
        i2c_adc.writeto(0x68,b'\x98')  # MCP3425のアドレスは0x68と仮定します
        time.sleep_ms(t)
        data = i2c_adc.readfrom(0x68, 3)
        data1 = (data[0] << 8) | data[1]
        
        
        voltage = data1 * 2.047 /  32767#16bit(符号＋15bit)
        difpres = ( voltage / 5  - 0.04) / 0.0012858
        
        if difpres < 0:
            difpres = 0
        

        
        print(difpres)
            
    except (ValueError , OSError) :
        print("!Error!")
        difpres = 99999999
        time.sleep_ms(t)
        
        
    return difpres



'''
#eeprom書き込み関数定義
'''
def writeData(buff):
    #print("buff>>",buff)
    i2c_eeprom.writeto_mem(device_address[k], addr, bytes([buff & 0xFF]), addrsize=16)
    time.sleep(0.01)
    
'''
関数　format_decimal(num)
  num(任意の正整数または正小数) >>> list（要素は全てstr型、長さ９）
センサ出力の時間平均値が任意桁の小数もしくは整数として与えられたとき、8桁の小数として扱い、
各桁の数字8個と小数点を含めて9個の要素（ただしstr型）を持つリストp_listを返す関数。
故障により、気圧センサの吐く値が異常な数字（整数部分が0,整数部分が8桁以上など）になっても、例
外処理は行わずにリストに格納し続ける。
（ただし整数部分が8桁以上の場合全ての要素を9で埋める。プログラムの動作は妨げない。）

例：
format_decimal(234.56)
    [' 0 ', ' 2 ', ' 3 ', ' 4 ', ' . ', ' 5 ', ' 6 ', ' 0 ', ' 0 ']
format_decimal(123456789.1)
    [' 9 ', ' 9 ', ' 9 ', ' 9 ', ' . ', ' 9 ', ' 9 ', ' 9 ', ' 9 '] <--9で埋める
format_decimal(12345678)
    [' 0 ', ' 0 ', ' 0 ', ' 0 ', ' . ', ' 1 ', ' 2 ', ' 3 ', ' 4 ']
format_decimal(1.2345678)
    [' 0 ', ' . ', ' 1 ', ' 2 ', ' 3 ', ' 4 ', ' 5 ', ' 6 ', ' 8 ']
'''
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




'''
関数 detect_dot(lst)
list(要素はstr型) >>> dot_posi（int型）
    9要素str型リストの要素から小数点"."を探し、その位置番号を
    dot_posiに格納する。ただし、小数点を要素に持たない場合、dot_
    posiには99を格納する。
例：    
    |0|1|2|3|4|5|6|7|8|  <位置番号(index)
     1 0 0 7 . 6 5 4 9   <リストの要素
    この場合dot_posi = 4 
'''
def detect_dot(lst):
    global dot_posi
    try:
        dot_posi = lst.index('.')
    except ValueError:
        dot_posi = 99
    #print("dot_posi ",dot_posi)    
    return dot_posi





"""
関数exclude_dot(lst)
list(要素str型) >>> list（要素str型）

小数点を含む長さ9のリストから小数点を排除し、長さ8のリストを返す関数。
ただし、小数点がない場合（つまり関数format_decimal(num)で9要素全
てが9で埋められた場合）、８要素が全て9のリストを返す。

この関数はformat_decimal(num)で出力されたリストに処理を施す関数。
必ずformat_decimal(num)の後に置くこと。

"""
def exclude_dot(lst):
    # 要素がすべて9の場合は[9]*8を返す
    if lst.count('9') == len(lst):
        return [9] * 8
    # '.'のインデックスを取得する
    dot_index = lst.index('.')
    # '.'を除いたリストを作成する
    int_lst = lst[:dot_index] + lst[dot_index+1:]
    # 要素をint型に変換する
    int_lst = [int(x) for x in int_lst]
    # 8桁に足りない場合は適宜0で埋める
    if len(int_lst) < 8:
        int_lst += [0] * (8 - len(int_lst))
    # 8桁を超える場合は切り捨てる
    elif len(int_lst) > 8:
        int_lst = int_lst[:8]
    return [str(i) for i in int_lst] #要素を全てstr型に戻して返す 




'''
関数　split_list
list(str型)　>>> list(int型)
与えられた長さ8のstr型整数要素リストを2要素ごとに分割し、長さ４のint型整数リストを返す関数。
引数として与えられるリストは必ず8要素で、その要素は全てstr型の数字である必要あり。

例：
splot_list(['1', '2', '3', '4', '0', '1', '2', '3'])
    >>[12, 34, 1, 23]
    

def split_list(lst):
    result = []
    for i in range(0, len(lst), 2):
        if i + 1 < len(lst):
            result.append([lst[i], lst[i+1]]) #2要素ずつ結合
        else:
            result.append([lst[i]])
        if len(result) == 4:
            break
    return [[int(j) for j in sublst] for sublst in result]
'''

def split_list(lst):
    """与えられた1桁正整数8個要素のリストを、2要素ごとにまとめ、長さ4のint型2桁もしくは1桁整数要素のリストを返す。
    ただし、与えられたリストの要素が上の条件を満たさない場合、リスト['99']*4を返す。

    Args:
        lst (list): 1桁正整数8個要素を持つリスト。

    Returns:
        list: 2要素ごとにまとめられ、長さ4のint型2桁もしくは1桁整数要素のリスト、または['99']*4。

    Examples:
        >>> split_list(['1', '2', '0', '4', '5', '6', '7', '0'])
        [12, 4, 56, 70]
        >>> split_list(['1', '2', '3', '4', '5', '6', '7', '8'])
        [12, 34, 56, 78]
        >>> split_list(['a', '2', '3', '4', '5', '6', '7', '8'])
        ['99', '99', '99', '99']
    """
    # lstの長さが8でない場合、['99']*4を返す
    if len(lst) != 8:
        return [99]*4
    
    # 2要素ごとにまとめて、int型2桁もしくは1桁整数要素のリストを返す
    return [int(lst[i] + lst[i+1]) for i in range(0, 8, 2)]


'''

関数　write_to_eeprom
1データ分（5バイト）の書き込みを行う関数。spilt_listで得た長さ4の整数型リストの4要素（
1桁もしくは2桁整数）を前半4バイトに書き込み、5バイト目にdot_posiを書き込む。この5バイト
を1つの気圧値を記憶する領域となる。
'''
def write_to_eeprom(lis):
    global addr
    for i in range (len(lis)):
        intdata = lis[i]
        #print(intdata)
        writeData(intdata)
        addr += 1
        #print("dataADDRESS=",addr)
    writeData(int(dot_posi))    
    addr += 1
    time.sleep(0.1)
    #print("dotADDRESS=",addr)

'''------------------関数定義の終わり----------------------------------'''












#########################################################



for i in range(count):
    
    list1 = format_decimal(read_adc())
    #print("a:",list1)
    '''list1 = ['1','0','0','6','.','5','5','1','0'] データを小数点を含め長さ９のリストのstr型要素に変換。'''
    detect_dot(list1) #dot_posiの更新 ここで小数点の位置をdot_posiに代入している
    list2 = exclude_dot(list1)
    #print("b:",list2)
    #print("dot:",dot_posi)
    '''list2 = ['1','0','0','6','5','5','1','0'] リストから小数点を除外。要素数が8になる。'''
    list3 = split_list(list2)
    #print("c:",list3)
    '''list3 = [10,6,55,10] 2要素ごとに分割したものを整数型に変換し、新たに長さ４のリストを作成'''
    write_to_eeprom(list3)
    '''1byte~4byte目にlist3の整数要素を、5byte目にdot_posiを書き込む。
    これで気圧値1006.551がeepromに保存されたことになる。'''
    print("writed_address!!",i)
   
    if FP.value() ==  1:
        t = 100
        print("FP")
        pass
    
    elif addr >= 0xFFFF:
        k = 1
        addr = 0x0000
        continue
    
     

    

 
print("write cycle over !!")
########################################################


