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

"""
Based on the Duck set fractal:
http://www.algorithmic-worlds.net/blog/blog.php?Post=20110227
Though the formula is log(z.real+abs(z.imag)i + c), hence the quack name...
"""

import os
import colorsys
import copy
import math
import io
import json
import pprint
import argparse
import sys
import subprocess
import time

import numpy as np
import pyopencl as cl
import pygame
import pygame.locals
try:
    import tkinter
    tk_ftw = True
except ImportError:
    print("Install tkinter for controller gui")
    tk_ftw = False

LOCATIONS = [
    # Cat face?
    {"c_real": 0.8113607147808848,
     "c_imag": -0.13926939853520198,
     "r_step": 1e-5, "i_step": 1e-4,
     "max_iter": 212,
     "center_imag": 27721805528.12306,
     "radius": 395065233724.0},
    # Skull
    {"c_real": 0.3175000000000004,
     "c_imag": -0.12666666666666632,
     "center_imag": 2.8750000000000004,
     "r_step": 0.01, "i_step": 0.01,
     "max_iter": 24,
     "radius": 9.703125,
     "gradient_length": 1024, "grad_freq": 2.864},
    # Siamoi
    {'c_imag': -3.002333333333332,
     'c_real': -0.6042899999999998,
     'center_imag': -3.0666666666666664, 'radius': 23,
     'grad_freq': 5.67, 'gradient_length': 1024,
     'i_step': 1e-4, 'r_step': 1e-5,
     'max_iter': 289},
    # Smiley
    {'c_imag': -0.3227777777777776,
     'c_real': 0.3519999999999998,
     'center_imag': 1.8186621093750004,
     'center_real': -0.04131408691406335,
     'grad_freq': 3.058,
     'gradient_length': 1024,
     'i_step': 1e-3, 'r_step': 1e-3,
     'max_iter': 82, 'radius': 5.4580078125},
    # Forest
    {'c_imag': -2.692868835794263,
     'c_real': -0.7477055835083013,
     'center_imag': 7.228938858176238,
     'center_real': 0.03129052525731807,
     'grad_freq': 2.09, 'gradient_length': 1024,
     'i_step': 1e-3, 'r_step': 1e-3,
     'max_iter': 266, 'radius': 9.70312499999998},
    # Spade
    {'c_imag': -0.13766939853520216,
     'c_real': 0.8106807147808879,
     'center_imag': -19100740691.017662,
     'grad_freq': 1.171, 'max_iter': 243,
     'i_step': 0.0001, 'r_step': 1e-05,
     'radius': 702338193287.111},
    # Bird
    {'c_imag': -2.3927856248537704,
     'c_real': -0.508264299352467,
     'center_imag': -152470.57611389644,
     'grad_freq': 1.316, 'max_iter': 231,
     'i_step': 0.0001, 'r_step': 0.0001,
     'radius': 1715293.9812813322},
    # Petal
    {'c_imag': -2.649679999999999,
     'c_real': -0.6994600000000002,
     'center_imag': -1.859146859638386e+27,
     'center_real': 0.0015762862198798189,
     'grad_freq': 2.09,
     'i_step': 1e-05,
     'max_iter': 128,
     'r_step': 1e-05,
     'radius': 1.6732321736745475e+28},
    # Crab
    {'c_imag': -0.06862119859059664,
     'c_real': 0.7834574090540408,
     'center_imag': 5.060867183983561,
     'center_real': 0.029246824759023404,
     'grad_freq': 3.058,
     'i_step': 0.0001,
     'max_iter': 393,
     'r_step': 0.001,
     'radius': 17.249999999999964},
    # Crab2
    {'c_imag': -0.20465459632873523,
     'c_real': 0.6388172976016997,
     'center_imag': -0.8373851296708139,
     'center_real': 0.49223223574268005,
     'grad_freq': 4.509,
     'i_step': 0.001,
     'max_iter': 254,
     'r_step': 0.0001,
     'radius': 22.99999999999995},
    # Palm tree 2
    {'c_imag': -1.543512414762484,
     'c_real': -0.4610122862620063,
     'center_imag': -1.219523620605469,
     'grad_freq': 2.28,
     'max_iter': 60,
     'radius': 2.3025970458984375},

    ]


