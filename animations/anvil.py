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
gradient: Teuns.ugr:Gayfish_Neon_Party
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
c_imag: -0.8004846834909829
c_real: -0.8922790836805631
max_iter: 68
grad_freq: 0.4
julia: true
mod: 0.38
radius: 200
r_step: 0.01
i_step: 0.01
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [5300, None],
            [4268, self.verse5],
            [3519, self.verse4],
            [2751, self.verse3],
            [2000, self.verse2],
            [1237, self.verse1],
            [1030, self.brk1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=10),
            "mid": AudioMod((152, 483), "max", decay=5),
            "hgh": AudioMod((12, 456), "avg"),
        }

    def verse5(self, frame):
        if self.scene_init:
            self.mod_mod = self.logspace(self.params["mod"], 2.638, 732)
            self.rad_mod = self.logspace(self.params["radius"], 57)
            self.r_mod = self.logspace(self.params["c_real"] + 10,
                                       0.2635375871984607 + 10)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        if frame < 5000:
#            self.params["mod"] = self.mod_mod[self.scene_pos]
        self.params["mod"] += 3e-4 * self.low
#        self.params["c_real"] = self.r_mod[self.scene_pos] - 10
        self.params["c_real"] -= 1e-3 * self.mid
        self.params["grad_freq"] -= 1e-3 * self.mid

    def verse4(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 15)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 1e-3 * self.low
        self.params["c_real"] -= 1e-3 * self.mid
        self.params["c_imag"] += 1e-3 * self.low
        self.params["grad_freq"] += 1e-3 * self.hgh

    def verse3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 7.9)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 1e-3 * self.low
        self.params["mod"] += 1e-3 * self.low
        self.params["grad_freq"] += 1e-3 * self.mid

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 5.21)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 1e-3 * self.low
        self.params["grad_freq"] += 1e-3 * self.mid

    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 31)
            self.c_mod = self.linspace(self.params["center_imag"] + 200,
                                       200)
        self.params["center_imag"] = self.c_mod[self.scene_pos] - 200
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 3e-4 * self.low
        self.params["c_real"] += 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.hgh

    def brk1(self, frame):
        self.params["mod"] += 1e-4 * self.low
        self.params["c_real"] -= 1e-3 * self.low
        self.params["c_imag"] -= 1e-4 * self.mid
        self.params["grad_freq"] += 1e-4 * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.params["center_imag"] = -58
            self.rad_mod = self.logspace(self.params["radius"], 20)
            self.c_mod = self.linspace(self.params["center_imag"] + 200,
                                       -3.3209154090540487 + 200)
        self.params["center_imag"] = self.c_mod[self.scene_pos] - 200
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["c_imag"] += 4e-5 * self.low
        self.params["c_real"] += 1e-3 * self.low #+ 2e-4 * self.hgh
        self.params["c_imag"] += 1e-4 * self.mid
        self.params["grad_freq"] += 1e-4 * self.hgh


if __name__ == "__main__":
    run_main(Demo())
