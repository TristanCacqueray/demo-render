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

import argparse
import json
import os
import time

import numpy as np

from . import game
from . audio import Audio, NoAudio
from . controller import Controller
from . fractal import Fractal
from . midi import Midi, NoMidi


def usage():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--wav", metavar="FILE")
    parser.add_argument("--midi", metavar="FILE")
    parser.add_argument("--midi_skip", type=int, default=0)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--skip", default=0, type=int, metavar="FRAMES_NUMBER")
    parser.add_argument("--size", type=float, default=2.5,
                        help="render size (2.5)")
    parser.add_argument("--super-sampling", type=int,
                        help="super sampling mode")
    args = parser.parse_args()
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.map_size = list(map(lambda x: x//5, args.winsize))
    args.length = args.winsize[0] * args.winsize[1]
    return args


class Animation(Controller):
    def __init__(self, params):
        # Insert scene length
        for idx in range(1, len(self.scenes)):
            length = self.scenes[idx - 1][0] - self.scenes[idx][0]
            self.scenes[idx].insert(1, length)
        self.end_frame = self.scenes[0][0]
        super().__init__(params)

    def setAudio(self, audio):
        self.audio = audio

    def updateAudio(self, audio_buf):
        pass

    def setMidi(self, midi):
        self.midi = midi

    def updateMidi(self, midi_events):
        pass

    def geomspace(self, start, end):
        return np.geomspace(start, end, self.scene_length)

    def logspace(self, start, end, length=None):
        if length is None:
            length = self.scene_length
        return np.logspace(np.log10(start), np.log10(end), length)

    def linspace(self, start, end, length=None):
        if length is None:
            length = self.scene_length
        return np.linspace(start, end, length)

    def update(self, frame):
        if not self.paused:
            try:
                audio_buf = self.audio.get(frame)
                self.updateAudio(audio_buf)
            except IndexError:
                pass
            try:
                midi_events = self.midi.get(frame)
                self.updateMidi(midi_events)
            except IndexError:
                pass
            self.scene.draw = True
        if frame >= self.end_frame:
            self.scene.alive = False
            return
        for idx in range(len(self.scenes)):
            if frame >= self.scenes[idx][0]:
                self.scene_start, self.scene_length, func = self.scenes[idx]
                self.scene_pos = frame - self.scene_start
                self.scene_init = self.scene_pos == 0
                break
        if idx == len(self.scenes):
            raise RuntimeError("Couldn't find scene for frame %d" % frame)
        func(frame)
        super().update(frame)


def run_main(demo, Scene=Fractal):
    args = usage()

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    demo.setAudio(audio)

    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = NoMidi()
    demo.setMidi(midi)

    if args.super_sampling:
        demo.params["super_sampling"] = args.super_sampling

    demo.map_size = args.map_size

    clock = game.clock()

    screen = game.Screen(args.winsize)
    scene = Scene(args.winsize, demo.params)
    screen.add(scene)

    demo.set(screen, scene)

    frame = args.skip

    # Warm opencl
    scene.render(0)
    audio.play = False
    for skip in range(args.skip):
        demo.update(skip)
    audio.play = not args.record

    while True and scene.alive:
        start_time = time.monotonic()
        demo.update(frame)
        if not demo.paused:
            frame += 1
        if scene.render(frame):
            screen.update()
            if args.record:
                screen.capture(os.path.join(args.record, "%04d.png" % frame))
            print("%04d: %.2f sec '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(demo.get(), sort_keys=True)))

        if not args.record:
            clock.tick(args.fps)

    if args.record:
        import subprocess
        subprocess.Popen([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-start_number", str(args.skip),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/%04d-render.mp4" % (args.record, args.skip)
        ]).wait()
