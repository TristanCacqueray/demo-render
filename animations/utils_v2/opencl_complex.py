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

import numpy as np
try:
    import pyopencl as cl
    prg, ctx = None, None
except ImportError:
    print("OpenCL is disabled")

DUCK = """
z.imag = fabs(z.imag);
//z = cdouble_powr(z, 2);
z = cdouble_add(z, c);
z = cdouble_log(z);
"""

BURNING_SHIP = """
z.real = fabs(z.real);
z.imag = fabs(z.imag);
z = cdouble_powr(z, 2);
z = cdouble_add(z, c);
"""

BUFALO_SHIP = """
zisqr = z.real * z.real;
zrsqr = z.imag * z.imag;
z.imag = fabs(z.real * z.imag) * -2.0 + c.imag;
z.real = fabs(zrsqr - zisqr) + c.real;
//z = cdouble_log(z);
"""


def calc_fractal_opencl(q, fractal, maxiter, args, seed=None, mod=None, f=None):
    global prg, ctx

    if not prg:
        ctx = cl.create_some_context()
        prg_src = []
        num_color = 10096
        if args.color.startswith("gradient"):
            colors_array = []
            for idx in range(num_color):
                colors_array.append(str(args.gradient.color(idx/num_color)))
            prg_src.append("__constant uint gradient[] = {%s};" %
                           ",".join(colors_array))

        extra_arg = ""
        init_real_value = "0"
        init_imag_value = "0"
        init_rseed_value = "0"
        init_iseed_value = "0"
        if fractal == "julia":
            extra_arg = ", double const seed_real, double const seed_imag, double const mod"
            init_real_value = "q[gid].y"
            init_imag_value = "q[gid].x"
            init_rseed_value = "seed_real"
            init_iseed_value = "seed_imag"
        elif fractal == "juliaship":
            extra_arg = ", double const seed_real, double const seed_imag, double const mod"
            init_real_value = "q[gid].x"
            init_imag_value = "q[gid].y"
            init_rseed_value = "seed_real"
            init_iseed_value = "seed_imag"
            if f is None:
                f = BURNING_SHIP
        elif fractal == "ship":
            extra_arg = ", double const mod"
            if f is None:
                f = BURNING_SHIP
            init_rseed_value = "q[gid].x"
            init_iseed_value = "q[gid].y"
        else:
            extra_arg = ", double const mod"
            init_rseed_value = "q[gid].x"
            init_iseed_value = "q[gid].y"
        print(f)
        prg_src.append("""
        #define PYOPENCL_DEFINE_CDOUBLE 1
        #include <pyopencl-complex.h>
        #pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
        #pragma OPENCL EXTENSION cl_khr_fp64 : enable
        __kernel void %s(__global double2 *q,
                                 __global uint *output, uint const max_iter,
                                 double const grad_freq%s)
        {
            int gid = get_global_id(0);
            cdouble_t z = cdouble_new(%s, %s);
            cdouble_t c = cdouble_new(%s, %s);
            cdouble_t z2;
            cdouble_t z3;
            cdouble_t m = cdouble_new(1, 2);
            int idx;
            double r;
            double zrsqr = 0.0;
            double zisqr = 0.0;

            double modulus = 0.0;
            double mean = 0.0;
            double escape = 55555.0f;
            double mu = 0;
            for(idx = 0; idx < max_iter; idx++) {
                %s
                modulus = cdouble_abs(z);
                mean += modulus;
                if (modulus > escape) {
        """ % (fractal, extra_arg,
               init_real_value, init_imag_value,
               init_rseed_value, init_iseed_value,
               f))
        if args.color_mod == "smooth_escape":
            prg_src.append(
                "mu = idx - log(log(modulus)) / log(2.0f) + "
                "log(log(escape)) / log(2.0f);"
            )
            prg_src.append("mu = mu / (double)max_iter;")

        else:
            prg_src.append("mu = idx / (double)max_iter;")
        if args.color == "gradient":
            prg_src.append("output[gid] = gradient[(int)("
                           "mu * %d * grad_freq) %% %d];" %
                           (num_color, num_color))
        elif args.color == "gradient_freq":
            prg_src.append("output[gid] = gradient[(int)("
                           "mu * %d * max_iter / 100.0f) %% %d];" % (
                               num_color, num_color))
        elif args.color == "dumb":
            prg_src.append("output[gid] = mu * 0xffff;")

        prg_src.append("\nbreak;\n}\n}")
        prg_src.append("""
        if (idx == max_iter) {
            mean = 1.0 - log2(log2(mean / (double)(idx)));
//            mean = (mean / (double)(idx));
            output[gid] = gradient[(int)(mean * %d * grad_freq) %% %d];
        }
        }
""" % (num_color, num_color))
        if args.debug:
            print("\n".join(prg_src[1:]))
        prg = cl.Program(ctx, "\n".join(prg_src)).build()
    output = np.empty(q.shape, dtype=np.uint32)

    queue = cl.CommandQueue(ctx)

    mf = cl.mem_flags
    q_opencl = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=q)
    output_opencl = cl.Buffer(ctx, mf.WRITE_ONLY, output.nbytes)

    if fractal == "mandelbrot":
        prg.mandelbrot(queue, output.shape, None, q_opencl,
                       output_opencl, np.uint32(maxiter),
                       np.double(args.gradient_frequency), np.double(args.mod))
    elif fractal == "ship":
        prg.ship(queue, output.shape, None, q_opencl,
                 output_opencl, np.uint32(maxiter), np.double(args.gradient_frequency),
                 np.double(args.mod))
    elif fractal == "julia":
        prg.julia(queue, output.shape, None, q_opencl,
                  output_opencl, np.uint32(maxiter),
                  np.double(args.gradient_frequency),
                  np.double(seed.real), np.double(seed.imag),
                  np.double(args.mod))
    elif fractal == "juliaship":
        prg.juliaship(queue, output.shape, None, q_opencl,
                      output_opencl, np.uint32(maxiter), np.double(args.gradient_frequency),
                      np.double(seed.real), np.double(seed.imag), np.double(args.mod))

    cl.enqueue_copy(queue, output, output_opencl).wait()
    return output
