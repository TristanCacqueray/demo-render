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
gradient: See_The_World.ugr:023
formula: |
  z = cdouble_mul(z, z);
  z = cdouble_add(z, c);
center_imag: -0.23190711123472404
center_real: -0.8628850479105111
grad_freq: 0.2
gradient: See_The_World.ugr:023
max_iter: 10000
radius: 7.740094426659362e-12
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [2700, None],
            [2300, self.finish],
            [0,    self.dezoom],
        ]
        super().__init__(yaml.load(p))

    def finish(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 2.0)
            self.mi_mod = self.linspace(self.params["max_iter"], 300)
            self.f_mod = self.linspace(self.params["grad_freq"], 13.3)
            self.r_mod = self.logspace(self.params["center_real"] + 4, 3.7)
            self.i_mod = self.logspace(self.params["center_imag"] + 4, 4)
        self.params["center_real"] = self.r_mod[self.scene_pos] - 4
        self.params["center_imag"] = self.i_mod[self.scene_pos] - 4
        self.params["max_iter"] = self.mi_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["grad_freq"] = self.f_mod[self.scene_pos]

    def dezoom(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 0.20)
            self.mi_mod = self.linspace(self.params["max_iter"], 3000)
        self.params["max_iter"] = self.mi_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["grad_freq"] += 5e-3 * self.low

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 6), "max", decay=5),
            "hgh": AudioMod((244, 895), "max", decay=30),
        }
        return


if __name__ == "__main__":
    run_main(Demo())
