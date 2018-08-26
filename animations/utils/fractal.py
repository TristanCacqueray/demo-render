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

import collections
import copy
import logging

import numpy as np


from . import game
from . import gradient
from . import opencl


log = logging.getLogger()

DEFAULT_FORMULAS = {
   "duck2": """
z = cdouble_divide(z, cdouble_cos(z));
z = cdouble_add(z, c);
z = cdouble_log(z);
   """,
   "m2": """
   """,
}


DEFAULT_KERNELS = {
    "orbit-rgb": """
__constant uint gradient[] = {{{gradient_values}}};
#define PYOPENCL_DEFINE_CDOUBLE 1
#include <pyopencl-complex.h>
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
__kernel void compute(
    __global double2 *plane,
    __global uint *pixels,
    char const julia,
    uint const max_iter,
    uint const pre_iter,
    double const gradient_frequency,
    double const c_real,
    double const c_imag
    {kernel_params}
) {{
    int gid = get_global_id(0);
    cdouble_t z;
    cdouble_t z2;
    cdouble_t c;

    if (julia) {{
        z = cdouble_new({pos_x}, {pos_y});
        c = cdouble_new(c_real, c_imag);
    }} else {{
        z = cdouble_new(0, 0);
        c = cdouble_new({pos_x}, {pos_y});
    }}
    {kernel_variables}
    double escape = {escape_distance};
    double modulus = 0.0f;
    cdouble_t orbit;
    double orbit_modulus = 0.0f;
    orbit = cdouble_new(mod, mod2);

    double mean = 0.0f;
    double rdistance = escape;
    double gdistance = escape;
    int iter;
    pixels[gid] = 0x00000000;
    for (iter = 0; iter < max_iter; iter++) {{
        {formula}

        orbit_modulus = fabs(z.imag - orbit.imag);

        if (orbit_modulus < trap) {{
            pixels[gid] = gradient[(int)(
                ((orbit_modulus / trap) * {gradient_length}/10)) + 20];
            break ;
        }}
        orbit_modulus = fabs(z.real - orbit.real);

        if (orbit_modulus < trap) {{
            pixels[gid] = gradient[(int)(
                ((orbit_modulus / trap) * {gradient_length} / 10))];
            // pixels[gid] = 0xff000000 | ((int)(0xff * orbit_modulus / trap) << 8);
            break ;
        }}

        modulus = cdouble_abs(z);
        if (modulus > escape) {{
            modulus = iter - log(log(modulus)) / log(2.0f) +
                             log(log(escape)) / log(2.0f);
            modulus = modulus / (double)max_iter;
            pixels[gid] = gradient[(int)(
                (modulus * {gradient_length} * gradient_frequency)) %
                {gradient_length}];
            break;
        }}
    }}
}}
""",

    "orbit-gradient": """
__constant uint gradient[] = {{{gradient_values}}};
#define PYOPENCL_DEFINE_CDOUBLE 1
#include <pyopencl-complex.h>
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
__kernel void compute(
    __global double2 *plane,
    __global uint *pixels,
    char const julia,
    uint const max_iter,
    uint const pre_iter,
    double const gradient_frequency,
    double const c_real,
    double const c_imag
    {kernel_params}
) {{
    int gid = get_global_id(0);
    cdouble_t z;
    cdouble_t z2;
    cdouble_t c;

    if (julia) {{
        z = cdouble_new({pos_x}, {pos_y});
        c = cdouble_new(c_real, c_imag);
    }} else {{
        z = cdouble_new(0, 0);
        c = cdouble_new({pos_x}, {pos_y});
    }}
    {kernel_variables}
    double escape = {escape_distance};
    double modulus = 0.0f;
    cdouble_t orbit;
    double orbit_modulus = 0.0f;
    orbit = cdouble_new(mod, mod2);

    double mean = 0.0f;
    double distance = escape;
    int iter;
    for (iter = 0; iter < max_iter; iter++) {{
        {formula}

        orbit_modulus = fabs(z.imag - orbit.imag);
        //mean += orbit_modulus;

        if (orbit_modulus < distance) {{
            distance = orbit_modulus;
        }}
        orbit_modulus = fabs(z.real - orbit.real);

        if (orbit_modulus < distance) {{
            distance = orbit_modulus;
        }}

        modulus = cdouble_abs(z);
        if (modulus > escape) {{
            break;
        }}
    }}
    distance = sqrt(distance);
    pixels[gid] = gradient[(int)(
          (distance * {gradient_length} * gradient_frequency)) %
          {gradient_length}]
        ;

}}
""",
    "escape-time-gradient": """
__constant uint gradient[] = {{{gradient_values}}};
#define PYOPENCL_DEFINE_CDOUBLE 1
#include <pyopencl-complex.h>
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
__kernel void compute(
    __global double2 *plane,
    __global uint *pixels,
    char const julia,
    uint const max_iter,
    uint const pre_iter,
    double const gradient_frequency,
    double const c_real,
    double const c_imag
    {kernel_params}
) {{
    int gid = get_global_id(0);
    cdouble_t z;
    cdouble_t z2;
    cdouble_t c;

    if (julia) {{
        z = cdouble_new({pos_x}, {pos_y});
        c = cdouble_new(c_real, c_imag);
    }} else {{
        z = cdouble_new(0, 0);
        c = cdouble_new({pos_x}, {pos_y});
    }}
    {kernel_variables}
    double escape = {escape_distance};
    double modulus = 0.0f;
    int iter;
    for (iter = 0; iter < max_iter; iter++) {{
        {formula}
        modulus = cdouble_abs(z);
        if (modulus > escape) {{
            modulus = iter - log(log(modulus)) / log(2.0f) +
                             log(log(escape)) / log(2.0f);
            modulus = modulus / (double)max_iter;
            pixels[gid] = gradient[(int)(
                (modulus * {gradient_length} * gradient_frequency)) %
                {gradient_length}];
            break;
        }}
    }}
}}
""",
    "mean-distance": """
__constant uint gradient[] = {{{gradient_values}}};
#define PYOPENCL_DEFINE_CDOUBLE 1
#include <pyopencl-complex.h>
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
#pragma OPENCL EXTENSION cl_khr_fp64 : enable

cdouble_t cdouble_iabs(cdouble_t t) {{
    t.imag = fabs(t.imag);
    return t;
}}

cdouble_t cdouble_rabs(cdouble_t t) {{
    t.real = fabs(t.real);
    return t;
}}

cdouble_t cdouble_fabs(cdouble_t t) {{
    t.real = fabs(t.real);
    t.imag = fabs(t.imag);
    return t;
}}

__kernel void compute(
    __global double2 *plane,
    __global uint *pixels,
    char const julia,
    uint const max_iter,
    uint const pre_iter,
    double const gradient_frequency,
    double const c_real,
    double const c_imag
    {kernel_params}
) {{
    int gid = get_global_id(0);
    cdouble_t z;
    cdouble_t z2;
    cdouble_t c;
    double mean = 0.0f;

    if (julia) {{
        z = cdouble_new({pos_x}, {pos_y});
        c = cdouble_new(c_real, c_imag);
    }} else {{
        z = cdouble_new(0, 0);
        c = cdouble_new({pos_x}, {pos_y});
    }}
    {kernel_variables}
    double escape = {escape_distance};
    double modulus = 0.0f;
    int iter;
    for (iter = 0; iter < max_iter; iter++) {{
        {formula}
        if (iter > pre_iter) {{
          modulus = cdouble_abs(z);
          mean += modulus;
        }}
        if (modulus > escape && iter > pre_iter) {{
            break;
        }}
    }}
    mean = 1.0 - log2(0.5 * log2(mean / (double)(iter - pre_iter)));
    pixels[gid] = gradient[(int)(
        (mean * {gradient_length} * gradient_frequency)) % {gradient_length}];
}}
""",
}


