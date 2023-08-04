'''
===========================================================================
EEPROM書き込みテストプログラム改定1 （23/04/20）
                                   (23/04/24)


使用したEEPROMは２４FC1025  つまりメモリ容量が128K　x 8 bit(1024K bit)
1バイト8bitであるから16進数表記でFF（10進数で255）までの整数を1バイトの
領域に書き込める。
 
 addr  |bit0|bit1|bit2|  ..... |bit7|
-------------------------------------
0x0000 | 1  | 0  | 0  |  ..... | 0  | <-1バイトに8bit（0000~1111;0~255）までの整数データを格納できる
-------------------------------------
0x0001 | 0  | 0  | 1  |  ..... | 1  |
     .             .
     .             .
     .             .
-------------------------------------
0xFFFF | 0  | 0  | 0  |  ..... | 0  |   (65535バイト目)
-------------------------------------

気圧センサ(bme280)で取得して変換した数値はほとんどの場合小数
になり、桁数もある程度多くなるため、1つのアドレスにその
まま押し込むことはできない。

1バイト領域に10進数2桁の書き込みは必ず可能(99=0x63<256)であるので、
必要最低限の桁数をとり、小数データを数列として扱って2桁ごとに区切って
整数データとして個別に格納する方法がいいかもしれない。

その場合小数点の位置をEEPROMからの読み出し時に復元できるよう、その位
置を指定する仕組みをつくる必要がある。

------データ処理の例----------------------------------
（たとえば10桁の小数値を記録したいとき）

保存したいデータ：458.9820065 (10進数表記で10桁)

(1)小数点を排除して2桁ごとに分割:45/89/82/00/65
(2)上記５整数をアドレス0x0000~0x0004に格納
(3)保存したいデータは必ず10桁にするとあらかじめ決めているなら、
   小数点の位置は最上位桁から数えた位置で一意に決まる。上の
   例の場合、小数点の位置を整数「３」で指定する。このデータをアドレス
   0x0005に収容する。
(4)同様に0x0006~0x0010に2桁整数データを格納し、0x0011に小
　　数点の位置を指定する整数を格納。これを繰り返す。
------------------------------------------------------------

65536（0~65535＝0xFFFF）バイト分のメモリ領域があるため、1個のEEPROMで、
10桁の10進数生データを10922個格納できることになる。EEPROMのピンアドレ
ス指定で最大4個併設できるので、合計43688データを記憶できる。この場合、
1秒に1回データをとったとしても半日分のデータを記録できる計算になる。
ロケットの滞空時間に比べてもかなり長いので十分だと思います。

(追記)メモリアドレッシングの切り替えについて
上下メモリ領域の切り替えは、スレーブアドレスが個別で2個
割り当てられている（80,84 in dec.）ことから、スレーブアドレスで指定
するモノと思われる。
==============================================================================
'''




import machine
import time
import utime

#ピン初期化

#0x50(eeprom)
sda_pin2=machine.Pin(12) 
scl_pin2=machine.Pin(13)
i2c_eeprom=machine.I2C(0,sda = sda_pin2, scl = scl_pin2, freq = 100000)

#0x68(adc)
sda_pin1=machine.Pin(26) 
scl_pin1=machine.Pin(27)
i2c_adc=machine.I2C(1,sda = sda_pin1, scl = scl_pin1, freq = 100000)



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
count = 10 #書き込みメインループの繰り返し回数
t = 100 #データサンプリング周期（ms）
dot_posi = 0 #小数点の位置を表す変数

time.sleep(0.1)



'''------------関数の定義-------------------------------'''
def read_adc():
    i2c_adc.writeto(0x68, b'\x80')  # MCP3425のアドレスは0x68と仮定します
    time.sleep_ms(t)
    data = i2c_adc.readfrom(0x68, 3)
    result = 1#(data[0] << 8) | data[1]
    """
    ここで差圧を計算してもいい
    """
    
    return result



'''
#eeprom読み書きの基本関数定義
'''
def writeData(buff):
    #print("buff>>",buff)
    i2c_eeprom.writeto_mem(device_address[k], addr, bytes([buff & 0xFF]), addrsize=16)
    time.sleep(0.01)
    
def readData():
    data = i2c_eeprom.readfrom_mem(device_address[k], addr,1, addrsize = 16)
    return data














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
    time.sleep(0.5)
    #print("dotADDRESS=",addr)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
'''
経過時間（基準時刻との差）を得る関数
'''

def get_time():
    current_time = utime.ticks_diff(utime.ticks_ms(), start_time) // 1000  # 経過時間を計算し、秒単位に変換
    return current_time





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


"???????????????????????"




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


#flight pin GP0

"""
ここから時間計測
"""
start_time = utime.ticks_ms()  # 現在の時刻を取得（ミリ秒単位）これが基準時刻










'''メインの書き込みサイクル'''
time.sleep(0.1)

for i in range(count):
    
    '''read_bme = 1006.551(float)'''
    #print("p_ave=",read_bme280())
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
    print("address!!",addr)
   
    
    if addr >= 0xFFFF:
        k = 1
        addr = 0x0000
        continue
    
    '''ここから時間書き込み'''
    #print("p_ave=",read_bme280())
    list1 = format_decimal(get_time())
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
time.sleep(0.1)

#読み込みを開始するメモリアドレスの初期値
addr = 0x0000


#device_address = 80 #スレーブアドレス（EEPROM）
dot_posi = 0 #小数点の位置を表す変数

with open(filename, "w") as f:
    

    for i in range (count):
        "5バイトデータ読み込み"
        result = convert_list(read_eeprom())
        data1 = create_decimal(result[0], result[1])
        #data = create_decimal( convert_list(read_eeprom())[0], convert_list(read_eeprom())[1] )
        print("decorded_press:",data)
        print("address",addr)
        
        if addr >= 0xFFFF:
            k = 1
            addr = 0x0000
            continue
        
        "5バイト時間読み込み"
        result = convert_list(read_eeprom())
        data1 = create_decimal(result[0], result[1])
        #data = create_decimal( convert_list(read_eeprom())[0], convert_list(read_eeprom())[1] )
        print("decorded_press:",data)
        print("address",addr)
        
        f.write(str(data2) + "ms : " + str(data1) + " \n")
        f.flush() 
        time.sleep(0.1)
        
        if addr >= 0xFFFF:
            k = 1
            addr = 0x0000
            continue
f.close()   
print("read cycle over \n DONE!!")    
    
