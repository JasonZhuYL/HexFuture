
#!/usr/bin/python3
#This script uses a as7262 6 colour spectral scanner from Pimoroni and displays the resulting values.
#raspberryconnect.com

from as7262 import AS7262

as7262 = AS7262()

as7262.set_gain(1) # 1, 3.7, 16, 64
as7262.set_integration_time(10) #1 to 255 x 2.8ms exposure
#mode 0 - bank 1 only continuous, mode 1 - bank 2 only continuous, mode 2 - both banks continuous, mode 3 - both banks single read 
as7262.set_measurement_mode(2) #2 all colours continuous
# as7262.set_illumination_led_current(12.5) #12.5mA 25mA 50mA 100mA
# as7262.set_illumination_led(1) # led on

def main():
	try:
		while 1:
			values = as7262.get_calibrated_values() #get values from scan
			
			spec = [float(i) for i in list(values)] #convert results from string to float
			spec /= list.size(values)
			print(spec)
	except KeyboardInterrupt:
			as7262.set_measurement_mode(3) #Switch to scan on demand
			as7262.set_illumination_led(0) #light off

if __name__ == '__main__':
    main()