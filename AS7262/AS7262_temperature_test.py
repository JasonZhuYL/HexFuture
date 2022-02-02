
from as7262 import AS7262
import matplotlib.pyplot as plt
import numpy as np

as7262 = AS7262()

as7262.set_gain(1) # 1, 3.7, 16, 64
as7262.set_integration_time(10) #1 to 255 x 2.8ms exposure
#mode 0 - bank 1 only continuous, mode 1 - bank 2 only continuous, mode 2 - both banks continuous, mode 3 - both banks single read 
as7262.set_measurement_mode(2) #2 all colours continuous
as7262.set_illumination_led_current(12.5) #12.5mA 25mA 50mA 100mA
as7262.set_illumination_led(1) # led on

def bargraph(self):
    label = ("Red","Ora","Yel","Gre","Blu","Vio")
    y_pos = np.arange(len(label))
    barcol = ('red','orange','yellow','green','blue','violet') #Graph bar colours
    plt.bar(y_pos,self,color=(barcol))
    plt.xticks(y_pos,label)
    plt.show()

try:
    while True:
        values = as7262.get_calibrated_values() #get values from scan
        spec = [float(i) for i in list(values)] #convert results from string to float
        print(spec)
        bargraph(spec)

except KeyboardInterrupt:
    as7262.set_measurement_mode(3) #switch to single scan mode
    as7262.set_illumination_led(0) 'led off