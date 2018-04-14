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
gradient: render_data/Solankii Gradients for Gimp/Gradient-#21.ggr
c_imag: -0.13422671142194348
c_real: 0.298544669649099
i_step: 0.012438114469344182
julia: true
map_center_imag: 0.298544669649099
map_center_real: -0.1217885969525993
map_radius: 0.12438114469344182
r_step: 0.012438114469344182
radius: 51.16156978094776
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4000, None],
            [3500, self.ending],
            [3286, self.zoom],
            [2526, self.verse4],
            [2025, self.verse3],
            [1770, self.verse2],
            [1520, self.tr1],
            [754, self.verse1],
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

    def ending(self, frame):
        self.params["c_imag"] -= 4e-5 * self.low + 1e-4 * self.mid + 1e-5
        self.params["grad_freq"] += 2e-1 * self.hgh

    def zoom(self, frame):
        if self.scene_init:
            self.imag_mod = self.logspace(self.params["c_imag"],
                                          0.9187686207968877)
            self.rad_mod = self.logspace(self.params["radius"], 0.03)
            self.freq_mod = self.logspace(self.params["grad_freq"], 0.20)
        self.params["grad_freq"] = self.freq_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        if frame < 3400:
            self.params["c_imag"] = self.imag_mod[self.scene_pos]
        else:
            self.params["c_imag"] -= 4e-5 * self.low + 1e-4 * self.mid

    def verse4(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 3606)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 5e-6 * self.low
        self.params["c_real"] -= 5e-6 * self.mid

    def verse3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 556)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 8e-5 * self.mid
        self.params["c_real"] -= 1e-5 * self.low
        self.params["grad_freq"] += 1e-2 * self.hgh

    def verse2(self, frame):
        if self.scene_init:
            self.base_real = self.params["c_real"]

        self.params["c_imag"] -= 8e-5 * self.low
        self.params["grad_freq"] += 1e-2 * self.mid
#        self.params["c_real"] += 1e-4 * self.mid
#        self.params["c_real"] += 1e-4 * self.mid

    def tr1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 129)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["grad_freq"] -= 1e-2 * self.low
        self.params["c_imag"] += 1e-4 * self.mid

    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.linspace(self.params["radius"], 0.1)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 4e-5 * self.low
        self.params["c_real"] += 1e-4 * self.mid
        self.params["grad_freq"] += 2e-2 * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.base_real = self.params["c_real"]
            self.rad_mod = self.linspace(self.params["radius"], 0.08)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 4e-5 * self.low
        self.params["c_real"] = self.base_real + 2e-4 * self.hgh
        self.params["grad_freq"] += 3e-3 * self.mid


if __name__ == "__main__":
    run_main(Demo())
