#version 450
// AMD FidelityFX Super Resolution 1.0 - Robust Contrast-Adaptive Sharpening (RCAS)
// Fragment Shader implementation for Vulkan presentation pipeline

layout(location = 0) in vec2 uv;
layout(location = 0) out vec4 out_color;

layout(set = 0, binding = 0) uniform sampler2D upscaled_tex;

layout(push_constant) uniform FsrRcasConstants {
    vec4 tex_size; // xy = (1.0/mid_w, 1.0/mid_h), zw = (dw/mid_w, dh/mid_h)
    float sharpness; // 0.0 (off) to 1.0 (max)
    float pad0;
    float pad1;
    float pad2;
} pc;

void main() {
    vec2 tc = uv * pc.tex_size.zw;
    vec2 dx = vec2(pc.tex_size.x, 0.0);
    vec2 dy = vec2(0.0, pc.tex_size.y);

    // 5-tap cross pattern: Center, North, South, West, East
    vec3 c = texture(upscaled_tex, tc).rgb;
    vec3 n = texture(upscaled_tex, tc - dy).rgb;
    vec3 s = texture(upscaled_tex, tc + dy).rgb;
    vec3 w = texture(upscaled_tex, tc - dx).rgb;
    vec3 e = texture(upscaled_tex, tc + dx).rgb;

    // Contrast limits to prevent ringing/haloing
    vec3 mn = min(c, min(min(n, s), min(w, e)));
    vec3 mx = max(c, max(max(n, s), max(w, e)));

    // Adaptive sharpness weight based on local contrast
    // Clamp to 0.0..0.25 to guarantee stability
    vec3 amp = clamp(min(mn, 2.0 - mx) / max(mx, vec3(0.001)), 0.0, 1.0);
    vec3 peak = -sqrt(amp);
    vec3 weight = peak * (pc.sharpness * 0.22);

    // Filter equation
    vec3 filtered = (c + weight * (n + s + w + e)) / (vec3(1.0) + vec3(4.0) * weight);

    // Final safety clamp against overshoot
    filtered = clamp(filtered, mn, mx);

    out_color = vec4(filtered, 1.0);
}
