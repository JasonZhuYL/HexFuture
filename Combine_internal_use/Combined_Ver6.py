import HexLibrary as Hex
import RPi.GPIO as GPIO
import smbus2
import time

bus = smbus2.SMBus(1)

time.sleep(0.3)
bus.write_byte(0x40, 0xF3)
time.sleep(0.3)

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


def main():
    as7262 = Hex.AS7262()

    as7262.set_gain(1)  # 1, 3.7, 16, 64
    as7262.set_integration_time(10)  # 1 to 255 x 2.8ms exposure
    # mode 0 - bank 1 only continuous, mode 1 - bank 2 only continuous, mode 2 - both banks continuous, mode 3 - both banks single read
    as7262.set_measurement_mode(2)  # 2 all colours continuous
    # as7262.set_illumination_led_current(12.5) #12.5mA 25mA 50mA 100mA
    # as7262.set_illumination_led(1) # led on
    adc = Hex.ADS1115()
    GAIN = 2
    SOIL_GAIN = 1
    diff = 0
    mode = 0
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)

    try:
        hum_plot = []
        diff = adc.read_adc_difference(differential=mode, gain=GAIN)
        soil_sensor = adc.read_adc(2, gain=SOIL_GAIN)

        values = as7262.get_calibrated_values()  # get values from scan

        # convert results from string to float
        spec = [float(i) for i in list(values)]
        sum = 0
        for j in range(len(spec)):
            sum += spec[j]
        if diff >= 0:
            weight_messsage = "Water is enough"
        else:
            weight_messsage = "No water"
        # >25000; Sensor not inserted into soil
        # >22000; Soil is very dry
        # >8000 <18000; Moisture is on suitable level
        # <8000; Soil is too humid
        if soil_sensor >= 25000:
            soil_messsage = "Sensor not inserted into soil"
        elif soil_sensor > 22000:
            soil_messsage = "Soil is very dry"
            print("blinking")
            GPIO.output(22, GPIO.HIGH)
            time.sleep(1)                   # Delay for 1 second
            GPIO.output(22, GPIO.LOW)  # Turn LED off
            time.sleep(1)                   # Delay for 1 second
        elif soil_sensor > 8000:
            soil_messsage = "Moisture is on suitable level"
        elif soil_sensor < 8000:
            soil_messsage = "Too Humid"
        t = time.strftime("%H:%M:%S", time.localtime())
        hum_plot = {'name': t, 'uv': round(soil_sensor, 2), 'amt': 2400}
        data = {
            'isPotConnected': 1,
            'humidity': soil_messsage,
            'tempurature': round(celsTemp, 2),
            'lightness': round(sum, 2),
            'weight': weight_messsage,
            'rHumidity': round(humidity, 2),
            'soil humidity: ': soil_sensor
        }
        return data, hum_plot
        # print('Load Cell Output: {}'.format(diff))
        # print('Moisture Output: {}'.format(soil_sensor))
        # print("Light Sensor Output: ",sum)
        #print("Spec: ",spec)
    except KeyboardInterrupt:
        sys.stdout.close()
        as7262.set_measurement_mode(3)  # Switch to scan on demand
        # as7262.set_illumination_led(0) #light off


if __name__ == '__main__':
    print("Starting...")
    # sys.stdout = open("train.csv", "w")
    # print ("Relative Humidity is : %.2f %%" %humidity)
    # print ("Temperature in Celsius is : %.2f C" %celsTemp)
    # print ("Temperature in Fahrenheit is : %.2f F" %fahrTemp)
    main()
