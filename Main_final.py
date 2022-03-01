import HexLibrary_final as Hex
import RPi.GPIO as GPIO
import time 
import sys 

GAIN = 2
SOIL_GAIN = 1

global threshold
treshold = 0

# Setting threshold for different plants (e.g. changing soil humidity threshold)
def set_threshold(thre):
    global threshold
    threshold = thre
    print(threshold)

def main():
    # Threshold for future use to give different threshold for different plants
    global threshold

    tempSensor = Hex.temperature_SI7021(0x40)
    humidity,celsTemp = tempSensor.measure()
    lumSensor = Hex.TCS34725()
    lum = lumSensor.readluminance()


    # Convert celsTemp into string to display in WebApp through json format below
    if celsTemp < 6.0:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is too low!)"
    elif celsTemp > 30.0:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is too high!)"
    else:
        celsTemp_str = str(round(celsTemp,2)) + "°C (Temperature is suitable)"


    adc = Hex.ADS1115(0x48)
    
    try:

        # Reading data from load cell
        diff = adc.read_adc_difference(0,gain = GAIN)
        soil_sensor = adc.read_adc(2, gain=SOIL_GAIN)

        # Checking water level in the compartment of pot
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
        elif soil_sensor > 8000:
            soil_messsage = "Moisture is on suitable level"

        elif soil_sensor< 8000:
            soil_messsage = "The soil too wet!"

        # Indicator for showing motor and pump usage in frontend
        motor = False
        pump = False

        # Convert dirt humidity raw data into percentage
        dirt_humidity = 100 - ( ((soil_sensor) / (32000) ) * 100 )

        # Setting timeframe for plotting and sending data for real-time plotting use in WebApp
        t = time.strftime("%H:%M", time.localtime())
        hum_plot = {'name': t, 'uv': round(dirt_humidity, 2), 'amt': 2400}

        # Putting data in JSON format for frontend use
        data = {
        'isPotConnected':1,
        'humidityValue' : round(dirt_humidity,2),
        'humidity': soil_messsage,
        'tempurature':  celsTemp_str,
        'lightness': round(lum['l'],2),
        'weight': weight_messsage,
        'rHumidity': round(humidity,2),
        'soil humidity':soil_sensor,
        'Ambient Light Luminance': lum['l'],
        'motor': motor,
        'waterpump1': pump
        }

        # Debug use
        print (data)
        return data, hum_plot

    except KeyboardInterrupt:
            print("Terminating...")


if __name__ == '__main__':
    print ("Starting...")
    main()