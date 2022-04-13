import RPi.GPIO as GPIO
from time import time
GPIO.setmode(GPIO.BCM)


class SpeedEncoder:
    def __init__(self, a_phase_port_l, b_phase_port_l, a_phase_port_r, b_phase_port_r):
        self.a_phase_port_l = a_phase_port_l
        self.b_phase_port_l = b_phase_port_l
        self.a_phase_port_r = a_phase_port_r
        self.b_phase_port_r = b_phase_port_r
        self.rot_a_l = 0
        self.rot_b_l = 0
        self.rot_a_r = 0
        self.rot_b_r = 0
        GPIO.setup(a_phase_port_l, GPIO.IN)
        GPIO.setup(b_phase_port_l, GPIO.IN)
        GPIO.setup(a_phase_port_r, GPIO.IN)
        GPIO.setup(b_phase_port_r, GPIO.IN)
        self.old_signal_a_l = -1
        self.old_time_a_l = -1

        self.old_signal_b_l = -1
        self.old_time_b_l = -1

        self.old_signal_a_r = -1
        self.old_time_a_r = -1

        self.old_signal_b_r = -1
        self.old_time_b_r = -1

    def poll(self):
        signal_a_l = GPIO.input(self.a_phase_port_l)
        signal_b_l = GPIO.input(self.b_phase_port_l)
        signal_a_r = GPIO.input(self.a_phase_port_r)
        signal_b_r = GPIO.input(self.b_phase_port_r)

        curr_time = time()
        if signal_a_l and signal_a_l != self.old_signal_a_l:
            diff = curr_time - self.old_time_a_l
            self.old_time_a_l = curr_time
            self.rot_a_l = 1 / diff

        if signal_b_l and signal_b_l != self.old_signal_b_l:
            diff = curr_time - self.old_time_b_l
            self.old_time_b_l = curr_time
            self.rot_b_l = 1 / diff

        self.old_signal_a_l = signal_a_l
        self.old_signal_b_l = signal_b_l

        if signal_a_r and signal_a_r != self.old_signal_a_r:
            diff = curr_time - self.old_time_a_r
            self.old_time_a_r = curr_time
            self.rot_a_r = 1 / diff

        if signal_b_r and signal_b_r != self.old_signal_b_r:
            diff = curr_time - self.old_time_b_r
            self.old_time_b_r = curr_time
            self.rot_b_r = 1 / diff

        self.old_signal_a_r = signal_a_r
        self.old_signal_b_r = signal_b_r

    def get_rot(self):
        return ((self.rot_a_l + self.rot_b_l) / 2, (self.rot_a_r + self.rot_b_r) / 2)
