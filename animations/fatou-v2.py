#!/usr/bin/env python
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

p = """
formula: |
  z.imag = fabs(z.imag);
  z = cdouble_mul(z, z);
  z = cdouble_add(z, c);
c_imag: 0.03
c_real: -1.732335158720565
center_imag: 0.0
center_real: 0.0
grad_freq: 42
gradient: Sunrise.ggr
i_step: 0.003
julia: true
map_center_imag: 0.0033627122824947584
map_center_real: -1.7315251587205658
map_radius: 0.0003474089609239853
max_iter: 1856
r_step: 3.0e-05
radius: 0.05639839548062174
show_map: true
xyinverted: true
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [4180, None],
            [3899, self.end],
            [3601, self.bass4],
            [3000, self.bass3],
            [2399, self.slow],
            [2099, self.brk],
            [1200, self.bass2],
            [599,  self.bass1],
            [584,  self.zoom],
            [299,  self.intro2],
            [0,    self.intro1],
        ]
        super().__init__(yaml.load(p))
        self.piano = 0
        self.kick = 0
        self.bells = 0
        self.snare = 0
        self.bass_mod = 0

    def end(self, frame):
        self.base_c -= 3e-4
        self.params["max_iter"] -= 2
#        self.params["grad_freq"] -= 0.1
        self.set_c(self.base_c)

    def bass4(self, frame):
        if self.scene_init:
            self.base_c = self.get_c()
            self.g_mod = self.logspace(self.params["grad_freq"], 60)
            self.r_mod = self.logspace(self.params["radius"], 0.3)
        if self.piano:
            self.base_c += 5e-4 * self.piano
        if self.bells:
            self.base_c += 3.7e-4 * self.bells
        self.set_c(self.base_c)
        self.params["c_imag"] += 5e-4 * self.kick
        self.params["c_imag"] -= 1e-3 * self.snare
        self.params["grad_freq"] = self.g_mod[self.scene_pos]
        self.params["radius"] = self.r_mod[self.scene_pos]

    def bass3(self, frame):
        if self.scene_init:
            self.base_c = self.get_c()
            self.r_mod = self.logspace(self.params["radius"], 0.16)

        if self.piano:
            self.base_c -= 5e-5j * self.piano
        if self.bells:
            self.base_c -= 2e-5j * self.bells
#            self.bells = 0

        self.set_c(self.base_c)
        self.params["c_imag"] -= 5e-4 * self.kick
        self.params["c_real"] -= 1e-3 * self.snare
        self.params["radius"] = self.r_mod[self.scene_pos]

    def slow(self, frame):
        if self.scene_init:
            self.base_c = self.get_c()
            self.base_iter = self.params["max_iter"]
            self.bass_mod = 1

        if self.piano:
            self.base_c -= 2e-5j * self.piano

        self.base_c -= 1e-5 * self.kick
        self.kick = self.kick / 1.5

        self.params["max_iter"] = self.base_iter - 10 * self.bass_mod
        self.set_c(self.base_c)
        self.params["c_real"] += 1e-4 * self.snare

    def brk(self, frame):
        if self.scene_init:
            self.base_c = self.get_c()
            self.r_mod = self.logspace(self.params["radius"], 0.052)

#        self.scene.max_iter = self.base_iter - 10000 * self.bass_mod
        if self.bells:
            self.base_c -= 1e-6 * self.bells

        self.base_c += 3e-6j * self.kick
        self.kick = self.kick / 2
        self.set_c(self.base_c)
        self.params["radius"] = self.r_mod[self.scene_pos]

    def bass2(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(self.params["radius"], 0.008)
            self.f_mod = self.linspace(self.params["grad_freq"], 30)
            self.m_mod = self.logspace(0.1, 200000)
        if self.piano:
            self.base_c -= 1e-10 * self.piano
        if self.bells:
            self.base_c -= 4e-12j * self.bells * self.m_mod[self.scene_pos]

        self.base_c -= 1e-11 * self.kick * self.m_mod[self.scene_pos]
        self.kick = self.kick / 2
        self.set_c(self.base_c)
        self.params["c_imag"] += 1e-10 * self.snare * self.m_mod[self.scene_pos]

        self.params["radius"] = self.r_mod[self.scene_pos]
        self.params["grad_freq"] = self.f_mod[self.scene_pos]
        if frame not in (1499, 1501):
            self.params["max_iter"] = self.base_iter - 1000 * self.bass_mod

    def bass1(self, frame):
        if self.scene_init:
            self.base_c = complex(-1.7325721547629551, 0.019931766475342925)
            self.base_iter = self.params["max_iter"]
            self.r_mod = self.logspace(self.params["radius"], 2.5e-05)

        self.params["radius"] = self.r_mod[self.scene_pos]
        self.base_c += 1e-11j * self.piano
        self.base_c += 1e-11 * self.kick
        self.kick = self.kick / 2
        self.set_c(self.base_c)
#        self.params["c_real"] -= 2e-10 * self.kick
        self.params["c_imag"] += 1e-9 * self.snare
        if frame != 871:
            self.params["max_iter"] = self.base_iter + 500 * self.bass_mod

    def zoom(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(
                self.params["radius"], 2.1e-05)
            self.c_mod = self.linspace(
                self.params["c_imag"], 0.019931766475342925)
        self.params["radius"] = self.r_mod[self.scene_pos]
        self.params["c_imag"] = self.c_mod[self.scene_pos]

    def intro2(self, frame):
        if self.scene_init:
            self.m_mod = self.logspace(1, 0.005)
            self.r_mod = self.logspace(self.params["radius"], 0.001)
        if self.piano:
            self.base_c -= (16.4e-6+1e-7j) * self.piano * self.m_mod[self.scene_pos]
        self.params["radius"] = self.r_mod[self.scene_pos]
        # adjust for upcoming zoom
        self.base_c += -1.0631578948102646e-10j
        self.set_c(self.base_c)

    def intro1(self, frame):
        if self.scene_init:
            self.params["c_imag"] = 0.08
            self.base_c = self.get_c()
            self.m_mod = self.logspace(1, 0.005)
            self.params["radius"] = 1
            self.r_mod = self.logspace(self.params["radius"], 0.1)
            self.g_mod = self.logspace(250, 42)
        if self.piano:
            self.base_c -= 0.004j * self.piano * self.m_mod[self.scene_pos]
        self.params["radius"] = self.r_mod[self.scene_pos]
        self.set_c(self.base_c)
        self.params["grad_freq"] = self.g_mod[self.scene_pos]

    def updateMidi(self, midi_events):
        for event in midi_events:
            if event["track"] == "Rhodes":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.piano = max(list(ev["pitch"].keys())) / 127
                    else:
                        print(event)
            elif event["track"] == "Bells":
                self.bells = 1
            elif event["track"] == "Matrix M":
                self.matrix = 1
            elif event["track"] == "kick":
                self.kick = 1
                print("kick")
            elif event["track"] == "snare":
                self.snare = 1
                print("snare")
            elif event["track"] == "seqbass":
                for ev in event["ev"]:
                    if ev["type"] == "mod": # and frame not in (871, 1499, 1501, 3004):
                        self.bass_mod = (127 - ev["val"]) / 127.0
            print(event)

    def update(self, frame):
        super().update(frame)
        if self.piano > 0:
            self.piano -= self.piano / 25
        if self.bells > 0:
            self.bells -= self.bells / 25
        if self.kick > 0:
            self.kick -= self.kick / 50
        if self.snare > 0:
            self.snare -= self.snare / 25
        if self.matrix > 0:
            self.matrix -= self.matrix / 25


if __name__ == "__main__":
    run_main(Demo())
