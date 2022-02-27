import sys
import smbus 
import smbus2
import time
import struct
import json
import RPi.GPIO as GPIO

# from i2cdevice import Device, Register, BitField, _int_to_bytes

from collections import namedtuple
#Device 

class MockSMBus:
    def __init__(self, i2c_bus, default_registers=None):
        self.regs = [0 for _ in range(255)]
        if default_registers is not None:
            for index in default_registers.keys():
                self.regs[index] = default_registers.get(index)

    def write_i2c_block_data(self, i2c_address, register, values):
        self.regs[register:register + len(values)] = values

    def read_i2c_block_data(self, i2c_address, register, length):
        return self.regs[register:register + length]


def _trailing_zeros(value, bit_width=8):
    """Count trailing zeros on a binary number with a given bit_width
    ie: 0b11000 = 3
    Used for shifting around values after masking.
    """
    count = 0
    for _ in range(bit_width):
        if value & 1:
            return count
        count += 1
        value >>= 1
    return count

class _RegisterProxy(object):
    """Register Proxy
    This proxy catches lookups against non existent get_fieldname and set_fieldname methods
    and converts them into calls against the device's get_field and set_field methods with
    the appropriate options.
    This means device.register.set_field(value) and device.register.get_field(value) will work
    and also transparently update the underlying device without the register or field objects
    having to know anything about how data is written/read/stored.
    """
    def __init__(self, device, register):
        self.device = device
        self.register = register

    def __getattribute__(self, name):
        if name.startswith("get_"):
            name = name.replace("get_", "")
            return lambda: self.device.get_field(self.register.name, name)
        if name.startswith("set_"):
            name = name.replace("set_", "")
            return lambda value: self.device.set_field(self.register.name, name, value)
        return object.__getattribute__(self, name)

    def write(self):
        return self.device.write_register(self.register.name)

    def read(self):
        return self.device.read_register(self.register.name)

    def __enter__(self):
        self.device.read_register(self.register.name)
        self.device.lock_register(self.register.name)
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.device.unlock_register(self.register.name)

class Register():
    """Store information about an i2c register"""
    def __init__(self, name, address, fields=None, bit_width=8, read_only=False, volatile=True):
        self.name = name
        self.address = address
        self.bit_width = bit_width
        self.read_only = read_only
        self.volatile = volatile
        self.is_read = False
        self.fields = {}

        for field in fields:
            self.fields[field.name] = field

        self.namedtuple = namedtuple(self.name, sorted(self.fields))
class BitField():
    """Store information about a field or flag in an i2c register"""
    def __init__(self, name, mask, adapter=None, bit_width=8, read_only=False):
        self.name = name
        self.mask = mask
        self.adapter = adapter
        self.bit_width = bit_width
        self.read_only = read_only
