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
formula: |
  z.imag = fabs(z.imag);
  z = cdouble_powr(z, mod);
  z = cdouble_add(z, c);
  z = cdouble_log(z);
kernel: mean-distance
kernel_params: "double mod"
kernel_params_mod:
  - mod
mod: 1
xyinverted: True
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
c_imag: -20.527517052500553
c_real: -42.74699796797575
grad_freq: 1.10
i_step: 0.8
julia: true
map_center_imag: -35.72795499922575
map_center_real: -21.404897423594303
map_radius: 8.773803710937491
max_iter: 72
mod: 3.007
r_step: 0.8
radius: 52.295945351943374
gradient: AG_zebra.ggr
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [1700, None],
            [1400, self.ending],
            [820,  self.main],
            [320,  self.pitched],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.low_mod = AudioMod((15, 100), "avg", decay=5)
        self.mid_mod = AudioMod((0, 240), "avg")
        self.hgh_mod = AudioMod((250, 418), "max")

    def updateAudio(self, audio_buf):
        self.spectre.transform(audio_buf)
        self.low = self.low_mod.update(self.spectre)
        self.mid = self.mid_mod.update(self.spectre)
        self.hgh = self.hgh_mod.update(self.spectre)

    def ending(self, frame):
        if self.scene_init:
            self.log_mod = self.logspace(1, 0.1)
        self.params["radius"] -= self.params["radius"] / 23 * \
            self.log_mod[self.scene_pos]
        self.params["c_imag"] += 0.05 * self.log_mod[self.scene_pos]

    def main(self, frame):
        self.params["c_real"] -= 1e-2 * self.hgh
        self.params["c_imag"] -= 1e-1 * self.mid
        self.params["grad_freq"] += 1e-3 * self.low
        self.params["radius"] += self.params["radius"] / 20 * self.mid

    def pitched(self, frame):
        self.params["c_imag"] -= 5e-2 * self.hgh
        self.params["radius"] += self.params["radius"] / 20 * self.mid
        self.params["grad_freq"] += 1e-3 * self.low

    def intro(self, frame):
        self.params["c_imag"] -= 1e-1 * self.hgh
        self.params["c_real"] += 1e-2 * self.mid
        self.params["grad_freq"] += 1e-3 * self.low


if __name__ == "__main__":
    run_main(Demo())
