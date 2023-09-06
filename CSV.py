

from machine import Pin,I2C 
import time, bme280


#ピン初期化
sda_pin=machine.Pin(16)
scl_pin=machine.Pin(17)
i2c=machine.I2C(0,sda = sda_pin, scl = scl_pin, freq = 100000)




'''
#=============================================================================
#I2Cアドレス表示（デバック用）
print("---address of eeproms and sensors---")
for i in i2c.scan():
    d = hex(i)
    print("I2C_address; ",d)
print("-----------------------------")
#=============================================================================
'''



'''------------定数設定・各変数初期設定-----------'''
addr = 0x0000 #書き込みを開始するメモリアドレス
device_address = 84 #スレーブアドレス（EEPROM）
#k = 0 #スレーブアドレスリストの要素番号
count = 700 #書き込みメインループの繰り返し回数
#厳密には682
dot_posi = 0 #小数点の位置を表す変数

header = ['address','pressure']# ファイルに書き込むヘッダー
'''----------------------------------------------'''

time.sleep(0.1)







'''------------関数の定義-------------------------------'''


'''
#基本関数定義
'''
'''
def writeData(buff):
    #print("buff>>",buff)
    i2c.writeto_mem(device_address[k], addr, bytes([buff & 0xFF]), addrsize=16)
    time.sleep(0.01)
'''

def readData():
    data = i2c.readfrom_mem(device_address[k], addr,1, addrsize = 16)
    return data





'''
関数read_bme280
bme280から10回気圧データを読み出し、その平均値をfloat型として返す関数
データを返す周期は0.1秒

def read_bme280():
    lis = []
    for i in range(10):
        p_comp = bme.read_compensated_data()[1] #タプルの第1要素が補正気圧値
        pres= ( float(p_comp) / 256 / 100 )
        lis.append(pres)
        time.sleep(0.01)
        
    p_ave = float(sum(lis) / 10 )
    print("p_ave: ",p_ave)
    return p_ave
'''    






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
1データ分（5バイト）の書き込みを行う関数。splot_listで得た長さ4の整数型リストの4要素（
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
    time.sleep(0.5)
    #print("dotADDRESS=",addr)
    

'''
関数　read_eeprom
eepromからデータを5バイト分読み込み、長さ5の2桁or1桁整数型リストを返す関数
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
    time.sleep(0.5)
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


'''------------------関数定義の終わり----------------------------------'''












'''メインの書き込みサイクル'''
"""
for i in range(count):
    
    '''read_bme = 1006.551(float)'''
    #print("p_ave=",read_bme280())
    list1 = format_decimal(read_bme280())
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
    print("address!!",addr)
    
    if addr >= 0xFFFF:
        k = 1
        addr = 0x0000
        continue
       
 
print("write cycle over !!") 
#書き込みサイクル終了後、読み込みに移行するまでの待機時間 
"""


time.sleep(0.1)

#読み込みを開始するメモリアドレスの初期値
addr = 0x0000


#device_address = 80 #スレーブアドレス（EEPROM）
dot_posi = 0 #小数点の位置を表す変数


filename = "data.txt"

'''dataをEEPROMから読み取り、csvファイルに逐次的に書き込んでいくサイクル'''
with open(filename, "w") as f:
    

    for i in range (count):
        
        result = convert_list(read_eeprom())
        data = create_decimal(result[0], result[1])
        #data = create_decimal( convert_list(read_eeprom())[0], convert_list(read_eeprom())[1] )
        print("decorded_press:",data)
        print("address",addr)
        f.write(str(data) + "\n")
        f.flush() 
        time.sleep(0.1)
        """
        if addr >= 0xFFFF:
            k = 1
            addr = 0x0000
            continue
        """    
f.close()   
print("read cycle over \n DONE!!")    
    
