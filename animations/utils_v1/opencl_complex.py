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


def calc_fractal_opencl(q, fractal, maxiter, args, seed=None):
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
        if fractal == "julia":
            extra_arg = ", double const seed_real, double const seed_imag"
            init_real_value = "q[gid].x"
            init_imag_value = "q[gid].y"
            real_compute = "real * real - imag * imag + seed_real"
            imag_compute = "2 * real * imag + seed_imag"
        elif fractal == "ship":
            real_compute = "fabs(real)*fabs(real) - fabs(imag)*fabs(imag) + " \
              "q[gid].x"
            imag_compute = "2 * fabs(real) * fabs(imag) + q[gid].y"
        else:
            real_compute = "real * real - imag * imag + q[gid].x"
            imag_compute = "2 * real * imag + q[gid].y"
        prg_src.append("""
        #pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
        #pragma OPENCL EXTENSION cl_khr_fp64 : enable
        __kernel void %s(__global double2 *q,
                                 __global uint *output, uint const max_iter%s)
        {
            int gid = get_global_id(0);
            double nreal = 0;
            double real = %s;
            double imag = %s;
            double modulus = 0;
            double escape = 512.0f;
            double mu = 0;
            output[gid] = 0;
            for(int idx = 0; idx < max_iter; idx++) {
                nreal = %s;
                imag = %s;
                real = nreal;
                modulus = sqrt(imag*imag + real*real);
                if (modulus > escape){
        """ % (fractal, extra_arg, init_real_value, init_imag_value,
               real_compute, imag_compute))
        if args.color_mod == "smooth_escape":
            prg_src.append(
                "mu = idx - log(log(modulus)) / log(2.0f) + "
                "log(log(escape)) / log(2.0f);"
            )
            prg_src.append("mu = mu / (double)max_iter;")

        else:
            prg_src.append("mu = idx / (double)max_iter;")
        if args.color == "gradient":
            prg_src.append("output[gid] = gradient[(int)(mu * %d)];" %
                           (num_color))
        elif args.color == "gradient_freq":
            prg_src.append("output[gid] = gradient[(int)("
                           "mu * %d * max_iter / 100.0f) %% %d];" % (
                               num_color, num_color))
        elif args.color == "dumb":
            prg_src.append("output[gid] = mu * 0xffff;")

        prg_src.append("break; }}}")
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
                       output_opencl, np.uint32(maxiter))
    elif fractal == "ship":
        prg.ship(queue, output.shape, None, q_opencl,
                 output_opencl, np.uint32(maxiter))
    elif fractal == "julia":
        prg.julia(queue, output.shape, None, q_opencl,
                  output_opencl, np.uint32(maxiter),
                  np.double(seed.real), np.double(seed.imag))

    cl.enqueue_copy(queue, output, output_opencl).wait()
    return output
