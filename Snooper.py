import pyaudio
import math
import collections
import audioop
import matplotlib.pyplot as plt
from AudioManager import _wav_2_arr, volume_score
import io
import wave  
import itertools
import speech_recognition as sr


class Snooper:

    def __init__(self,mic_num,recognizer):
        self.recognizer = recognizer
        self.mic_num = mic_num
        self.chunk = 8192
        self.buffer_len = 2 * self.chunk
        self.sample_rate = 44100
        self.sample_width = 2
        self.energy_threshold = 300  # minimum audio energy to consider for recording
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
        self.operation_timeout = None  # seconds after an internal operation (e.g., an API request) starts before it times out, or ``None`` for no timeout
        self.phrase_threshold = 0.3  # minimum seconds of speaking audio before we consider the speaking audio a phrase - values below this are ignored (for filtering out clicks and pops)
        self.non_speaking_duration = 3  # seconds of non-speaking audio to keep on both sides of the recording
        self.seconds_per_buffer = float(self.chunk) / self.sample_rate
        self.pause_buffer_count = int(math.ceil(self.pause_threshold / self.seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        self.phrase_buffer_count = int(math.ceil(self.phrase_threshold / self.seconds_per_buffer))  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
        self.non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / self.seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase
        self.frames = collections.deque()
        self.vol = 0



    def get_wav_data(self, num_frames=None, convert_rate=None, convert_width=None):
            """
            Returns a byte string representing the contents of a WAV file containing the audio represented by the ``AudioData`` instance.
            If ``convert_width`` is specified and the audio samples are not ``convert_width`` bytes each, the resulting audio is converted to match.
            If ``convert_rate`` is specified and the audio sample rate is not ``convert_rate`` Hz, the resulting audio is resampled to match.
            Writing these bytes directly to a file results in a valid `WAV file <https://en.wikipedia.org/wiki/WAV>`__.
            """
            if not num_frames:
                raw_data = b''.join(self.frames)
            else:
                raw_data = b''.join(itertools.islice(self.frames, len(self.frames)-num_frames, len(self.frames)))
            # sample_rate = 44100 if convert_rate is None else convert_rate
            # sample_width = 2 if convert_width is None else convert_width

            # generate the WAV file contents
            with io.BytesIO() as wav_file:
                wav_writer = wave.open(wav_file, "wb")
                try:  # note that we can't use context manager, since that was only added in Python 3.4
                    wav_writer.setframerate(self.sample_rate)
                    wav_writer.setsampwidth(self.sample_width)
                    wav_writer.setnchannels(1)
                    wav_writer.writeframes(raw_data)
                    wav_data = wav_file.getvalue()
                finally:  # make sure resources are cleaned up
                    wav_writer.close()
            return wav_data

    def set_volume(self):
        self.vol = volume_score(_wav_2_arr(self.get_wav_data()))
    
    def get_volume(self, num_frames=None):
        return volume_score(_wav_2_arr(self.get_wav_data(num_frames=num_frames)))

    def recognize(self, audiofile):
        response = {
            'transcribed':'',
            'error': False,
            'success': False
        }
        print('trying to recognize')
        try:
            response['transcribed'] = self.recognizer.recognize_google(audiofile)
            print('recognized')
            response['success'] = True
        except sr.UnknownValueError:
            response['error'] = 'No Intelligible speech'
        except sr.RequestError:
            response['error'] = 'API unavailable'

        return response

    def record(self,callback):
        print('listening')
        # read audio input for phrases until there is a phrase that is long enough
        buffer = b''  # an empty buffer means that the stream has ended and there is no data left to read

        stream = pyaudio.PyAudio().open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=self.mic_num,
            frames_per_buffer=1024,
        )
        phrase_time_limit = None
        while True:
            # store audio input until the phrase starts
            while True:
                # handle waiting too long for phrase by raising an exception
                buffer = stream.read(self.chunk,exception_on_overflow = False)
                if len(buffer) == 0: break  # reached end of the stream
                self.frames.append(buffer)
                if len(self.frames) > self.non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
                    self.frames.popleft()

                # detect whether speaking has started on audio input
                energy = audioop.rms(buffer, self.sample_width)  # energy of the audio signal
                if energy > self.energy_threshold: break
                energy_threshold = self.energy_threshold
                # dynamically adjust the energy threshold using asymmetric weighted average
                if self.dynamic_energy_threshold:
                    damping = self.dynamic_energy_adjustment_damping ** self.seconds_per_buffer  # account for different chunk sizes and rates
                    target_energy = energy * self.dynamic_energy_ratio
                    energy_threshold = self.energy_threshold * damping + target_energy * (1 - damping)
                # print(f'snooper {self.mic_num}: {self.get_volume()}')

            pause_count, phrase_count = 0, 0
            print('starting phrase')
            while True:
                # handle phrase being too long by cutting off the audio

                buffer = stream.read(self.chunk,exception_on_overflow = False)
                if len(buffer) == 0: break  # reached end of the stream
                self.frames.append(buffer)
                phrase_count += 1

                # check if speaking has stopped for longer than the pause threshold on the audio input
                energy = audioop.rms(buffer, self.sample_width)  # unit energy of the audio signal within the buffer
                if energy > energy_threshold:
                    pause_count = 0
                else:
                    pause_count += 1
                if pause_count > self.pause_buffer_count:  # end of the phrase
                    break
            print('finished phrase')

            # check how long the detected phrase is, and retry listening if the phrase is too short
            phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
            # if phrase_count >= self.phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening
            callback(phrase_count+pause_count)
            wav = io.BytesIO(self.get_wav_data(num_frames=(phrase_count+pause_count)))
            talk = sr.AudioFile(wav)
            with talk as source:
                aud_data = self.recognizer.record(source)
                res = self.recognize(aud_data)
                if res['success']:
                    print(f'snooper {self.mic_num} heard: {res["transcribed"]}')
                else:
                    print(f'snooper {self.mic_num} had error: {res["error"]}')
            for i in range(phrase_count+pause_count):
                self.frames.pop()  # remove extra non-speaking frames at the end
            callback(len(self.frames))
    
if __name__ == "__main__":
    snooper = Snooper(3)
    snooper.record()