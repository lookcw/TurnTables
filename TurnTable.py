import random
import time
import speech_recognition as sr
import numpy as np
from AudioManager import get_volume, print_devices, get_device_inds
import threading
from Snooper import Snooper
import concurrent.futures
import argparse
import pyaudio
from StepperController import StepperController

class TurnTable:

    def __init__(self,device_inds):
        self.recognizer = sr.Recognizer()
        self.snoopers = []
        self.should_turn = False
        self.talk_frames = -1
        self.vol_0 = 0
        self.vol_1 = 0
        self.vol_2 = 0
        self.step_controller = None
        self.device_inds = device_inds

    def connect(self):
        self.snoopers = [Snooper(ind,self.recognizer) for ind in self.device_inds]
        self.step_controller = StepperController()


    def _response_callback(self,talk_length):
        print('called back')
        self.should_turn = True
        self.talk_frames = talk_length
    
    def turn(self):
        print('turning')
        vols = [snooper.get_volume(num_frames=self.talk_frames) for snooper in self.snoopers]
        for (i,snooper) in enumerate(self.snoopers):
            print(f'snooper: {snooper.mic_num} has vol: {vols[i]}')
        print('getting volumes')
        print('after get volume')
        source_angle = self.step_controller.get_source_angle(vols[0],vols[1],vols[2])
        print(f'turning towards {source_angle}')
        self.step_controller.goto_angle(source_angle)
        self.should_turn = False
    
    def record(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for snooper in self.snoopers:
                print('why')
                executor.submit(snooper.record,self._response_callback)
            self.listen()
    
    def listen(self):
        while True:
            if self.should_turn:
                self.turn()
            time.sleep(.1)





parser = argparse.ArgumentParser(description='Alright Google...')
parser.add_argument("-p", "--dont_print", action="count",
                    help="increase output verbosity")
args = parser.parse_args()

print_devices()
if not args.dont_print:
    inds = get_device_inds()
    assert len(inds) == 3
    tt = TurnTable(inds)
    tt.connect()
    tt.record()
