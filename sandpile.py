#!/bin/env python
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

"""Sandpile fractal"""

import colorsys
import numpy as np
import scipy.signal
import pygame
import pygame.locals
import time

ZOOM = 4
WINSIZE = [500, 500]
INIT = 1000


###############################################################################
# Pygame abstraction
###############################################################################
def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


class Screen:
    def __init__(self, screen_size):
        pygame.init()
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.screen = pygame.display.set_mode(screen_size)
        self.windows = []

    def capture(self, fname):
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
        pygame.display.update()


class Window:
    def __init__(self, window_size):
        self.surface = pygame.Surface(window_size)
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.window_size = window_size
        self.length = window_size[0] * window_size[1]
        self.pixels = None
        self.draw = False

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface,
                                    nparray.reshape(*self.window_size))


###############################################################################
# Topple code
###############################################################################
class Sandpile(Window):
    def __init__(self, winsize, amount=100000):
        super().__init__(winsize)
        self.data_size = list(map(lambda x: x // ZOOM, winsize))
        self.data_length = self.data_size[0] * self.data_size[1]
        self.data = np.zeros(self.data_size, dtype=np.int32)
        self.data[tuple(np.array(self.data_size) // 2)] = amount
        self.kernel = np.array([
            [0,  1, 0],
            [1, -4, 1],
            [0,  1, 0]], dtype=np.int32)

        i = INIT
        while i > 0:
            toppling = self.data > 3
            c = scipy.signal.correlate2d(toppling, self.kernel, mode='same')
            self.data += c
            i -= 1

    def render(self):
        pixels = np.zeros(self.data_length, dtype='i4').reshape(
            *self.data_size)

        # Colorize pixels
        pixels[self.data == 0] = hsv(0.6, 1, 0.9)
        pixels[self.data == 1] = hsv(0.6, 0.9, 0.9)
        pixels[self.data == 2] = hsv(0.6, 0.6, 0.9)
        pixels[self.data == 3] = hsv(0.6, 0.4, 0.9)
        pixels[self.data > 3] = hsv(0.6, 0.1, 0.9)

        # Tupple sands
        toppling = self.data > 3
        c = scipy.signal.correlate2d(toppling, self.kernel, mode='same')
        self.data += c
        enlarge = np.repeat(np.repeat(pixels, ZOOM, axis=0), ZOOM, axis=1)
        self.blit(enlarge)


def main():
    screen = Screen(WINSIZE)
    clock = pygame.time.Clock()
    scene = Sandpile(WINSIZE)
    screen.add(scene)
    while True:
        scene.render()
        screen.update()
        pygame.display.update()
        for e in pygame.event.get():
            if e.type != pygame.locals.KEYDOWN:
                continue
            if e.key == pygame.locals.K_ESCAPE:
                exit(0)
            if e.key == pygame.locals.K_p:
                screen.capture("./%d.png" % time.time())
        clock.tick(25)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
