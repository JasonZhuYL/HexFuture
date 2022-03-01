import time
import json
import paho.mqtt.client as mqtt
import Combined_Ver6 as combine


def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))


client = mqtt.Client()
client.on_connect = on_connect
# set private key
# (ca_certs=BROKER_CERT,certfile=CLIENT_CERT,keyfile=PRIVATE_KEY,tls_version=ssl.PROTOCOL_TLSv1_2)
#client.tls_set(ca_certs="mosquitto.org.crt", certfile="client.crt",keyfile='client.key')
# (BROKER_ADDRESS,port=N)
client.connect("broker.mqttdashboard.com", port=1883)
h = 10
hum_plot = []

while True:
    # package into JSON
    sensor_data, plot_data = combine.main()
    hum_plot.append(plot_data)
    sensor_data['humidityValue'] = hum_plot
    payload = json.dumps(sensor_data)
    # pulish message
    MSG_INFO = client.publish("IC.embedded/hexfuture/test", payload, qos=2)
    mqtt.error_string(MSG_INFO.rc)
    print(payload)
    time.sleep(5)
