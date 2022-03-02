# Embedded System Coursework 1 (Group HexFuture)

## Overall Architecture for HexPot (Smart Pot for Plant)

![alt text](HexPot_Architecture.jpg)

## Explanation for code

```bash
HexLibrary_final.py
```

This file is a library that contains implementation for accessing low-level sensors.

```bash
Main_final.py
```

This file contains code that runs the functions within HexLibrary_final.py and package the data from sensors into JSON format.

```bash
MQTT_final.py
```

This file is used for encryption communication with backend server through MQTT protocol. It will be called multiple times as long as the embedded system is running.

```bash
client.crt
client.csr
client.key
mosquitto.org.crt
```

All these files are used for MQTT encryption.

## To use

```bash
python3 MQTT_final.py
```

## Visit Webapp

```bash
18.134.242.125:5410
```
