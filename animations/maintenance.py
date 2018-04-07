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
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
c_imag: -0.7678836263313208
c_real: 0.49745210709906457
grad_freq: 5
julia: true
max_iter: 90
mod: 2.304
radius: 28.93659509744101
gradient: purples
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [3500, None],
            [2700, self.verse3],
            [2300, self.brk2],
            [1700, self.verse2],
            [1300, self.brk1],
            [500, self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=5),
            "mid": AudioMod((79, 160), "mean"),
            "hgh": AudioMod((250, 418), "max"),
        }

    def verse3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 73, 200)
        if frame > 3300:
            self.params["radius"] = self.rad_mod[frame - 3300]
        self.params["mod"] += 1e-4 * self.hgh
        self.params["c_real"] -= 3e-3 * self.mid
        self.params["c_imag"] += 3e-3 * self.low
        self.params["grad_freq"] -= 5e-3 * self.low

    def brk2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 17)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 4e-4 * self.hgh
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["c_real"] -= 1e-3 * self.low
        self.params["grad_freq"] -= 1e-3 * self.low

    def verse2(self, frame):
        self.params["c_real"] -= 2.8e-3 * self.low
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["grad_freq"] += 1e-2 * self.hgh
        self.params["radius"] += self.params["radius"] / 100 * self.low

    def brk1(self, frame):
        self.params["mod"] += 8e-4 * self.hgh
        self.params["c_real"] += 1e-3 * self.low
        self.params["grad_freq"] += 1e-3 * self.mid

    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 80)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 2.8e-3 * self.low
        self.params["c_imag"] -= 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 1000)
#        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 1e-2 * self.low
        self.params["c_real"] -= 1e-3 * self.hgh
        self.params["grad_freq"] += 2e-3 * self.mid


if __name__ == "__main__":
    run_main(Demo())