class Fractal(game.Window, game.ComplexPlane):
    def __init__(self, winsize, params, gpu=None):
        game.Window.__init__(self, winsize)
        self.params = params
        self.draw = True
        self.alive = True
        self.mapmode = False
        self.map_scene = None
        if gpu:
            self.gpu = gpu
            self.mapmode = True
            self.previous_c = collections.deque(maxlen=2000)
            self.set_view(self.params["map_center_real"],
                          self.params["map_center_imag"],
                          self.params["map_radius"])
            return
        x, y = 'x', 'y'
        if params['xyinverted']:
            x, y = 'y', 'x'
        cl_params = copy.copy(params)
        cl_params["pos_x"] = "plane[gid]." + x
        cl_params["pos_y"] = "plane[gid]." + y

        if "gradient" in params:
            cl_params["gradient_values"] = gradient.generate_array(
                params["gradient"], params["gradient_length"])
            cl_params["gradient_length"] = params["gradient_length"]

        if cl_params["formula"] in DEFAULT_FORMULAS:
            cl_params["formula"] = DEFAULT_FORMULAS[cl_params["formula"]]
        if cl_params["kernel"] in DEFAULT_KERNELS:
            kernel = DEFAULT_KERNELS[cl_params["kernel"]]

        if cl_params.get("kernel_params"):
            cl_params["kernel_params"] = "," + cl_params["kernel_params"]

        program = kernel.format(**cl_params)
        log.debug(program)
        self.gpu = opencl.OpenCLCompute(program)

    def render(self, frame):
        if self.map_scene:
            self.map_scene.add_c(
                complex(self.params["c_real"], self.params["c_imag"]))
        updated = False
        if self.map_scene:
            updated = self.map_scene.render(frame)
        if not self.draw:
            return updated
        if self.mapmode:
            view_prefix = "map_"
        else:
            view_prefix = ""
        super_sampling = self.params["super_sampling"]
        self.set_view(self.params[view_prefix + "center_real"],
                      self.params[view_prefix + "center_imag"],
                      self.params[view_prefix + "radius"])
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0] * super_sampling)
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1] * super_sampling) * 1j
        plane = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        render_args = [
            plane,
            np.byte(self.params["julia"] and not self.mapmode),
            np.uint32(self.params["max_iter"]),
            np.uint32(self.params.get("pre_iter", 0)),
            np.double(self.params["grad_freq"]),
            np.double(self.params["c_real"]),
            np.double(self.params["c_imag"]),
        ]
        for kernel_param in self.params["kernel_params_mod"]:
            render_args.append(np.double(self.params[kernel_param]))
        nparray = self.gpu.render(*render_args)
        if super_sampling > 1:
            import scipy.ndimage
            import scipy.misc
            s = (self.window_size[0], self.window_size[1])
            nparray = scipy.misc.imresize(
                nparray.view(np.uint8).reshape(s[0]*super_sampling,
                                               s[1]*super_sampling, 4),
                s,
                interp='cubic',
                mode='RGBA')
        self.blit(nparray.view(np.uint32))
        self.draw = False
        if self.mapmode:
            self.draw_previous_c()
        return True

    def create_map_scene(self, win_size, params):
        self.map_scene = Fractal(win_size, params, gpu=self.gpu)

    def add_c(self, c):
        if self.params["show_map"]:
            if self.params["xyinverted"]:
                c = complex(c.imag, c.real)
            if not len(self.previous_c) or self.previous_c[-1] != c:
                self.previous_c.append(c)
                self.draw = True
                if not self.included(c):
                    # Re-center
                    self.params["map_center_real"] = c.real
                    self.params["map_center_imag"] = c.imag
                    self.draw = True

    def draw_previous_c(self):
        length = len(self.previous_c)
        pos = 0
        for c in self.previous_c:
            pos += 1
            self.draw_complex(
                c, color=[100 + int(100 * (pos / length))]*3, width=2)
