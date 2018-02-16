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

"""Audio spectrogram"""

import argparse
import colorsys
import os
import sys

import numpy as np
import pygame
import pygame.locals
import scipy.io.wavfile


###############################################################################
# FFT code
###############################################################################
class SpectroGram:
    def __init__(self, frame_size):
        self.frame_size = frame_size
        self.fft_window = np.hanning(self.frame_size)
        self.inner_pad = np.zeros(self.frame_size)

    def transform(self, buf):
        mono = np.mean(buf, axis=1)
        windowed = self.fft_window * mono
        padded = np.append(windowed, self.inner_pad)
        spectrum = np.fft.fft(padded) / self.frame_size
        autopower = np.abs(spectrum * np.conj(spectrum)).real
        if (mono == 0).all():
            self.freq = autopower[:self.frame_size//2]
        else:
            dbres = 20 * np.log10(autopower[:self.frame_size//2])
            clipres = np.clip(dbres, -40, 200) * 1 / (8 * 16)
            self.freq = clipres + 0.3125
        self.band = np.copy(self.freq)
        # Clean noise
        self.band[self.band < 0.5] = 0.5
        self.band = np.log10(self.band + 0.5) * 3


###############################################################################
# Pygame abstraction
###############################################################################
class Screen:
    def __init__(self, screen_size):
        pygame.init()
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.screen = pygame.display.set_mode(screen_size)
        self.windows = []

    def capture(self, fname):
        try:
            pygame.image.save(self.screen, fname)
            print("Saved to %s" % fname)
        except Exception as e:
            print(fname, e)
            raise

    def add(self, window, coord=(0, 0)):
        self.windows.append((window, coord))

    def update(self):
        for window, coord in self.windows:
            if window.pixels is not None:
                pygame.surfarray.blit_array(window.surface, window.pixels)
            self.screen.blit(window.surface, coord)
        pygame.display.update()


class Window:
    def __init__(self, window_size):
        self.surface = pygame.Surface(window_size)
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.length = window_size[0] * window_size[1]
        self.size = window_size
        self.pixels = None
        self.draw = False

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def draw_line(self, start_coord, end_coord, color=(28, 28, 28)):
        pygame.draw.line(self.surface, color, start_coord, end_coord)

    def draw_point(self, coord, color=[242]*3):
        self.surface.set_at(coord, color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface, nparray.reshape(*self.size))


class Audio:
    def __init__(self, wav_file, fps=25, play=True):
        freq, wav = scipy.io.wavfile.read(wav_file)
        if freq % fps != 0:
            raise RuntimeError("Can't load wav %d Hz at %d fps" % (freq, fps))
        self.audio_frame_size = freq // fps
        self.audio_frame_number = int(len(wav) / freq * fps)
        self.audio_frames_path = np.linspace(
            0, len(wav), int(len(wav) / freq * fps), endpoint=False, dtype=int)
        if play:
            pygame.mixer.pre_init(
                frequency=freq,
                channels=len(wav[0]),
                buffer=self.audio_frame_size)
            pygame.mixer.init()
            self.chan = pygame.mixer.find_channel()
        self.wav = wav
        self.play = play

    def get(self, frame):
        buf = self.wav[self.audio_frames_path[frame]:
                       self.audio_frames_path[frame] + self.audio_frame_size]
        if self.play:
            self.chan.queue(pygame.sndarray.make_sound(buf))
        return buf


###############################################################################
# Widgets
###############################################################################
def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


class Waterfall(Window):
    def __init__(self, window_size, zoom=1):
        Window.__init__(self, window_size)
        self.zoom = zoom
        self.pixels = np.zeros(self.length, dtype='i4').reshape(*self.size)

    def render(self, spectrogram):
        self.pixels = np.roll(self.pixels, -1, axis=0)
        for y in range(0, self.size[1], self.zoom):
            inv_y = self.size[1] - y - 1
            point = spectrogram.freq[y // self.zoom]
            for suby in range(self.zoom):
                self.pixels[-1][inv_y - suby] = hsv(
                    0.5 + 0.4 * point,
                    0.3 + 0.6 * point,
                    0.2 + 0.7 * point)


class SpectroGraph(Window):
    def __init__(self, window_size, frame_size):
        super().__init__(window_size)
        self.zoom = 1
        self.decay = 10
        self.values = np.zeros(frame_size // 2)
        self.graph_length = min(self.size[0] - self.zoom, frame_size // 2)

    def render(self, spectrogram):
        self.fill(0x00000)
        for x in range(0, self.graph_length, self.zoom):
            freq_pos = x // self.zoom
            val = spectrogram.band[freq_pos]
            if self.values[freq_pos] > val:
                decay = (self.values[freq_pos] - val) / self.decay
                val = self.values[freq_pos] - decay
            self.values[freq_pos] = val
            for subx in range(self.zoom):
                self.draw_line(
                    (x + subx, self.size[1]),
                    (x + subx, self.size[1] - val * self.size[1]),
                    0xfafafa
                    )


###############################################################################
# Main code
###############################################################################
def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 10)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--wav", required=True, metavar="FILE",
                        help="A wav file")
    parser.add_argument("--skip", type=int, default=0,
                        help="Frame to skip")
    parser.add_argument("--fps", type=int, default=25,
                        help="Frame per seconds")
    args = parser.parse_args(argv)
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    return args


def main():
    args = usage()
    audio = Audio(args.wav, args.fps, play=True)
    clock = pygame.time.Clock()
    screen = Screen(args.winsize)
    spectre = SpectroGram(audio.audio_frame_size)

    x, y = args.winsize
    waterfall = Waterfall((x, y//2))
    graph = SpectroGraph((x, y//2), audio.audio_frame_size)
    screen.add(waterfall)
    screen.add(graph, (0, y//2))
    frame = args.skip
    paused = False
    while True:
        if not paused:
            if frame % args.fps == 0:
                print("\rpos: %3d" % (frame // args.fps), end='')
            audio_buf = audio.get(frame)

            spectre.transform(audio_buf)
            graph.render(spectre)
            waterfall.render(spectre)
            screen.update()
            frame += 1

        for e in pygame.event.get():
            if e.type == pygame.locals.MOUSEBUTTONDOWN:
                print("Clicked", e.pos)
            elif e.type == pygame.locals.KEYDOWN:
                if e.key == pygame.locals.K_RIGHT:
                    frame += args.fps * 5
                elif e.key == pygame.locals.K_p:
                    screen.capture("./spectrogram.png")
                elif e.key == pygame.locals.K_LEFT:
                    frame = max(0, frame - args.fps * 5)
                elif e.key == pygame.locals.K_UP:
                    frame += args.fps * 60
                elif e.key == pygame.locals.K_DOWN:
                    frame = max(0, frame - args.fps * 60)
                elif e.key == pygame.locals.K_SPACE:
                    paused = not paused
                elif e.key == pygame.locals.K_ESCAPE:
                    exit(0)

        clock.tick(args.fps)


if __name__ == "__main__":
    main()
