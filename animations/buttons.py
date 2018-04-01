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
xyinverted: True
c_imag: -0.566064898761892
c_real: 0.18463369201226695
grad_freq: 2.4
i_step: 0.0008163331511743347
julia: true
max_iter: 96
mod: 1.44
r_step: 0.0008163331511743347
radius: 511461322
gradient: Sunrise.ggr
mods:
  mod:
    type: ratio
    sliders: true
    min: 0.0001
    max: 10
    resolution: 0.001
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [5200, None],
            [4985, self.zoom_out],
            [4501, self.ending],
            [3500, self.verse4],
            [3000, self.verse3],
            [2751, self.tr],
            [2001, self.sub],
            [1253, self.verse2],
            [503,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

#    def setAudio(self, audio):
#        self.audio = audio
#        self.spectre = SpectroGram(audio.audio_frame_size)
#        self.low_mod = AudioMod((15, 26), "max", decay=5, threshold=0.5)

#    def updateAudio(self, audio_buf):
#        self.spectre.transform(audio_buf)
#        self.low = self.low_mod.update(self.spectre)

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 0
        self.midi_events = {
            "perc": MidiMod("perc low", mod="one-off", decay=5),
            "kick": MidiMod("kick", decay=15),
            "bass": MidiMod("BF sub", decay=23, mod="one-off"),
            "rhode": MidiMod("BF friend"),
            "bell": MidiMod("BF buttons", mod="one-off", decay=42),
            "flute": MidiMod("BFbendy lead"),
        }

    def updateMidi(self, midi_events):
        super().updateMidi(midi_events)
        if midi_events:
            print(midi_events)

    def zoom_out(self, frame):
        if self.scene_init:
            self.speed = 1.4
            self.log_mod = self.logspace(1, 0.2)
        self.speed /= 1.01
        self.bass -= self.bass / 20
#        self.params["grad_freq"] += 3e-3 # * self.bass
        self.params["radius"] += (self.params["radius"] / 20 * self.speed +
                                  self.params["radius"] / 5 * self.bass) * \
            self.log_mod[self.scene_pos]

    def ending(self, frame):
        if self.scene_init:
            self.log_mod = self.logspace(1, 0.01)
            self.lmod = self.logspace(1, 0.5)
        self.params["c_real"] += 3e-3 * self.perc
        self.params["c_imag"] += 1e-3 * self.bell * self.lmod[self.scene_pos]
        self.params["mod"] += 1e-2 * self.rhode * self.log_mod[self.scene_pos]
        self.params["grad_freq"] += 2e-2 * self.bass * \
            self.lmod[self.scene_pos]
        self.params["radius"] -= self.params["radius"] / 75 * self.bell

    def verse4(self, frame):
        self.params["c_real"] += 1e-3 * self.perc
        self.params["c_imag"] += 1e-3 * self.rhode
        self.params["mod"] += 1e-3 * self.flute
        self.params["grad_freq"] -= 1e-4 * self.bass
        self.params["radius"] += self.params["radius"] / 150 * self.bell

    def verse3(self, frame):
        # self.params["c_real"] -= 5e-5 * self.perc
        self.params["c_real"] -= 1e-3 * self.rhode
        self.params["grad_freq"] += 5e-3 * self.bass

    def tr(self, frame):
        self.params["mod"] -= 0.00172
        self.params["grad_freq"] += 1e-3 * self.bass
        self.params["c_imag"] -= 3e-3 * self.perc

    def sub(self, frame):
        self.params["radius"] -= self.params["radius"] / 10 * self.bass
        self.params["c_real"] -= 4e-4 * self.perc
        self.params["c_imag"] -= 1e-4 * self.rhode
        self.params["grad_freq"] -= 1e-3 * self.bell

    def verse2(self, frame):
        self.params["grad_freq"] += 1e-4 * self.bell
        self.params["c_real"] -= 5e-5 * self.perc
        self.params["c_imag"] -= 1e-4 * self.bell + 1e-5
        self.params["mod"] += 1e-4 * self.rhode

    def verse1(self, frame):
        self.params["grad_freq"] += 4e-4 * self.bell
        # self.params["c_real"] += 1e-4 * self.perc
        self.params["c_imag"] -= 1e-4 * self.rhode + 1e-5
        self.params["mod"] += 2e-5 * self.bell

    def intro(self, frame):
        # self.params["max_iter"] = 128 + 50 * self.bass
        self.params["grad_freq"] += 1e-3 * self.bell
        self.params["c_real"] -= 1e-4 * self.bell + 1e-5


if __name__ == "__main__":
    run_main(Demo())
