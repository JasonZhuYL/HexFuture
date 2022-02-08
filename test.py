import smbus2
import time
import json
import paho.mqtt.client as mqtt

bus = smbus2.SMBus(1)
meas_temp= smbus2.i2c_msg.write(0x40,[0xf3])
bus.i2c_rdwr(meas_temp)
time.sleep(0.1)
read_result= smbus2.i2c_msg.read(0x40,2)
bus.i2c_rdwr(read_result)
temp = int.from_bytes(read_result.buf[0]+read_result.buf[1],'big')
sensor_data = {'temp':temp,'name':'hexfuture','time':time.time()}
payload = json.dumps(sensor_data)
client = mqtt.Client()
client.tls_set(ca_certs="mosquitto.org.crt", certfile="client.crt",keyfile='client.key')
client.connect("test.mosquitto.org",port=8884)
MSG_INFO = client.publish("IC.embedded/hexfuture/test",payload)
mqtt.error_string(MSG_INFO.rc)
print(payload)

