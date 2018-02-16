#!/usr/bin/env python
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

"""
The lyapunov exponent of population growth using markus function to
change the rate based on a binary seed, see
https://en.wikipedia.org/wiki/Lyapunov_fractal.
"""

import colorsys
import sys
import time
import math
import numpy as np
import multiprocessing
import pygame
import pygame.locals
import signal
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN
from pygame.locals import K_ESCAPE, K_UP, K_DOWN, K_LEFT, K_RIGHT
from pygame.locals import K_a, K_e, K_p, K_r


SEED = "AB"
WINSIZE = [100, 100]
CENTER = 2+2j
RADIUS = 2
WORKERS = 8


###############################################################################
# Multiprocessed code
###############################################################################
def compute_markus_lyapunov(param):
    window_size, offset, scale, sampling, seed, x0, max_iter, max_init, \
        step_size, chunk = param

    results = np.zeros(step_size, dtype='i4')
    pos = 0

    while pos < step_size:
        step_pos = pos + chunk * step_size
        screen_coord = (step_pos / window_size[1], step_pos % window_size[1])
        c = np.complex128(complex(
            screen_coord[0] / scale[0] + offset[0],
            ((window_size[1] - screen_coord[1]) / scale[1] + offset[1])
        ))
        markus_func = lambda x: c.real if seed[idx % len(seed)] == "A" \
                      else c.imag

        # Init
        x = np.float128(x0)
        try:
            for idx in range(0, max_init):
                r = markus_func(idx)
                with np.errstate(over='raise'):
                    x = r * x * (1 - x)
        except FloatingPointError:
            pass

        # Exponent
        total = np.float64(0)
        try:
            for idx in range(0, max_iter):
                r = markus_func(idx)
                with np.errstate(over='raise'):
                    x = r * x * (1 - x)
                v = abs(r - 2 * r * x)
                if v == 0:
                    break
                total = total + math.log(v) / math.log(1.23)
        except FloatingPointError:
            pass

        if total == 0 or total == float('Inf'):
            exponent = 0
        else:
            exponent = total / float(max_iter)
        results[pos] = exponent
        pos += sampling
    return results


###############################################################################
# Pygame abstraction
###############################################################################
def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def color_factory(size, base_hue=0.65):
    def color_scale(x):
        if x < 0:
            v = abs(x) / size
            hue = base_hue - .4 * v
            sat = 0.6 + 0.4 * v
        else:
            hue = base_hue
            sat = 0.6
        return hsv(hue, sat, 0.7)
    return color_scale


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


class ComplexPlane:
    def set_view(self, center=None, radius=None):
        if center is not None:
            self.center = center
        if radius is not None:
            if radius == 0:
                raise RuntimeError("Radius can't be null")
            self.radius = radius
        self.plane_min = (self.center.real - self.radius,
                          self.center.imag - self.radius)
        self.plane_max = (self.center.real + self.radius,
                          self.center.imag + self.radius)
        # Coordinate conversion vector
        self.offset = (self.plane_min[0], self.plane_min[1])
        self.scale = (
            self.window_size[0] / float(self.plane_max[0] - self.plane_min[0]),
            self.window_size[1] / float(self.plane_max[1] - self.plane_min[1])
        )

    def compute_chunks(self, method, params):
        params = [self.window_size, self.offset, self.scale,
                  1] + params + [self.length]
        if WORKERS >= 2:
            # Divide image length by number of worker
            params[-1] //= WORKERS
            # Append chunk position
            params = list(map(lambda x: params + [x], range(WORKERS)))
            # Compute
            res = self.pool.map(method, params)
            # Return flatten array
            return np.array(res).flatten()
        # Mono process just compute first chunk
        return method(params + [0])

    def convert_to_plane(self, screen_coord):
        return complex(
            screen_coord[0] / self.scale[0] + self.offset[0],
            screen_coord[1] / self.scale[1] + self.offset[1]
        )

    def convert_to_screen(self, plane_coord):
        return [
            int((plane_coord.real - self.offset[0]) * self.scale[0]),
            int((plane_coord.imag - self.offset[1]) * self.scale[1])
        ]

    def draw_complex(self, complex_coord, color=[242]*3):
        self.draw_point(self.convert_to_screen(complex_coord), color)

    def draw_axis(self, axis_color=(28, 28, 28)):
        center_coord = self.convert_to_screen(0j)
        self.draw_line(
            (center_coord[0], 0),
            (center_coord[0], self.window_size[1]),
            color=axis_color)
        self.draw_line(
            (0, center_coord[1]),
            (self.window_size[0], center_coord[1]),
            color=axis_color)


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


###############################################################################
# Main
###############################################################################
class MarkusLyapunov(Window, ComplexPlane):
    def __init__(self):
        Window.__init__(self, WINSIZE)
        self.pool = multiprocessing.Pool(
            WORKERS, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
        self.seed = SEED
        self.x0 = 0.5
        self.max_iter = 100
        self.max_init = 50
        self.set_view(CENTER, RADIUS)
        self.color_vector = np.vectorize(color_factory(22.))

    def render(self, frame):
        start_time = time.time()

        nparray = self.compute_chunks(compute_markus_lyapunov, [
            self.seed, self.x0, self.max_iter, self.max_init])

        self.blit(self.color_vector(nparray))
        print("%04d: %.2f sec: ./markus_lyapunov.py --seed '%s' --center '%s' "
              "--radius '%s'" % (frame, time.time() - start_time, self.seed,
                                 self.center, self.radius))


def main():
    if len(sys.argv) <= 3:
        print("Markus-Lyapunov explorer\n"
              "========================\n"
              "\n"
              "Click the window to center\n"
              "Use keyboard arrow to move window, 'a'/'e' to zoom in/out, "
              "'r' to reset view\n")

    screen = Screen(WINSIZE)
    clock = pygame.time.Clock()
    scene = MarkusLyapunov()
    screen.add(scene)
    frame = 0
    redraw = True
    while True:
        if redraw:
            frame += 1
            scene.render(frame)
            screen.update()
            pygame.display.update()
            redraw = False

        for e in pygame.event.get():
            if e.type == MOUSEBUTTONDOWN:
                plane_coord = scene.convert_to_plane(e.pos)
                if e.button in (1, 3):
                    if e.button == 1:
                        step = 3/4.0
                    else:
                        step = 4/3.0
                    scene.set_view(center=plane_coord,
                                   radius=scene.radius * step)
                    redraw = True
                else:
                    print("Clicked", e.pos)
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    exit(0)
                elif e.key == K_p:
                    screen.capture("./%d.png" % (time.time()))
                redraw = True
                if e.key in (K_a, K_e):
                    if e.key == K_a:
                        step = 1/4.0
                    elif e.key == K_e:
                        step = 4/1.0
                    scene.set_view(radius=scene.radius * step)
                elif e.key in (K_LEFT, K_RIGHT,
                               K_DOWN, K_UP):
                    if e.key == K_LEFT:
                        step = -10/scene.scale[0]
                    elif e.key == K_RIGHT:
                        step = +10/scene.scale[0]
                    elif e.key == K_DOWN:
                        step = complex(0, -10/scene.scale[1])
                    elif e.key == K_UP:
                        step = complex(0,  10/scene.scale[1])
                    scene.set_view(center=scene.center + step)
                elif e.key == K_r:
                    scene.set_view(center=2+2j, radius=2.)
                else:
                    redraw = False
                    continue
        clock.tick(25)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
