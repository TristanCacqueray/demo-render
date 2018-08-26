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

import pygame


def clock():
    return pygame.time.Clock()


class Screen:
    def __init__(self, screen_size):
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        self.windows = []

    def capture(self, fname):
        if not fname.endswith(".png"):
            fname += ".png"
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
        self.font = None
        self.window_size = window_size
        self.length = window_size[0] * window_size[1]
        self.pixels = None
        self.draw = False

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        if self.font is None:
            self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        text = self.font.render(msg, True, color)
        self.surface.blit(text, coord)

    def draw_line(self, start_coord, end_coord, color=(28, 28, 28), width=1):
        pygame.draw.line(self.surface, color, start_coord, end_coord, width)

    def draw_circle(self, coord, size, color=(28, 28, 28)):
        pygame.draw.circle(self.surface, color, coord, size)

    def draw_point(self, coord, color=[242]*3, width=1):
        if width > 1:
            self.draw_circle(coord, width, color)
        else:
            self.surface.set_at(coord, color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(
            self.surface, nparray.reshape(*self.window_size))


class ComplexPlane:
    def set_view(self, center_real, center_imag, radius):
        # Plane dimensions
        self.plane_min = (center_real - radius,
                          center_imag - radius)
        self.plane_max = (center_real + radius,
                          center_imag + radius)
        # Coordinate conversion vector
        self.offset = (self.plane_min[0], self.plane_min[1])
        self.scale = (
            self.window_size[0] / float(self.plane_max[0] - self.plane_min[0]),
            self.window_size[1] / float(self.plane_max[1] - self.plane_min[1])
        )

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

    def included(self, complex_coord):
        return complex_coord.real >= self.plane_min[0] and \
               complex_coord.imag >= self.plane_min[1] and \
               complex_coord.real < self.plane_max[0] and \
               complex_coord.imag < self.plane_max[1]

    def draw_complex(self, complex_coord, color=[242]*3, width=1):
        if self.included(complex_coord):
            self.draw_point(
                self.convert_to_screen(complex_coord), color, width)

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


class Mixer:
    def __init__(self, frequency, channels, frame_size):
        pygame.mixer.pre_init(
            frequency=frequency,
            channels=channels,
            buffer=frame_size)
        pygame.mixer.init()
        self.chan = pygame.mixer.find_channel()

    def play(self, buf):
        self.chan.queue(pygame.sndarray.make_sound(buf))
