#!/bin/env python3
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

import os
import sys
import pygame
import math

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE

from utils_v2.pygame_utils import Screen, Window, ComplexPlane, Waterfall, SpectroGraph
from utils_v2.common import PHI, usage_cli_complex, run_main, gradient, rgb250
from utils_v2.common import Animation
from utils_v2.midi import Midi
from utils_v2.scipy_utils import Audio, NoAudio, SpectroGram, AudioBand, AudioMod
from utils_v2.pygame_utils import ColorMod, Graph
from utils_v2.burning_julia import BurningJuliaSet


class Demo(Animation):
    def __init__(self, scene, midi):
        self.scenes = [
            [4650, None],
            [4281, self.end],
            [3009, self.intro3],
            [2890, self.tr2],
            [2390, self.main],
            [1625, self.reve],
            [1500, self.tr1],
            [749,  self.intro2],
            [0,    self.intro1],
        ]
        super().__init__()
        self.scene = scene
        self.args = scene.args
        self.midi = midi

        self.piano = 0
        self.kick = 0
        self.hat = 0
        self.bells = 0
        self.snare = 0
        self.bass_mod = 0
        self.hat_count = 0
        self.last_hat = 0
        self.hat_dir = -1
        self.drum = 0
        self.reves = 0
        self.hum = 0
        self.lead = 0

    def end(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 0.0004)
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.base_c -= 9e-5j * self.rad_mod[self.scene_pos]
        self.args.gradient_frequency -= 0.5 * self.rad_mod[self.scene_pos]
        self.scene.c = self.base_c


    def intro3(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.rad_mod = self.logspace(self.scene.radius, 0.15)
            self.base_freq = self.args.gradient_frequency
        if self.lead > 0:
            self.base_freq += 0.01 * self.lead
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.base_c -= 1e-4j * self.piano
        self.scene.c = self.base_c + 4e-3 * self.kick + 1e-2j * self.lead
        self.args.gradient_frequency = self.base_freq

    def tr2(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 0.09)
            self.freq_mod = self.logspace(self.args.gradient_frequency,
                                          9.4)
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.args.gradient_frequency = self.freq_mod[self.scene_pos]


    def main(self, frame):
        if self.scene_init:
            ...
        if self.hum > 0:
            self.base_c -= 1e-8j * self.hum
            self.hum -= self.hum / 10.0
            self.base_freq += 1e-1 * self.hum
        else:
            self.hum = 0
        self.base_c += 5e-10j * self.drum
        self.args.gradient_frequency = self.base_freq + math.cos(self.scene_pos / 42) / 23
        self.scene.c = self.base_c + 1e-7 * self.piano

    def reve(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.rad_mod = self.logspace(self.scene.radius, 0.0004)
            self.base_freq = self.freq_mod[-1]
            self.hum = 0
        if self.hum > 0:
            self.base_c -= 1e-8j * self.hum
            self.hum -= self.hum / 10.0
            self.base_freq -= 1e-1 * self.hum
        else:
            self.hum = 0
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.base_c -= 1e-10 * self.reves
        self.scene.c = self.base_c + 1e-8j * self.piano - 1e-9 * self.drum
        self.base_freq += 1e-3
        self.args.gradient_frequency = self.base_freq

    def tr1(self, frame):
        if self.scene_init:
            self.cr_mod = self.linspace(-1.9437215284314704+10,
                                        -1.943722628431471+10)
            self.ci_mod = self.linspace(0.019152374471573055,
                                        0.023440701855685746)
            self.rad_mod = self.logspace(self.scene.radius, 8.91903357825e-05)
            self.iter_mod = self.linspace(self.scene.max_iter, 335)
            self.freq_mod = self.logspace(self.args.gradient_frequency, 5.0)
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        self.args.gradient_frequency = self.freq_mod[self.scene_pos]
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
#        self.scene.c = complex(self.cr_mod[self.scene_pos]-10, self.ci_mod[self.scene_pos])

    def intro2(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.rad_mod = self.linspace(self.scene.radius, 0.05)
            self.base_freq = self.scene.args.gradient_frequency

        if self.hum > 0:
            mod = self.hum * 9 + 1
            self.hum -= self.hum / 10.0
        else:
            mod = 1
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.base_c += 5e-5j * self.drum
        self.scene.c = self.base_c + 1e-3 * self.piano * mod + 5e-4j * (mod - 1)
        self.scene.args.gradient_frequency = self.base_freq - 0.3 * self.bells #* (mod / 3)


    def intro1(self, frame):
        if self.scene_init:
            self.base_c = (-2.0335132635991524-0.0009975703823460465j)
            self.scene.set_view(radius=0.23)
            self.args.gradient_frequency = 3
        self.base_c += 1e-3 * self.piano
        if frame < 450:
            self.hat_mod = 1e-2 * self.hat
        else:
            self.hat_mod -= self.hat_mod / 10.
        self.scene.c = self.base_c + 8e-3j * self.kick + self.hat_mod

    def update(self, frame):
        try:
            midi_events = self.midi.get(frame)
        except Exception:
            midi_events = []
        for event in midi_events:
            if event["track"] == "Combinator 2":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.piano = max(list(ev["pitch"].keys())) / 127
                    else:
                        print(event)
            elif event["track"] == "Thor 2":
                self.bells = 1
            elif event["track"] == "Kick":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.kick = max(list(ev["pitch"].keys())) / 127
                    else:
                        print(event)
            elif event["track"] == "Hats high":
                self.hat_count += 1
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.hat = max(list(ev["pitch"].keys())) / 127
                    else:
                        print(event)
            elif event["track"] == "Reves":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.reves = len(ev["pitch"])
            elif event["track"] == "Dr. Octo Rex 1":
                self.drum = 1
                print(event["ev"])
                for ev in event["ev"]:
                    if ev["type"] == "chords" and (55 in ev["pitch"] or 54 in ev["pitch"]):
                        self.hum = 1
            elif event["track"] == "Lead Hard":
                self.lead = 1
            else:
                for ev in event["ev"]:
                    if ev["type"] != "mod":
                        print(event)
            print(event)

        super().update(frame)

        if self.lead > 0:
            self.lead -= self.lead / 25
        else:
            self.lead = 0
        if self.hat > 0:
            self.hat -= self.hat / 5
        if self.drum > 0:
            self.drum -= self.drum / 10
        if self.piano > 0:
            self.piano -= self.piano / 10
        if self.bells > 0:
            self.bells -= self.bells / 50
        if self.reves > 0:
            self.reves -= self.reves / 10
        if self.kick > 0:
            self.kick -= self.kick / 15
        if self.snare > 0:
            self.snare -= self.snare / 25


def main():
    args = usage_cli_complex(gradient="duna.ggr")
    args.midi = "duna.mid"

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()

    midi = Midi(args.midi, args.fps)

    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = BurningJuliaSet(args, "bufalo")

    demo = Demo(scene, midi)

    screen.add(scene)

    frame = args.skip
    paused = False

    # Warm opencl
    scene.render(0)
    for skip in range(args.skip):
        demo.update(skip)

    while True:
        if not paused:
            try:
                audio.get(frame)
            except IndexError:
                ...

            demo.update(frame)

            scene.render(frame)
            screen.update()
            if args.record:
                screen.capture(args.record, frame)
            pygame.display.update()
            frame += 1

        for e in pygame.event.get():
            if e.type not in (KEYDOWN, MOUSEBUTTONDOWN):
                continue
            if e.type == MOUSEBUTTONDOWN:
                print("Clicked", e.pos)
            else:
                if e.key == K_RIGHT:
                    frame += args.fps
                elif e.key == K_LEFT:
                    frame = max(0, frame - args.fps)
                elif e.key == K_UP:
                    frame += args.fps * 60
                elif e.key == K_DOWN:
                    frame = max(0, frame - args.fps * 60)
                elif e.key == K_SPACE:
                    paused = not paused
                elif e.key == K_ESCAPE:
                    exit(0)

        if not args.record:
            clock.tick(args.fps)
    if args.video and args.record:
        import subprocess
        subprocess.Popen([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-start_number", str(args.skip),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/%04d-%s.mp4" % (args.record, args.skip, args.anim)
        ]).wait()


if __name__ == "__main__":
    run_main(main)
