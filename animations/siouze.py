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
  z = cdouble_powr(z, mod);
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
c_real: 0.5128172976017
c_imag: -0.2046
center_imag: 1.109 # 3.7872537137634277
grad_freq: 0.55
max_iter: 56
radius: 21.3033021399192
julia: true
radius: 15
gradient: Pastels.ggr
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4700, None],
            [4200, self.ending],
            [3120, self.verse3],
            [2100, self.verse2],
            [1480, self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=10),
            "mid": AudioMod((98, 478), "max", decay=5),
            "hgh": AudioMod((12, 456), "avg"),
        }

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 6)
            self.center_mod = self.linspace(self.params["center_imag"],
                                            1.43) #-17.551221567139567)
        self.params["center_imag"] = self.center_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 3e-4 * self.low + 4e-4 * self.mid

    def verse3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 8.42)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] -= self.params["mod"] / 5200 * self.low
        self.params["c_real"] -= 1e-4 * self.mid
        self.params["grad_freq"] -= 4.5e-4 * self.hgh

    def verse2(self, frame):
        if self.scene_init:
            self.center_mod = self.logspace(self.params["center_imag"], 0.43)
            self.rad_mod = self.logspace(self.params["radius"], 13)
        self.params["center_imag"] = self.center_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["mod"] += 1e-4 * self.low
#        self.params["c_imag"] -= 3e-3 * self.mid
#        self.params["grad_freq"] += 1e-3 * self.hgh
#        return
        self.params["mod"] += 1e-4 * self.low
        self.params["c_real"] += 0.8e-4 * self.mid
        self.params["c_imag"] += 0.7e-4 * self.low
        self.params["grad_freq"] += 6e-4 * self.hgh
        #self.params["grad_freq"] -= self.params["grad_freq"] / 40 * self.hgh

    def verse1(self, frame):
        if self.scene_init:
            self.center_mod = self.logspace(
                self.params["center_imag"], 3.775666666666666)
        self.params["center_imag"] = self.center_mod[self.scene_pos]
        self.params["mod"] += 1e-4 * self.low
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["grad_freq"] -= self.params["grad_freq"] / 40 * self.hgh

    def intro(self, frame):
        self.params["c_real"] += 2e-4 * self.low
        self.params["c_imag"] += 2e-4 * self.mid
        self.params["grad_freq"] += 1e-4 * self.hgh

if __name__ == "__main__":
    run_main(Demo())
