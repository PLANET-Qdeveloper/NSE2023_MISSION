import machine
import time

sda_pin1=machine.Pin(26) 
scl_pin1=machine.Pin(27)
i2c1=machine.I2C(1,sda = sda_pin1, scl = scl_pin1, freq = 100000)

print("---address of eeproms and sensors---")
for i in i2c1.scan():
    d = hex(i)
    print("I2C_address; ",d)
print("-----------------------------")


def read_adc():
    i2c1.writeto(0x68, b'\x80')  # MCP3425のアドレスは0x68と仮定します
    time.sleep_ms(100)
    data = i2c1.readfrom(0x68, 3)
    result = (data[0] << 8) | data[1]
    return result

while True:
    adc_value = read_adc()
    print("ADC Value:", adc_value)
    time.sleep(1)
