import RPi.GPIO as GPIO
from inputs import devices, get_gamepad
from SpeedEncoder import SpeedEncoder
from threading import Thread
from time import time
import Accelerometer
from math import floor
import os
import numpy as np
import signal


MODE = 3

if MODE == 1:
    import tflite_runtime.interpreter as tflite
    interpreter = tflite.Interpreter('../analyze/basic_model.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
elif MODE == 2:
    import tensorflow.keras as keras
    model = keras.models.load_model('../analyze/best_model_ever.h5')
elif MODE == 3:
    import tflite_runtime.interpreter as tflite
    interpreter = tflite.Interpreter('../analyze/contextual_model.tflite')
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

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

def handler(a,b):
    mc_r.set_duty_cycle(0)
    mc_l.set_duty_cycle(0)
    exit(1)

signal.signal(signal.SIGINT, handler)

se = SpeedEncoder(20,21,23,24)

if MODE == 0:
    pass
    # if os.path.exists("./write.csv"):
    #     os.remove("./write.csv") 
    # f = open("./write.csv", "a")
    # f.write("ts,duty_cycle,acc,speed_l,speed_r,speed_avg\n")

N = 30
# poll for sensor data
turn = 0
duty_cycle = 0
requested_speed = 0
# acc = -999

def infer():
    global duty_cycle
    old_time = time()
    speed = (0,0)

    if MODE == 2:
        LOOK_BACK = 5
        prev_state = [[0,0] for _ in range(LOOK_BACK)]

    while 1:
        # se.poll()

        #report sensor data N times per second
        curr_time = time()
        if curr_time - old_time > 1 / N:
            try:
                acc = Accelerometer.get()[1]
            except:
                pass
            if turn == 0 and acc != -999 and duty_cycle != 0:
                # print(f"hmm: {se.get_rot()} accel = {acc}, {turn}, {duty_cycle}")
                speed = se.get_rot()
                # print(speed)
                # f.write(f"{floor(time()*1000)},{duty_cycle},{acc},{speed[0]},{speed[1]},{(speed[0] + speed[1]) / 2}\n")
                # f.flush()
            old_time = curr_time
        
            if MODE == 1 or MODE == 2 or MODE == 3:
                if turn == 0 and acc != -999:
                    mc_l.set_dir(True)
                    mc_r.set_dir(True)
                    norm_acc = (acc + 4.02297436) / 8.75475849
                    norm_speed = (((speed[0] + speed[1]) / 2) - 4.73178413) / 538.80656938
                    norm_requested_speed = requested_speed
                    norm_duty_cycle = duty_cycle / 100

                    res = 0
                    if MODE == 1:
                        inp = np.array([[norm_acc,norm_requested_speed]], dtype='float32')
                        interpreter.set_tensor(input_details[0]['index'], inp)
                        interpreter.invoke()
                        res = interpreter.get_tensor(output_details[0]['index'])[0][0]
                    elif MODE == 2:
                        prev_state.pop(0)
                        prev_state.append([norm_acc, norm_requested_speed])
                        # print(f'req: {norm_requested_speed}')
                        inp = np.array([prev_state], dtype='float32')
                        # print(inp)
                        res = model.predict(inp)[0][0]
                        print(res * 100, norm_requested_speed * 100)
                    elif MODE == 3:
                        if norm_requested_speed > 0.01:
                            inp = np.array([[norm_acc,norm_speed,norm_requested_speed]], dtype='float32')
                            interpreter.set_tensor(input_details[0]['index'], inp)
                            interpreter.invoke()
                            res = interpreter.get_tensor(output_details[0]['index'])[0][0]
                        else:
                            res = 0

                    duty_cycle = res * 100
                    
                    print(f"{norm_acc},{norm_speed},{norm_requested_speed}={res} -- speed err:{abs(norm_requested_speed - norm_speed) * 100}")
                    mc_l.set_duty_cycle(duty_cycle)
                    mc_r.set_duty_cycle(duty_cycle)
                elif turn > 0:
                    mc_l.set_dir(True)
                    mc_l.set_duty_cycle(100)
                    mc_r.set_dir(False)
                    mc_r.set_duty_cycle(100)
                elif turn < 0:
                    mc_l.set_dir(False)
                    mc_l.set_duty_cycle(100)
                    mc_r.set_dir(True)
                    mc_r.set_duty_cycle(100)

            # print(requested_speed)

def speed_poller():
    while 1:
        se.poll()


infer_thread = Thread(target=infer, args=[])
infer_thread.start()
speed_polling_thread = Thread(target=speed_poller, args=[])
speed_polling_thread.start()


while 1:
    events = get_gamepad()
    for event in events:
        if event.code == "ABS_RZ":
            if MODE == 0:
                new_duty_cycle = round(event.state / 1023 * 100)
                # print(f"nds {new_duty_cycle}")
                duty_cycle = new_duty_cycle
            if MODE == 1 or MODE == 2 or MODE == 3:
                requested_speed = event.state / 1023
        elif event.code == "ABS_X":
            new_turn = event.state / 32768
            # print(se_l.get_rot())
            # print(f"LR: {new_turn}")
            turn = new_turn
    if MODE == 0:
        mc_l.set_duty_cycle(duty_cycle * max(0,min(1, (1 + turn))))
        mc_r.set_duty_cycle(duty_cycle * max(0,min(1, (1 - turn))))