###############################################################################
# OpenCL kernel code
###############################################################################
CLKERNEL = """__constant uint gradient[] = {{{gradient_values}}};
#define PYOPENCL_DEFINE_CDOUBLE 1
#include <pyopencl-complex.h>
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
__kernel void quack(
    __global double2 *plane,
    __global uint *pixels,
    uint const max_iter,
    double const gradient_frequency,
    double const c_real,
    double const c_imag,
    double const mod
) {{
    int gid = get_global_id(0);
    cdouble_t z = cdouble_new({zr}, {zi});
    cdouble_t c = cdouble_new({cr}, {ci});
    double escape = 4242.0f;
    double modulus = 0.0f;
    double mean = 0.0f;
    int iter;
    for (iter = 0; iter < max_iter; iter++) {{
        z.imag = fabs(z.imag);
        z = cdouble_add(z, c);
        z = cdouble_powr(z, mod);
        z = cdouble_log(z);

        modulus = cdouble_abs(z);
        mean += modulus;
        if (modulus > escape) {{
            break;
        }}
    }}
    if (iter == max_iter) {{
    mean = 1.0 - log2(0.5 * log2(mean / (double)(iter)));
    }} else {{
        modulus = iter - log(log(modulus)) / log(2.0f) + log(log(escape)) / log(2.0f);
        mean = modulus / (double)max_iter;
    }}

    pixels[gid] = gradient[(int)(
        (mean * {gradient_length} * gradient_frequency)) % {gradient_length}];
}}"""


class OpenCLCompute:
    def __init__(self, program):
        self.ctx = cl.create_some_context()
        if DEBUG:
            print("\n".join(program.split("\n")[1:]))
        self.kernel = cl.Program(self.ctx, program).build()

    def render(self, plane, *args):
        mf = cl.mem_flags
        # Plane is the input array of complex coordinate
        plane_opencl = cl.Buffer(
            self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=plane)
        # Pixels is the output array
        pixels = np.empty(plane.shape, dtype=np.uint32)
        pixels_opencl = cl.Buffer(self.ctx, mf.WRITE_ONLY, pixels.nbytes)
        # Call kernel
        queue = cl.CommandQueue(self.ctx)
        self.kernel.quack(
            queue, pixels.shape, None, plane_opencl, pixels_opencl, *args)
        # Read pixel buffer
        cl.enqueue_copy(queue, pixels, pixels_opencl).wait()
        return pixels


###############################################################################
# Gimp Gradient loader
###############################################################################
DEFAULT_GRADIENT = """GIMP Gradient
Name: Purples
7
0.00000 0.05759 0.09849 0.30303 0.10963 0.27308 1 0.51441 0.27924 0.73484 1 0 0
0.09849 0.17696 0.22871 0.51441 0.27924 0.73484 1 0.60460 0.33150 0.65000 1 0 0
0.22871 0.34724 0.40400 0.60460 0.33150 0.65000 1 0.20050 0.16988 0.39393 1 0 0
0.40400 0.48080 0.54424 0.20050 0.16988 0.39393 1 0.50053 0.32330 0.53000 1 0 0
0.54424 0.62876 0.71328 0.50053 0.32330 0.53000 1 0.60064 0.44574 0.68166 1 0 0
0.71328 0.76649 0.81969 0.60064 0.44574 0.68166 1 0.70075 0.56818 0.83333 1 0 0
0.81969 0.92821 1.00000 0.70075 0.56818 0.83333 1 0.18474 0.14979 0.21969 1 0 0
"""


