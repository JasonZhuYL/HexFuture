import smbus2
bus = smbus2.SMBus(1)


time.sleep(0.3)
bus.write_byte(0x40, 0xF3)
time.sleep(0.3)
 
# SI7021 address, 0x40 Read data 2 bytes, Temperature
data0 = bus.read_byte(0x40)
data1 = bus.read_byte(0x40)

# Convert the data
humidity = ((data0 * 256 + data1) * 125 / 65536.0) - 6

# Convert the data and output it
celsTemp = ((data0 * 256 + data1) * 175.72 / 65536.0) - 46.85
fahrTemp = celsTemp * 1.8 + 32
 
print ("Relative Humidity is : %.2f %%" %humidity)
print ("Temperature in Celsius is : %.2f C" %celsTemp)
print ("Temperature in Fahrenheit is : %.2f F" %fahrTemp)