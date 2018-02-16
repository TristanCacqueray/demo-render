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

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE

from utils_v2.common import usage_cli_complex, run_main, Animation
from utils_v2.pygame_utils import ColorMod
from utils_v2.scipy_utils import Audio, NoAudio, SpectroGram
from utils_v2.pygame_utils import Screen
from utils_v2.burning_julia import BurningJuliaSet


class Demo(Animation):
    def __init__(self, scene):
        self.scenes = [
            [6792, None],
            [5990, self.end],
            [4900,  self.kick3],
            [4515,  self.brk2],
            [4060,  self.bass],
            [3019,  self.kick2],
            [2415,  self.brk],
            [1819,  self.kick],
            [1219,  self.p1],
            [620,   self.zoom],
            [0,     self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.m = 0
        self.hgh = ColorMod((1, 1), (80, 200), "high", threshold=0.1)
        self.mid = ColorMod((1, 1), (190, 300), "avg", threshold=0.1)
        self.low = ColorMod((1, 1), (0, 100), "mean", threshold=0.1)

    def end(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 1)
            self.pow_mod = self.logspace(1000000, 1)
            self.base_c = self.scene.c
        self.base_c -= 5e-10 * self.rad_mod[self.scene_pos] * self.hgh_mod * self.pow_mod[self.scene_length - self.scene_pos - 1]
        self.scene.c = self.base_c + 1e-6 * self.rad_mod[self.scene_pos] * self.low_mod * self.pow_mod[self.scene_length - self.scene_pos - 1]
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])

    def kick3(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.iter_mod = self.logspace(self.scene.max_iter, 2000)
#        self.scene.max_iter = self.iter_mod[self.scene_pos]
        self.base_c += 1e-14j * self.hgh_mod
        self.scene.c = self.base_c + 1e-12j * self.mid_mod

    def brk2(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.iter_mod = self.logspace(self.scene.max_iter - 564, 3500)
            self.rad_mod = self.logspace(self.scene.radius, 1e-6)
            self.pow_mod = self.logspace(1, 1e-8)
        self.scene.max_iter = self.iter_mod[self.scene_pos] + 600 * self.hgh_mod
        self.base_c += 4.4775e-5j * self.low_mod * self.pow_mod[self.scene_pos]
        self.scene.c = self.base_c + 1e-5 * self.low_mod * self.pow_mod[self.scene_pos]
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])

    def bass(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.iter_mod = self.logspace(self.scene.max_iter, 2000)
            self.rad_mod = self.logspace(self.scene.radius, 0.02, self.scene_length - 200)
        self.base_c -= 1e-6j * self.hgh_mod
        self.scene.c = self.base_c - 1e-5 * self.mid_mod #- 1e-3 * self.mid_mod
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        if self.scene_pos < self.scene_length - 200:
            self.scene.set_view(radius=self.rad_mod[self.scene_pos])


    def kick2(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.iter_mod = self.logspace(self.scene.max_iter, 1000)
        self.scene.max_iter = self.iter_mod[self.scene_pos] #+ 200 * self.hgh_mod
        self.base_c += 1e-7j * self.hgh_mod
        self.scene.c = self.base_c - 1e-6 * self.low_mod - 1e-5 * self.mid_mod

    def brk(self, frame):
        if self.scene_init:
            self.base_radius = self.scene.radius
            self.rad_mod = self.logspace(self.scene.radius, 0.002)
            self.base_iter = self.scene.max_iter
            self.iter_mod = self.linspace(self.scene.max_iter, 1000)
            self.base_c = self.scene.c

        self.base_c += 3e-13
        self.scene.c = self.base_c
        self.base_radius -= 1e-6 * self.hgh_mod
        self.scene.max_iter = self.iter_mod[self.scene_pos] - 200 * self.hgh_mod
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])

    def kick(self, frame):
        if self.scene_init:
            self.iter_mod = self.logspace(self.scene.max_iter, 1700)
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        self.base_c += 2e-13
        self.scene.c = self.base_c - 1e-10j * self.low_mod + 5e-11 * self.mid_mod

    def p1(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.iter_mod = self.logspace(self.scene.max_iter, 1800)

        self.scene.max_iter = self.iter_mod[self.scene_pos]

        self.base_c -= (1e-13+1e-12j) * self.low_mod
        self.scene.c = self.base_c + 1e-10j * self.low_mod

    def zoom(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 1e-5)
#            self.base_c = self.scene.c
        self.scene.c = self.base_c - 1e-3j * self.low_mod * self.rad_mod[self.scene_pos]
        self.scene.max_iter = self.base_iter + 1000 * self.mid_mod
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])

    def intro(self, frame):
        if self.scene_init:
            self.base_c = -1.7107802103169505+0.001469444644572093j
            self.base_c = -1.71073318821-0.0113388787725j
            self.base_c = -1.71073318821-0.0113388786136j
            self.base_radius = 0.025508404546
            self.base_radius = 0.000678823472683
            self.scene.set_view(radius=self.base_radius)
            self.base_iter = 1000
            self.prev_hgh = 0
            self.rad_mod = self.logspace(1, 0.002) #, 300)
#        if self.hgh_mod:
#            self.base_iter += 100 * self.hgh_mod
#            self.base_c -= 0.0000014j * self.hgh_mod
#        self.scene.c = self.base_c + 0.00001 * self.mid_mod + 0.000001j * self.low_mod
        if frame < 1300:
            self.scene.set_view(radius=self.rad_mod[self.scene_pos])
            pow_mod = frame
        else:
            pow_mod = 299
        self.scene.c = self.base_c + 1e-2 * self.low_mod * self.rad_mod[pow_mod]
        self.scene.max_iter = self.base_iter + 1000 * self.mid_mod

    def update(self, frame, spectrogram):
        self.hgh_mod = self.hgh.get(spectrogram)
        self.mid_mod = self.mid.get(spectrogram)
        self.low_mod = self.low.get(spectrogram)
        super().update(frame)


def main():
    args = usage_cli_complex(gradient="ggb.ggr")

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()

    spectre = SpectroGram(audio.audio_frame_size)
    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = BurningJuliaSet(args)

    demo = Demo(scene)

    screen.add(scene)

    frame = args.skip
    paused = False

    # Warm opencl
    scene.render(0)
    audio.play = False
    for skip in range(args.skip):
        audio_buf = audio.get(skip)
        spectre.transform(audio_buf)
        demo.update(skip, spectre)
    audio.play = not args.record

    while True:
        if not paused:
            try:
                audio_buf = audio.get(frame)
                spectre.transform(audio_buf)
            except IndexError:
                audio_buf = 0

            try:
                demo.update(frame, spectre)
            except ValueError:
                break

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


if __name__ == "__main__":
    run_main(main)
