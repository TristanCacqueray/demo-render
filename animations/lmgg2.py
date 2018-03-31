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

"""
Inspired from Paul Bourke's thorn fractal:
http://paulbourke.net/fractals/thorn/
"""

import cmath
import math
import yaml

from utils.animation import Animation, run_main
from utils.audio import SpectroGram, AudioMod


p = """
formula: |
  z2.real = z.real;
  z2.imag = z.imag;
  z.real = z2.real / cos(z2.imag) + c.real;
  z.imag = z2.imag / sin(z2.real) + c.imag;
julia: True
c_real: 0.662
c_imag: 2.086
center_imag: 0.0
center_real: -1.5769255934890847
# radius: 4.5969500206410885
radius: 1.45
grad_freq: 42.0
map_center_imag: -2.3000000000000007
map_center_real: -2.7755575615628914e-17
max_iter: 730
show_map: false
#gradient: AG_firecode.ggr
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [5600, None],
            [4350, self.ending],
            [2550, self.main],
            [2025, self.tr],
            [1125, self.low_change],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.hgh_mod = AudioMod((150, audio.audio_frame_size // 2), "avg")
        self.mid_mod = AudioMod((151, 530), "max", threshold=0.4)
        self.low_mod = AudioMod((4, 10), "mean")

    def updateAudio(self, audio_buf):
        self.spectre.transform(audio_buf)
        self.hgh = self.hgh_mod.update(self.spectre)
        self.mid = self.mid_mod.update(self.spectre)
        self.low = self.low_mod.update(self.spectre)

        self.params["grad_freq"] -= 0.002

#        self.params["grad_freq"] = max(23, 32 - 100 * self.hgh)
#        self.params["max_iter"] = 600 + 1000 * self.hgh

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 1.59)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 0.5 * self.mid
        self.params["c_real"] += 0.1 * self.low

    def main(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 7.17)
            self.center_c = self.get_c()
            self.angle = 0
            self.radius = 2
            self.idir = 1

        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.angle = self.angle + 4 * self.low
        self.center_c += 0.25j * self.mid * self.idir
        if self.center_c.imag > 10:
            self.idir = -1
        if self.center_c.imag < -10:
            self.idir = 1
        self.radius = 2 * 10 * self.hgh
        m = cmath.rect(self.radius, math.radians(self.angle))
        new_c = self.center_c + m
        self.set_c(new_c)

    def tr(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 4.59)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 0.2 * self.mid
        self.params["c_imag"] -= 0.3 * self.low

    def low_change(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 4.59 * 2)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 0.2 * self.mid
        self.params["c_imag"] -= 0.3 * self.low
        ...

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 4.59)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 0.5 * self.mid
        self.params["c_real"] += 0.1 * self.low


if __name__ == "__main__":
    run_main(Demo())
