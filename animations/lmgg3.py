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
gradient: Sunrise.ggr
center_real: 9.42477796076938
center_imag: 0.0
c_imag: 4.75000000000001
c_real: 10.983999999999996
grad_freq: 50.0
max_iter: 832
radius: 3
show_map: false
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [1500, None],
            [1263, self.ending],
            [0,    self.main],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.hgh_mod = AudioMod((400, audio.audio_frame_size // 2), "max")
        self.mid_mod = AudioMod((134, 365), "avg")
        self.low_mod = AudioMod((4, 16), "mean")

    def updateAudio(self, audio_buf):
        self.spectre.transform(audio_buf)
        self.hgh = self.mid_mod.update(self.spectre)
        self.mid = self.mid_mod.update(self.spectre)
        self.low = self.low_mod.update(self.spectre)

    def ending(self, frame):
        self.params["grad_freq"] -= 0.01
        self.params["max_iter"] += 0.5
        self.params["c_real"] -= 0.1
        self.params["c_imag"] -= 0.1
        self.params["radius"] += 0.04

    def main(self, frame):
        if self.scene_init:
            self.center_c = self.get_c()
            self.angle = 0
            self.radius = 1
            self.params["radius"] = 0.1
            self.base_freq = self.params["grad_freq"]

        self.params["grad_freq"] = self.base_freq + 100 * self.mid
        self.params["radius"] += 0.001
        self.angle = self.angle + 8 * self.hgh
        self.radius = 6 * self.low
        m = cmath.rect(self.radius, math.radians(self.angle))
        new_c = self.center_c + m
        self.set_c(new_c)


if __name__ == "__main__":
    run_main(Demo())
