import time
import RPi.GPIO as GPIO

# Pin definitions
led_pin = 22

# Suppress warnings
GPIO.setwarnings(False)

# Use "GPIO" pin numbering
GPIO.setmode(GPIO.BCM)

# Set LED pin as output
GPIO.setup(led_pin, GPIO.OUT)
#GPIO.setup(10,GPIO.OUT)
#GPIO.setup(24,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)

# Blink forever
print("blinking")
GPIO.output(led_pin, GPIO.HIGH) # Turn LED on
GPIO.output(22,GPIO.HIGH)
time.sleep(1)                   # Delay for 1 second
GPIO.output(22, GPIO.LOW)  # Turn LED off
time.sleep(1)                   # Delay for 1 second


