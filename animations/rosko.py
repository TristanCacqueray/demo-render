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
julia: true

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

c_imag: -0.19768712350300383
c_real: -0.2173534911019462
formula: |
  // z=abs(1/z)*m+c
  z = cdouble_rdivide(1, z);
  z.real = fabs(z.real);
  z.imag = fabs(z.imag);
  z2 = cdouble_new(0, 1);
  z = cdouble_mul(z, z2);
  z = cdouble_add(z, c);

grad_freq: 0.15
i_step: 0.01295210838317871
map_center_imag: -0.19768712350300383
map_center_real: -0.20440138271876748
map_radius: 0.1295210838317871
max_iter: 86
r_step: 0.01295210838317871
radius: 4.7

"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [5700, None],
            [5500, self.ending],
            [4250, self.verse5],
            [3624, self.verse4],
            [2999, self.verse3],
            [2508, self.verse2],
            [1750, self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def ending(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 0.05)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] += (1e-4 * self.hum) + 1e-3
        self.params["c_real"] += 1e-4 * self.snare #- 1e-4 * self.kick

    def verse5(self, frame):
        self.params["c_imag"] += (1e-4 * self.hum)
        self.params["c_real"] += 1e-4 * self.snare #- 1e-4 * self.kick

    def verse4(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 1)
#        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_imag"] -= (1e-4 * self.hum)
        self.params["c_real"] -= (1e-4 * self.waldo)
#        self.params["c_real"] -= 1e-4 * self.snare #- 1e-4 * self.kick
        self.params["grad_freq"] += 1e-3 * self.hat

    def verse3(self, frame):
        self.params["c_real"] += 1e-4 * self.kick
        self.params["c_imag"] -= 1e-3 * self.snare
        self.params["grad_freq"] -= 1e-3 * self.bass
        ks = 3500
        if frame == ks:
            self.rad_mod = self.logspace(self.params["radius"], 274,
                                         3624 - ks)
        if frame >= ks:
            self.params["radius"] = self.rad_mod[frame - ks]

    def verse2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.params["radius"], 3)
        self.params["radius"] += self.params["radius"] / 100 * self.kick
        self.params["c_imag"] += 1e-4 * self.soft
        self.params["c_real"] -= 5e-4 * self.snare

    def verse1(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(
                self.params["radius"], 1.7881393432617188)
        self.params["radius"] = self.rad_mod[self.scene_pos]
        self.params["c_real"] -= 5e-4 * self.hum + 2e-5 * self.soft
        self.params["c_imag"] += 1e-4 * self.hum

    def intro(self, frame):
#        self.params["c_imag"] += 4e-5 * self.low
#        self.params["radius"] += self.params["radius"] / 500 * self.fx
        self.params["c_imag"] -= 1e-4 * self.fx
        self.params["c_real"] += 5e-4 * self.hum + 2e-5
        self.params["grad_freq"] += 1e-3 * self.hat

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((0, 6), "max", decay=5),
            "hgh": AudioMod((244, 895), "max", decay=30),
        }
        return

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 250
        self.midi_events = {
            "soft": MidiMod("softies", mod="one-off"),
            "snare": MidiMod(["snare", "Copy of snare"], mod="one-off"),
            "kick": MidiMod(["KCK", "lowkick"], mod="one-off"),
            "rhode": MidiMod(["epiano B76", "epiano high"], mod="one-off"),
            "bass": MidiMod("virusA", mod="one-off"),
            "fx": MidiMod("fx", mod="one-off"),
            "hum": MidiMod("hum", mod="one-off", decay=50),
            "waldo": MidiMod("waldo", mod="one-off", decay=50),
            "hat": MidiMod(["hats", "Copy of percs"], mod="one-off"),
        }

if __name__ == "__main__":
    run_main(Demo())
