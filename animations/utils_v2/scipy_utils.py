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

import subprocess
import numpy as np
import pygame
import os
try:
    import scipy.io.wavfile
    use_scipy = True
except ImportError:
    use_scipy = False


# scipyio abstraction
class NoAudio:
    audio_frame_size = 1

    def get(self, _):
        return [(0, 0)]


class Audio:
    def __init__(self, wav_file, fps=25, play=True):
        freq, wav = scipy.io.wavfile.read(wav_file)
        if freq % fps != 0:
            raise RuntimeError("Can't load wav %d Hz at %d fps" % (freq, fps))
        self.audio_frame_size = freq // fps
        self.audio_frame_number = int(len(wav) / freq * fps)
        self.audio_frames_path = np.linspace(
            0, len(wav), int(len(wav) / freq * fps), endpoint=False, dtype=int)
        if play:
            pygame.mixer.pre_init(
                frequency=freq,
                channels=len(wav[0]),
                buffer=self.audio_frame_size)
            pygame.mixer.init()
            self.chan = pygame.mixer.find_channel()
        self.wav = wav
        self.play = play

    def get(self, frame):
        buf = self.wav[self.audio_frames_path[frame]:
                       self.audio_frames_path[frame] + self.audio_frame_size]
        if self.play:
            self.chan.queue(pygame.sndarray.make_sound(buf))
        return buf


class AudioBand:
    def __init__(self, band, mode, decay=20):
        self.band = band
        self.mode = mode
        self.decay = decay
        self.attack = 10
        self.prev_val = 0

    def update(self, spectrogram):
        band = spectrogram.band[self.band[0]:self.band[1]]
        if (band == 0).all():
            val = 0
        elif self.mode == "avg":
            val = np.sum(band) / len(band)
        elif self.mode == "max":
            val = np.argmax(band) / len(band)
        elif self.mode == "mean":
            val = np.mean(band)
        if self.prev_val > val:
            decay = (self.prev_val - val) / self.decay
            val = self.prev_val - decay
#        if self.prev_val < val:
#            decay = (val - self.prev_val) / self.attack
#            val = self.prev_val + decay
        self.prev_val = val # - self.prev_val
        return val


# Fft abstraction (frame based short fft)
class SpectroGram:
    def __init__(self, frame_size):
        self.frame_size = frame_size
        overlap_fac = 0.5
        self.hop_size = np.int32(np.floor(self.frame_size * (1 - overlap_fac)))
        self.fft_window = np.hanning(self.frame_size)
        self.inner_pad = np.zeros(self.frame_size)

    def transform(self, buf):
        mono = np.mean(buf, axis=1)

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


# IIR filter abstraction
class Filter:
    def __init__(self, bpass, bstop, ftype='butter'):
        import scipy.signal.filter_design as fd
        import scipy.signal.signaltools as st
        self.b, self.a = fd.iirdesign(bpass, bstop, 1, 100, ftype=ftype,
                                      output='ba')
        self.ic = st.lfiltic(self.b, self.a, (0.0,))

    def filter(self, data):
        import scipy.signal.signaltools as st
        res = st.lfilter(self.b, self.a, data, zi=self.ic)
        self.ic = res[-1]
        return res[0]


class AudioMod:
    def __init__(self, filename, frames, filter_type, fadein=6, fadeout=10.0):
        self.frames = frames
        self.mod = np.zeros(frames)
        self.cache_filename = "%s.%d.mod" % (filename, filter_type)
        if not os.path.isfile(self.cache_filename):
            if filter_type == 1:
                self.fp = Filter(0.01, 0.1, ftype='ellip')
            elif filter_type == 2:
                self.fp = Filter((0.1, 0.2),  (0.05, 0.25), ftype='ellip')
            elif filter_type == 3:
                self.fp = Filter((0.4, 0.9),  (0.05, 0.25), ftype='ellip')
            else:
                self.fp = None
            if not os.path.isfile(filename):
                print("Could not load %s" % filename)
                return
            wave_values = self.load_wave(filename)
            open(self.cache_filename, "w").write("\n".join(
                map(str, wave_values))+"\n")
        else:
            wave_values = list(map(float,
                                   open(self.cache_filename).readlines()))
        imp = 0.0
        for i in range(0, self.frames):
            if wave_values[i] >= imp:
                delta = (wave_values[i] - imp) / fadein
                imp += delta
#                imp = wave_values[i]
            else:
                delta = (imp - wave_values[i]) / fadeout
                imp -= delta
            self.mod[i] = imp

    def load_wave(self, filename):
        import wave
        wav = wave.open(filename, "r")
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            print("Only support mono 16bit encoding...")
            exit(1)

        # Read all frames
        buf = wav.readframes(wav.getnframes())

        # Convert to float array [-1; 1]
        w = np.fromstring(buf, np.int16) / float((2 ** (2 * 8)) / 2)

        step = wav.getnframes() // self.frames + 1
        wave_values = []
        for i in range(0, wav.getnframes(), step):
            wf = w[i:i+step]
            if self.fp:
                wf = self.fp.filter(wf)

            v = np.max(np.abs(wf))
            wave_values.append(float(v))
        return wave_values

    def plot(self):
        p = subprocess.Popen(['gnuplot'], stdin=subprocess.PIPE)
        open("/tmp/plot", "w").write("\n".join(
            map(lambda x: str(self.get(x)), range(0, self.frames))))
        p.stdin.write(b"plot '/tmp/plot' with lines\n")
        p.wait()

    def get(self, frame):
        return self.mod[frame]
