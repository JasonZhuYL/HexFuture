from fcntl import F_SEAL_SEAL
from operator import truediv
import time
import json
import paho.mqtt.client as mqtt
import Main_final as combine
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
servoPIN = 17
GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setup(22,GPIO.OUT,initial=GPIO.LOW)
p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
p.start(12.5) # Initialization

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


def on_message(client, userdata, message):
    print("Received message:{} on topic {}".format(
        message.payload, message.topic))
    if message.topic == 'type':
        combine.set_threshold(message.payload['type'])


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# set private key
#client.tls_set(ca_certs="mosquitto.org.crt", certfile="client.crt",keyfile='client.key')
#client.connect("test.mosquitto.org", 8884)

client.connect("broker.mqttdashboard.com", port=1883)

h = 10
hum_plot = []
lumtotal = 0
direction = False

while True:
    client.subscribe('IC.embedded/hexfuture/type',qos=2)
    # package into JSON
    sensor_data, plot_data = combine.main()

    if sensor_data['Ambient Light Luminance'] > 25000:
        lumtotal += sensor_data['Ambient Light Luminance']/10

    if lumtotal > 10000:
        if direction == False :
            p.ChangeDutyCycle(2)
            sensor_data['motor'] = True
            direction=True
        else:
            p.ChangeDutyCycle(12.5)
            sensor_data['motor'] = True
            direction=False
        lumtotal=0
    
    if sensor_data['soil humidity'] > 22000:
        sensor_data['waterpump1'] = True
        GPIO.output(22,GPIO.HIGH)
    
    if sensor_data['soil humidity'] < 22000:
        sensor_data['waterpump1'] = False
        GPIO.output(22, GPIO.LOW) 

    hum_plot.append(plot_data)
    sensor_data['humidityValue'] = hum_plot
    payload = json.dumps(sensor_data)
    # pulish message
    MSG_INFO = client.publish("IC.embedded/hexfuture/data", payload, qos=2)
    mqtt.error_string(MSG_INFO.rc)
    print(payload)
    sensor_data['motor'] = False
    time.sleep(60)
