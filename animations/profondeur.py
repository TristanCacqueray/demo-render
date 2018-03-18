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
            [5800, None],
            [5575, self.end],
            [4240, self.main2],
            [3100, self.main],
            [2875, self.brk],
            [1400, self.intro3],
            [840, self.intro2],
            [0,     self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.m = 0
        self.low = ColorMod((1, 1), (4, 8), "mean")
        self.hgh = ColorMod((1, 1), (89, 120), "mean", threshold=0.4)
        self.mid = ColorMod((1, 1), (160, 180), "avg", threshold=0.1)
        self.low_mod = 0
        self.mid_mod = 0
        self.hgh_mod = 0
        self.prev_mod = 0

    def end(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 2061776)
            self.base_c = self.scene.c
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.scene.c = self.base_c + 1e-1 * self.mid_mod + 1e-2j * self.low_mod


    def main2(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
        if self.mid_mod > 0.1:
            self.base_c += 1e-3 * self.mid_mod
        self.scene.c = self.base_c - 1e-1j * self.hgh_mod
#        self.freq_mod[-1] += 2e-3
        self.scene.args.gradient_frequency = self.freq_mod[-1] + 0.2 * self.low_mod

    def main(self, frame):
        if self.low_mod > 0.2:
            self.base_c -= 2.5e-4 * self.low_mod
        self.scene.c = self.base_c + 5e-1j * self.mid_mod
        self.scene.args.gradient_frequency = self.freq_mod[-1] + 1 * self.hgh_mod

    def brk(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 53083)
        self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.scene.args.gradient_frequency = self.freq_mod[-1] + 2 * self.hgh_mod

    def intro3(self, frame):
        if self.scene_init:
            self.rad_mod = self.logspace(self.scene.radius, 3972306)
            self.freq_mod = self.linspace(self.scene.args.gradient_frequency,
                                          3.6)
        if self.scene_length - self.scene_pos > 20:
            self.scene.set_view(radius=self.rad_mod[self.scene_pos])
        self.scene.args.gradient_frequency = self.freq_mod[self.scene_pos]
        self.base_c -= 2e-3j * self.low_mod
        self.scene.c = self.base_c + 1e-2j * self.mid_mod

    def intro2(self, frame):
        if self.scene_init:
            self.base_freq = self.scene.args.gradient_frequency
        self.base_c += 1e-3j * self.low_mod
        self.scene.c = self.base_c
#        self.base_freq += 5e-3 * self.low_mod
        self.scene.args.gradient_frequency = self.base_freq


    def intro(self, frame):
        if self.scene_init:
            self.base_c = 0.3938888888888892-1.3455802469135802j
            self.scene.set_view(radius=2242)
            self.scene.max_iter = 100
            self.base_freq = 3.2
#            self.freq_mod = self.logspace(self.base_freq, 3.9)
        if self.low_mod > 0.4:
            self.base_c -= 1e-3 * self.low_mod
        self.base_freq -= 5e-4
        self.scene.c = self.base_c - 1e-2 * self.mid_mod - 1e-1j * self.hgh_mod
        self.scene.args.gradient_frequency = self.base_freq \
          - 2 * self.mid_mod

    def update(self, frame, spectrogram):
        hgh_mod = self.hgh.get(spectrogram)
        if hgh_mod > self.hgh_mod:
            self.hgh_mod += (hgh_mod - self.hgh_mod) / 7.
        else:
            self.hgh_mod -= (self.hgh_mod - hgh_mod) / 7.

        self.low_mod = self.low.get(spectrogram)

        mid_mod = self.mid.get(spectrogram)
        if mid_mod > self.mid_mod:
            self.mid_mod += (mid_mod - self.mid_mod) / 10.
        else:
            self.mid_mod -= (self.mid_mod - mid_mod) / 50.

        super().update(frame)


def main():
    args = usage_cli_complex(gradient="profondeur.ggr")
    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()

    spectre = SpectroGram(audio.audio_frame_size)
    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = BurningJuliaSet(args, "powduck")

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
