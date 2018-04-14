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

import colorsys
import io
import math


class Gradient:
    multi_gradients = False

    def to_array(self, length):
        colors_array = []
        for idx in range(length):
            colors_array.append(str(self.color(idx / length)))
        return ",".join(colors_array)


class GimpGradient(Gradient):
    """ Read and interpret a Gimp .ggr gradient file.
        Code adapted from https://nedbatchelder.com/code/modules/ggr.html
    """
    def __init__(self, f=None):
        if f:
            self.read(f)

    class _segment:
        pass

    def read(self, f):
        """ Read a .ggr file from f (either an open file or a file path)."""
        if isinstance(f, str):
            f = open(f)
        if f.readline().strip() != "GIMP Gradient":
            raise Exception("Not a GIMP gradient file")
        line = f.readline().strip()
        if not line.startswith("Name: "):
            raise Exception("Not a GIMP gradient file")
        self.name = line.split(": ", 1)[1]
        nsegs = int(f.readline().strip())
        self.segs = []
        for i in range(nsegs):
            line = f.readline().strip()
            seg = self._segment()
            (seg.k, seg.m, seg.r,
                seg.rl, seg.gl, seg.bl, _,
                seg.rr, seg.gr, seg.br, _,
                seg.fn, seg.space) = map(float, line.split()[:13])
            self.segs.append(seg)

    def color(self, x):
        """ Get the color for the point x in the range [0..1)."""
        # Find the segment.
        for seg in self.segs:
            if seg.k <= x <= seg.r:
                break
        else:
            # No segment applies! Return black I guess.
            return (0, 0, 0)

        # Normalize the segment geometry.
        mid = (seg.m - seg.k)/(seg.r - seg.k)
        pos = (x - seg.k)/(seg.r - seg.k)

        # Assume linear (most common, and needed by most others).
        if pos <= mid:
            f = pos/mid/2
        else:
            f = (pos - mid)/(1 - mid)/2 + 0.5

        # Find the correct interpolation factor.
        if seg.fn == 1:     # Curved
            f = math.pow(pos, math.log(0.5) / math.log(mid))
        elif seg.fn == 2:   # Sinusoidal
            f = (math.sin((-math.pi/2) + math.pi*f) + 1)/2
        elif seg.fn == 3:   # Spherical increasing
            f -= 1
            f = math.sqrt(1 - f*f)
        elif seg.fn == 4:   # Spherical decreasing
            f = 1 - math.sqrt(1 - f*f)

        # Interpolate the colors
        if seg.space == 0:
            return (0xff << 24 |
                    int((seg.rl + (seg.rr-seg.rl) * f) * 0xff) << 16 |
                    int((seg.gl + (seg.gr-seg.gl) * f) * 0xff) << 8 |
                    int((seg.bl + (seg.br-seg.bl) * f) * 0xff))
        elif seg.space in (1, 2):
            hl, sl, vl = colorsys.rgb_to_hsv(seg.rl, seg.gl, seg.bl)
            hr, sr, vr = colorsys.rgb_to_hsv(seg.rr, seg.gr, seg.br)

            if seg.space == 1 and hr < hl:
                hr += 1
            elif seg.space == 2 and hr > hl:
                hr -= 1

            c = colorsys.hsv_to_rgb(
                (hl + (hr-hl) * f) % 1.0,
                sl + (sr-sl) * f,
                vl + (vr-vl) * f
                )
            return (0xff << 24 |
                    int(c[0] * 0xff) << 16 |
                    int((c[1] * 0xff)) << 8 |
                    int(c[2] * 0xff))


class Ugr(Gradient):
    def __init__(self, f, name=None):
        self.gradients = {}
        if isinstance(f, str):
            f = open(f)
        gradient = []
        while True:
            line = f.readline()
            if line == '':
                break
            if "}" in line:
                self.gradients[gradient[0]] = gradient[1]
            if "title=" in line:
                gradient = [line.split('"')[1], []]
                if name is None:
                    self.multi_gradients = True
                    name = gradient[0]
            if "color=" in line:
                gradient[1].append(int(line.split('=')[-1]))
        if name not in self.gradients:
            raise RuntimeError("Unknown gradient %s in %s" % (
                name, list(self.gradients.keys())))
        self.name = name

    def color(self, x, name=None):
        if name is None:
            name = self.name
        pos = int(len(self.gradients[name]) * x)
        return self.gradients[name][pos]


