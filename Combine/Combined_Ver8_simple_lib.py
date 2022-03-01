import HexLibrary2 as Hex
import RPi.GPIO as GPIO
import time 
import sys 

GAIN = 2
SOIL_GAIN = 1
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(22,GPIO.OUT,initial=GPIO.LOW)
sum=0
# lumTotal = 0
global threshold
treshold = 0

servoPIN = 17
GPIO.setup(servoPIN, GPIO.OUT)

p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
p.start(2.5) # Initialization

def set_threshold(thre):
    global threshold
    threshold = thre

def main():
    global threshold
    tempSensor = Hex.temperature_SI7021(0x40)
    humidity,celsTemp = tempSensor.measure()
    lumSensor = Hex.TCS34725()
    lum = lumSensor.readluminance()

    
    #Calculate cumulative luminosity
    # if lum['l'] > 25000: 
    #     lumTotal += lum['l']/10
    # #print(lumTotal)

    # if lumTotal > 35000: 
    #     lumTotal = 0 
    #     print("Sunflower system activated")

    # Convert celsTemp into string to display in WebApp through json format below
    if celsTemp < 6.0:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is too low!)"
    elif celsTemp > 30.0:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is too high!)"
    else:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is suitable)"
    # "celsTemp .C (Temperature is suitable)"
    adc = Hex.ADS1115(0x48)
    
    try:
        diff = adc.read_adc_difference(0,gain = GAIN)
        soil_sensor = adc.read_adc(2, gain=SOIL_GAIN)

        if diff>=0:
            weight_messsage = "Water is enough"
        else:
            weight_messsage = "Refill water!"
        
        # >25000; Sensor not inserted into soil
        # >22000; Soil is very dry
        # >8000 <18000; Moisture is on suitable level
        # <8000; Soil is too humid
        if soil_sensor>=25000:
            soil_messsage = "Sensor not inserted into soil!"
        elif soil_sensor>22000:
            soil_messsage = "Soil is very dry! Attempting to pump water to the plant..."
            print("blinking")
            GPIO.output(22,GPIO.HIGH)
            # time.sleep(5)                   # Delay for 1 second
        elif soil_sensor > 8000:
            soil_messsage = "Moisture is on suitable level"
            GPIO.output(22, GPIO.LOW)  # Turn LED off

        elif soil_sensor< 8000:
            soil_messsage = "The soil too wet!"

        if lum['l'] > 25000: 
            time.sleep(1)
            p.ChangeDutyCycle(12.5)

        
        # Convert dirt humidity raw data into percentage
        dirt_humidity = 100 - ( ((soil_sensor) / (26000) ) * 100 )
        t = time.strftime("%H:%M:%S", time.localtime())
        hum_plot = {'name': t, 'uv': round(dirt_humidity, 2), 'amt': 2400}
        data = {
        'isPotConnected':1,
        'humidityValue' : round(dirt_humidity,2),
        'humidity': soil_messsage,
        'tempurature':  celsTemp_str,
        'lightness': round(lum['l'],2),
        'weight': weight_messsage,
        'rHumidity': round(humidity,2),
        'soil humidity: ':soil_sensor
        # 'Ambient Light Luminance: ': lum['l']
        }
        print (data)
        return data, hum_plot
        # print('Load Cell Output: {}'.format(diff))
        # print('Moisture Output: {}'.format(soil_sensor))	 
        # print("Light Sensor Output: ",sum)
        #print("Spec: ",spec)
    except KeyboardInterrupt:
            sys.stdout.close()


if __name__ == '__main__':
    print ("Starting...")
    # sys.stdout = open("train.csv", "w")
    # print ("Relative Humidity is : %.2f %%" %humidity)
    # print ("Temperature in Celsius is : %.2f C" %celsTemp)
    # print ("Temperature in Fahrenheit is : %.2f F" %fahrTemp)
    # lumTotal = 0
    while True: 
        main()
        # print(lumTotal)
        time.sleep(1)