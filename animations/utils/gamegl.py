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
import time
import os
import numpy as np
from PIL import Image

from glumpy import app, gl
from glumpy.app.window import key
from glumpy.app.window.event import EventDispatcher

from . audio import Audio, NoAudio
from . midi import Midi, NoMidi


class Window(EventDispatcher):
    alive = True
    draw = True

    def __init__(self, winsize, screen, demo, record):
        self.winsize = winsize
        self.window = screen
        self.demo = demo
        self.params = demo.params
        self.dorecord = record
        self.init_program()
        self.fbuffer = np.zeros(
            (self.window.height, self.window.width * 3), dtype=np.uint8)

    def capture(self, filename):
        gl.glReadPixels(
            0, 0, self.window.width, self.window.height,
            gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.fbuffer)
        image = Image.frombytes("RGB", self.winsize, self.fbuffer)
        image.save(filename, 'png')

    def on_draw(self, dt):
        pass

    def on_resize(self, width, height):
        print("on_resize!")

    def on_key_press(self, k, modifiers):
        if k == key.ESCAPE:
            self.alive = False
        elif k == key.SPACE:
            self.demo.paused = not self.demo.paused
        self.draw = True


def usage():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paused", action='store_true')
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--wav", metavar="FILE")
    parser.add_argument("--midi", metavar="FILE")
    parser.add_argument("--midi_skip", type=int, default=0)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--skip", default=0, type=int, metavar="FRAMES_NUMBER")
    parser.add_argument("--size", type=float, default=8,
                        help="render size")
    args = parser.parse_args()
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.map_size = list(map(lambda x: x//5, args.winsize))
    return args


def run_main(demo, Scene):
    args = usage()
    screen = app.Window(width=args.winsize[0], height=args.winsize[1])
    scene = Scene(args.winsize, screen, demo, args.record)
    screen.attach(scene)

    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    demo.setAudio(audio)

    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = NoMidi()
    demo.setMidi(midi, args.midi_skip)
    demo.set(screen, scene)

    import pygame
    pygame.init()
    scene.render(0)
    audio.play = False
    demo.silent = True
    for skip in range(args.skip):
        demo.update(skip)
    demo.silent = False
    audio.play = not args.record
    demo.update_sliders()

    scene.alive = True

    if args.paused:
        demo.paused = True
        args.paused = False

    frame = args.skip
    while scene.alive:
        start_time = time.monotonic()
        demo.update(frame)

        if not demo.paused:
            frame += 1
        if scene.render(frame):
            print("%04d: %.2f sec '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(demo.get(), sort_keys=True)))

        if args.record:
            scene.capture(os.path.join(args.record, "%04d.png" % frame))

        backend.process(clock.tick())

    if args.record:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/render.mp4" % (args.record)]
        print("Running: %s" % " ".join(cmd))
        subprocess.Popen(cmd).wait()