class Device(object):
    def __init__(self, i2c_address, i2c_dev=None, bit_width=8, registers=None):
        self._bit_width = bit_width

        self.locked = {}
        self.registers = {}
        self.values = {}
        if type(i2c_address) is list:
            self._i2c_addresses = i2c_address
            self._i2c_address = i2c_address[0]
        else:
            self._i2c_addresses = [i2c_address]
            self._i2c_address = i2c_address

        self._i2c = i2c_dev

        if self._i2c is None:
            import smbus
            self._i2c = smbus.SMBus(1)

        for register in registers:
            self.locked[register.name] = False
            self.values[register.name] = 0
            self.registers[register.name] = register
            self.__dict__[register.name] = _RegisterProxy(self, register)

    def lock_register(self, name):
        self.locked[name] = True

    def unlock_register(self, name):
        self.locked[name] = False

    def read_register(self, name):
        register = self.registers[name]
        if register.volatile or not register.is_read:
            self.values[register.name] = self._i2c_read(register.address, register.bit_width)
            register.is_read = True
        return self.values[register.name]

    def write_register(self, name):
        register = self.registers[name]
        return self._i2c_write(register.address, self.values[register.name], register.bit_width)

    def set(self, register, **kwargs):
        """Write one or more fields on a device register.
        Accepts multiple keyword arguments, one for each field to write.
        :param register: Name of register to write.
        """
        self.read_register(register)
        self.lock_register(register)
        for field in kwargs.keys():
            value = kwargs.get(field)
            self.set_field(register, field, value)
        self.write_register(register)
        self.unlock_register(register)

    def get(self, register):
        """Get a namedtuple containing register fields.
        :param register: Name of register to retrieve
        """
        result = {}
        self.read_register(register)
        self.lock_register(register)
        for field in self.registers[register].fields:
            result[field] = self.get_field(register, field)
        self.unlock_register(register)
        return self.registers[register].namedtuple(**result)

    def get_field(self, register, field):
        register = self.registers[register]
        field = register.fields[field]

        if not self.locked[register.name]:
            self.read_register(register.name)

        value = self.values[register.name]

        value = (value & field.mask) >> _trailing_zeros(field.mask, register.bit_width)

        if field.adapter is not None:
            try:
                value = field.adapter._decode(value)
            except ValueError as value_error:
                raise ValueError("{}: {}".format(field.name, str(value_error)))

        return value

    def set_field(self, register, field, value):
        register = self.registers[register]
        field = register.fields[field]
        shift = _trailing_zeros(field.mask, register.bit_width)

        if field.adapter is not None:
            value = field.adapter._encode(value)

        if not self.locked[register.name]:
            self.read_register(register.name)

        reg_value = self.values[register.name]

        reg_value &= ~field.mask
        reg_value |= (value << shift) & field.mask

        self.values[register.name] = reg_value

        if not self.locked[register.name]:
            self.write_register(register.name)

    # def get_register(self, register):
    #     register = self.registers[register]
    #     return self._i2c_read(register.address, register.bit_width)

    def _i2c_write(self, register, value, bit_width):
        values = _int_to_bytes(value, bit_width // self._bit_width, 'big')
        values = list(values)
        self._i2c.write_i2c_block_data(self._i2c_address, register, values)

    def _i2c_read(self, register, bit_width):
        value = 0
        for x in self._i2c.read_i2c_block_data(self._i2c_address, register, bit_width // self._bit_width):
            value <<= 8
            value |= x
        return value
def _int_to_bytes(value, length, endianness='big'):
    try:
        return value.to_bytes(length, endianness)
    except AttributeError:
        output = bytearray()
        for x in range(length):
            offset = x * 8
            mask = 0xff << offset
            output.append((value & mask) >> offset)
        if endianness == 'big':
            output.reverse()
        return output

class Adapter:
    """
    Must implement `_decode()` and `_encode()`.
    """
    def _decode(self, value):
        raise NotImplementedError

    def _encode(self, value):
        raise NotImplementedError

class LookupAdapter(Adapter):
    """Adaptor with a dictionary of values.
    :param lookup_table: A dictionary of one or more key/value pairs where the key is the human-readable value and the value is the bitwise register value
    """
    def __init__(self, lookup_table, snap=True):
        self.lookup_table = lookup_table
        self.snap = snap

    def _decode(self, value):
        for k, v in self.lookup_table.items():
            if v == value:
                return k
        raise ValueError("{} not in lookup table".format(value))

    def _encode(self, value):
        if self.snap and type(value) in [int, float]:
            value = min(list(self.lookup_table.keys()), key=lambda x: abs(x - value))
        return self.lookup_table[value]



bus = smbus2.SMBus(1)


# Register and other configuration values:
ADS1115_DEFAULT_ADDRESS        = 0x48
# address of conversion register in P[1:0]
ADS1115_POINTER_CONVERSION_REGISTER     = 0x00
# address of config register in P[1:0]
ADS1115_POINTER_CONFIG_REGISTER         = 0x01
ADS1115_CONFIG_OS_SINGLE       = 0x8000

ADS1115_CONFIG_MUX_OFFSET      = 12
# Maping of gain values to config register values.
ADS1115_CONFIG_GAIN = {
    2/3: 0x0000,
    1:   0x0200,
    2:   0x0400,
    4:   0x0600,
    8:   0x0800,
    16:  0x0A00
}
ADS1115_CONFIG_MODE_CONTINUOUS  = 0x0000
ADS1115_CONFIG_MODE_SINGLE      = 0x0100

# Mapping of data/sample rate to config register values for ADS1115 (slower).
# DR is set in the config register 
ADS1115_CONFIG_DR = {
    8:    0x0000,
    16:   0x0020,
    32:   0x0040,
    64:   0x0060,
    128:  0x0080,
    250:  0x00A0,
    475:  0x00C0,
    860:  0x00E0
}
ADS1115_CONFIG_COMP_QUE = {
    1: 0x0000,
    2: 0x0001,
    4: 0x0002
}
ADS1115_CONFIG_COMP_QUE_DISABLE = 0x0003
#----------------------------------------------------------------------------------------------------------------#
class ADS1115_new(): 
    def __init__(self,address):
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

        return self._read(channel + 0x04, gain, ADS1115_CONFIG_MODE_SINGLE)

    def _read(self, mux, gain, mode):
        """Perform an ADC read with the provided mux, gain, data_rate, and mode
        values.  Returns the signed integer result of the read.
        """
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

        #writing to the let slave know which register to write 
        #last bit is 0 for written 
        # bus.write_byte((self.address<<1)&0xFF)

        #0x01 for config register 
        # bus.write_byte(self.address,0x01)
        # bus.write_block_data(self.address,0x01,[(config >> 8) & 0xFF, config & 0xFF])
        # bus.write(self.address,[0x01,(config >> 8) & 0xFF, config & 0xFF])
        bus.write_word_data(self.address,0x01,config)
        print("sending ",config)

        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes. 
        # bus.write_byte(self.address,(config >> 8) & 0xFF)
        # bus.write_byte(self.address, config & 0xFF)

        # self._device.writeList(ADS1115_POINTER_CONFIG_REGISTER, [(config >> 8) & 0xFF, config & 0xFF])
       
        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/128.0+0.0001)

        # reading process 
        # Retrieve the result.

        word = bus.read_word_data(self.address,0x01)
        print("the word (two byte) is ",word)

        # print("data0: ",word[1],"  data1: ", word[0])


        # [(config >> 8) & 0xFF, config & 0xFF]
        data0 = (word >> 8) & 0xFF
        data1 =  word  & 0xFF
        print("data0: ",data0,"  data1: ", data1)
        result = self._device.readList(ADS1115_POINTER_CONVERSION_REGISTER, 2)
        return self._conversion_value(data0,  data1)

    def read_adc_difference(self, differential, gain=1, data_rate=None):
        """Read the difference between two ADC channels and return the ADC value
        as a signed integer result.  Differential must be one of:
          - 0 = Channel 0 minus channel 1
          - 1 = Channel 0 minus channel 3
          - 2 = Channel 1 minus channel 3
          - 3 = Channel 2 minus channel 3
        """
        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Perform a single shot read using the provided differential value
        # as the mux value (which will enable differential mode).
        return self._read(differential, gain, ADS1115_CONFIG_MODE_SINGLE)


class ADS1115():
    """Base functionality for ADS1115 analog to digital converters."""

    def __init__(self, address=ADS1115_DEFAULT_ADDRESS, i2c=None, **kwargs):
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            print("Adafruit i2c library imported!")
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)
        
    # def _data_rate_default(self):
    #     # Default from datasheet page 16, config register DR bit default.
    #     return 128
    
    def _data_rate_config(self, data_rate):
        if data_rate not in ADS1115_CONFIG_DR:
            raise ValueError('Data rate must be one of: 8, 16, 32, 64, 128, 250, 475, 860')
        return ADS1115_CONFIG_DR[data_rate]
    
    def _conversion_value(self, low, high):
        # Convert to 16-bit signed value.
        value = ((high & 0xFF) << 8) | (low & 0xFF)
        # Check for sign bit and turn into a negative value if set.
        if value & 0x8000 != 0:
            value -= 1 << 16
        return value

    def read_adc(self, channel, gain=1, data_rate=None):
        """Read a single ADC channel and return the ADC value as a signed integer
        result.  Channel must be a value within 0-3.
        """
        assert 0 <= channel <= 3, 'Channel must be a value within 0-3!'
        # Perform a single shot read and set the mux value to the channel plus
        # the highest bit (bit 3) set.
        return self._read(channel + 0x04, gain, data_rate, ADS1115_CONFIG_MODE_SINGLE)

    def _read(self, mux, gain, data_rate, mode):
        """Perform an ADC read with the provided mux, gain, data_rate, and mode
        values.  Returns the signed integer result of the read.
        """
        config = ADS1115_CONFIG_OS_SINGLE  # Go out of power-down mode for conversion.
        # Specify mux value.
        config |= (mux & 0x07) << ADS1115_CONFIG_MUX_OFFSET
        # Validate the passed in gain and then set it in the config.
        if gain not in ADS1115_CONFIG_GAIN:
            raise ValueError('Gain must be one of: 2/3, 1, 2, 4, 8, 16')
        config |= ADS1115_CONFIG_GAIN[gain]
        # Set the mode (continuous or single shot).
        config |= mode
        # Get the default data rate if none is specified (default differs between
        # ADS1015 and ADS1115).
        if data_rate is None:
            # data_rate = self._data_rate_default()
            data_rate = 128
        # Set the data rate (this is controlled by the subclass as it differs
        # between ADS1015 and ADS1115).
        config |= self._data_rate_config(data_rate)
        config |= ADS1115_CONFIG_COMP_QUE_DISABLE  # Disble comparator mode.
        # Send the config value to start the ADC conversion.
        # Explicitly break the 16-bit value down to a big endian pair of bytes.
        print("sending " ,config)
        self._device.writeList(ADS1115_POINTER_CONFIG_REGISTER, [(config >> 8) & 0xFF, config & 0xFF])
        # Wait for the ADC sample to finish based on the sample rate plus a
        # small offset to be sure (0.1 millisecond).
        time.sleep(1.0/data_rate+0.0001)
        # Retrieve the result.
        result = self._device.readList(ADS1115_POINTER_CONVERSION_REGISTER, 2)
        print ("the result0 is ",result[0], " the result 1 is ", result[1])

        return self._conversion_value(result[1], result[0])

    def read_adc_difference(self, differential, gain=1, data_rate=None):
        """Read the difference between two ADC channels and return the ADC value
        as a signed integer result.  Differential must be one of:
          - 0 = Channel 0 minus channel 1
          - 1 = Channel 0 minus channel 3
          - 2 = Channel 1 minus channel 3
          - 3 = Channel 2 minus channel 3
        """
        assert 0 <= differential <= 3, 'Differential must be a value within 0-3!'
        # Perform a single shot read using the provided differential value
        # as the mux value (which will enable differential mode).
        return self._read(differential, gain, data_rate, ADS1115_CONFIG_MODE_SINGLE)