class GimpGradient:
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
            return (int((seg.rl + (seg.rr-seg.rl) * f) * 0xff) |
                    int((seg.gl + (seg.gr-seg.gl) * f) * 0xff) << 8 |
                    int((seg.bl + (seg.br-seg.bl) * f) * 0xff) << 16)
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
            return (int(c[0] * 0xff) |
                    int((c[1] * 0xff)) << 8 |
                    int(c[2] * 0xff) << 16)

    def to_array(self, length):
        colors_array = []
        for idx in range(length):
            colors_array.append(str(self.color(idx / length)))
        return ",".join(colors_array)


###############################################################################
# Pixels <-> Complex Plane conversion
###############################################################################
class ComplexPlane:
    def set_view(self, center_real, center_imag, radius):
        # Plane dimensions
        self.plane_min = (center_real - radius,
                          center_imag - radius)
        self.plane_max = (center_real + radius,
                          center_imag + radius)
        # Coordinate conversion vector
        self.offset = (self.plane_min[0], self.plane_min[1])
        self.scale = (
            self.window_size[0] / float(self.plane_max[0] - self.plane_min[0]),
            self.window_size[1] / float(self.plane_max[1] - self.plane_min[1])
        )

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
        self.window_size = window_size
        self.length = window_size[0] * window_size[1]
        self.pixels = None
        self.draw = False

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        text = self.font.render(msg, True, color)
        self.surface.blit(text, coord)

    def draw_line(self, start_coord, end_coord, color=(28, 28, 28)):
        pygame.draw.line(self.surface, color, start_coord, end_coord)

    def draw_point(self, coord, color=[242]*3):
        self.surface.set_at(coord, color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface,
                                    nparray.reshape(*self.window_size))


