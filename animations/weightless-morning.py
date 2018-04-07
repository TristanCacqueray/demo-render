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
c_imag: -3
c_real: -0.6104166666666669
center_imag: -1.42 # 3.0464596218532987
grad_freq: 2
i_step: 0.3
julia: true
map_radius: 3.59375
r_step: 0.003
radius: 6.65 # 17.136335372924805
max_iter: 50
gradient: Sunrise.ggr
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [8116, None],
            [7529, self.zoomout],
            [6589, self.ending],
            [5647, self.verse5],
            [5176, self.verse4],
            [4706, self.reloc],
            [3764, self.tr1],
            [2823, self.verse3],
            [1882, self.verse2],
            [940,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 235
        self.midi_events = {
            "waldo": MidiMod("waldo A61", mod="one-off"), #, decay=2),
            "guitar": MidiMod("andy 084", mod="one-off"),
            "bell": MidiMod("vti twinkle", mod="one-off"),
            "violon": MidiMod("vti violon", mod="one-off"),
            "tb": MidiMod("tracebackbass"),
            "kick": MidiMod(["kick", 'Copy of kick'], mod="one-off"),
            "bass": MidiMod(" andy  low 084", mod="one-off"),
        }

    def zoomout(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 160)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.bell
        self.params["mod"] -= 1e-4 * self.bell

    def ending(self, frame):
        self.params["c_real"] += 1e-4 * self.bell
        self.params["c_imag"] -= 1e-3 * self.bass
#        self.params["grad_freq"] -= 5e-3 * self.guitar
        self.params["mod"] -= 8e-5 * self.bell
#        self.params["radius"] += self.params["radius"] / 100 * self.bass
        self.params["grad_freq"] -= 1e-2 * self.bass


    def verse5(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(
                self.params["radius"], 9.26971435546875)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["c_real"] -= 2e-4 * self.waldo
#        self.params["c_imag"] += 2e-4 * self.bell
#        self.params["mod"] -= 4e-4 * self.bass
        self.params["c_real"] -= 1e-4 * self.bell
        self.params["c_imag"] += 1e-3 * self.bass
#        self.params["grad_freq"] -= 5e-3 * self.guitar
        self.params["mod"] -= 1e-4 * self.waldo
#        self.params["radius"] += self.params["radius"] / 100 * self.bass
        self.params["grad_freq"] += 1e-3 * self.bass

    def verse4(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 149)
#        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] += 2e-4 * self.waldo
        self.params["c_imag"] -= 2e-4 * self.bell
        self.params["mod"] += 4e-4 * self.bass
        self.params["grad_freq"] -= 1e-2 * self.waldo

    def reloc(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 16)
            self.center_mod = self.linspace(self.params["center_imag"], -1.36)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["center_imag"] = self.center_mod[self.scene_pos]
        self.params["c_real"] += 2e-4 * self.bell
        self.params["c_imag"] += 1e-3 * self.kick
#        self.params["mod"] -= 1e-4 * self.bell
        self.params["grad_freq"] += 2e-2 * self.kick

    def tr1(self, frame):
        self.params["c_imag"] += 5e-4 * self.waldo
        self.params["mod"] += 5e-5 * self.bell
#        self.params["radius"] -= self.params["radius"] / 80 * self.kick
        self.params["grad_freq"] -= 5e-3 * self.kick

    def verse3(self, frame):
        self.params["c_imag"] -= 8e-4 * self.kick
        self.params["c_real"] += 2e-4 * self.guitar
        #self.params["radius"] -= self.params["radius"] / 100 * self.bell
        #self.params["mod"] += 1e-5 * self.bell
        self.params["grad_freq"] += 1e-3 * self.bass

    def verse2(self, frame):
        self.params["c_imag"] += 8e-4 * self.kick
        self.params["c_real"] -= 3e-4 * self.guitar
        self.params["radius"] += self.params["radius"] / 300 * self.waldo
        self.params["grad_freq"] -= 1e-3 * self.bass

    def verse1(self, frame):
        self.params["c_imag"] += 1e-4 * self.waldo
        self.params["c_real"] -= 1e-4 * self.bell
        self.params["grad_freq"] += 4e-3 * self.violon
        self.params["mod"] += 1e-5 * self.tb

    def intro(self, frame):
        self.params["c_imag"] += 1e-4 * self.waldo
        self.params["c_real"] -= 1e-4 * self.bell
        self.params["grad_freq"] += 4e-3 * self.violon


if __name__ == "__main__":
    run_main(Demo())
