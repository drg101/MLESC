import RPi.GPIO as GPIO
from inputs import devices, get_gamepad
from SpeedEncoder import SpeedEncoder
from threading import Thread
from time import time
import Accelerometer

GPIO.setmode(GPIO.BCM)

class MotorControl:
    def __init__(self, pwm_port, pos_port, neg_port, pwm_hz):
        self.pwm_port = pwm_port
        self.pos_port = pos_port
        self.neg_port = neg_port
        self.pwm_hz = pwm_hz

        GPIO.setup(pwm_port,GPIO.OUT)
        GPIO.setup(pos_port,GPIO.OUT)
        GPIO.setup(neg_port,GPIO.OUT)
        self.pwm=GPIO.PWM(pwm_port,pwm_hz)

        self.pwm.start(0)
        GPIO.output(pos_port,GPIO.LOW)
        GPIO.output(neg_port,GPIO.LOW)
    
    def set_dir(self, forward):
        if forward:
            print("here")
            GPIO.output(self.pos_port,GPIO.HIGH)
            GPIO.output(self.neg_port,GPIO.LOW)
        else:
            GPIO.output(self.pos_port,GPIO.LOW)
            GPIO.output(self.neg_port,GPIO.HIGH)
        
    def set_duty_cycle(self, duty_cycle):
        self.pwm.ChangeDutyCycle(duty_cycle)

dir = True
mc_l = MotorControl(13,19,26,1024)
mc_l.set_dir(dir)

mc_r = MotorControl(17,27,22,1024)
mc_r.set_dir(dir)

se = SpeedEncoder(20,21,23,24)

N = 25
# poll for sensor data
def poll_sensors():
    old_time = time()
    while 1:
        se.poll()

        #report sensor data N times per second
        curr_time = time()
        if curr_time - old_time > 1 / N:
            acc = -1
            try:
                acc = Accelerometer.get()[1]
            except:
                pass
            if acc > 0:
                print(f"hmm: {se.get_rot()} accel = {acc}")
            old_time = curr_time


sensor_poller_thread = Thread(target=poll_sensors, args=[])
sensor_poller_thread.start()


turn = 0
duty_cycle = 0
while 1:
    events = get_gamepad()
    for event in events:
        if event.code == "ABS_RZ":
            new_duty_cycle = round(event.state / 1023 * 100)
            # print(f"nds {new_duty_cycle}")
            duty_cycle = new_duty_cycle
        elif event.code == "ABS_X":
            new_turn = event.state / 32768
            # print(se_l.get_rot())
            # print(f"LR: {new_turn}")
            turn = new_turn
    mc_l.set_duty_cycle(duty_cycle * max(0,min(1, (1 + turn))))
    mc_r.set_duty_cycle(duty_cycle * max(0,min(1, (1 - turn))))
