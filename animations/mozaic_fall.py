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
from utils.midi import MidiMod


p = """
formula: |
  z.imag = fabs(z.imag);
  z.real = fabs(z.real);
  z = cdouble_powr(z, mod);
  z = cdouble_add(z, c);
  z = cdouble_mul(cdouble_log(z), c);

kernel: mean-distance
kernel_params: "double mod"
kernel_params_mod:
  - mod
xyinverted: True
julia: True
escape_distance: 5
mod: 1
mods:
  pre_iter:
    type: int
    sliders: true
    min: 0
    max: 1000
    resolution: 1
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
show_map: false
c_imag: 1.7086588800495475
#c_real: -3.86415012640109
c_real: -3.92415012640109
grad_freq: 0.8
gradient: sunrise
i_step: 0.06
map_center_imag: -3.7276999310885905
map_center_real: 1.7086588800495475
map_radius: 0.682250976562497
max_iter: 90
pre_iter: 88
r_step: 0.06
radius: 4.918377122018591e+24
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [3000, None],
            [2751, self.zoom_out],
            [2001, self.sub],
            [1500, self.verse3],
            [1253, self.verse2],
            [503,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def zoom_out(self, frame):
        if self.scene_init:
            self.m_mod = self.logspace(self.params["mod"],
                                       0.989)
            self.rad_mod = self.logspace(self.params["radius"],
                                         101021144950.87495)
            self.r_mod = self.logspace(self.params["c_real"] + 10,
                                       -4.018242228001911 + 10)
            self.i_mod = self.logspace(self.params["c_imag"],
                                       1.710114014738142)
            self.f_mod = self.logspace(self.params["grad_freq"],
                                       3.00)
        self.params["grad_freq"] = self.f_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] = self.i_mod[self.scene_pos]
        self.params["c_real"] = self.r_mod[self.scene_pos] - 10
        self.params["mod"] = self.m_mod[self.scene_pos]

    def sub(self, frame):
        if self.scene_init:
            self.idx = 0
            self.rad_mod = self.logspace(self.params["radius"],
                                         21230142690754)
            self.f_mod = self.logspace(self.params["grad_freq"],
                                       1.20)
        self.params["grad_freq"] = self.f_mod[self.scene_pos]
        pre_iter = [69, 71, 72, 74, 76, 77, 79, 77]
        if self.idx < 9:
            if self.perc > 0.1:
                if self.idx > 0:
                    self.params["pre_iter"] = pre_iter[self.idx - 1]
                self.midi_events["perc"].prev_val = 0
                self.idx += 1
                self.perc = 0
        self.params["c_real"] -= 1e-3 * self.perc
        self.params["mod"] += 1e-5 * self.bass
        self.params["radius"] = self.rad_mod[self.scene_pos]

    def verse3(self, frame):
        self.params["c_imag"] -= 1e-4 * self.perc
        self.params["c_real"] += 1e-4 * self.hgh
        self.params["grad_freq"] += 5e-3 * self.bell

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         151911706106)
                                         #43635202)

        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 8e-4 * self.perc
        self.params["c_real"] += 1e-4 * self.hgh
        self.params["grad_freq"] += 5e-3 * self.bell

    def verse1(self, frame):
        if self.scene_init:
            self.params["map_radius"] = 0.030567910119860146
        self.params["radius"] = self.rad_mod[frame]
        self.params["mod"] += 3e-5 * self.rhode
        self.params["c_imag"] = self.i_mod[frame]
        self.params["c_real"] += 5e-4 * self.hgh
        self.params["grad_freq"] += 5e-3 * self.bell

    def intro(self, frame):
        if self.scene_init:
            self.params["pre_iter"] = 67
            self.rad_mod = self.logspace(4.918377122018591e+17,
                                         25347206211,
                                         1253)
            self.i_mod = self.linspace(1.7486588800495475,
                                       1.7086588800495475, 1253)
        self.params["c_imag"] = self.i_mod[frame]
        self.params["grad_freq"] += 5e-3 * self.bell
        self.params["radius"] = self.rad_mod[self.scene_pos]

    def updateMidi(self, midi_events, frame):
        super().updateMidi(midi_events, frame)
        if frame < 775:
            self.midi_events["hgh"].prev_val = 0
            self.hgh = 0

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 0
        self.midi_events = {
            "hgh": MidiMod("perc high", mod="one-off", decay=20),
            "perc": MidiMod("perc low", mod="one-off", decay=5),
            "kick": MidiMod("kick", decay=15),
            "bass": MidiMod("BF sub", decay=23, mod="one-off"),
            "rhode": MidiMod("BF friend"),
            "bell": MidiMod("BF buttons", mod="one-off", decay=42),
            "flute": MidiMod("BFbendy lead"),
        }


if __name__ == "__main__":
    run_main(Demo())
