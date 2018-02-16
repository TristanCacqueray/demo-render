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
    def __init__(self, window_size, band, mode="max", base_hue=0.6,
                 decay=20, threshold=0.4):
        super().__init__(window_size, use_array=False)
        self.band = band
        self.band_length = self.band[1] - self.band[0]
        self.mode = mode
        self.base_hue = base_hue
        self.decay = decay
        self.prev_val = 0
        self.values = np.zeros(self.window_size[0]) + self.window_size[1]
        self.threshold = threshold

    def get(self, spectrogram):
        band = spectrogram.band[self.band[0]:self.band[1]]
        if self.mode == "high":
            high_val = np.where(band > self.threshold)
            if np.any(high_val):
                high_val = high_val[-1]
                if np.any(high_val):
                    val = high_val[-1] / self.band_length
                else:
                    val = 0
            else:
                val = 0 #self.prev_val
        elif (band == 0).all():
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
        self.prev_val = val
        return val

    def render(self, spectrogram):
        self.values = np.roll(self.values, -1)
        val = self.get(spectrogram)
        self.values[-1] = self.window_size[1] - self.window_size[1] * val
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
        self.redraw = False

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


import tkinter
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_a, K_e, K_z, K_s, K_q, K_d, K_r, K_p
from pygame.locals import K_w, K_x, K_c, K_v, K_t, K_g, K_y, K_h
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP
import time

class Controller:
    def __init__(self, scene=None, args=None):
        self.root = tkinter.Tk()
        self.width = 600
        self.scene = scene
        self.args = args
        self.params = []
        self.add_float("Real")
        self.add_float("Imag")
        self.add_int("Iter", 1, 10000, self.args.max_iter)
        self.add_int("Grad", 1, 100, self.args.gradient_frequency, 0.1)
        self.add_int("Mod", 0, 10, 1, 0.001)
        self.root.update()
        self.param_clic(None)

    def _get_row(self):
        row = 0
        for param in self.params:
            if param[0] == "float":
                row += 3
            else:
                row += 1
        return row

    def add_int(self, name, from_, to, default=1, resolution=1):
        r = self._get_row()

        param_int = tkinter.Scale(self.root,
                                  from_=from_, to=to, resolution=resolution,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        param_int.set(default)
        tkinter.Label(self.root, text=name).grid(row=r, column=0)
        param_int.grid(row=r, column=1)
        param_int.bind("<ButtonRelease-1>", self.param_clic)
        self.params.append(["int", name, (param_int, )])
        self.__dict__[name] = default

    def add_float(self, name):
        r = self._get_row()

        param_int = tkinter.Scale(self.root,
                                  from_=0, to=42, resolution=1,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        param_int.set(1)
        tkinter.Label(self.root, text='%s int' % name).grid(row=r, column=0)
        param_int.grid(row=r, column=1)
        param_int.bind("<ButtonRelease-1>", self.param_clic)

        param_flt = tkinter.Scale(self.root,
                                  from_=0, to=1000, resolution=1,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text='%s flt' % name).grid(row=r+1, column=0)
        param_flt.grid(row=r+1, column=1)
        param_flt.bind("<ButtonRelease-1>", self.param_clic)

        param_exp = tkinter.Scale(self.root,
                                  from_=-15, to=15, resolution=1,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        param_exp.set(-1)
        tkinter.Label(self.root, text='%s exp' % name).grid(row=r+2, column=0)
        param_exp.grid(row=r+2, column=1)
        param_exp.bind("<ButtonRelease-1>", self.param_clic)

        self.params.append(["float", name, (param_int, param_flt, param_exp)])
        self.__dict__[name] = 0.0

    def param_apply(self):
        self.scene.max_iter = self.Iter
        self.args.gradient_frequency = self.Grad
        self.args.mod = self.Mod
        self.scene.redraw = True

    def param_clic(self, ev):
        for t, n, v in self.params:
            if t == "float":
                val = float("%d.%de%d" % (v[0].get(), v[1].get(), v[2].get()))
                self.__dict__[n] = val
            if t == "int":
                self.__dict__[n] = v[0].get()
        self.param_apply()

    def update(self):
        self.root.update()

    def pygame_event(self, e):
        redraw = False
        if e.type not in (KEYDOWN, MOUSEBUTTONDOWN):
            return
        if e.type == MOUSEBUTTONDOWN:
            plane_coord = self.scene.convert_to_plane(e.pos)
            if e.button in (1, 3):
                if e.button == 1:
                    step = 3/4.0
                else:
                    step = 4/3.0
                self.scene.set_view(center=plane_coord,
                                    radius=self.scene.radius * step)
                return True
            print("Clicked", e.pos, plane_coord)
            return
        if e.key == K_ESCAPE:
            exit(0)
        if e.key == K_p:
            self.screen.capture("./", time.time())
            return False
        redraw = True
        if e.key in (K_a, K_e):
            if e.key == K_e:
                step = 3/4.0
            elif e.key == K_a:
                step = 4/3.0
            self.scene.set_view(radius=self.scene.radius * step)
        elif e.key in (K_z, K_s, K_q, K_d):
            fact = 20
            if e.key == K_z:
                step = complex(0, self.Imag)
            elif e.key == K_s:
                step = complex(0, -1 * self.Imag)
            elif e.key == K_q:
                step = -1 * self.Real
            elif e.key == K_d:
                step = self.Real
            self.scene.c += step
        elif e.key in (K_LEFT, K_RIGHT, K_DOWN, K_UP):
            if e.key == K_LEFT:
                step = -10/self.scene.scale[0]
            elif e.key == K_RIGHT:
                step = +10/self.scene.scale[0]
            elif e.key == K_DOWN:
                step = complex(0, -10/self.scene.scale[1])
            elif e.key == K_UP:
                step = complex(0,  10/self.scene.scale[1])
            self.scene.set_view(center=self.scene.center + step)
        elif e.key == K_r:
            self.scene.set_view(center=self.args.center, radius=self.args.radius)
        else:
            redraw = False
        return redraw