def get(name):
    import os

    gname = None
    if ":" in name:
        name, gname = name.split(':')

    local_file = os.path.join(os.path.dirname(__file__), "gradients", name)
    if os.path.exists(local_file):
        name = local_file
    if name in DEFAULT_GRADIENTS:
        gradient = GimpGradient(io.StringIO(DEFAULT_GRADIENTS[name]))
    else:
        if name.endswith(".ggr"):
            gradient = GimpGradient(name)
        elif name.endswith(".ugr"):
            gradient = Ugr(name, gname)
        else:
            raise RuntimeError("Only GimpGradient/UGR format is supported")
    return gradient


def generate_array(name, length):
    return get(name).to_array(length)


DEFAULT_GRADIENTS = {
    "purples": """GIMP Gradient
Name: Purples
7
0.00000 0.05759 0.09849 0.30303 0.10963 0.27308 1 0.51441 0.27924 0.73484 1 0 0
0.09849 0.17696 0.22871 0.51441 0.27924 0.73484 1 0.60460 0.33150 0.65000 1 0 0
0.22871 0.34724 0.40400 0.60460 0.33150 0.65000 1 0.20050 0.16988 0.39393 1 0 0
0.40400 0.48080 0.54424 0.20050 0.16988 0.39393 1 0.50053 0.32330 0.53000 1 0 0
0.54424 0.62876 0.71328 0.50053 0.32330 0.53000 1 0.60064 0.44574 0.68166 1 0 0
0.71328 0.76649 0.81969 0.60064 0.44574 0.68166 1 0.70075 0.56818 0.83333 1 0 0
0.81969 0.92821 1.00000 0.70075 0.56818 0.83333 1 0.18474 0.14979 0.21969 1 0 0
""",
    "sunrise": """GIMP Gradient
Name: Sunrise
6
0.000000 0.101798 0.203595 1.000000 1.000000 1.000000 1.000000 0.948165 0.969697 0.812122 1 0 0
0.203595 0.379143 0.487479 0.948165 0.969697 0.812122 1.000000 1.000000 0.552632 0.270000 1 0 0
0.487479 0.503577 0.529137 1.000000 0.552632 0.270000 1.000000 0.581721 0.096155 0.170043 1 0 0
0.529137 0.545165 0.562604 0.581721 0.096155 0.170043 1.000000 0.287879 0.155229 0.049835 1 0 0
0.562604 0.609349 0.697830 0.287879 0.155229 0.049835 1.000000 0.336000 0.425966 0.800000 1 0 0
0.697830 0.845064 1.000000 0.336000 0.425966 0.800000 1.000000 0.852165 0.985930 1.000000 1 0 0
""",
    "incandescent": """GIMP Gradient
Name: Incandescent
4
0.000000 0.459098 0.594324 0.000000 0.000000 0.000000 1.000000 0.729412 0.000000 0.000000 1 0 0
0.594324 0.677796 0.809683 0.729412 0.000000 0.000000 1.000000 1.000000 0.545098 0.196078 1 0 0
0.809683 0.853088 0.899833 1.000000 0.545098 0.196078 1.000000 0.972549 0.937255 0.074510 1 0 0
0.899833 0.948247 1.000000 0.972549 0.937255 0.074510 1.000000 0.976471 0.968627 0.831373 1 0 0
"""
}


if __name__ == '__main__':
    import sys
    from game import Screen, Window

    WINSIZE = (1000, 200)
    screen = Screen(WINSIZE)
    window = Window(WINSIZE)
    screen.add(window)

    for name in sys.argv[1:]:
        gradient = get(name)

        if gradient.multi_gradients:
            for gname in gradient.gradients:
                print("%s:%s" % (name, gname), end='')
                for x in range(WINSIZE[0]):
                    window.draw_line((x, 0),
                                     (x, WINSIZE[1]),
                                     gradient.color(x / WINSIZE[0], gname))
                screen.update()
                input()
        else:
            print(name, end='')
            for x in range(WINSIZE[0]):
                window.draw_line((x, 0),
                                 (x, WINSIZE[1]),
                                 gradient.color(x / WINSIZE[0]))
            screen.update()
            input()
