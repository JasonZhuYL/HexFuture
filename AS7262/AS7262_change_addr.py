
#!/usr/bin/python3
#This script uses a as7262 6 colour spectral scanner from Pimoroni and displays the resulting values.
#raspberryconnect.com

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

#----------------------------------------------------------------------------------------------------------------#


as7262 = AS7262()

as7262.set_gain(1) # 1, 3.7, 16, 64
as7262.set_integration_time(10) #1 to 255 x 2.8ms exposure
#mode 0 - bank 1 only continuous, mode 1 - bank 2 only continuous, mode 2 - both banks continuous, mode 3 - both banks single read 
as7262.set_measurement_mode(2) #2 all colours continuous
# as7262.set_illumination_led_current(12.5) #12.5mA 25mA 50mA 100mA
# as7262.set_illumination_led(1) # led on

def main():
	try:
		while 1:
			values = as7262.get_calibrated_values() #get values from scan
			
			spec = [float(i) for i in list(values)] #convert results from string to float				
			sum=0
			for j in range(len(spec)):
				sum += spec[j]	 
			print("Sum: ",sum)
			#print("Spec: ",spec)
	except KeyboardInterrupt:
			as7262.set_measurement_mode(3) #Switch to scan on demand
			as7262.set_illumination_led(0) #light off

if __name__ == '__main__':
    main()
