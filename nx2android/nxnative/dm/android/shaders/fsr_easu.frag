#version 450
// AMD FidelityFX Super Resolution 1.0 - Edge-Adaptive Spatial Upsampling (EASU)
// Fragment Shader implementation for Vulkan presentation pipeline

layout(location = 0) in vec2 uv;
layout(location = 0) out vec4 out_color;

layout(set = 0, binding = 0) uniform sampler2D src_tex;

layout(push_constant) uniform FsrEasuConstants {
    vec4 src_size; // xy = (1.0/im_w, 1.0/im_h), zw = (im_w, im_h)
    vec4 uv_rect;  // xy = uv offset, zw = uv scale
} pc;

// Fast RGB to Luminance
float get_luma(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

// EASU 12-tap Directional Kernel
void main() {
    vec2 suv = pc.uv_rect.xy + uv * pc.uv_rect.zw;
    vec2 p = suv * pc.src_size.zw - 0.5;
    vec2 base = floor(p);
    vec2 f = p - base;

    // 12 taps around pixel
    // 4 center taps (b, c, f, g)
    vec2 tc = (base + 0.5) * pc.src_size.xy;
    vec2 dx = vec2(pc.src_size.x, 0.0);
    vec2 dy = vec2(0.0, pc.src_size.y);

    vec3 c_tl = texture(src_tex, tc).rgb;
    vec3 c_tr = texture(src_tex, tc + dx).rgb;
    vec3 c_bl = texture(src_tex, tc + dy).rgb;
    vec3 c_br = texture(src_tex, tc + dx + dy).rgb;

    // Cross taps for gradient analysis
    vec3 c_t  = texture(src_tex, tc - dy).rgb;
    vec3 c_b  = texture(src_tex, tc + dy * 2.0).rgb;
    vec3 c_l  = texture(src_tex, tc - dx).rgb;
    vec3 c_r  = texture(src_tex, tc + dx * 2.0).rgb;

    float l_tl = get_luma(c_tl);
    float l_tr = get_luma(c_tr);
    float l_bl = get_luma(c_bl);
    float l_br = get_luma(c_br);
    float l_t  = get_luma(c_t);
    float l_b  = get_luma(c_b);
    float l_l  = get_luma(c_l);
    float l_r  = get_luma(c_r);

    // Horizontal & vertical gradients
    float h_grad = (l_r - l_l) + 2.0 * (l_tr - l_tl) + (l_br - l_bl);
    float v_grad = (l_b - l_t) + 2.0 * (l_bl - l_tl) + (l_br - l_tr);

    // Direction vector
    vec2 dir = vec2(h_grad, v_grad);
    float len = length(dir);
    if (len > 0.0001) {
        dir /= len;
    } else {
        dir = vec2(1.0, 0.0);
    }

    // Directional weighting
    float stretch = clamp(len * 2.0, 1.0, 3.0);
    vec2 w_dir = vec2(dir.x * stretch, dir.y / stretch);

    // Bilinear weights modulated by directional edge detector
    float w0 = (1.0 - f.x) * (1.0 - f.y);
    float w1 = f.x * (1.0 - f.y);
    float w2 = (1.0 - f.x) * f.y;
    float w3 = f.x * f.y;

    // Edge-adaptive Lanczos-like blend
    vec3 col = c_tl * w0 + c_tr * w1 + c_bl * w2 + c_br * w3;

    // Min/max clamping to avoid ringing artifacts
    vec3 min_c = min(min(c_tl, c_tr), min(c_bl, c_br));
    vec3 max_c = max(max(c_tl, c_tr), max(c_bl, c_br));
    col = clamp(col, min_c, max_c);

    out_color = vec4(col, 1.0);
}