##############################################################################
# Controller
##############################################################################
class Controller:
    default_params = {
        'c_real': 0.0,
        'c_imag': 0.0,
        'center_real': 0.0,
        'center_imag': 0.0,
        'r_step': 1e-2,
        'i_step': 1e-2,
        'max_iter': 42,
        'radius': 23,
        'grad_freq': 1.0,
        'mod': 1.0,
    }

    def __init__(self, mapmode):
        self.mapmode = mapmode
        if not tk_ftw:
            self.root = None
            return
        self.root = tkinter.Tk()
        self.width = 900
        self.location_pos = 0
        self.controllers = []
        if not mapmode:
            self.add_fine("r_step")
            self.add_fine("i_step")
        self.add_float("max_iter", 1, 500)
        self.add_float("grad_freq", 0.01, 42, 0.04)
        self.add_float("mod", 0.01, 6, 0.01)
        self.root.update()
        # Give tcl/tk sometime to reserve resources
        time.sleep(0.1)

    def set(self, params, screen=None, scene=None):
        """Set provided params"""
        if screen:
            self.screen = screen
        if scene:
            self.scene = scene
        self.params = params
        self.scene.params = params

        for k, v in self.default_params.items():
            params.setdefault(k, v)
        self.start_params = copy.copy(params)

        # Set sliders position
        if not self.root:
            return
        for t, n, v in self.controllers:
            value = self.params[n]
            if t == "float":
                v.set(value)
            else:
                val, magnitude = list(map(lambda x: int(x.split('.')[0]),
                                          "{:1e}".format(value).split('e')))
                v[0].set(val)
                v[1].set(magnitude)

    def _get_row(self):
        row = 0
        for controller in self.controllers:
            if controller[0] == "fine":
                row += 2
            else:
                row += 1
        return row

    def add_float(self, name, from_, to, resolution=1):
        """Add simple slider"""
        r = self._get_row()

        param = tkinter.Scale(self.root,
                              from_=from_, to=to, resolution=resolution,
                              orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text=name).grid(row=r, column=0)
        param.grid(row=r, column=1)
        param.bind("<ButtonRelease-1>", self.on_tkclic)
        self.controllers.append(["float", name, param])

    def add_fine(self, name):
        """Add 2 sliders, one for value, one for magnitude order"""
        r = self._get_row()
        param = tkinter.Scale(self.root,
                              from_=0, to=10, resolution=1,
                              orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text='%s value' % name).grid(row=r, column=0)
        param.grid(row=r, column=1)
        param.bind("<ButtonRelease-1>", self.on_tkclic)

        param_mag = tkinter.Scale(self.root,
                                  from_=-15, to=15, resolution=1,
                                  orient=tkinter.HORIZONTAL, length=self.width)
        tkinter.Label(self.root, text='%s mag' % name).grid(row=r+1, column=0)
        param_mag.grid(row=r+1, column=1)
        param_mag.bind("<ButtonRelease-1>", self.on_tkclic)
        self.controllers.append(["fine", name, (param, param_mag)])

    def on_tkclic(self, ev=None):
        # Read all sliders values
        for t, n, v in self.controllers:
            if t == "fine":
                val = float("%de%d" % (v[0].get(), v[1].get()))
                self.params[n] = val
            if t == "float":
                self.params[n] = v.get()
        self.scene.draw = True

    def on_pygame_clic(self, ev):
        plane_coord = self.scene.convert_to_plane(ev.pos)
        if ev.button in (1, 3):
            if ev.button == 1:
                step = 3/4.0
            else:
                step = 4/3.0
            self.params["radius"] *= step
            self.params["center_real"] = plane_coord.real
            self.params["center_imag"] = plane_coord.imag
            self.scene.set_view(center_real=self.params["center_real"],
                                center_imag=self.params["center_imag"],
                                radius=self.params["radius"])
            self.scene.draw = True
        else:
            if self.mapmode:
                params = self.get()
                params["center_real"] = 0
                params["center_imag"] = 0
                params["c_real"] = plane_coord.real
                params["c_imag"] = plane_coord.imag
                subprocess.Popen([sys.argv[0], "--params", json.dumps(params)])
            else:
                print("Clicked", ev.pos, plane_coord)

    def on_key(self, scancode):
        if DEBUG:
            print("Key press code:", scancode)
        self.scene.draw = True
        direction = 1
        if scancode == 9:
            self.scene.draw = False
            self.scene.alive = False
        elif scancode in (24, 26):
            if scancode == 26:
                step = 3/4.0
            else:
                step = 4/3.0
            self.params["radius"] *= step
        elif scancode in (25, 39):
            if scancode == 39:
                direction = -1
            self.params["c_imag"] += direction * self.params["i_step"]
        elif scancode in (38, 40):
            if scancode == 40:
                direction = -1
            self.params["c_real"] += direction * self.params["r_step"]
        elif scancode in (113, 114):
            if scancode == 113:
                direction = -1
            self.params["center_real"] += direction * 10 / self.scene.scale[0]
        elif scancode in (111, 116):
            if scancode == 111:
                direction = -1
            self.params["center_imag"] += direction * 10 / self.scene.scale[1]
        elif scancode == 27:
            self.params["center_real"] = self.start_params["center_real"]
            self.params["center_imag"] = self.start_params["center_imag"]
            self.params["radius"] = self.start_params["radius"]
        elif scancode == 36:
            self.location_pos += 1
            self.set(LOCATIONS[self.location_pos % len(LOCATIONS)])
        elif scancode == 33:
            self.screen.capture("./{time}_{rsign}{r}{isign}{i}i.png".format(
                time=time.strftime("%Y-%m-%d_%H:%M"),
                rsign="" if self.params["c_real"] >= 0 else "-",
                r=abs(self.params["c_real"]),
                isign="+" if self.params["c_imag"] >= 0 else "-",
                i=abs(self.params["c_imag"])))
            self.scene.draw = False
        elif scancode == 53:
            pprint.pprint(self.get())
            self.scene.draw = False
        else:
            self.scene.draw = False

    def update(self, frame):
        if self.root:
            self.root.update()
        for ev in pygame.event.get():
            if ev.type == pygame.locals.KEYDOWN:
                self.on_key(ev.dict['scancode'])
            elif ev.type == pygame.locals.MOUSEBUTTONDOWN:
                self.on_pygame_clic(ev)

    def get(self):
        """Get modified params"""
        params = {}
        for k, v in self.default_params.items():
            if self.params[k] != v:
                params[k] = self.params[k]
        return params


