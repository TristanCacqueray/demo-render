#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import sys
import pygame
import numpy as np

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
            [4180, None],
            [3899, self.end],
            [3000, self.bass3],
            [2399, self.slow],
            [2099, self.brk],
            [1200, self.bass2],
            [599,  self.bass1],
            [584,  self.zoom],
            [299,  self.intro2],
            [0,    self.intro1],
        ]
        super().__init__()
        self.scene = scene
        self.midi = midi

        self.piano = 0
        self.kick = 0
        self.bells = 0
        self.snare = 0
        self.bass_mod = 0

    def end(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(self.scene.radius, 3)
            self.i_mod = self.logspace(self.scene.max_iter, 100)

        self.scene.c -= (1e-4-1e-5j) * self.r_mod[self.scene_pos]
        self.scene.set_view(radius=self.r_mod[self.scene_pos])
        self.scene.max_iter = self.i_mod[self.scene_pos]

    def bass3(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.scene.max_iter = 20000

        if self.piano:
            self.base_c -= 1.1e-9 * self.piano
        if frame < 3599:
            bell_fx = 0.7
        else:
            bell_fx = -7.5
        if self.bells:
            self.base_c += 2e-10 * self.bells * bell_fx
#            self.bells = 0
        self.scene.c = self.base_c \
        - 3e-11j * self.kick + 4e-11j * self.snare
#        self.scene.max_iter = self.base_iter + 10000 * self.bass_mod
        self.scene.max_iter = self.base_iter - 5000 * self.bass_mod

    def slow(self, frame):
        if self.scene_init:
            self.base_c = (-1.4185605664579781+8.601365142247895e-11j)
            self.scene.set_view(radius=2.00225830078e-05)
            self.base_iter = 20000
            self.bass_mod = 1
            self.r_mod = self.logspace(self.scene.radius, 1e-04)

        if self.piano:
            self.base_c -= 1e-11 * self.piano
            self.piano -= self.piano / 3

        self.scene.max_iter = self.base_iter - 5000 * self.bass_mod
        if frame < 2700:
            fx = 1
        else:
            fx = 2
        self.scene.c = self.base_c + \
            1.5e-11j * self.kick * fx + \
            1.5e-10 * self.snare * fx
        self.scene.set_view(radius=self.r_mod[self.scene_pos])

    def brk(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
            self.base_iter = self.scene.max_iter
            self.c_mod = self.geomspace(self.scene.c, -1.4220841573466878+1.6654664112925148e-09j)
            self.r_mod = self.logspace(self.scene.radius, 1.50338936364e-05, self.scene_length - 10)
            self.r2_mod = self.logspace(1.50338936364e-05,1.50338936364e-06 ,10)

#        self.scene.max_iter = self.base_iter - 10000 * self.bass_mod
        if self.bells:
            self.base_c -= 1e-6 * self.bells
            self.bells = 0

        self.scene.c = self.c_mod[self.scene_pos]
        if self.scene_pos < (self.scene_length - 10):
            self.scene.set_view(radius=self.r_mod[self.scene_pos])
        else:
            self.scene.set_view(radius=self.r2_mod[
                self.scene_pos - self.scene_length])

    def bass2(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(self.scene.radius, 0.0002)
            self.base_c = -1.422084165770339+9.592066707536862e-11j
            self.base_c = -1.4220841653189504+8.601365142247895e-11j
            self.base_iter = self.scene.max_iter
        if self.piano:
            self.base_c += 1e-9
            self.piano = 0
        if self.bells:
            self.base_c += 1e-9
            self.bells = 0
        self.scene.c = self.base_c + 6e-10 * self.kick #- 1e-9 * self.snare
        self.scene.set_view(radius=self.r_mod[self.scene_pos])
        self.scene.max_iter = self.base_iter - 10000 * self.bass_mod

    def bass1(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(0.001, 0.0005)
            self.base_c = (-1.4220841661210148+8.470329472543003e-22j)
            self.base_iter = self.scene.max_iter

        if self.piano:
            self.base_c += 1e-9
            self.piano = 0
        self.scene.c = self.base_c - 2e-9 * self.kick + 2e-10j * self.snare
        self.scene.set_view(radius=self.r_mod[self.scene_pos])
        self.scene.max_iter = self.base_iter + 10000 * self.bass_mod


    def zoom(self, frame):
        if self.scene_init:
            self.r_mod = self.linspace(self.scene.radius, 1)
            self.c_mod = self.linspace(self.scene.c.real,
                                       -1.4220841661210148)
        self.scene.set_view(radius=self.r_mod[self.scene_pos])
        self.scene.c = complex(self.c_mod[self.scene_pos], self.scene.c.imag)

    def intro2(self, frame):
        if self.scene_init:
#            self.i_mod = self.logspace(self.scene.max_iter, 1000)
             self.i_mod = self.linspace(self.scene.c.imag,
                                        8.470329472543003e-22)
             self.base_c = self.scene.c.real

        if self.piano:
            self.base_c += 4.1 * self.piano * self.m_mod[self.scene_pos + 299]

#        self.scene.max_iter = self.i_mod[self.scene_pos]
#        self.scene.set_view(radius=self.r_mod[self.scene_pos])
        self.scene.c = complex(self.base_c, self.i_mod[self.scene_pos])
        self.scene.set_view(radius=self.r_mod[self.scene_pos+299])
        self.scene.max_iter = self.iter_mod[self.scene_pos+299]

    def intro1(self, frame):
        if self.scene_init:
            self.base_c = -1.722084166121015-5.466666666666666j
            self.r_mod = self.logspace(3, 0.1, 584)
            self.m_mod = self.logspace(1, 0.00001, 600)
            self.iter_mod = self.logspace(50, 10000, 600)
        if self.piano:
            self.base_c += 0.38j * self.piano * self.m_mod[self.scene_pos]
        self.scene.c = self.base_c
        self.scene.max_iter = self.iter_mod[self.scene_pos]
        self.scene.set_view(radius=self.r_mod[self.scene_pos])

    def update(self, frame):
        try:
            midi_events = self.midi.get(frame)
        except Exception:
            midi_events = []
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
                    if ev["type"] == "mod" and frame not in (871, 1499, 1501, 3004):
                        self.bass_mod = (127 - ev["val"]) / 127.0
            print(event)

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


def main():
    args = usage_cli_complex(gradient="fatou.ggr")
    args.midi = "fatou.mid"

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()

    midi = Midi(args.midi, args.fps)

    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = BurningJuliaSet(args)

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


if __name__ == "__main__":
    run_main(main)
