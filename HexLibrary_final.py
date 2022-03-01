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



# Start of color sensor 
TCS34725_DEFAULT_ADDRESS = 0x29

# TCS34725 Register Set
TCS34725_COMMAND_BIT = 0x80
TCS34725_REG_ENABLE = 0x00 # Enables states and interrupts
TCS34725_REG_ATIME = 0x01 # RGBC integration time
TCS34725_REG_WTIME = 0x03 # Wait time
TCS34725_REG_CONFIG = 0x0D # Configuration register
TCS34725_REG_CONTROL = 0x0F # Control register
TCS34725_REG_CDATAL = 0x14 # Clear/IR channel low data register
# TCS34725_REG_CDATAH = 0x15 # Clear/IR channel high data register
# TCS34725_REG_RDATAL = 0x16 # Red ADC low data register
# TCS34725_REG_RDATAH = 0x17 # Red ADC high data register
# TCS34725_REG_GDATAL = 0x18 # Green ADC low data register
# TCS34725_REG_GDATAH = 0x19 # Green ADC high data register
# TCS34725_REG_BDATAL = 0x1A # Blue ADC low data register
# TCS34725_REG_BDATAH = 0x1B # Blue ADC high data register

# TCS34725 Enable Register Configuration
# TCS34725_REG_ENABLE_SAI = 0x40 # Sleep After Interrupt
# TCS34725_REG_ENABLE_AIEN = 0x10 # ALS Interrupt Enable
# TCS34725_REG_ENABLE_WEN = 0x08 # Wait Enable
TCS34725_REG_ENABLE_AEN = 0x02 # ADC Enable
TCS34725_REG_ENABLE_PON = 0x01 # Power ON

# TCS34725 Time Register Configuration
TCS34725_REG_ATIME_2_4 = 0xFF # Atime = 2.4 ms, Cycles = 1
TCS34725_REG_ATIME_24 = 0xF6 # Atime = 24 ms, Cycles = 10
TCS34725_REG_ATIME_101 = 0xDB # Atime = 101 ms, Cycles = 42
TCS34725_REG_ATIME_154 = 0xC0 # Atime = 154 ms, Cycles = 64
TCS34725_REG_ATIME_700 = 0x00 # Atime = 700 ms, Cycles = 256
TCS34725_REG_WTIME_2_4 = 0xFF # Wtime = 2.4 ms
TCS34725_REG_WTIME_204 = 0xAB # Wtime = 204 ms
TCS34725_REG_WTIME_614 = 0x00 # Wtime = 614 ms

# TCS34725 Gain Configuration
TCS34725_REG_CONTROL_AGAIN_1 = 0x00 # 1x Gain
TCS34725_REG_CONTROL_AGAIN_4 = 0x01 # 4x Gain
TCS34725_REG_CONTROL_AGAIN_16 = 0x02 # 16x Gain
TCS34725_REG_CONTROL_AGAIN_60 = 0x03 # 60x Gain

class TCS34725():
    def __init__(self):
        self.enable_selection()
        self.time_selection()
        self.gain_selection()

    def enable_selection(self):
        #Select the ENABLE register configuration from the given provided values
        ENABLE_CONFIGURATION = (TCS34725_REG_ENABLE_AEN | TCS34725_REG_ENABLE_PON)
        bus.write_byte_data(TCS34725_DEFAULT_ADDRESS, TCS34725_REG_ENABLE | TCS34725_COMMAND_BIT, ENABLE_CONFIGURATION)

    def time_selection(self):
        #Select the ATIME register configuration from the given provided values
        bus.write_byte_data(TCS34725_DEFAULT_ADDRESS, TCS34725_REG_ATIME | TCS34725_COMMAND_BIT, TCS34725_REG_ATIME_700)

        #Select the WTIME register configuration from the given provided values
        bus.write_byte_data(TCS34725_DEFAULT_ADDRESS, TCS34725_REG_WTIME | TCS34725_COMMAND_BIT, TCS34725_REG_WTIME_2_4)

    def gain_selection(self):
        #Select the gain register configuration from the given provided values
        bus.write_byte_data(TCS34725_DEFAULT_ADDRESS, TCS34725_REG_CONTROL | TCS34725_COMMAND_BIT, TCS34725_REG_CONTROL_AGAIN_1)

    def readluminance(self):
        #Read data back from TCS34725_REG_CDATAL(0x94), 8 bytes, with TCS34725_COMMAND_BIT, (0x80)
        #cData LSB, cData MSB, Red LSB, Red MSB, Green LSB, Green MSB, Blue LSB, Blue MSB
        data = bus.read_i2c_block_data(TCS34725_DEFAULT_ADDRESS, TCS34725_REG_CDATAL | TCS34725_COMMAND_BIT, 8)

    # Convert the data
        cData = data[1] * 256 + data[0]
        red = data[3] * 256 + data[2]
        green = data[5] * 256 + data[4]
        blue = data[7] * 256 + data[6]

        # Calculate luminance
        luminance = (-0.32466 * red) + (1.57837 * green) + (-0.73191 * blue)

        return {'c' : cData, 'r' : red, 'g' : green, 'b' : blue, 'l' : luminance}
