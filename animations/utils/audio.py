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

import numpy as np
import pygame.mixer
import pygame.sndarray
import scipy.io.wavfile
import scipy.signal.filter_design as fd
import scipy.signal.signaltools as st


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


class NoAudio:
    audio_frame_size = 1

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
