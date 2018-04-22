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
gradient: MySunrise.ggr
#gradient: purples
#gradient: Teuns.ugr:Gayfish_Neon_Party
kernel: mean-distance
kernel_params: "double mod"
kernel_params_mod:
  - mod
mod: 1
xyinverted: True
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
julia: true
mod: 1
radius: 200

r_step: 0.01
i_step: 0.01

c_imag: 0
c_real: -0.11073385975110824
center_imag: 11.08226622006142
center_real: 0
formula: z = cdouble_iabs(cdouble_iabs(cdouble_log(cdouble_log(cdouble_radd(mod,
      cdouble_fabs(cdouble_pow(c, cdouble_sub(c, cdouble_log(cdouble_fabs(cdouble_log(cdouble_sub(c,
      cdouble_sub(cdouble_divide(c, c) , z) ) ) ) ) ) ) ) ) ) ) ) ) ;
grad_freq: 1
i_step: 0.0017807098289912549
julia: true
map_center_imag: -0.3155879841025344
map_center_real: 0.028752751793054115
map_radius: 0.01780709828991255
max_iter: 60
r_step: 0.0017807098289912549
radius: 5.451851851851851
"""
grad_mod = 1e-3


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [6100, None],
            [5836, self.ending],
            [4955, self.verse5],
            [4200, self.verse4],
            [3604, self.verse3],
            [2700, self.verse2],
            [2273, self.tr2],
            [1804, self.verse1],
            [1355, self.tr1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def ending(self, frame):
        if self.scene_init:
            self.i_mod = self.logspace(self.params["c_imag"] + 10,
                                       0 + 10)
            self.r_mod = self.logspace(self.params["c_real"] + 10,
                                       -0.28385400063502964 + 10)
            self.rad_mod = self.logspace(self.params["radius"], 233969)
            self.mod_mod = self.logspace(self.params["mod"] + 1, 2.373 + 1)
            self.c_mod = self.logspace(self.params["center_imag"], 82348)
            self.g_mod = self.logspace(self.params["grad_freq"], 2)
        self.params["center_imag"] = self.c_mod[self.scene_pos]
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["mod"] = self.mod_mod[self.scene_pos] - 1
        self.params["c_imag"] = self.i_mod[self.scene_pos] - 10
        self.params["c_real"] = self.r_mod[self.scene_pos] - 10
        self.params["grad_freq"] = self.g_mod[self.scene_pos]

    def verse5(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 256)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= 2e-4 * self.rhode
        self.params["c_real"] -= 1e-3 * self.muffin
        self.params["mod"] -= 3e-3 * self.low
        self.params["grad_freq"] -= grad_mod * self.hgh

    def verse4(self, frame):
        if self.scene_init:
            self.c_mod = self.logspace(self.params["center_imag"],
                                       28.628512639623754)
            self.rad_mod = self.logspace(self.params["radius"], 57)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["center_imag"] = self.c_mod[self.scene_pos]
        self.params["c_imag"] += 1e-4 * self.low
        self.params["c_real"] -= 1e-4 * self.low
        self.params["mod"] += 4e-3 * self.muffin
        self.params["grad_freq"] += grad_mod * self.hgh

    def verse3(self, frame):
        self.params["c_imag"] -= 5e-5 * self.low
        self.params["c_real"] += 5e-5 * self.muffin
        self.params["grad_freq"] += grad_mod * self.hgh
        self.params["mod"] -= 1e-3 * self.drone

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 46)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += 5e-5 * self.low
        self.params["c_real"] -= 5e-5 * self.muffin
        self.params["grad_freq"] += grad_mod * self.hgh
        self.params["mod"] += 1e-3 * self.drone

    def tr2(self, frame):
        if self.scene_init:
            self.mod_mod = self.logspace(self.params["mod"], 0.5)
        self.params["mod"] = self.mod_mod[self.scene_pos]
        self.params["c_imag"] -= 1e-4 * self.muffin
        self.params["grad_freq"] += grad_mod * self.rhode

    def verse1(self, frame):
        if self.scene_init:
            self.c_mod = self.logspace(self.params["center_imag"],
                                       11.072957084068197)
        self.params["center_imag"] = self.c_mod[self.scene_pos]
        self.params["c_imag"] -= 1e-4 * self.muffin
        self.params["c_real"] -= 1e-4 * self.low
        self.params["grad_freq"] += grad_mod * self.rhode

    def tr1(self, frame):
        if self.scene_init:
            self.imod = self.linspace(self.params["c_imag"],
                                      0.07635127173705021)
            self.c_mod = self.logspace(self.params["center_imag"],
                                       8.184068195179307)
        self.params["center_imag"] = self.c_mod[self.scene_pos]
        self.params["c_imag"] = self.imod[self.scene_pos]
        self.params["c_real"] += 1e-4 * self.rhode
        self.params["grad_freq"] += grad_mod * self.hgh

    def intro(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 13)
        self.params["radius"] = self.rad_mod[self.scene_pos]
#        self.params["c_imag"] += 4e-5 * self.low
        self.params["c_imag"] += 1e-4 * self.low
        self.params["c_real"] += 2e-4 * self.rhode
        self.params["grad_freq"] += grad_mod * self.hgh

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 6), "max", decay=5),
            "hgh": AudioMod((244, 895), "max", decay=30),
        }

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 295
        self.midi_events = {
            "rhode": MidiMod(["epiano B76", "epiano high"], mod="one-off"),
            "drone": MidiMod("drone highdre@d", decay=3),
            "muffin": MidiMod(["muffin"], decay=4),
        }

if __name__ == "__main__":
    run_main(Demo())
