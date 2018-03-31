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
c_imag: -2.8454190476190493
c_real: -0.3964285714285715
grad_freq: 3 # 5.8
i_step: 0.0002
julia: true
map_center_imag: -2.4576190476190476
map_center_real: -0.3964285714285715
max_iter: 128
r_step: 0.0002
radius: 2486.3401631812214
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [3600, None],
            [3376, self.zoom_out],
            [2937, self.end],
            [2688, self.tr],
            [1874, self.verse3],
            [1375, self.verse2],
            [375,  self.verse1],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

#    def setAudio(self, audio):
#        self.audio = audio
#        self.spectre = SpectroGram(audio.audio_frame_size)
#        self.hgh_mod = AudioMod((373, 800), "max")
#        self.mid_mod = AudioMod((25, 70), "avg")

#    def updateAudio(self, audio_buf):
#        self.spectre.transform(audio_buf)
#        self.hgh = self.hgh_mod.update(self.spectre)
#        self.mid = self.mid_mod.update(self.spectre)

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = 123
        self.snare_mod = MidiMod("snare", decay=13)
        self.kick_mod = MidiMod("kick", decay=15)
        self.bass_mod = MidiMod("andy 67", decay=1)
        self.flute_mod = MidiMod("madflute", decay=3)
        self.rhode_mod = MidiMod("MIDI 08")

    def updateMidi(self, midi_events):
        self.snare = self.snare_mod.update(midi_events)
        self.kick = self.kick_mod.update(midi_events)
        self.bass = self.bass_mod.update(midi_events)
        self.flute = self.flute_mod.update(midi_events)
        self.rhode = self.rhode_mod.update(midi_events)
        if midi_events:
            print(midi_events)

    def zoom_out(self, frame):
        if self.scene_init:
            self.speed = 1.4
        self.speed /= 1.01
        self.bass -= self.bass / 20
        self.params["radius"] += self.params["radius"] / 20 * self.speed + \
                                 self.params["radius"] / 5 * self.bass

    def end(self, frame):
        self.params["c_imag"] += 7e-4 * self.kick
        self.params["c_real"] -= 5e-4 * self.snare
        self.params["grad_freq"] += 1e-3 * self.bass
        if self.rhode:
            self.rhode_mod.prev_val = 0
            self.params["max_iter"] += 4 * self.rhode

    def tr(self, frame):
        self.params["radius"] -= self.params["radius"] / 11 * self.flute
        self.params["grad_freq"] -= 2e-3 * self.bass

    def verse3(self, frame):
        self.params["c_imag"] += 4e-5 * self.kick
#        self.params["c_real"] -= 1e-4 * self.snare
        self.params["grad_freq"] -= 3e-3 * self.bass
        self.params["radius"] -= self.params["radius"] / 30 * self.flute


    def verse2(self, frame):
        self.params["c_imag"] += 0.6e-4 * self.kick
        self.params["c_real"] -= 1e-4 * self.snare
        self.params["grad_freq"] += 2e-3 * self.bass
        self.params["radius"] += self.params["radius"] / 15 * self.flute

    def verse1(self, frame):
        self.params["c_imag"] += 4e-5 * self.kick
        self.params["c_real"] -= 5e-5 * self.snare
        self.params["grad_freq"] += 2e-3 * self.bass

    def intro(self, frame):
        #self.params["max_iter"] = 128 + 50 * self.bass
        self.params["grad_freq"] += 4e-3 * self.bass
        #self.params["c_imag"] -= 1e-5 * self.bass


if __name__ == "__main__":
    run_main(Demo())