class QuackSet(Window, ComplexPlane):
    def __init__(self, winsize, mapmode, params):
        Window.__init__(self, winsize)
        self.alive = True
        self.draw = True

        gradient_file = params['gradient_file']
        if not gradient_file:
            gradient = GimpGradient(io.StringIO(DEFAULT_GRADIENT))
        else:
            if gradient_file.endswith(".ggr"):
                gradient = GimpGradient(gradient_file)
            else:
                print("Only GimpGradient format is supported")
                exit(1)

        x, y = 'y', 'x'
        if params['notinversed']:
            x, y = 'x', 'y'

        self.gpu = OpenCLCompute(CLKERNEL.format(
            gradient_values=gradient.to_array(params['gradient_length']),
            gradient_length=params['gradient_length'],
            zr=0 if mapmode else "plane[gid]."+x,
            zi=0 if mapmode else "plane[gid]."+y,
            cr="plane[gid].x" if mapmode else "c_real",
            ci="plane[gid].y" if mapmode else "c_imag",
        ))

    def render(self, frame):
        if not self.draw:
            return
        self.set_view(self.params["center_real"],
                      self.params["center_imag"],
                      self.params["radius"])
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        plane = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        nparray = self.gpu.render(plane,
                                  np.uint32(self.params["max_iter"]),
                                  np.double(self.params["grad_freq"]),
                                  np.double(self.params["c_real"]),
                                  np.double(self.params["c_imag"]),
                                  np.double(self.params["mod"]))
        self.blit(nparray)
        self.draw = False
        return True


def show_help(args):
    print("QuackSet explorer\n"
          "=================\n"
          "Mouse binding:\n"
          " Right/left button zoom in/out and center view")
    if args.map:
        print(" Middle button render the set with c=click coord")
    print()
    print("Keyboard binding:\n"
          " 'p' print the image to a png file\n"
          " arrows move the window\n"
          " 'a'/'e' zoom in/out")
    if not args.map:
        print(" 'wsad' change c value\n")
        print(" enter cycle through interesting positions\n")


def usage(argv=sys.argv[1:], params=LOCATIONS[0]):
    global DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 7)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--record", metavar="DIR",
                        help="record rendering destination")
    parser.add_argument("--map", action="store_true",
                        help="show set map")
    parser.add_argument("--params", metavar="JSON", default=json.dumps(params),
                        help="Fractal parameters")
    parser.add_argument("--debug", action="store_true",
                        help="show debug information")
    args = parser.parse_args(argv)
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    if not args.map:
        args.params = json.loads(args.params)
    else:
        args.params = {'radius': 3, 'center_imag': -0.5}
    args.params.setdefault('gradient_file', os.environ.get("GRADIENT"))
    args.params.setdefault('gradient_length', 1024)
    args.params.setdefault('notinversed', 0)
    DEBUG = args.debug or os.environ.get("DEBUG")
    if DEBUG:
        os.environ["DEBUG"] = "1"
    os.environ["SIZE"] = str(args.size)
    return args


def main():
    args = usage()
    if len(sys.argv) == 1:
        show_help(args)

    controller = Controller(args.map)
    screen = Screen(args.winsize)
    scene = QuackSet(args.winsize, args.map, args.params)
    screen.add(scene)
    controller.set(args.params, screen, scene)

    clock = pygame.time.Clock()
    frame = 0
    while scene.alive:
        start_time = time.monotonic()
        controller.update(frame)
        if scene.render(frame):
            print("%04d: %.2f sec --params '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(controller.get())))

        screen.update()
        if args.record:
            if not os.path.isdir(args.record):
                os.makedirs(args.record)
            screen.capture(os.path.join(args.record, "%04d.png" % frame))
        clock.tick(25)
        frame += 1


if __name__ == "__main__":
    main()
