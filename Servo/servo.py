import servo
from time import sleep

servo_ent = servo(10)
val = -1

try:
    while True:
        servo_ent.value = val
        sleep(0.1)
        val = val + 0.1
        if val > 1:
            val = -1
except KeyboardInterrupt:
    print("Program stopped")
