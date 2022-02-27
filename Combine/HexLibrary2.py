import smbus2
import time


bus = smbus2.SMBus(1)


# SI7021 address, 0x40 
class temperature_SI7021 ():
    def __init__(self,address=0x40): 
        self.address = address
    def startMeasure(self):
        # 0xF3 is the measurement command 
        bus.write_byte(self.address, 0xF3)
    def read_temp_cels(self):
        data0 = bus.read_byte(0x40)
        data1 = bus.read_byte(0x40)
        # functino provided in the data sheet 
        humidity = ((data0 * 256 + data1) * 125 / 65536.0) - 6
        # Convert the data and output it
        celsTemp = ((data0 * 256 + data1) * 175.72 / 65536.0) - 46.85
        return humidity,celsTemp

    def measure(self):
        self.startMeasure()
        time.sleep(0.01)
        return self.read_temp_cels()

ADS1115_CONFIG_GAIN = {
    2/3: 0x0000,
    1:   0x0200,
    2:   0x0400,
    4:   0x0600,
    8:   0x0800,
    16:  0x0A00
}

class ADS1115(): 
    def __init__(self,address=0x48):
        self.address = address
        # the default datarate  
        self.datarate = 0x0080

    def _conversion_value(self, low, high):
        # Convert to 16-bit signed value.
        value = ((high & 0xFF) << 8) | (low & 0xFF)
        # Check for sign bit and turn into a negative value if set.
        if value & 0x8000 != 0:
            value -= 1 << 16
        return value
    
    def read_adc(self, channel, gain=1):
        assert 0<= channel <= 3, 'Channel must be a value within 0-3!'
        return self._read(channel + 0x04, gain)

    def _read(self, mux, gain):
        config = 0x8000
        config |= (mux & 0x07) << 12
        if gain not in ADS1115_CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        config |= ADS1115_CONFIG_GAIN[gain]

        #setting datarate to default 128
        config |= 0x0080
        #mode for single shot (set to 0 for continuous)
        config |= 0x0100
        #diable the comparator mode 
        config |= 0x0003

        #0x01 for config register 
        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes.         
        write1 = smbus2.i2c_msg.write(self.address,[0x01,(config >> 8) & 0xFF, config & 0xFF])
        bus.i2c_rdwr(write1)

        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/128.0+0.0001)

        # reading process 
        # Retrieve the result.
        write2 = smbus2.i2c_msg.write(self.address,[0x00])
        read1 = smbus2.i2c_msg.read(self.address,2)
        bus.i2c_rdwr(write2,read1)
        result = list(read1)
        return self._conversion_value(int(result[1]),int(result[0]))


    def read_adc_difference(self, differential, gain=1, data_rate=None):
        # Read the difference between two ADC channels and return the ADC value
        # as a signed integer result.  Differential must be one of:
        #   - 0 = Channel 0 minus channel 1
        #   - 1 = Channel 0 minus channel 3
        #   - 2 = Channel 1 minus channel 3
        #   - 3 = Channel 2 minus channel 3

        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Perform a single shot read using the provided differential value
        # as the mux value (which will enable differential mode).
        return self._read(differential, gain)


class ColourSensor:

    def __init__(self, i2cAddress):

        self.address = i2cAddress


    def convert_value(self, lowByte, highByte):
        #convert_value,  add low and high bytes of data together to 
        #provide output
        value = (highByte<<8) + lowByte        
        return value

    def single_access_read(self, reg=0x00):
        #single_access_read, function to read a single data register
        #of the TCS34725 RGB colour sensor

        cmdBit = 0b1 # cmd field set to 1
        msBit = 0b01 # type field set to auto increment

        cmd = (cmdBit<<7)+(msBit<<5)+reg              
        dataTransfer = bus.read_byte_data(self.address,cmd)
        return dataTransfer


    def read_CRGB(self):

        output=[]
        # according to register address on the specification 
        clearLow = self.single_access_read(0x14)
        clearHigh = self.single_access_read(0x15)
        redLow = self.single_access_read(0x16)
        redHigh = self.single_access_read(0x17)
        greenLow = self.single_access_read(0x18)
        greenHigh = self.single_access_read(0x19)
        blueLow = self.single_access_read(0x1A)
        blueHigh = self.single_access_read(0x1B)

        output.append(self.convert_value(clearLow, clearHigh))
        output.append(self.convert_value(redLow, redHigh))
        output.append(self.convert_value(greenLow, greenHigh))
        output.append(self.convert_value(blueLow, blueHigh))

        return output
