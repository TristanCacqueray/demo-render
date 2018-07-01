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
#gradient: See_The_World.ugr:023
gradient: sunrise

formula: |
  modulus = cdouble_abs_squared(z);
  z.real = fabs(z.real);
  z.imag = fabs(z.imag);
  z = cdouble_divider(z, modulus);
  z = cdouble_mulr(z, -1.9231);
  z = cdouble_add(z, c);
  z = cdouble_log(z);

c_real: 1.83071
c_imag: 1.63084

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

c_imag: 0.8186175943765636
c_real: 1.6151902268959706
i_step: 0.00971408128738402
julia: true
map_center_imag: 0.8695008773104799
map_center_real: 1.6079046659304324
map_radius: 0.0971408128738402
max_iter: 72
r_step: 0.00971408128738402
radius: 12.94


c_imag: 0.9546147323999402
grad_freq: 0.15

grad_freq: 1
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [2100, None],
            [1700, self.ending],
            [1150, self.verse2],
            [785,  self.verse1],
            [653,  self.zoom],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         10)
            self.mod_mod = self.linspace(1, 10)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 1e-4 * self.mid * self.mod_mod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.low * self.mod_mod[self.scene_pos]
        self.params["grad_freq"] -= 1e-2 * self.hgh

    def verse2(self, frame):
        self.params["c_imag"] += 1e-4 * self.mid
        self.params["c_real"] -= 1e-4 * self.low
        self.params["grad_freq"] += 1e-2 * self.hgh

    def verse1(self, frame):
        self.params["c_real"] -= 1e-5 * self.low
        self.params["grad_freq"] += 1e-2 * self.hgh


    def zoom(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         0.0003084615395356189)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 1e-4 * self.low
        self.params["grad_freq"] += 1e-2 * self.hgh

    def intro(self, frame):
        self.params["c_real"] -= 1e-4 * self.low
        self.params["grad_freq"] += 1e-2 * self.hgh

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "hgh": AudioMod((575, 878), "mean", decay=5),
            "mid": AudioMod((162, 335), "max", decay=8),
            "low": AudioMod((1, 17), "mean", decay=10,
                            threshold=0.5)
        }
        return


if __name__ == "__main__":
    run_main(Demo())
