/* This file is part of the Marble Marcher (https://github.com/HackerPoet/MarbleMarcher).
 * Copyright(C) 2018 CodeParade
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.If not, see http://www.gnu.org/licenses/.
 */

/* demo-code notes:
 * - removed the marble and the flags
 * - add uniforms default
 * - change coloring
 */
#version 120
#define AMBIENT_OCCLUSION_COLOR_DELTA vec3(0.7)
#define AMBIENT_OCCLUSION_STRENGTH 0.008 /* 0.008 */
#define ANTIALIASING_SAMPLES 1
#define BACKGROUND_COLOR vec3(0.6,0.8,1.0)
#define COL col_fractal
#define DE de_fractal
#define DIFFUSE_ENABLED 0
#define DIFFUSE_ENHANCED_ENABLED 0
#define FOCAL_DIST 1.73205080757
#define FOG_ENABLED 0
#define LIGHT_COLOR vec3(1.0,0.95,0.8)
#define LIGHT_DIRECTION vec3(-0.36, 0.8, 0.48)
#define MAX_DIST 30.0
#define MAX_MARCHES 1000
#define MIN_DIST 1e-5
#define PI 3.14159265358979
#define SHADOWS_ENABLED 1
#define SHADOW_DARKNESS 0.5
#define SHADOW_SHARPNESS 10.0
#define SPECULAR_HIGHLIGHT 40
#define SPECULAR_MULT 0.25
#define SUN_ENABLED 0
#define SUN_SHARPNESS 2.0
#define SUN_SIZE 0.004
#define VIGNETTE_STRENGTH 0.5

uniform vec3 iDebug;

uniform float iFracScale; // slider[1.0,5.0,0.01] 1.87
uniform float iFracAng1;  // slider[-20.0,20.0,0.01] -3.12
uniform float iFracAng2;  // slider[-20.0,20.0,0.01] 0.02
uniform vec3 iFracShift;  // slider[-10.0,10.0,0.01] -3.57,0.129,2.95
uniform vec3 iFracCol;    // slider[0.,1.0,0.05] 0.42,0.38,0.19
uniform float iExposure;  // 0.7

vec3 refraction(vec3 rd, vec3 n, float p) {
  float dot_nd = dot(rd, n);
  return p * (rd - dot_nd * n) + sqrt(1.0 - (p * p) * (1.0 - dot_nd * dot_nd)) * n;
}

//##########################################
//   Space folding
//##########################################
void planeFold(inout vec4 z, vec3 n, float d) {
  z.xyz -= 2.0 * min(0.0, dot(z.xyz, n) - d) * n;
}
void sierpinskiFold(inout vec4 z) {
  z.xy -= min(z.x + z.y, 0.0);
  z.xz -= min(z.x + z.z, 0.0);
  z.yz -= min(z.y + z.z, 0.0);
}
void mengerFold(inout vec4 z) {
  float a = min(z.x - z.y, 0.0);
  z.x -= a;
  z.y += a;
  a = min(z.x - z.z, 0.0);
  z.x -= a;
  z.z += a;
  a = min(z.y - z.z, 0.0);
  z.y -= a;
  z.z += a;
}
void boxFold(inout vec4 z, vec3 r) {
  z.xyz = clamp(z.xyz, -r, r) * 2.0 - z.xyz;
}
void rotX(inout vec4 z, float s, float c) {
  z.yz = vec2(c*z.y + s*z.z, c*z.z - s*z.y);
}
void rotY(inout vec4 z, float s, float c) {
  z.xz = vec2(c*z.x - s*z.z, c*z.z + s*z.x);
}
void rotZ(inout vec4 z, float s, float c) {
  z.xy = vec2(c*z.x + s*z.y, c*z.y - s*z.x);
}
void rotX(inout vec4 z, float a) {
  rotX(z, sin(a), cos(a));
}
void rotY(inout vec4 z, float a) {
  rotY(z, sin(a), cos(a));
}
void rotZ(inout vec4 z, float a) {
  rotZ(z, sin(a), cos(a));
}

//##########################################
//   Primitive DEs
//##########################################
float de_box(vec4 p, vec3 s) {
  vec3 a = abs(p.xyz) - s;
  return (min(max(max(a.x, a.y), a.z), 0.0) + length(max(a, 0.0))) / p.w;
}

//##########################################
//   Main DEs
//##########################################
float de_fractal(vec4 p) {
  for (int i = 0; i < 16; ++i) {
    p.xyz = abs(p.xyz);
    rotZ(p, iFracAng1);
    mengerFold(p);
    rotX(p, iFracAng2);
    p *= iFracScale;
    p.xyz += iFracShift;
  }
  return de_box(p, vec3(6.0));
}
vec4 col_fractal(vec4 p) {
  vec3 orbit = vec3(0.0);
  float modulus = 0.0;
  for (int i = 0; i < 16; ++i) {
    p.xyz = abs(p.xyz);
    rotZ(p, iFracAng1);
    mengerFold(p);
    rotX(p, iFracAng2);
    p *= iFracScale;
    p.xyz += iFracShift;
    orbit = max(orbit, p.xyz);
    modulus += length(p.xyz);
  }
  modulus = 1.0 - log2(0.5 * log2(modulus / 16));
  return vec4(vec3(.5) + vec3(.5) * cos(6.2 * (modulus * vec3(.8) + iFracCol)), 1.0);
}

