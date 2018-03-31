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
import pyopencl as cl


class OpenCLCompute:
    ctx = None

    def __init__(self, program):
        if self.ctx is None:
            self.ctx = cl.create_some_context()
            self.queue = cl.CommandQueue(self.ctx)
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
        self.kernel.compute(
            self.queue, pixels.shape, None, plane_opencl, pixels_opencl, *args)
        # Read pixel buffer
        cl.enqueue_copy(self.queue, pixels, pixels_opencl).wait()
        return pixels
