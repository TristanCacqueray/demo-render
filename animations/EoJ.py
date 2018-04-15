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

import yaml

from utils.animation import Animation, run_main
from utils.audio import SpectroGram, AudioMod


p = """
c_imag: 0.34668012319133695
c_real: -0.41101714591988414
formula: |
  z2 = cdouble_mul(z, c);
  z2 = cdouble_addr(z2, 1);
  z2.real = fabs(z2.real);
  z2.imag = fabs(z2.imag);
  z = cdouble_rdivide(mod, z2);
  z = cdouble_add(z2, z);
kernel_params: "double mod"
kernel_params_mod:
  - mod
mod: 1
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
radius: 9.481943481529465
kernel: mean-distance
xyinverted: True
gradient: MySunrise.ggr
julia: True
max_iter: 256
radius: 847
center_real: -19
center_imag: 16
grad_freq: 0.65
"""

grad_mod = 6e-3


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [3000, None],
            [2790, self.ending],
            [320,  self.main],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.low_mod = AudioMod((0, 98), "max")
        self.mid_mod = AudioMod((100, 240), "max")
        self.hgh_mod = AudioMod((495, 560), "max")

    def updateAudio(self, audio_buf):
        self.spectre.transform(audio_buf)
        self.low = self.low_mod.update(self.spectre)
        self.mid = self.mid_mod.update(self.spectre)
        self.hgh = self.hgh_mod.update(self.spectre)

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 169)
            self.creal_mod = self.linspace(self.params["center_real"] + 40,
                                           0 + 40)
            self.cimag_mod = self.linspace(self.params["center_imag"] + 40,
                                           0 + 40)
        self.params["center_real"] = self.creal_mod[self.scene_pos] - 40
        self.params["center_imag"] = self.cimag_mod[self.scene_pos] - 40
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["mod"] -= 6e-4
        self.params["grad_freq"] += grad_mod / 6
#        self.params["c_real"] += 1e-4

    def main(self, frame):
        if self.scene_init:
            self.creal_mod = self.linspace(self.params["center_real"] + 40,
                                           17.276334090196123 + 40)
            self.cimag_mod = self.linspace(self.params["center_imag"] + 40,
                                           -2 + 40)
            self.rad_mod = self.logspace(self.params["radius"], 12)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["center_real"] = self.creal_mod[self.scene_pos] - 40
        self.params["center_imag"] = self.cimag_mod[self.scene_pos] - 40
        self.params["c_imag"] -= 1e-4 * self.low
        if frame > 720:
            self.params["mod"] -= 2e-4 * self.mid
        if frame > 2400:
            self.params["c_real"] += 1e-4 * self.mid
        self.params["grad_freq"] += grad_mod * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 7.42)
        self.params["radius"] = self.rad_mod[frame]
        self.params["c_imag"] -= 3e-4 * self.low
        self.params["grad_freq"] += grad_mod * self.hgh


if __name__ == "__main__":
    run_main(Demo())
