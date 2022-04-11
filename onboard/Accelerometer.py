import board
import adafruit_lis3dh

i2c = board.I2C()
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)

def get():
    return lis3dh.acceleration