#----------------------------------------------------------------------------------------------------------------#
class as7262VirtualRegisterBus():
    """AS7262 Virtual Register.
    This class implements the wacky virtual register setup
    of the AS7262 annd allows i2cdevice.Device to "just work"
    without having to worry about how registers are actually
    read or written under the hood.
    """

    def __init__(self, i2c_dev=None):
        """Initialise virtual register class.
        :param bus: SMBus bus ID
        """
        if i2c_dev is None:
            import smbus
            self._i2c_bus = smbus.SMBus(1)
            print("smbus imported in AS7262")
        else:
            self._i2c_bus = i2c_dev

    def get_status(self, address):
        """Return the AS7262 status register."""
        return self._i2c_bus.read_byte_data(address, 0x00)

    def write_i2c_block_data(self, address, register, values):
        """Right one or more values to AS7262 virtual registers."""
        for offset in range(len(values)):
            while True:
                if (self.get_status(address) & 0b10) == 0:
                    break
            self._i2c_bus.write_byte_data(address, 0x01, register | 0x80)
            while True:
                if (self.get_status(address) & 0b10) == 0:
                    break
            self._i2c_bus.write_byte_data(address, 0x01, values[offset])

    def read_i2c_block_data(self, address, register, length):
        """Read one or more values from AS7262 virtual registers."""
        result = []
        for offset in range(length):
            while True:
                if (self.get_status(address) & 0b10) == 0:
                    break
            self._i2c_bus.write_byte_data(address, 0x01, register + offset)
            while True:
                if (self.get_status(address) & 0b01) == 1:
                    break
            result.append(self._i2c_bus.read_byte_data(address, 0x02))
        return result

