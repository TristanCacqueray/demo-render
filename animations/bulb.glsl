// open source under the http://opensource.org/licenses/BSD-2-Clause license
// adapted from https://www.shadertoy.com/view/XsXXWS

uniform vec2  size;
uniform float pitch;
uniform float yaw;
uniform float zoom;
uniform float aO;

uniform float power;

uniform int max_iter;
uniform int max_march;

uniform vec3  C;

uniform float hue;

uniform float minDist;

uniform int fast;


const vec3 lightDirection = vec3(0.57735026919, 0.57735026919, -0.57735026919);

const vec3 keyLightColor  = vec3(1.0, 1.0, 1.0);
const vec3 fillLightColor = vec3(0.0, 0.2, 1.0);

mat3 rotation;

float distanceToSurface(vec3 P, out float AO) {
    P = rotation * P;
    AO = aO;

    vec3 Z = P;

    // Put the whole shape in a bounding sphere to
    // speed up distant ray marching. This is necessary
    // to ensure that we don't expend all ray march iterations
    // before even approaching the surface
    {
        float r = length(P) - 2.;
        if (r > 1.0) { return r; }
    }

    // Embed a sphere within the fractal
    const float internalBoundingRadius = 1.8;

    // Used to smooth discrete iterations into continuous distance field
    // (similar to the trick used for coloring the Mandelbrot set)
    float derivative = 1.1;

    for (int i = 0; i < max_iter; ++i) {
        // Darken as we go deeper
        AO *= 0.725;
        float r = length(Z);

        if (r > 2.0) {
            // The point escaped. Remap AO for more brightness and return
            AO = min((AO + 0.075) * 4.1, 1.0);
            return min(length(Z) - internalBoundingRadius,
                       0.5 * log(r) * r / derivative);
        } else {
            // Convert to polar coordinates and then rotate by the power
            float theta = acos(Z.z / r) * power;
            float phi   = atan(Z.y, Z.x) * power;

            // Update the derivative
            derivative = pow(r, power - 1.0) * power * derivative + 1.0;

            // Convert back to Cartesian coordinates and
            // offset by the original point (which we're orbiting)
            float sinTheta = sin(theta);

            Z = vec3(sinTheta * cos(phi),
                     sinTheta * sin(phi),
                     cos(theta)) * (pow(r, power) + C);
        }
    }

    // Never escaped, so either already in the set...or a complete miss
    return minDist;
}


vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec3 trace(vec2 coord) {
    vec3 eps = vec3(minDist * 5.0, 0.0, 0.0);
    vec3 rayOrigin = vec3(2.0 * coord / size - 1.0, -5.0);
    float ignore;

    // Correct for aspect ratio
    rayOrigin.x *= size.x / size.y;

    vec3 rayDirection = normalize(
        normalize(vec3(0, 0, 1.0) - rayOrigin) +
        0.2 * vec3(rayOrigin.xy, 0.0) / zoom);

    // Distance from ray origin to hit point
    float t = 0.0;

    // Point on (technically, near) the surface of the Mandelbulb
    vec3 X;

    bool hit = false;
    float d;
    int i;

    // March along the ray, detecting when we are very close to the surface
    for (i = 0; i < max_march; ++i) {
        X = rayOrigin + rayDirection * t;

        d = distanceToSurface(X, ignore);
        hit = (d < minDist);
        if (hit) { break; }

        // Advance along the ray by the worst-case distance to the
        // surface in any direction
        t += d;
    }

    vec3 color;
    if (hit) {
        // Compute AO term
        float AO;
        distanceToSurface(X, AO);

        // Back away from the surface a bit before computing the gradient
        X -= rayDirection * eps.x;

        // Accurate micro-normal
        vec3 n = normalize(
                           vec3(d - distanceToSurface(X - eps.xyz, ignore),
                                d - distanceToSurface(X - eps.yxz, ignore),
                                d - distanceToSurface(X - eps.zyx, ignore)));

        // Bend the local surface normal by the
        // gross local shape normal and the bounding sphere
        // normal to avoid the hyper-detailed look
        n = normalize(n + normalize(X));

        // Fade between the key and fill light based on the normal
        // (Gooch-style wrap shading).
        // Also darken the surface in cracks (on top of the AO term)
        float fi = i;
        float mi = max_march;
        return AO * mix(
          fillLightColor,
          hsv2rgb(vec3(hue, .9 * fi / mi * 10, 1.)),
          clamp(0.7 * dot(lightDirection, n) + 0.6, 0.0, 1.0)
        );
    } else {
        return vec3(0, 0, 0);
    }
}

void main(void) {
    vec4 fragColor = gl_FragColor;
    vec2 fragCoord = gl_FragCoord.xy;
    rotation = mat3(1.0,        0.0,      0.0,
                    0.0, cos(pitch), -sin(pitch),
                    0.0, sin(pitch), cos(pitch)) *
               mat3(cos(yaw),   0.0, sin(yaw),
                    0.0,        1.0,      0.0,
                    -sin(yaw),  0.0, cos(yaw));

    vec3 color;
    if (fast == 1) {
      color = (
         trace(fragCoord.xy + vec2(-0.125, -0.375)) +
         trace(fragCoord.xy + vec2(+0.375, -0.125)) +
         trace(fragCoord.xy + vec2(+0.125, +0.375)) +
         trace(fragCoord.xy + vec2(-0.375, +0.125))
      ) / 4.0;
    } else {
      color = trace(fragCoord.xy);
    }

    // Coarse RGB->sRGB encoding via sqrt
    color = sqrt(color);

    // Vignetting (from iq https://www.shadertoy.com/view/MdX3Rr)
    vec2 xy = 2.0 * fragCoord.xy / size - 1.0;
    color *= 0.5 + 0.5*pow((xy.x+1.0)*(xy.y+1.0)*(xy.x-1.0)*(xy.y-1.0), 0.2);

    gl_FragColor = vec4(color, 1.0);
}
