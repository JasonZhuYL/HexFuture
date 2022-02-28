import HexLibrary2 as Hex
import RPi.GPIO as GPIO
import time 

GAIN = 2
SOIL_GAIN = 1
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(22,GPIO.OUT,initial=GPIO.LOW)
sum=0

def main():
    tempSensor = Hex.temperature_SI7021(0x40)
    humidity,celsTemp = tempSensor.measure()
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
            time.sleep(1)                   # Delay for 1 second
            GPIO.output(22, GPIO.LOW)  # Turn LED off
        elif soil_sensor > 8000:
            soil_messsage = "Moisture is on suitable level"
        elif soil_sensor< 8000:
            soil_messsage = "The soil too wet!"
        
        # Convert dirt humidity raw data into percentage
        dirt_humidity = 100 - ( ((soil_sensor) / (26000) ) * 100 )

        data = {
        'isPotConnected':1,
        'humidityValue' : round(dirt_humidity,2),
        'humidity': soil_messsage,
        'tempurature':  celsTemp_str,
        'lightness': round(sum,2),
        'weight': weight_messsage,
        'rHumidity': round(humidity,2),
        'soil humidity: ':soil_sensor
        }
        print (data)
        return data
        # print('Load Cell Output: {}'.format(diff))
        # print('Moisture Output: {}'.format(soil_sensor))	 
        # print("Light Sensor Output: ",sum)
        #print("Spec: ",spec)
    except KeyboardInterrupt:
            sys.stdout.close()
            as7262.set_measurement_mode(3) #Switch to scan on demand
            #as7262.set_illumination_led(0) #light off

if __name__ == '__main__':
    print ("Starting...")
    # sys.stdout = open("train.csv", "w")
    # print ("Relative Humidity is : %.2f %%" %humidity)
    # print ("Temperature in Celsius is : %.2f C" %celsTemp)
    # print ("Temperature in Fahrenheit is : %.2f F" %fahrTemp)
    main()