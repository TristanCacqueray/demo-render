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
xyinverted: True
mod: 1
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
max_iter: 96
c_imag: -0.11963864334579546
c_real: 0.6080486111111111
center_imag: 1.7136335372924805
grad_freq: 1.15
julia: true
radius: 9.639188647270203
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [1400, None],
            [960, self.verse3],
            [480, self.verse2],
            [0, self.verse1],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=10),
            "mid": AudioMod((98, 478), "max", decay=5),
            "hgh": AudioMod((0, 456), "avg"),
        }

    def verse3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 24)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.low
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.hgh

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 100)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 1e-4 * self.low
        self.params["c_imag"] += 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.hgh
#        self.params["mod"] -= 1e-3 * self.hgh

    def verse1(self, frame):
        self.params["c_real"] += 1e-4 * self.low
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.hgh


if __name__ == "__main__":
    run_main(Demo())