//##########################################
//   Main code
//##########################################
vec4 ray_march(inout vec4 p, vec4 ray, float sharpness) {
  //March the ray
  float d = DE(p);
  float s = 0.0;
  float td = 0.0;
  float min_d = 1.0;
  for (; s < MAX_MARCHES; s += 1.0) {
    if (d < MIN_DIST) {
      s += d / MIN_DIST;
      break;
    } else if (td > MAX_DIST) {
      break;
    }
    td += d;
    p += ray * d;
    min_d = min(min_d, sharpness * d / td);
    d = DE(p);
  }
  return vec4(d, s, td, min_d);
}

vec4 scene(inout vec4 p, inout vec4 ray, float vignette) {
  //Trace the ray
  vec4 d_s_td_m = ray_march(p, ray, 1.0f);
  float d = d_s_td_m.x;
  float s = d_s_td_m.y;
  float td = d_s_td_m.z;

  //Determine the color for this pixel
  vec4 col = vec4(0.0);
  if (d < MIN_DIST) {
    //Get the surface normal
    vec4 e = vec4(MIN_DIST, 0.0, 0.0, 0.0);
    vec3 n = vec3(DE(p + e.xyyy) - DE(p - e.xyyy),
                  DE(p + e.yxyy) - DE(p - e.yxyy),
                  DE(p + e.yyxy) - DE(p - e.yyxy));
    n /= length(n);
    vec3 reflected = ray.xyz - 2.0*dot(ray.xyz, n) * n;

    //Get coloring
    vec4 orig_col = clamp(COL(p), 0.0, 1.0);
    //vec4 orig_col = vec4(td, d, td, 1.0);
    col.w = orig_col.w;

    //Get if this point is in shadow
    float k = 1.0;
#if SHADOWS_ENABLED
    vec4 light_pt = p;
    light_pt.xyz += n * MIN_DIST * 100;
    vec4 rm = ray_march(light_pt, vec4(LIGHT_DIRECTION, 0.0), SHADOW_SHARPNESS);
    k = rm.w * min(rm.z, 1.0);
#endif

    //Get specular
#if SPECULAR_HIGHLIGHT > 0
    float specular = max(dot(reflected, LIGHT_DIRECTION), 0.0);
    specular = pow(specular, SPECULAR_HIGHLIGHT);
    col.xyz += specular * LIGHT_COLOR * (k * SPECULAR_MULT);
#endif

    //Get diffuse lighting
#if DIFFUSE_ENHANCED_ENABLED
    k = min(k, SHADOW_DARKNESS * 0.5 * (dot(n, LIGHT_DIRECTION) - 1.0) + 1.0);
#elif DIFFUSE_ENABLED
    k = min(k, dot(n, LIGHT_DIRECTION));
#endif

    //Don't make shadows entirely dark
    k = max(k, 1.0 - SHADOW_DARKNESS);
    col.xyz += orig_col.xyz * LIGHT_COLOR * k;

    //Add small amount of ambient occlusion
    float a = 1.0 / (1.0 + s * AMBIENT_OCCLUSION_STRENGTH);
    col.xyz += (1.0 - a) * AMBIENT_OCCLUSION_COLOR_DELTA;

    //Add fog effects
#if FOG_ENABLED
    a = td / MAX_DIST;
    col.xyz = (1.0 - a) * col.xyz + a * BACKGROUND_COLOR;
#endif

    //Return normal through ray
    ray = vec4(n, 0.0);
  } else {
    //Ray missed, start with solid background color
    col.xyz += BACKGROUND_COLOR;

    col.xyz *= vignette;
    //Background specular
#if SUN_ENABLED
    float sun_spec = dot(ray.xyz, LIGHT_DIRECTION) - 1.0 + SUN_SIZE;
    sun_spec = min(exp(sun_spec * SUN_SHARPNESS / SUN_SIZE), 1.0);
    col.xyz += LIGHT_COLOR * sun_spec;
#endif
  }

  return col;
}

uniform vec2 iResolution;
uniform mat4 iMat;
void main() {
  vec3 col = vec3(0.0);
  vec4 p = iMat[3];
  for (int i = 0; i < ANTIALIASING_SAMPLES; ++i) {
    for (int j = 0; j < ANTIALIASING_SAMPLES; ++j) {
      //Get normalized screen coordinate
      vec2 delta = vec2(i, j) / ANTIALIASING_SAMPLES;
      vec2 screen_pos = (gl_FragCoord.xy + delta) / iResolution.xy;
      vec2 uv = 2*screen_pos - 1;
      uv.x *= iResolution.x / iResolution.y;

      //Convert screen coordinate to 3d ray
      vec4 ray = iMat * normalize(vec4(uv.x, uv.y, -FOCAL_DIST, 0.0));

      //Reflect light if needed
      float vignette = 1.0 - VIGNETTE_STRENGTH * length(screen_pos - 0.5);
      vec3 r = ray.xyz;
      vec4 col_r = scene(p, ray, vignette);

      col += col_r.xyz;
    }
  }

  col *= iExposure / (ANTIALIASING_SAMPLES * ANTIALIASING_SAMPLES);
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
