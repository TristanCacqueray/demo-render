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

import pygame
import numpy as np

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE

from utils_v1.common import usage_cli_complex, run_main, Animation
from utils_v1.pygame_utils import Screen
from utils_v1.julia_set import JuliaSet
from utils_v1.scipy_utils import Audio, NoAudio, AudioBand, SpectroGram
from utils_v1.midi import Midi


class Demo(Animation):
    def __init__(self, scene, audio, spectre, midi):
        self.scenes = [
            [4350, None],
            [3975, self.end],
            [3700, self.tr4],
            [3092, self.bassfx],
            [2098, self.fx1],
            [1950, self.tr3],
            [1498, self.bass2],
            [1350, self.tr2],
            [898,  self.bass1],
            [598,  self.tr1],
            [0,    self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.spectre = spectre
        self.midi = midi
        self.audio = audio

        max_freq = audio.audio_frame_size // 2
        self.pitch_mod = AudioBand((308, max_freq), "avg", 50)
        self.pitch = 0

        self.piano = 0
        self.space_piano = 0
        self.kick = 0
        self.hat = 0
        self.snare = 0
        self.bass_mod = 0

        self.zoom_mod = None

    def end(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.c_real_mod = self.linspace(self.scene.c.real, 0.45393)
            self.c_base_imag = self.scene.c.imag
            self.iter_mod = self.logspace(2500, 170)
            self.piano_norm = 0

        if self.piano > self.piano_norm:
            self.piano_norm = self.piano
        else:
            self.piano_norm -= 0.01
        self.scene.c = complex(self.c_real_mod[self.scene_pos],
                               self.c_base_imag + 0.0425 * self.piano)
        self.scene.max_iter = self.iter_mod[self.scene_pos]

    def tr4(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.c_mod = self.geomspace(
                self.scene.c, (0.3422029384477769-0.41621828491048335j))
        self.scene.c = self.c_mod[self.scene_pos] - (-0.002+0.01j) * self.piano

    def bassfx(self, frame):
        if self.scene_init:
            self.zoom_mod = self.linspace(self.scene.radius, 1.22373113855)
            self.base_c = self.scene.c
        self.scene.c = self.base_c + 0.025 * self.kick + 0.01j * self.snare

    def fx1(self, frame):
        self.zoom_mod = None
        if self.scene_init:
            self.base_c = (0.3419 - 0.38987j)
            self.base_iter = self.scene.max_iter
            self.c_real_mod = self.linspace(0.3419, 0.33515)
            self.scene.max_iter = 6000
        self.scene.c = (
            complex(self.c_real_mod[self.scene_pos], self.base_c.imag) +
            0.002 * self.snare +
            0.0045j * self.kick +
            0.004 * self.space_piano - 0.0005 * self.piano)
#        self.scene.max_iter = self.base_iter - 3000 * self.snare

    def tr3(self, frame):
        # 0.3444396976570036-0.3799998811212446j
        # '(0.34199698401299994-0.38987654191607013j)' --center '0j' --radius 0.2109375
        if self.scene_init:
            self.zoom_mod = np.linspace(self.scene.radius, 0.2, self.scene_length / 8)
            self.c_real_mod = self.logspace(self.scene.c.real, 0.3419)
            self.c_imag_mod = self.geomspace(self.scene.c.imag, -0.38987)
            self.iter_mod = self.logspace(self.scene.max_iter, 5000)
        self.scene.c = complex(self.c_real_mod[self.scene_pos],
                               self.c_imag_mod[self.scene_pos] + (
                                   -0.005j * self.piano))
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        if self.scene_pos >= self.scene_length // 8:
            self.zoom_mod = None

    def bass2(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.z_mod = np.linspace(self.scene.radius, 0.15, 30)
            self.base_c = self.scene.c
            self.base_iter = 3000
            self.iter_mod = 0
            self.imag_mod = self.logspace(1, 0.1)
            self.real_mod = self.logspace(0.1, 1)
        self.scene.c = self.base_c - (
            0.0005 * self.piano * self.real_mod[self.scene_pos]) - (
                -0.0001j * self.piano * self.imag_mod[self.scene_pos])
#        if self.scene_length - self.scene_pos <= 30:
#            self.scene.set_view(radius=self.z_mod[30 - (self.scene_length - self.scene_pos)])
#        i_mod = 2000 * self.kick
#        if i_mod < self.iter_mod:
#            self.iter_mod -= (self.iter_mod - i_mod) / 25
#        else:
#            self.iter_mod = i_mod
#        self.scene.max_iter = self.base_iter - self.iter_mod

    def tr2(self, frame):
        if self.scene_init:
            self.zoom_mod = self.linspace(self.scene.radius, 0.02)
            self.iter_mod = self.logspace(self.scene.max_iter, 2000)
            self.base_c = self.scene.c
            self.piano_mod = self.linspace(1, 0.2)
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        self.scene.c = self.base_c + 0.0003 * self.piano * self.piano_mod[self.scene_pos]

    def bass1(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.z_mod = np.linspace(self.scene.radius, 0.05, 150)
            self.base_c = self.scene.c
            self.scene.max_iter = 2000
        self.scene.max_iter = 2000 - 800 * self.bass_mod
        self.scene.c = self.base_c - 0.018 * self.kick + 0.1j * self.snare
        if self.scene_pos >= 302:
            self.scene.set_view(radius=self.z_mod[self.scene_pos - 302])

    def tr1(self, frame):
        if self.scene_init:
            self.zoom_mod = self.linspace(self.zoom_mod[-1], 0.5)
            self.scene.max_iter = 2000
        self.scene.c = self.c_mod[-1] - 0.015 * self.kick - 0.54j + 0.05 * self.snare
#        self.scene.max_iter = 2000 + 1500 * self.hat
#        print("Kick", self.kick)

    def intro(self, frame):
        if self.scene_init:
            self.c_mod = self.geomspace((9.17), (0.337))
            self.iter_mod = self.logspace(100, 1000)
            self.zoom_mod = self.linspace(3.5, 1.5)
            self.piano_mod = self.linspace(10, 1)
        self.scene.c = self.c_mod[self.scene_pos] - 0.54j + 0.1 * self.piano * self.piano_mod[self.scene_pos]
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        if frame < 300:
            self.scene.max_iter -= 1500 * self.pitch
        else:
            self.scene.max_iter -= 7000 * self.pitch

    def update(self, frame):
        self.pitch = self.pitch_mod.update(self.spectre)
        try:
            midi_events = self.midi.get(frame)
        except:
            midi_events = []
        for event in midi_events:
            if event["track"] == "SpacePiano1":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.piano = np.max(list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"] == "SpacePiano":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.space_piano = np.max(list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"] == "Redrum 1 copy":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        for pitch in ev["pitch"]:
                            if pitch == 36:
                                self.kick = ev["pitch"][36] / 127
                            elif pitch == 37:
                                self.snare = ev["pitch"][37] / 127
                            elif pitch == 43:
                                self.hat = ev["pitch"][43] / 127
                            else:
                                print("Drum %d : %d" % (pitch, ev["pitch"][pitch]))
                    else:
                        print(ev)
            elif event["track"] == "DirtyBass":
                for ev in event["ev"]:
                    if ev["type"] == "mod" and ev["mod"] == 1:
                        if ev["val"] < self.bass_mod * 127:
                            self.bass_mod -= self.bass_mod / 10
                        else:
                            self.bass_mod = ev["val"] / 127
            else:
                print(event)
        super().update(frame)
        if self.zoom_mod is not None:
            self.scene.set_view(radius=self.zoom_mod[self.scene_pos])

        if self.piano > 0:
            self.piano -= self.piano / 25
        if self.space_piano > 0:
            self.space_piano -= self.space_piano / 50
        if self.kick > 0:
            self.kick -= self.kick / 10
        if self.snare > 0:
            self.snare -= self.snare / 10
        if self.hat > 0:
            self.hat -= self.hat / 10
        self.piano


def main():
    args = usage_cli_complex(worker=1)
    args.midi = "tounex.mid"

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    spectre = SpectroGram(audio.audio_frame_size)
    midi = Midi(args.midi, args.fps)

    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = JuliaSet(args)

    demo = Demo(scene, audio, spectre, midi)

    screen.add(scene)

    frame = args.skip
    paused = False

    # Warm opencl
    scene.render(0)
    audio.play = False
    for skip in range(args.skip):
        audio_buf = audio.get(frame)
        spectre.transform(audio_buf)
        demo.update(skip)
    audio.play = not args.record

    while True:
        if not paused:
            try:
                audio_buf = audio.get(frame)
            except IndexError:
                break

            spectre.transform(audio_buf)

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
            "-c:a", "libvorbis", "-c:v", "libvpx", "-threads", "4",
            "-b:v", "5M",
            "%s/%04d-%s.webm" % (args.record, args.skip, args.anim)
        ]).wait()


if __name__ == "__main__":
    run_main(main)