#----------------------------------------------------------------------------------------------------------------#
class FloatAdapter(Adapter):
    """Convert a 4 byte register set into a float."""

    def _decode(self, value):
        b = _int_to_bytes(value, 4)
        return struct.unpack('>f', bytearray(b))[0]

class IntegrationTimeAdapter(Adapter):
    """Scale integration time in ms to LSBs."""

    def _decode(self, value):
        return value / 2.8

    def _encode(self, value):
        return int(value * 2.8) & 0xff

class FWVersionAdapter(Adapter):
    """Convert the AS7262 firmware version number to a human-readable string."""

    def _decode(self, value):
        major_version = (value & 0x00F0) >> 4
        minor_version = ((value & 0x000F) << 2) | ((value & 0b1100000000000000) >> 14)
        sub_version = (value & 0b0011111100000000) >> 8
        return '{}.{}.{}'.format(major_version, minor_version, sub_version)

class CalibratedValues:
    """Store the 6 band spectral values."""

    def __init__(self, red, orange, yellow, green, blue, violet):  # noqa D107
        self.red = red
        self.orange = orange
        self.yellow = yellow
        self.green = green
        self.blue = blue
        self.violet = violet

    def __iter__(self):  # noqa D107
        for colour in ['red', 'orange', 'yellow', 'green', 'blue', 'violet']:
            yield getattr(self, colour)

