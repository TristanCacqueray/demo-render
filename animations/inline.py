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
  // z=abs(1/z)*m+c
  z = cdouble_rdivide(1, z);
  z.real = fabs(z.real);
  z.imag = fabs(z.imag);
  z2 = cdouble_new(imod, mod);
  z = cdouble_mul(z, z2);
  z = cdouble_add(z, c);
julia: True
kernel: mean-distance
kernel_params: "double mod, double imod"
kernel_params_mod:
  - mod
  - imod
mod: 1
imod: 0
xyinverted: True
c_imag: -0.22359134026936126
c_real: -0.2950661414010185
grad_freq: 0.15
max_iter: 128
radius: 1.50 # 10.967254638671875
gradient: Solankii-21.ggr
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
  imod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [8000, None],
            [7650, self.ending],
            [5864, self.verse4],
            [5270, self.verse3],
            [4665, self.verse2],
            [4366, self.brk3],
            [3466, self.verse1],
            [2259, self.brk2],
            [1359, self.brk1],
            [758, self.bass1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 12), "max", decay=5),
            "mid": AudioMod((152, 483), "mean"),
        }

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 0
        self.midi_events = {
            "rhode": MidiMod("Combinator 1"),
            "perc": MidiMod(["Dr. Octo Rex 1", "Dr. Octo Rex 1 copy 2",
                             "Kong 1"],
                            mod="one-off"),
            "bass": MidiMod(["Combinator 2 copy", "Combinator 2 copy"],
                             mod="one-off", decay=30),
        }

    def ending(self, frame):
        self.params["imod"] -= 4e-2
        self.params["mod"] -= 1e-3
        self.params["grad_freq"] -= 1e-2

    def verse4(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 11)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["imod"] += 3e-2 * self.low
        self.params["mod"] -= 2e-3 * self.low
        self.params["c_imag"] -= 2e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.low + 5e-2 * self.mid

    def verse3(self, frame):
        self.params["mod"] += 2e-2 * self.low
        self.params["c_real"] += 4e-3 * self.mid
        self.params["grad_freq"] -= 6e-3 * self.low

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 6.60)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] += 2e-2 * self.bass
        self.params["c_real"] += 2e-3 * self.mid
        self.params["grad_freq"] += 6e-3 * self.low

    def brk3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 5)
            self.i_mod = self.logspace(self.params["imod"], 4.150005977979411)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["imod"] = self.i_mod[self.scene_pos] # 2e-2 * self.low
        self.params["mod"] += 2e-2 * self.mid
#        self.params["c_imag"] -= 5e-3 * self.low
        self.params["c_real"] += 1e-3 * self.mid
        self.params["grad_freq"] += 1e-3 * self.low


    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 2.10)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["imod"] += 1e-2 * self.mid
        self.params["mod"] -= 1e-3 * self.low
        self.params["grad_freq"] += 2e-3 * self.low
        self.params["c_imag"] += 3e-3 * self.mid
        self.params["c_real"] += 1e-4 * self.mid

    def brk2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 5.91)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.perc
        self.params["c_imag"] -= 2e-3 * self.rhode
        self.params["grad_freq"] -= 4e-4 * self.rhode
#        self.params["imod"] += 1e-2 * self.rhode

    def brk1(self, frame):
        if self.scene_init:
            self.real_mod = self.logspace(self.params["c_real"] + 2,
                                          0.24168538207709653 + 2)
            self.rad_mod = self.logspace(self.params["radius"], 2.28)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["c_real"] = self.real_mod[self.scene_pos] - 2
        self.params["c_imag"] += 1e-3 * self.rhode
        self.params["imod"] += 1e-4 * self.bass
        self.params["mod"] += 1e-3 * self.bass
        self.params["grad_freq"] -= 1e-4 * self.perc

    def bass1(self, frame):
        if self.scene_init:
            self.imag_mod = self.logspace(self.params["c_imag"] + 2,
                                          -0.33221083852945177 + 2)
            self.rad_mod = self.logspace(self.params["radius"], 11.6268)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["c_imag"] = self.imag_mod[self.scene_pos] - 2
        self.params["c_imag"] -= 2e-5 #* self.rhode
#        self.params["c_real"] -= 1e-4 * self.bass
        self.params["grad_freq"] += 1e-3 * self.bass + 7e-4
        self.params["imod"] += 3.6e-4 * self.bass #+ 0.1e-5
        self.params["mod"] += 1e-4 * self.bass

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 6.17)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 2e-3 * self.rhode
        self.params["c_imag"] -= 1e-3 * self.perc


if __name__ == "__main__":
    run_main(Demo())
