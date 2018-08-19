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
#gradient: purples
#gradient: Sunrise.ggr
#gradient: AG_zebra.ggr
#gradient: See_The_World.ugr:023
formula: |
  // log(log((ibas(z)^tan(ibas(z)) + z)^m + c))
  z2.real = x;
  z2.imag = y;
  z.imag = fabs(z.imag);
  //z.real = fabs(z.real);
  z = cdouble_pow(z, cdouble_tan(z));
  z = cdouble_add(z, z2);
  z = cdouble_powr(z, mod);
  z = cdouble_add(z, c);
  z = cdouble_log(z);
  z = cdouble_log(z);
kernel_params: double mod, double x, double y
kernel_params_mod:
  - mod
  - x
  - y

x: 0
y: 0
mod: 2
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
  x:
    type: int
    sliders: true
    min: 0
    max: 10
    resolution: 0.001
  y:
    type: int
    sliders: true
    min: 0
    max: 10
    resolution: 0.001
  pre_iter:
    type: int
    sliders: true
    min: 0
    max: 1000
    resolution: 1


pre_iter: 0
kernel: mean-distance
xyinverted: true
show_map: False

c_imag: 0.014250692979614425
c_real: 1.12146005173486
grad_freq: 3.95
i_step: 0.004098128043115138
julia: true
map_center_imag: 1.1091656676055146
map_center_real: 0.014250692979614425
map_radius: 0.04098128043115138
max_iter: 36
mod: 1.993
r_step: 0.004098128043115138
radius: 697.96764975237

center_imag: -68.02040481824366
center_imag: -67.71003818732763
c_imag: 0.014250177602093694


max_iter: 42
pre_iter: 1
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4700, None],
            [4600, self.ending],
            [4281, self.outro],
            [3009, self.intro2],
            [2890, self.tr2],
            [2390, self.main],
            [1625, self.reve],
            [1500, self.tr],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def ending(self, frame):
        if self.scene_init:
            self.f_mod = self.logspace(self.params["grad_freq"], 4.05)
        self.params["grad_freq"] = self.f_mod[self.scene_pos]

    def outro(self, frame):
        if self.scene_init:
            self.y_mod = self.linspace(self.params["y"], 0.023)
            self.x_mod = self.linspace(self.params["x"], 0.001)
            self.m_mod = self.logspace(self.params["mod"], 1.9)
        self.params["y"] = self.y_mod[self.scene_pos]
#        self.params["x"] = self.x_mod[self.scene_pos]
        self.params["mod"] = self.m_mod[self.scene_pos]

    def intro2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 60462)
            self.m_mod = self.logspace(1, 0.1)
            self.base_y = self.params["y"]
            self.base_imag = self.params["c_imag"]
        m = self.m_mod[self.scene_pos]
        if frame > 3770:
            self.params["grad_freq"] -= 1e-3 * self.lead
            self.params["mod"] += 4e-3 * self.lead * m
        else:
            self.params["mod"] -= 1e-3 * m
        self.params["radius"] = self.rad_mod[self.scene_pos]

    def tr2(self, frame):
        if self.scene_init:
            self.x_mod = self.logspace(self.params["x"], 0.0001)
            self.y_mod = self.logspace(self.params["y"], 0.0001)
            self.m_mod = self.logspace(self.params["mod"], 2.155)
        self.params["mod"] = self.m_mod[self.scene_pos]
        self.params["x"] = self.x_mod[self.scene_pos]
        self.params["y"] = self.y_mod[self.scene_pos]

    def main(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         0.0014815960306413505)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["x"] += 1e-4 * self.kick
        self.params["y"] += 1e-5 * self.drum
        self.params["mod"] -= 1e-4 * self.piano

    def reve(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"],
                                         0.001227508969422842)
            self.base_mod = self.params["mod"]
            self.m_mod = self.logspace(0.05, 0.1)
        if frame == 1893:
            self.mod_mod = self.logspace(
                self.params["mod"],
                2.158843370136789 + 0.01566298632110641, 2390 - 1893)
        m = self.m_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        if frame < 1893 and self.scene_pos > 0:
            self.base_mod -= 1e-3
            self.params["grad_freq"] -= 5e-4 * self.reves
        elif frame >= 1893:
            self.base_mod = self.mod_mod[frame - 1893]
        self.params["mod"] = self.base_mod - 0.4 * self.reves * m
        self.params["x"] = -1e-2 * self.piano
        self.params["y"] = 5e-2 * self.kick

    def tr(self, frame):
        if self.scene_init:
            self.m_mod = self.logspace(self.params["mod"],
                                       2.159)
        self.params["mod"] = self.m_mod[self.scene_pos]

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(1e20,
                                         75, 1500)
            self.m_mod = self.logspace(1.6, self.params["mod"])
            self.f_mod = self.logspace(3, 4)
            self.base_real = self.params["c_real"]
            self.base_imag = self.params["c_imag"]
            self.base_x = 0.015000000000002482
        self.params["grad_freq"] = self.f_mod[self.scene_pos]
        self.params["mod"] = self.m_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.base_x -= 1e-5
        self.params["x"] = self.base_x

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((1, 4), "avg"),
        }
        return

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = midi_skip
        self.midi_events = {
            "piano": MidiMod("Combinator 2", mod="pitch", decay=1),
            "bell": MidiMod("Thor 2", mod="one-off"),
            "kick": MidiMod("Kick", mod="one-off", decay=5),
            "hgh": MidiMod("Hats high", mod="one-off"),
            "reves": MidiMod("Reves", mod="pitch", decay=2),
            "drum": MidiMod("Dr. Octo Rex 1", mod="one-off"),
            "lead": MidiMod("Lead Hard", mod="pitch", decay=1)
        }


if __name__ == "__main__":
    run_main(Demo())
