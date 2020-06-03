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

class TurnTable:

    def __init__(self,device_inds):
        self.recognizer = sr.Recognizer()
        self.snoopers = [Snooper(ind,self.recognizer) for ind in device_inds]
        self.should_turn = False
        self.talk_frames = -1

    def _response_callback(self,talk_length):
        self.should_turn = True
        print(talk_length)
        self.talk_frames = talk_length
    
    def turn(self):
        for snooper in self.snoopers:
            print(f'snooper {snooper.mic_num}: {snooper.get_volume(num_frames=self.talk_frames)}')
        self.talk_frames = -1
        time.sleep(1)
        self.should_turn = False
        print('am turning')
        #TODO figure out how to manage turning lmao
    
    def record(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for snooper in self.snoopers:
                executor.submit(snooper.record,self._response_callback)
            self.listen()
        # self.snoopers[0].record(self._response_callback)
        print('why not continue')
    
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
    tt = TurnTable(inds)
    tt.record()
