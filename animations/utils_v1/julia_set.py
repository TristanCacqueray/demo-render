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

import random
import numpy as np
import pygame
import sys
import time

from . pygame_utils import Screen, Window, ComplexPlane
from . common import PHI, usage_cli_complex, run_main, gradient, rgb250

try:
    import pyopencl as cl
    prg, ctx = None, None
except ImportError:
    print("OpenCL is disabled")


def compute_julia_opencl(q, max_iter, c, norm, color_mod):
    global prg, ctx

    if not prg:
        ctx = cl.create_some_context()
        prg_src = []
        num_color = 4096
        if color_mod == "gradient":
            colors = gradient(num_color)
            colors_array = []
            for idx in range(num_color):
                colors_array.append(str(colors(idx)))
            prg_src.append("__constant uint gradient[] = {%s};" %
                           ",".join(colors_array))
        prg_src.append("""
        #pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
        #pragma OPENCL EXTENSION cl_khr_fp64 : enable
        __kernel void julia(__global double2 *q,
                            __global uint *output, uint const max_iter,
                            double const seed_real, double const seed_imag)
        {
            int gid = get_global_id(0);
            double nreal = 0;
            double real = q[gid].x;
            double imag = q[gid].y;
            double modulus = 0;
            double escape = 32.0f;
            double mu = 0;
            output[gid] = 0;
            for(uint idx = 0; idx < max_iter; idx++) {
                nreal = real*real - imag*imag + seed_real;
                imag = 2* real*imag + seed_imag;
                real = nreal;
                modulus = sqrt(imag*imag + real*real);
                if (modulus > escape){
        """)
        if norm == "escape":
            prg_src.append(
                "mu = idx - log(log(modulus)) / log(2.0f) + "
                "log(log(escape)) / log(2.0f);"
            )
            prg_src.append("mu = mu / (double)max_iter;")
        else:
            prg_src.append("mu = idx / (double)max_iter;")
        if color_mod == "gradient":
            prg_src.append("output[gid] = gradient[(int)(mu * %d)];" %
                           (num_color - 1))
        elif color_mod == "dumb":
            prg_src.append("output[gid] = mu * 0xffff;")
        prg_src.append("break; }}}")
        prg = cl.Program(ctx, "\n".join(prg_src)).build()
    output = np.empty(q.shape, dtype=np.uint32)

    queue = cl.CommandQueue(ctx)

    mf = cl.mem_flags
    q_opencl = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=q)
    output_opencl = cl.Buffer(ctx, mf.WRITE_ONLY, output.nbytes)

    prg.julia(queue, output.shape, None, q_opencl,
              output_opencl, np.uint32(max_iter),
              np.double(c.real), np.double(c.imag))
    cl.enqueue_copy(queue, output, output_opencl).wait()
    return output


class JuliaSet(Window, ComplexPlane):
    def __init__(self, args):
        Window.__init__(self, args.winsize)
        self.c = args.c
        self.args = args
        self.max_iter = args.max_iter
        self.color_mod = args.color
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame, draw_info=False):
        start_time = time.monotonic()
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        q = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        nparray = compute_julia_opencl(
            q, self.max_iter, self.c, "escape", self.color_mod)
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

    def draw_function_msg(self):
        if self.c.real >= 0:
            r_sign = "+"
        else:
            r_sign = ""
        if self.c.imag >= 0:
            i_sign = "+"
        else:
            i_sign = ""
        self.c_str = "z*z%s%.5f%s%.5fj" % (
            r_sign, self.c.real, i_sign, self.c.imag)
        self.draw_msg(self.c_str)

    def draw_cpoint(self):
        self.draw_complex(self.c, (255, 0, 0))


seeds = (
    complex(PHI, PHI),
    (-0.15000+0.95000j),
    (-0.64000+0.70000j),
    (-0.64000+0.50000j),
    (+0.47000-0.24000j),
    (-0.77000-0.15000j),
    (-1.38000-0.09000j),
    (-1.17000+0.18000j),
    (-0.08000+0.70000j),
    (-0.11000+1.00000j),
    (0.28200+0.48000j),
)
