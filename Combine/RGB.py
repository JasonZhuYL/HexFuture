import HexLibrary2 as Hex
import time

# def lux(self, R, G , B)
#     R_Coef = 0.136  # |
#     G_Coef = 1.0  # | used in lux computation
#     B_Coef = -0.444  # |
#     # IR Rejection (DN40 3.1)

#     # Lux Calculation (DN40 3.2)
#     G1 = R_Coef * R + G_Coef * G + B_Coef * B
#     lux = G1 / CPL


def main():
    RGB = Hex.ColourSensor(0x29)

    try:
        while True:
            data = RGB.read_CRGB()
            print('Clear '+str(data[0])+' Red '+str(data[1])+' Green '+
                str(data[2])+' Blue '+str(data[3]))
            time.sleep(1)
    except KeyboardInterrupt:
        print("stop")

if __name__ == '__main__':
    print ("Starting...")
    main()
