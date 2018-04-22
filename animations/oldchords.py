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
max_iter: 69
kernel: mean-distance
kernel_params: "double mod"
kernel_params_mod:
  - mod
mod: 1
xyinverted: True
gradient: MySunrise.ggr # Teuns.ugr:Gayfish_Neon_Party
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001


c_imag: 0.026247891847576282
c_imag: 0.048
c_real: -0.725818194069517
formula:
  // z = sin(log(z - z / iabs(tan(c * c)))) ** mod + c
  z = cdouble_sin(cdouble_log(cdouble_sub(z,
    cdouble_divide(z, cdouble_iabs(cdouble_tan(
      cdouble_mul(c, c)))))));
  z = cdouble_powr(z, mod);
  z = cdouble_add(z, c);
grad_freq: 1.05
i_step: 0.02223376759502571
julia: true
map_center_imag: -0.5257142857142856
map_center_real: 0.026247891847576282
map_radius: 0.2223376759502571
max_iter: 69
r_step: 0.02223376759502571
radius: 1648850.1280220877
show_map: false
center_imag: -6095394.964582769
center_real: -678929.0893288688
"""

grad_mod = 1e-3


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4000, None],
            [3320, self.ending],
            [2314, self.verse2],
            [1315, self.verse1],
            [1256, self.tr],
            [750, self.verse0],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 35), "mean", decay=5),
            "mid": AudioMod((152, 483), "max", decay=5),
            "hgh": AudioMod((495, 560), "max"),
        }

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 16092193376)
            self.fx_mod = self.logspace(1, 0.5)
            self.mod_mod = self.linspace(self.params["mod"], 1.0)
        self.params["mod"] = self.mod_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 1e-3 * self.low
        self.params["c_imag"] += 1e-4 * self.fx_mod[self.scene_pos]
        self.params["grad_freq"] -= 1e-3 * self.fx_mod[self.scene_pos]

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 185530358)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 4e-4 * self.low * 0.9
        self.params["c_real"] += 1e-3 * self.mid * 0.9
#        self.params["grad_freq"] -= grad_mod * self.hgh / 10

    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 35102735824)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 1e-3 * self.mid
        self.params["mod"] += 5e-4 * self.mid
        self.params["c_real"] += 1e-3 * self.low
        self.params["grad_freq"] += grad_mod * self.hgh

    def tr(self, frame):
        if self.scene_init:
            self.mod_mod = self.linspace(self.params["mod"], 0.975)
        self.params["mod"] = self.mod_mod[self.scene_pos]
        self.params["grad_freq"] += grad_mod * self.hgh

    def verse0(self, frame):
        self.params["c_real"] += 4e-4 * self.low
        self.params["c_imag"] += 1e-4 * self.mid
        self.params["grad_freq"] += grad_mod * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 9923655735)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 4e-4 * self.low
        self.params["grad_freq"] += grad_mod * self.hgh * 10


if __name__ == "__main__":
    run_main(Demo())
