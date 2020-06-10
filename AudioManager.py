from scipy.io.wavfile import read
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import pyaudio

def print_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    print(info)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

def get_device_inds():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    all_ind = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0 \
        and f'USB PnP Sound Device' in p.get_device_info_by_host_api_device_index(0, i).get('name'):
            all_ind.append(i)
    return all_ind

def get_volume(wav_bytes):
    arr = _wav_2_arr(wav_bytes)
    background = get_background_noise(arr)
    abs_arr = np.absolute(arr)
    return (snr(abs_arr),len(arr))

def _wav_2_arr(wav_bytes):
    wav_bytes_IO = BytesIO(wav_bytes)
    a = read(wav_bytes_IO)
    arr = np.array(a[1],dtype=float)
    return arr


def get_background_noise(arr):
    return np.sqrt(np.mean(np.square(arr)))

def volume_score(arr):
    arr = np.absolute(arr)
    denom = np.mean(arr[arr<np.percentile(arr, 20)])
    if denom != 0:
        return np.mean(arr[arr>np.percentile(arr, 80)])/denom
    else:
        return 100000000

def snr(a): 
    a = np.asanyarray(a) 
    m = a.mean() 
    sd = a.std(axis = 0, ddof = 0) 
    return np.where(sd == 0, 0, m / sd) 


