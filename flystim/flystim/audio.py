import sys
import pyaudio
from time import sleep, time
import numpy as np

from flyrpc.transceiver import MySocketServer
from flyrpc.util import get_kwargs


def sine_song(sr, volume=1.0, duration=1.0, freq=225.0):
    t = np.linspace(0, duration, round(duration * sr))
    samples = volume * np.sin(2 * np.pi * freq * t)
    return np.floor(samples*2**15).astype(np.int16)


def pulse_song(sr, volume=1.0, duration=1.0, freq=125.0, pcycle=0.016, ncycle=0.020):
    cycles = round(duration/(pcycle + ncycle))

    sigm = pcycle / 4
    K = 0.5 * sigm ** 2

    seg = (pcycle + ncycle) * sr
    seg = int(seg)
    t = np.linspace(0, (seg - 1) / sr, seg)
    t = t - np.mean(t)
    y = np.exp(-t ** 2 / K) * np.cos(2 * np.pi * freq * t)

    samples = np.zeros(seg * cycles)
    for i in range(cycles):
        samples[seg * i:seg * (i + 1)] = y
    samples = np.delete(samples, slice(0, int(seg / 4)))
    samples = volume * samples
    return np.floor(samples * 2 ** 15).astype(np.int16)


class AudioPlay:

    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.speaker = pyaudio.PyAudio()
        self.soundTrack = None
        self.stream = None

    def __del__(self):
        self.speaker.terminate()

    def load_stim(self, name, **kwargs):
        stim = getattr(sys.modules[__name__], name)
        kwargs['sr'] = self.sr
        self.soundTrack = stim(**kwargs)
        self.stream = self.speaker.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=self.sr,
                                        output=True)



    def start_stim(self):
        print('command executed to speaker at %s' % time())
        if (self.soundTrack is not None) and (len(self.soundTrack) > 0):
            self.stream.write(self.soundTrack, num_frames=len(self.soundTrack))

    def stop_stim(self):
        self.soundTrack = None
        self.stream.stop_stream()
        self.stream.close()


def main():
    # get the configuration parameters
    kwargs = get_kwargs()

    # launch the server
    server = MySocketServer(host=kwargs['host'], port=kwargs['port'], threaded=True, auto_stop=True, name='speaker')

    # launch application
    audio = AudioPlay(sample_rate=44100)

    # register functions
    server.register_function(audio.load_stim)
    server.register_function(audio.start_stim)
    server.register_function(audio.stop_stim)

    while True:
        server.process_queue()


if __name__ == '__main__':
    main()
