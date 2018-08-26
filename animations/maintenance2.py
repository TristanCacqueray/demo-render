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
from utils.midi import MidiMod


p = """
formula: |
  // log(log((ibas(z)^exp(ibas(z)))^m + c))
  z.imag = fabs(z.imag);
  z = cdouble_powr(z, mod);
  z = cdouble_add(z, c);
  z = cdouble_log(z);
  z = cdouble_log(z);
kernel_params: double mod
kernel_params_mod:
  - mod

mod: 2
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001

kernel: mean-distance
xyinverted: true
show_map: false
julia: true

radius: 697.96764975237

c_imag: -0.8681996302752029
c_real: 0.9954434638927422
mod: 2.408
radius: 96.09477454508452

max_iter: 42
gradient: See_The_World.ugr:023
grad_freq: 0.45
"""

grad_mul = 1e-4


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [3500, None],
            [2700, self.verse3],
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
            self.rad_mod = self.logspace(self.params["radius"],
                                         2)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.low + 1e-3 * self.mid
        self.params["mod"] -= 1e-4 * self.hgh

    def verse2(self, frame):
        if self.scene_init:
            self.base_real = self.params["c_real"]
            self.rad_mod = self.logspace(self.params["radius"], 14)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        if frame < 2300:
            self.params["c_real"] += 1e-3 * self.mid
            self.params["c_imag"] -= 1e-3 * self.mid
        else:
            self.params["c_real"] -= 2e-3 * self.mid
            self.params["c_imag"] += 5e-4 * self.mid
            self.params["mod"] += 5e-3 * self.low
        self.params["grad_freq"] += grad_mul * self.low

    def brk1(self, frame):
        if self.scene_init:
            self.m_mod = self.logspace(self.params["mod"],
                                       0.5)
            self.i_mod = self.logspace(self.params["c_imag"] + 10,
                                       -0.7860954594451277
                                       + 10)
            self.r_mod = self.logspace(self.params["c_real"] + 10,
                                       0.6993515791507731
                                       + 10)
            self.rad_mod = self.logspace(self.params["radius"],
                                         9.13005769553133)
            self.f_mod = self.logspace(self.params["grad_freq"],
                                       0.6)
        self.params["c_imag"] = self.i_mod[self.scene_pos] - 10
        self.params["c_real"] = self.r_mod[self.scene_pos] - 10
        self.params["mod"] = self.m_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["grad_freq"] = self.f_mod[self.scene_pos]

    def verse1(self, frame):
        if self.scene_init:
            self.base_imag = self.params["c_imag"]
            self.rad_mod = self.logspace(self.params["radius"],
                                         5)
        self.params["mod"] -= 2e-3 * self.low
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] = self.base_imag - 1e-2 * self.mid
        self.params["grad_freq"] += grad_mul * self.low

    def intro(self, frame):
        if self.scene_init:
            self.base_real = self.params["c_real"]
            self.rad_mod = self.logspace(1000, 11.89427058043356)
        self.params["c_imag"] += 2e-3 * self.low
        self.params["c_real"] = self.base_real - 1e-2 * self.mid
        self.base_real -= 2e-4 * self.low
        self.params["grad_freq"] += grad_mul * self.hgh
        self.params["radius"] = self.rad_mod[self.scene_pos]

    def todo(self, frame):
        self.paused = True


if __name__ == "__main__":
    run_main(Demo())
