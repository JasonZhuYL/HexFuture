import time
import json
import paho.mqtt.client as mqtt
import Combined_Ver7_simple_lib as combine


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


def on_message(client, userdata, message):
    print("Received message:{} on topic {}".format(
        message.payload, message.topic))
    if message.topic == 'type':
        combine.set_threshold(message.payload['type'])


client = mqtt.Client()
client.on_connect = on_connect
# set private key
#client.tls_set(ca_certs="mosquitto.org.crt", certfile="client.crt",keyfile='client.key')
#client.connect("test.mosquitto.org", 8884)

client.connect("broker.mqttdashboard.com", port=1883)
h = 10
hum_plot = []
client.subscribe('IC.embedded/hexfuture/type',qos=2)
while True:
    # package into JSON
    sensor_data, plot_data = combine.main()
    hum_plot.append(plot_data)
    sensor_data['humidityValue'] = hum_plot
    payload = json.dumps(sensor_data)
    # pulish message
    MSG_INFO = client.publish("IC.embedded/hexfuture/data", payload, qos=2)
    mqtt.error_string(MSG_INFO.rc)
    print(payload)
    time.sleep(5)
