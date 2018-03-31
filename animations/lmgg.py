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
c_imag: -3.1000000000000014
c_real: -2.7755575615628914e-17
center_imag: 0.0
center_real: -1.5707963267948966
grad_freq: 42.0
map_center_imag: -2.3000000000000007
map_center_real: -2.7755575615628914e-17
max_iter: 730
radius: 1.56
show_map: false
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [2200, None],
            [1950, self.ending],
            [1140, self.verse2],
            [393,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.mid_mod = AudioMod((190, 220), "max")
        self.low_mod = AudioMod((4, 8), "mean", threshold=0.6)

    def updateAudio(self, audio_buf):
        self.spectre.transform(audio_buf)
        self.mid = self.mid_mod.update(self.spectre)
        self.low = self.low_mod.update(self.spectre)

    def ending(self, frame):
        self.params["grad_freq"] += 0.5
        self.params["c_real"] -= 0.1
        self.params["max_iter"] -= 1
        self.params["radius"] += 0.04

    def verse2(self, frame):
        self.params["c_imag"] += 0.1 * self.low
        self.params["c_real"] -= 0.2 * self.mid
        self.params["max_iter"] += 1 + 5 * self.low
        self.params["grad_freq"] -= 0.1 * self.mid

    def verse1(self, frame):
        self.params["c_real"] += 0.1 * self.low
        self.params["c_imag"] -= 0.2 * self.mid

    def intro(self, frame):
        self.params["c_imag"] -= 0.1 * self.mid
        self.params["c_real"] -= 0.1 * self.low


if __name__ == "__main__":
    run_main(Demo())
