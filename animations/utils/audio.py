# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import queue

import sounddevice as sd
import soundfile as sf
import numpy as np
import scipy.signal.filter_design as fd
import scipy.signal.signaltools as st


class AudioPlayer:
    def __init__(self, samplerate, blocksize, channels):
        self.queue = queue.Queue(maxsize=25)
        self.stream = sd.RawOutputStream(
            samplerate=samplerate, blocksize=blocksize,
            device="default", channels=channels, dtype='int16',
            latency='low',
            callback=self.callback, finished_callback=self.finished)

    def play(self, buf):
        self.queue.put(buf)
        if not self.stream.active:
            self.stream.start()

    def callback(self, outdata, frames, time, status):
        if status.output_underflow:
            print("Underflow...")
        try:
            data = self.queue.get_nowait().tobytes()
        except queue.Empty:
            # TODO: display this message when scene is not paused
            #       or stop the stream when scene is paused
            #print('Buffer is empty: increase buffersize?')
            data = b''
        if len(data) < len(outdata):
            data += b'\x00' * (len(outdata) - len(data))
        outdata[:] = data

    def finished(self):
        print("Over...")


class AudioInput:
    def __init__(self, fps, freq):
        self.queue = queue.Queue(maxsize=25)
        self.stream = sd.InputStream(
            device="default", channels=1, dtype='int16',
            samplerate=freq, blocksize=freq // fps,
            callback=self.callback)

    def callback(self, indata, frames, time, status):
        if status:
            print("Input status:", status)
        self.queue.put(indata)

    def read(self):
        if not self.stream.active:
            self.stream.start()
        while self.queue.qsize() > 1:
            print("Audio input dropping...")
            self.queue.get()
        return self.queue.get()


class Audio:
    def __init__(self, audio_file=None, fps=25, play=True):
        if not audio_file:
            play = False
            freq = 44100
            channels = 1
            self.input = AudioInput(fps, freq)
            self.wav = []
        else:
            ifile = sf.SoundFile(audio_file)
            freq = ifile.samplerate
            channels = ifile.channels
            self.input = None
            self.wav = ifile.read(-1, dtype='int16')
        self.play = play
        if freq % fps != 0:
            raise RuntimeError("Can't load %d Hz at %d fps" % (freq, fps))
        self.blocksize = freq // fps
        self.audio_frame_number = int(len(self.wav) / freq * fps)
        self.audio_frames_path = np.linspace(
            0, len(self.wav), int(len(self.wav) / freq * fps),
            endpoint=False, dtype=int)
        if play:
            self.player = AudioPlayer(freq, self.blocksize, channels)
        else:
            self.player = None

    def get(self, frame):
        if self.input:
            buf = self.input.read()
        else:
            try:
                buf = self.wav[
                    self.audio_frames_path[frame]:
                    self.audio_frames_path[frame] + self.blocksize]
            except IndexError:
                buf = None
        if self.player and self.play and buf is not None:
            self.player.play(buf)
        return buf


class NoAudio:
    blocksize = 1

    def get(self, _):
        return [(0, 0)]


class Filter:
    def __init__(self, bpass, bstop, ftype='butter'):
        self.b, self.a = fd.iirdesign(bpass, bstop, 1, 100, ftype=ftype,
                                      output='ba')
        self.ic = st.lfiltic(self.b, self.a, (0.0,))

    def filter(self, data):
        res = st.lfilter(self.b, self.a, data, zi=self.ic)
        self.ic = res[-1]
        return res[0]


class SpectroGram:
    def __init__(self, frame_size):
        self.frame_size = frame_size
        self.fft_window = np.hanning(self.frame_size)
        self.inner_pad = np.zeros(self.frame_size)

    def transform(self, buf):
        mono = np.mean(buf, axis=1)
        # Pre-Emphasis to amplify high freq
        #mono = np.append(mono[0], mono[1:] - 0.5 * mono[:-1])
        windowed = self.fft_window * mono
        padded = np.append(windowed, self.inner_pad)
        spectrum = np.fft.fft(padded) / self.frame_size
        autopower = np.abs(spectrum * np.conj(spectrum)).real
        if (mono == 0).all():
            self.freq = autopower[:self.frame_size//2]
        else:
            dbres = 20 * np.log10(autopower[:self.frame_size//2])
            clipres = np.clip(dbres, -40, 200) * 1 / (8 * 16)
            self.freq = clipres + 0.3125
        self.band = np.copy(self.freq)
        # Clean noise
        self.band[self.band < 0.5] = 0.5
        self.band = np.log10(self.band + 0.5) * 3


class AudioMod:
    def __init__(self, band, mode, decay=20, attack=10, threshold=0):
        self.band = band
        self.band_length = self.band[1] - self.band[0]
        self.mode = mode
        self.decay = decay
        self.attack = attack
        self.threshold = threshold
        self.prev_val = 0

    def update(self, spectrogram):
        band = spectrogram.band[self.band[0]:self.band[1]]
        if (band == 0).all():
            val = 0
        elif self.mode == "high":
            high_val = np.where(band > self.threshold)
            if np.any(high_val):
                high_val = high_val[-1]
                if np.any(high_val):
                    val = high_val[-1] / self.band_length
                else:
                    val = 0
            else:
                val = 0
        elif self.mode == "avg":
            val = np.sum(band) / len(band)
        elif self.mode == "max":
            val = np.max(band)
        elif self.mode == "mean":
            val = np.mean(band)
        if val < self.threshold:
            val = 0
        if self.prev_val > val:
            decay = (self.prev_val - val) / self.decay
            val = self.prev_val - decay
        self.prev_val = val
        return val
