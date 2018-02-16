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
import pygame
import time
import numpy as np

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE
from utils_v1.common import usage_cli_complex, run_main, Animation
from utils_v1.pygame_utils import Screen, Window, ComplexPlane
from utils_v1.scipy_utils import Audio, NoAudio
from utils_v1.midi import Midi
from utils_v1.opencl_complex import calc_fractal_opencl


class Demo(Animation):
    def __init__(self, scene, midi, mod):
        self.scenes = [
            [6625, None],
            [6006, self.end],
            [5250, self.intim1],
            [4015, self.bass1],
            [2242, self.tr1],
            [0,    self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.midi = midi
        self.mod = mod

        self.piano = 0
        self.space_piano = 0
        self.kick = 0
        self.hat = 0
        self.snare = 0
        self.bass_mod = 0

        self.zoom_mod = None

    def end(self, frame):
        if self.scene_init:
            self.zoom_mod = self.logspace(0.1, 7)
            self.pow_mod = self.logspace(1, 100)
        self.scene.c -= (0.00001-0.0001j) * self.pow_mod[self.scene_pos]

    def intim1(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
#            self.zoom_mod = self.logspace(0.1, 0.2)
        if self.piano:
            self.snare = 0
            self.base_c += complex(0, 0.00008)
            self.piano = 0
#            self.kick = self.kick / 2
#            self.kick = 0
#        self.base_c += complex(0, 0.00001) * self.piano
        self.scene.c = self.base_c + \
            1e-4 * self.kick + \
            complex(0, 8e-5) * self.snare

    def bass1(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.piano = 0
            self.base_c = self.scene.c
            self.fadeout = self.logspace(0.00951363581679, 0.1, 20)
        if self.piano:
            self.base_c += 1e-7
            self.piano = 0
            self.snare = 0
        self.scene.c = self.base_c + \
            complex(0, 1e-6) * self.kick + \
            complex(-3e-6, 0) * self.snare
        if frame > 5230:
            self.scene.set_view(radius=self.fadeout[frame - 5230])

    def tr1(self, frame):
        if self.scene_init:
            self.zoom_mod = self.logspace(self.base_radius, 0.00951363581679)
            self.pow_mod = self.logspace(1, 500)
            self.base_c = self.scene.c
            self.bass = 0
        if frame < 3000:
            bass = np.max(self.mod.get(frame)) * 3
            if bass > self.bass:
                self.bass += (bass - self.bass) / 5
            else:
                self.bass -= (self.bass - bass) / 10
            self.scene.c = self.base_c + \
                self.pow_mod[self.scene_pos] * 0.1e-12 * self.bass
#            if self.bass > 0:
#                self.bass -= self.bass / 50
        else:
            if self.piano:
                self.base_c += self.pow_mod[self.scene_pos] * 1e-9
                self.piano = 0
                self.snare = self.snare / 10
            self.scene.c = self.base_c + \
                self.pow_mod[self.scene_pos] * complex(0, 1e-9) * self.kick + \
                self.pow_mod[self.scene_pos] * complex(-1e-9, 0) * self.snare

    def intro(self, frame):
        if self.scene_init:
            self.scene.max_iter = 5000
            self.base_c = -0.7488757803975103+0.06927834896471036j
            self.base_radius = 4.02263406465e-05
            self.scene.set_view(radius=self.base_radius)
        if frame == 0:
            self.scene.c = self.base_c
            self.piano = 0
        else:
            if self.piano:
                self.base_c += 3e-12
                self.piano = 0
                self.snare = 0
            snare_effect = -1e-11
            if frame < 1250:
                kick_effect = 8e-12
            else:
                kick_effect = 4e-11
            self.scene.c = self.base_c + \
                complex(0, kick_effect) * self.kick +  \
                complex(snare_effect, 0) * self.snare

    def update(self, frame):
        try:
            midi_events = self.midi.get(frame + 250)
        except Exception:
            midi_events = []
        for event in midi_events:
            if event["track"] == "Intim8" or event["track"] == "tow of us":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.piano = np.max(list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"].startswith("les "):
                print("HEREEE", event)
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.space_piano = np.max(
                            list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"] == "kick":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        for pitch in ev["pitch"]:
                            if pitch == 48:
                                self.kick = ev["pitch"][48] / 127
                            else:
                                print("Drum %d : %d" % (
                                    pitch, ev["pitch"][pitch]))
                    else:
                        print(ev)
            elif event["track"] == "snares":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        for pitch in ev["pitch"]:
                            if pitch == 112:
                                self.snare = ev["pitch"][112] / 127
                            else:
                                print("Snare %d: %d" % (
                                    pitch, ev["pitch"][pitch]))

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


class JuliaSet(Window, ComplexPlane):
    def __init__(self, args):
        Window.__init__(self, args.winsize)
        self.c = args.c
        self.args = args
        self.max_iter = args.max_iter
        self.color = args.color
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame, draw_info=False):
        start_time = time.monotonic()
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        q = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        nparray = calc_fractal_opencl(q, "julia", self.max_iter, self.args,
                                      seed=self.c)
        self.blit(nparray)
        if draw_info:
            self.draw_axis()
            self.draw_function_msg()
            self.draw_cpoint()
        print("%04d: %.2f sec: ./julia_set.py --max_iter '%s' --c '%s' "
              "--center '%s' "
              "--radius %s" % (
                    frame, time.monotonic() - start_time,
                    int(self.max_iter),
                    self.c,
                    self.center, self.radius))


def main():
    args = usage_cli_complex(midi="dirty-muffin.mid")
    args.color = "gradient_freq"
    args.midi_skip = 250

    if not args.audio_mod:
        args.audio_mod = "../render_data/muffin/dirty_muffin-vti_satubass.wav"

    if os.path.isfile(args.audio_mod):
        mod = Audio(args.audio_mod, args.fps, play=False)
    else:
        print("No audio mod")
        mod = NoAudio()

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        print("No audio")
        audio = NoAudio()

    midi = Midi(args.midi, args.fps)

    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = JuliaSet(args)

    demo = Demo(scene, midi, mod)

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
                break

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
