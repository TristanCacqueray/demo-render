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
import cmath
import math
import colorsys
import os
import sys
import numpy as np


# Raw color
def rgb(r, g, b):
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def rgb250(r, g, b):
    return int(b) | int(g) << 8 | int(r) << 16


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def grayscale(r):
    return int(r * 0xff) | int((r * 0xff)) << 8 | int(r * 0xff) << 16


def dark_color_factory(scale, dummy):
    def dark_color(x):
        if x == scale:
            return 0
        return hsv(0.6 + 0.4 * x / (2 * scale), 0.7, 0.5)
    return dark_color


def bright_color_factory(scale, base_hue=0.4):
    def bright_color(x):
        if x == scale:
            return 0
        return hsv(base_hue + x / scale, 0.7, 0.7)
    return bright_color


def grayscale_color_factory(scale):
    def grayscale_color(x):
        if x == scale:
            return 0
        return grayscale(x / scale)
    return grayscale_color


def log_sin_lightblue(scale, base=1):
    def color_func(x, y, z):
        if x == 0: # or x == scale:
            return 0
        rlog = abs(math.sin(math.log(math.pow(x + 50, 7))))
        glog = abs(math.sin(math.log(math.pow(x + 50, 7))))
        blog = abs(math.sin(math.log(math.pow(x + 150, 7))))
        return rgb250(10 + 150 * rlog, 40 + 150 * glog, 100 + 150 * blog * base)
    return color_func


def log_sin_lightpurple(scale):
    def color_func(x):
        if x == 0 or x == scale:
            return 0
#        x = np.exp(1j*(i + 1 - np.log(np.log(abs(z)))/np.log(2)))
        rlog = abs(math.sin(math.log(math.pow(x + 50, 2))))
        glog = abs(math.sin(math.log(math.pow(x + 50, 2))))
        blog = abs(math.sin(math.log(math.pow(x + 150, 4))))
        return rgb250(100 + 100 * rlog, 40 + 120 * glog, 60 + 150 * blog)
    return color_func


def gradient(scale):
    color_map = np.zeros(scale, dtype='uint32')

    def gaussian(x, a, b, c, d=0):
        return a * math.exp(-(x - b)**2 / (2 * c**2)) + d
    for x in range(scale):
        r = int(gaussian(x, 158.8242, 201, 87.0739) +
                gaussian(x, 158.8242, 402, 87.0739))
        g = int(gaussian(x, 129.9851, 157.7571, 108.0298) +
                gaussian(x, 200.6831, 399.4535, 143.6828))
        b = int(gaussian(x, 231.3135, 206.4774, 201.5447) +
                gaussian(x, 17.1017, 395.8819, 39.3148))
        color_map[x] = rgb250(r, g, b)

    def color_func(x):
        return color_map[x]
    return color_func


def gradient2(scale):
    def color_func(x):
        if x == scale - 1 or x == scale - 2 or x == 0:
            return 0
        return hsv(0.6 + (x / scale) * 0.2,
                   (1 - (x / scale) * 0.5),
                   (1 - (x / scale) * 0.5))
    return color_func


ColorMap = {
    'gradient': gradient,
    'bright': bright_color_factory,
    'grayscale': grayscale_color_factory,
    'log+sin+lightblue': log_sin_lightblue,
    'log+sin+lightpurple': log_sin_lightpurple,
}

# Basic maths
MAX_SHORT = float((2 ** (2 * 8)) // 2)
PHI = (1+math.sqrt(5))/2.0


def rotate_point(point, angle):
    return complex(point[0] * math.cos(angle) - point[1] * math.sin(angle),
                   point[0] * math.sin(angle) + point[1] * math.cos(angle))


# CLI usage
def usage_cli_complex(argv=sys.argv[1:], center=0j, radius=3., c=0, seed='',
                      gradient="/usr/share/gimp/2.0/gradients/Purples.ggr"):
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true')
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--video", action='store_true')
    parser.add_argument("--frame_start", type=int, default=0)
    parser.add_argument("--wav", metavar="FILE")
    parser.add_argument("--audio_mod", metavar="FILE")
    parser.add_argument("--midi", metavar="FILE")
    parser.add_argument("--midi_skip", type=int, default=0)
    parser.add_argument("--play", action='store_true')
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--skip", default=0, type=int, metavar="FRAMES_NUMBER")
    parser.add_argument("--gradient", metavar="FILE",
                        default=os.environ.get("GRADIENT", gradient))
    parser.add_argument("--gradient_frequency", default=1)
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 2.5)),
                        help="render size (2.5)")
    parser.add_argument("--center", type=complex, default=center,
                        help="plane center(%s)" % center)
    parser.add_argument("--radius", type=float, default=radius,
                        help="plane radius (%s)" % radius)
    parser.add_argument("--sub-radius", type=float,
                        help="radius of sub rendering")
    parser.add_argument("--seed", type=str, default=seed,
                        help="str seed")
    parser.add_argument("--color_mod", default="smooth_escape")
    parser.add_argument("--color", default=os.environ.get("COLOR", "gradient"))
    parser.add_argument("--antialias", default=1, type=int)
    parser.add_argument("--max_iter", type=int,
                        default=int(os.environ.get("MAX_ITER", 256)))
    parser.add_argument("--c", type=complex, default=c,
                        help="complex seed (%s)" % c)
    parser.add_argument("--opencl", action="store_const", const=True,
                        default=bool(os.environ.get("OPENCL", False)))
    parser.add_argument("--sampling", type=int, default=1)
    args = parser.parse_args(argv)
    args.mod = 1
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.length = args.winsize[0] * args.winsize[1]
    args.pids = set()
    args.center = np.complex128(args.center)
    args.radius = np.float64(args.radius)
    args.pool = None
    if args.gradient.endswith(".ggr"):
        from . ggr import GimpGradient
        args.gradient = GimpGradient(args.gradient)
    return args


