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
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
xyinverted: True
max_iter: 82
grad_freq: 0.5
gradient: Solankii-21.ggr
c_imag: -0.07871177943265353
c_real: 0.7446564780738132
i_step: 7.302023242507268e-05
julia: true
center_imag: 3.23742241261087
map_center_imag: 0.7442183566792628
map_center_real: -0.07871177943265353
map_radius: 0.0007302023242507269
r_step: 7.302023242507268e-05
radius: 5444.685880270128
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4500, None],
            [4000, self.ending],
            [3230, self.verse2],
            [1880, self.verse1],
            [1020, self.bass],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=10),
            "mid": AudioMod((46, 114), "max", decay=2),
            "hgh": AudioMod((12, 456), "avg"),
        }

    def ending(self, frame):
        if self.scene_init:
            self.center_mod = self.logspace(self.params["center_imag"] + 5,
                                            -2.242204444444445 + 5)
        self.params["center_imag"] = self.center_mod[self.scene_pos] - 5
        self.params["mod"] -= 1e-3 * self.low
        self.params["c_imag"] += 1e-4 * self.mid

    def verse2(self, frame):
        if self.scene_init:
            self.center_mod = self.logspace(self.params["center_imag"] + 1,
                                            0 + 1)
            self.rad_mod = self.logspace(self.params["radius"], 13.7374)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["center_imag"] = self.center_mod[self.scene_pos] - 1
        self.params["mod"] += 2e-3 * self.mid
        self.params["grad_freq"] += 3e-3 * self.low

    def verse1(self, frame):
        self.params["c_imag"] += 4e-5 * self.mid
        self.params["c_real"] -= 1e-4 * self.low
        self.params["grad_freq"] += 1e-3 * self.hgh

    def bass(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         8.536172377001316)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 1e-4 * self.low
        #self.params["c_real"] += 1e-4 * self.mid
#        self.params["c_real"] += 1e-4 * self.mid
#        self.params["c_real"] += 1e-4 * self.low
        self.params["grad_freq"] += 1e-3 * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 43)
        self.params["c_imag"] -= 5e-5 * self.mid
        self.params["c_real"] += 1e-4 * self.low
        self.params["grad_freq"] += 1e-3 * self.hgh
#        self.params["mod"] += 1e-4 * self.hgh


if __name__ == "__main__":
    run_main(Demo())