class AS7262:
    def __init__(self, i2c_dev=None):
        self._as7262 = Device(0x49, i2c_dev=as7262VirtualRegisterBus(i2c_dev=i2c_dev), bit_width=8, registers=(
            Register('VERSION', 0x00, fields=(
                BitField('hw_type', 0xFF000000),
                BitField('hw_version', 0x00FF0000),
                BitField('fw_version', 0x0000FFFF, adapter=FWVersionAdapter()),
            ), bit_width=32, read_only=True),
            Register('CONTROL', 0x04, fields=(
                BitField('reset', 0b10000000),
                BitField('interrupt', 0b01000000),
                BitField('gain_x', 0b00110000, adapter=LookupAdapter({
                    1: 0b00, 3.7: 0b01, 16: 0b10, 64: 0b11
                })),
                BitField('measurement_mode', 0b00001100),
                BitField('data_ready', 0b00000010),
            )),
            Register('INTEGRATION_TIME', 0x05, fields=(
                BitField('ms', 0xFF, adapter=IntegrationTimeAdapter()),
            )),
            Register('TEMPERATURE', 0x06, fields=(
                BitField('degrees_c', 0xFF),
            )),
            Register('LED_CONTROL', 0x07, fields=(
                BitField('illumination_current_limit_ma', 0b00110000, adapter=LookupAdapter({
                    12.5: 0b00, 25: 0b01, 50: 0b10, 100: 0b11
                })),
                BitField('illumination_enable', 0b00001000),
                BitField('indicator_current_limit_ma', 0b00000110, adapter=LookupAdapter({
                    1: 0b00, 2: 0b01, 4: 0b10, 8: 0b11
                })),
                BitField('indicator_enable', 0b00000001),
            )),
            Register('DATA', 0x08, fields=(
                BitField('v', 0xFFFF00000000000000000000),
                BitField('b', 0x0000FFFF0000000000000000),
                BitField('g', 0x00000000FFFF000000000000),
                BitField('y', 0x000000000000FFFF00000000),
                BitField('o', 0x0000000000000000FFFF0000),
                BitField('r', 0x00000000000000000000FFFF),
            ), bit_width=96),
            Register('CALIBRATED_DATA', 0x14, fields=(
                BitField('v', 0xFFFFFFFF << (32 * 5), adapter=FloatAdapter()),
                BitField('b', 0xFFFFFFFF << (32 * 4), adapter=FloatAdapter()),
                BitField('g', 0xFFFFFFFF << (32 * 3), adapter=FloatAdapter()),
                BitField('y', 0xFFFFFFFF << (32 * 2), adapter=FloatAdapter()),
                BitField('o', 0xFFFFFFFF << (32 * 1), adapter=FloatAdapter()),
                BitField('r', 0xFFFFFFFF << (32 * 0), adapter=FloatAdapter()),
            ), bit_width=192),
        ))

        # TODO : Integrate into i2cdevice so that LookupAdapter fields can always be exported to constants
        # Iterate through all register fields and export their lookup tables to constants
        for register in self._as7262.registers:
            register = self._as7262.registers[register]
            for field in register.fields:
                field = register.fields[field]
                if isinstance(field.adapter, LookupAdapter):
                    for key in field.adapter.lookup_table:
                        value = field.adapter.lookup_table[key]
                        name = 'AS7262_{register}_{field}_{key}'.format(
                            register=register.name,
                            field=field.name,
                            key=key
                        ).upper()
                        locals()[name] = key

        self.soft_reset()

    def soft_reset(self):
        """Set the soft reset register bit of the AS7262."""
        self._as7262.set('CONTROL', reset=1)
        # Polling for the state of the reset flag does not work here
        # since the fragile virtual register state machine cannot
        # respond while in a soft reset condition
        # So, just wait long enough for it to reset fully...
        time.sleep(2.0)

    def get_calibrated_values(self, timeout=10):
        """Return an instance of CalibratedValues containing the 6 spectral bands."""
        t_start = time.time()
        while self._as7262.get('CONTROL').data_ready == 0 and (time.time() - t_start) <= timeout:
            pass
        data = self._as7262.get('CALIBRATED_DATA')
        return CalibratedValues(data.r, data.o, data.y, data.g, data.b, data.v)

    def set_gain(self, gain):
        """Set the gain amount of the AS7262.
        :param gain: gain multiplier, one of 1, 3.7, 16 or 64
        """
        self._as7262.set('CONTROL', gain_x=gain)

    def set_measurement_mode(self, mode):
        """Set the AS7262 measurement mode.
        :param mode: 0-3
        """
        self._as7262.set('CONTROL', measurement_mode=mode)

    def set_integration_time(self, time_ms):
        """Set the AS7262 sensor integration time in milliseconds.
        :param time_ms: Time in milliseconds from 0 to ~91
        """
        self._as7262.set('INTEGRATION_TIME', ms=time_ms)
