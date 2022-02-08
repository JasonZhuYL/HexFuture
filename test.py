import smbus2
import time
import json
import paho.mqtt.client as mqtt

#create the i2c bus
bus = smbus2.SMBus(1)

#send the measure temperature command
meas_temp= smbus2.i2c_msg.write(0x40,[0xf3])
bus.i2c_rdwr(meas_temp)

#wait for measurement
time.sleep(0.1)

#send the read temperature command and read 2 bytes of data
read_result= smbus2.i2c_msg.read(0x40,2)
bus.i2c_rdwr(read_result)

#convert the result to INT type
temp = int.from_bytes(read_result.buf[0]+read_result.buf[1],'big')

#package into JSON
sensor_data = {'temp':temp,'name':'hexfuture','time':time.time()}
payload = json.dumps(sensor_data)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code: " + str(rc))

client = mqtt.Client()
client.on_connect = on_connect
#set private key 
#(ca_certs=BROKER_CERT,certfile=CLIENT_CERT,keyfile=PRIVATE_KEY,tls_version=ssl.PROTOCOL_TLSv1_2)
#client.tls_set(ca_certs="mosquitto.org.crt", certfile="client.crt",keyfile='client.key')
#(BROKER_ADDRESS,port=N)
client.connect("broker.mqttdashboard.com",port=1883)

while True:
    meas_temp= smbus2.i2c_msg.write(0x40,[0xf3])
    bus.i2c_rdwr(meas_temp)

    #wait for measurement
    time.sleep(0.1)

    #send the read temperature command and read 2 bytes of data
    read_result= smbus2.i2c_msg.read(0x40,2)
    bus.i2c_rdwr(read_result)

    #convert the result to INT type
    temp = int.from_bytes(read_result.buf[0]+read_result.buf[1],'big')

    #package into JSON
    sensor_data = {'temp':temp,'name':'hexfuture','time':time.time()}
    payload = json.dumps(sensor_data)
    #pulish message
    MSG_INFO = client.publish("IC.embedded/hexfuture/test",payload,qos=2)
    mqtt.error_string(MSG_INFO.rc)
    print(payload)
    time.sleep(60)