def run_main(main):
    try:
        main()
    except KeyboardInterrupt:
        pass
    if args.pool:
        args.pool.terminate()
        args.pool.join()
        del args.pool
    for pid in args.pids:
        pid.terminate()


class ComplexPlane:
    def set_view(self, center=None, radius=None):
        if center is not None:
            self.center = center
        if radius is not None:
            if radius == 0:
                raise RuntimeError("Radius can't be null")
            self.radius = radius
        self.plane_min = (self.center.real - self.radius,
                          self.center.imag - self.radius)
        self.plane_max = (self.center.real + self.radius,
                          self.center.imag + self.radius)
        # Coordinate conversion vector
        self.offset = (self.plane_min[0], self.plane_min[1])
        self.scale = (
            self.window_size[0] / float(self.plane_max[0] - self.plane_min[0]),
            self.window_size[1] / float(self.plane_max[1] - self.plane_min[1])
        )

    def compute_chunks(self, method, params):
        params = [self.window_size, self.offset, self.scale,
                  self.args.sampling] + params + [self.length]
        if self.args.worker >= 2:
            # Divide image length by number of worker
            params[-1] //= self.args.worker
            # Append chunk position
            params = list(map(lambda x: params + [x], range(self.args.worker)))
            # Compute
            res = self.args.pool.map(method, params)
            # Return flatten array
            return np.array(res).flatten()
        # Mono process just compute first chunk
        return method(params + [0])

    def convert_to_plane(self, screen_coord):
        return complex(
            screen_coord[0] / self.scale[0] + self.offset[0],
            screen_coord[1] / self.scale[1] + self.offset[1]
        )

    def convert_to_screen(self, plane_coord):
        return [
            int((plane_coord.real - self.offset[0]) * self.scale[0]),
            int((plane_coord.imag - self.offset[1]) * self.scale[1])
        ]

    def draw_complex(self, complex_coord, color=[242]*3):
        self.draw_point(self.convert_to_screen(complex_coord), color)

    def draw_axis(self, axis_color=(28, 28, 28)):
        center_coord = self.convert_to_screen(0j)
        self.draw_line(
            (center_coord[0], 0),
            (center_coord[0], self.window_size[1]),
            color=axis_color)
        self.draw_line(
            (0, center_coord[1]),
            (self.window_size[0], center_coord[1]),
            color=axis_color)


# Animation helpers
class Animation:
    def __init__(self):
        # Insert scene length
        for idx in range(1, len(self.scenes)):
            length = self.scenes[idx - 1][0] - self.scenes[idx][0]
            self.scenes[idx].insert(1, length)

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
        for idx in range(len(self.scenes)):
            if frame >= self.scenes[idx][0]:
                self.scene_start, self.scene_length, func = self.scenes[idx]
                self.scene_pos = frame - self.scene_start
                self.scene_init = self.scene_pos == 0
                break
        if idx == len(self.scenes):
            raise RuntimeError("Couldn't find scene for frame %d" % frame)
        func(frame)
        #return func.func_name


# Modulation
class Path:
    def __init__(self, points, size):
        self.points = points
        self.size = size
        self.len_pairs = float(len(points) - 1)
        self.xpath = np.array(list(map(lambda x: x.__getattribute__("real"),
                                  self.points)))
        self.ypath = np.array(list(map(lambda x: x.__getattribute__("imag"),
                                  self.points)))

    def points_pairs(self):
        for idx in range(len(self.points) - 1):
            yield (self.points[idx], self.points[idx + 1])

    def logs(self):
        path = []
        for a, b in self.points_pairs():
            for point in np.logspace(np.log10(a), np.log10(b),
                                     self.size // self.len_pairs):
                path.append(point)
        return path

    def gen_logs(self):
        logs = self.logs()
        for c in logs:
            yield c

    def lines(self):
        path = []
        for a, b in self.points_pairs():
            for point in np.linspace(a, b, self.size / self.len_pairs):
                path.append(point)
        return path

    def gen_lines(self):
        path = self.lines()
        for c in path:
            yield c

    def sin(self, factor=0.23, cycles=1, sign=1, maxy=1.0):
        path = []
        for a, b in self.points_pairs():
            idx = 0
            angle = cmath.phase(b - a)
            distance = cmath.polar(b - a)[0]
            sinx = np.linspace(0, distance, self.size / self.len_pairs)
            siny = list(map(lambda x: sign * maxy * math.sin(
                cycles * x * math.pi / float(distance)), sinx))
            for idx in range(int(self.size // self.len_pairs)):
                p = (sinx[idx], siny[idx] * factor)
                path.append(a + rotate_point(p, angle))
        return path

    def gen_sin(self, factor=0.23, cycles=1, sign=1, maxy=1.0):
        path = self.sin(factor, cycles, sign, maxy)
        for c in path:
            yield c

    def splines(self):
        try:
            import scipy.interpolate
        except ImportError:
            return []
        path = []
        t = np.arange(self.xpath.shape[0], dtype=float)
        t /= t[-1]
        nt = np.linspace(0, 1, self.size)
        x1 = scipy.interpolate.spline(t, self.xpath, nt)
        y1 = scipy.interpolate.spline(t, self.ypath, nt)
        for pos in range(len(nt)):
            path.append(complex(x1[pos], y1[pos]))
        return path

    def gen_splines(self):
        path = self.splines()
        for c in path:
            yield c
