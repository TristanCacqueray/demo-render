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

import os
import math
import numpy as np

from . common import MAX_SHORT, hsv, ComplexPlane, Path
import pygame
import pygame.draw
import pygame.image
from pygame.locals import KEYDOWN, K_ESCAPE

# for headless rendering
if "XAUTHORITY" not in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
if "AUDIO" not in os.environ and "PULSE_SERVER" not in os.environ:
    os.environ["SDL_AUDIODRIVER"] = "dummy"


# Pygame abstraction
class Screen:
    def __init__(self, screen_size):
        pygame.init()
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.screen = pygame.display.set_mode(screen_size)
        self.windows = []

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        text = self.font.render(msg, True, color)
        self.screen.blit(text, coord)

    def capture(self, dname, frame):
        if not os.path.isdir(dname):
            os.mkdir(dname)
        fname = "%s/%04d.png" % (dname, frame)
        try:
            pygame.image.save(self.screen, fname)
            print("Saved to %s" % fname)
        except Exception as e:
            print(fname, e)
            raise

    def add(self, window, coord=(0, 0)):
        self.windows.append((window, coord))

    def update(self):
        for window, coord in self.windows:
            if window.pixels is not None:
                pygame.surfarray.blit_array(window.surface, window.pixels)
            self.screen.blit(window.surface, coord)


class ScreenPart:
    def __init__(self, window_size, use_array=True):
        try:
            self.surface = pygame.Surface(window_size)
            self.window_size = list(map(int, window_size))
            self.length = self.window_size[0] * self.window_size[1]
            if use_array:
                self.pixels = np.zeros(self.length, dtype='i4').reshape(
                    *self.window_size)
            else:
                self.pixels = None
        except Exception:
            print("Invalid window_size", window_size)
            raise

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface, nparray.reshape(
            *self.window_size))


# Ready to use 'widget'
class WavGraph(ScreenPart):
    def __init__(self, window_size, frame_size):
        ScreenPart.__init__(self, window_size)
        self.frame_size = frame_size
        self.wav_step = self.frame_size // self.window_size[1]
        self.x_range = self.window_size[0] // 2

    def render(self, buf):
        # Wav graph
        pixels = np.zeros(self.length, dtype='i4').reshape(*self.window_size)
        for y in range(0, self.window_size[1]):
            mbuf = np.mean(buf[y * self.wav_step:(y + 1) * self.wav_step])
            x = int(self.x_range + self.x_range * mbuf / (MAX_SHORT / 2))
            pixels[x][y] = 0xf1
            continue
            mbuf = np.mean(buf[y * self.wav_step:(y + 1) * self.wav_step],
                           axis=1)
            left = mbuf[0]
            right = mbuf[1]
            mono = np.mean(mbuf)
            for point, offset, color in ((left, -10, 0xf10000),
                                         (right, +10, 0x00f100),
                                         (mono, 0, 0xf1)):
                pixels[int(self.x_range + offset + (
                    (self.x_range - abs(offset)) / 2.) * point /
                           (MAX_SHORT/2.))][y] = color
        self.pixels = pixels


class Graph(ScreenPart):
    def __init__(self, window_size):
        super().__init__(window_size, use_array=False)
        self.values = np.zeros(window_size[0])

    def render(self, value):
        self.surface.fill(0x0)
        self.values = np.roll(self.values, -1)
        self.values[-1] = value
        for x in range(self.window_size[0]):
            pygame.draw.line(
                self.surface, 0xfafafa,
                (x, self.window_size[1]),
                (x, self.window_size[1] - self.values[x] * self.window_size[1])
            )


class SpectroGraph(ScreenPart):
    def __init__(self, window_size, frame_size):
        super().__init__(window_size, use_array=False)
        self.frame_size = frame_size
        self.zoom = 1
        self.decay = 10
        self.length = self.frame_size // 2
        self.values = np.zeros(self.length)
        self.graph_length = min(self.window_size[0] - self.zoom, self.length)
        print("FFT length: %d" % self.length)

    def render(self, spectrogram):
        self.surface.fill(0x00000)
        for x in range(0, self.graph_length, self.zoom):
            freq_pos = x // self.zoom
            val = spectrogram.band[freq_pos]
            if self.values[freq_pos] > val:
                decay = (self.values[freq_pos] - val) / self.decay
                val = self.values[freq_pos] - decay
            self.values[freq_pos] = val
            for subx in range(self.zoom):
                pygame.draw.line(
                    self.surface, 0xfafafa,
                    (x + subx, self.window_size[1]),
                    (x + subx, self.window_size[1] - val * self.window_size[1])
                    )


class ColorMod(ScreenPart):
    def __init__(self, window_size, band, mode="max", base_hue=0.6):
        super().__init__(window_size, use_array=False)
        self.band = band
        self.mode = mode
        self.base_hue = base_hue
        self.decay = 20
        self.prev_val = 0
        self.values = np.zeros(self.window_size[0]) + self.window_size[1]

    def render(self, spectrogram):
        self.values = np.roll(self.values, -1)
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

        self.values[-1] = self.window_size[1] - self.window_size[1] * val
        self.prev_val = val
        self.surface.fill(hsv(self.base_hue + 0.3 * val, 0.8, 0.5 + 2 * val))
        for x in range(0, self.window_size[0] - 1):
            pygame.draw.line(self.surface, 0xfafafa,
                             (x, self.values[x]),
                             (x + 1, self.values[x+1]))


class Waterfall(ScreenPart):
    def __init__(self, window_size, frame_size, zoom=4):
        ScreenPart.__init__(self, window_size)
        self.frame_size = frame_size
        self.zoom = zoom

    def render(self, spectrogram):
        self.pixels = np.roll(self.pixels, -1, axis=0)
        for y in range(0, self.window_size[1], self.zoom):
            inv_y = self.window_size[1] - y - 1
            point = spectrogram.freq[y // self.zoom]
            for suby in range(self.zoom):
                self.pixels[-1][inv_y - suby] = hsv(
                    0.5 + 0.3 * point,
                    0.3 + 0.6 * point,
                    0.2 + 0.8 * point)


# Legacy abstraction
class Window:
    def __init__(self, window_size):
        self.surface = pygame.Surface(window_size)
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.window_size = window_size
        self.length = window_size[0] * window_size[1]
        self.pixels = None

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        text = self.font.render(msg, True, color)
        self.surface.blit(text, coord)

    def draw_line(self, start_coord, end_coord, color=(28, 28, 28)):
        pygame.draw.line(self.surface, color, start_coord, end_coord)

    def draw_point(self, coord, color=[242]*3):
        self.surface.set_at(coord, color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface,
                                    nparray.reshape(*self.window_size))


class Plane(ComplexPlane, Window):
    pass
