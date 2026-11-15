#!/usr/bin/env python3
"""Generate 96x96 alpha-mask HUD_ICONS in nfshpr_icons.h directly from the exact SVG glyphs in both HTML launchers."""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HTML_FILES = [
    Path(r"c:\Users\Andrew\Downloads\nfs_hot_pursuit_remastered_android_launcher(2).html"),
    Path(r"c:\Users\Andrew\Downloads\burnout_paradise_remastered_android_launcher(1).html"),
]
OUT_H = Path(__file__).resolve().parent / "nfshpr_icons.h"

S = 4  # 4x supersampling: 384x384 -> 96x96
SZ = 96

FONT_PATH = None
for cand in [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
]:
    if Path(cand).exists():
        FONT_PATH = cand
        break


def extract_glyphs(html_path: Path) -> dict[str, str]:
    txt = html_path.read_text(encoding="utf-8")
    i1 = txt.find("const glyphs = {")
    i2 = txt.find("const isMenuPad", i1)
    block = txt[i1:i2]
    # Match key: `...` or key: `...`
    out = {}
    for m in re.finditer(r"([a-zA-Z0-9_]+)\s*:\s*`([^`]*)`", block):
        out[m.group(1)] = m.group(2)
    return out


def parse_color_alpha(val: str | None) -> int:
    if not val or val == "none":
        return 0
    if "rgba" in val:
        m = re.search(r"rgba\([^,]+,[^,]+,[^,]+,\s*([0-9.]+)\)", val)
        if m:
            return max(0, min(255, int(round(float(m.group(1)) * 255))))
    return 255


def draw_thick_polyline(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]], width: float, fill: int, closed: bool = False):
    if len(pts) < 2:
        return
    w = max(1, int(round(width)))
    seq = pts + [pts[0]] if closed else pts
    draw.line(seq, fill=fill, width=w, joint="curve")
    r = width * 0.5
    if r >= 0.6:
        for x, y in pts:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def cubic_bezier(p0, p1, p2, p3, steps=20):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def svg_arc_to_pts(x0, y0, rx, ry, phi_deg, large_arc, sweep, x1, y1, steps=24):
    if rx == 0 or ry == 0:
        return [(x1, y1)]
    phi = math.radians(phi_deg)
    dx2 = (x0 - x1) / 2.0
    dy2 = (y0 - y1) / 2.0
    x1p = math.cos(phi) * dx2 + math.sin(phi) * dy2
    y1p = -math.sin(phi) * dx2 + math.cos(phi) * dy2
    rx, ry = abs(rx), abs(ry)
    lam = (x1p**2) / (rx**2) + (y1p**2) / (ry**2)
    if lam > 1:
        s = math.sqrt(lam)
        rx *= s
        ry *= s
    num = max(0.0, rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2)
    den = rx**2 * y1p**2 + ry**2 * x1p**2
    coef = math.sqrt(num / den) if den > 1e-9 else 0.0
    if large_arc == sweep:
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = math.cos(phi) * cxp - math.sin(phi) * cyp + (x0 + x1) / 2.0
    cy = math.sin(phi) * cxp + math.cos(phi) * cyp + (y0 + y1) / 2.0

    def vec_ang(ux, uy, vx, vy):
        n = math.hypot(ux, uy) * math.hypot(vx, vy)
        if n < 1e-9:
            return 0.0
        c = max(-1.0, min(1.0, (ux * vx + uy * vy) / n))
        a = math.acos(c)
        return -a if (ux * vy - uy * vx) < 0 else a

    t1 = vec_ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = vec_ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    pts = []
    for i in range(1, steps + 1):
        ang = t1 + dt * (i / steps)
        px = cx + math.cos(phi) * rx * math.cos(ang) - math.sin(phi) * ry * math.sin(ang)
        py = cy + math.sin(phi) * rx * math.cos(ang) + math.cos(phi) * ry * math.sin(ang)
        pts.append((px, py))
    return pts


def parse_path_subpaths(d: str) -> list[tuple[list[tuple[float, float]], bool]]:
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", d)
    subpaths = []
    cur: list[tuple[float, float]] = []
    cx = cy = 0.0
    sx = sy = 0.0
    last_cp = None
    i = 0
    cmd = ""
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in ("Z", "z"):
                if cur:
                    subpaths.append((cur, True))
                    cur = []
                cx, cy = sx, sy
                last_cp = None
                continue
        if cmd in ("M", "m"):
            nx, ny = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if cmd == "m":
                nx += cx
                ny += cy
            if cur:
                subpaths.append((cur, False))
            cx, cy = nx, ny
            sx, sy = cx, cy
            cur = [(cx * S, cy * S)]
            cmd = "L" if cmd == "M" else "l"
            last_cp = None
        elif cmd in ("L", "l"):
            nx, ny = float(tokens[i]), float(tokens[i + 1])
            i += 2
            if cmd == "l":
                nx += cx
                ny += cy
            cx, cy = nx, ny
            cur.append((cx * S, cy * S))
            last_cp = None
        elif cmd in ("H", "h"):
            nx = float(tokens[i])
            i += 1
            if cmd == "h":
                nx += cx
            cx = nx
            cur.append((cx * S, cy * S))
            last_cp = None
        elif cmd in ("V", "v"):
            ny = float(tokens[i])
            i += 1
            if cmd == "v":
                ny += cy
            cy = ny
            cur.append((cx * S, cy * S))
            last_cp = None
        elif cmd in ("C", "c"):
            x1, y1, x2, y2, nx, ny = map(float, tokens[i : i + 6])
            i += 6
            if cmd == "c":
                x1 += cx; y1 += cy; x2 += cx; y2 += cy; nx += cx; ny += cy
            pts = cubic_bezier((cx * S, cy * S), (x1 * S, y1 * S), (x2 * S, y2 * S), (nx * S, ny * S))
            cur.extend(pts[1:])
            last_cp = (x2, y2)
            cx, cy = nx, ny
        elif cmd in ("S", "s"):
            x2, y2, nx, ny = map(float, tokens[i : i + 4])
            i += 4
            if cmd == "s":
                x2 += cx; y2 += cy; nx += cx; ny += cy
            if last_cp is not None:
                x1, y1 = 2 * cx - last_cp[0], 2 * cy - last_cp[1]
            else:
                x1, y1 = cx, cy
            pts = cubic_bezier((cx * S, cy * S), (x1 * S, y1 * S), (x2 * S, y2 * S), (nx * S, ny * S))
            cur.extend(pts[1:])
            last_cp = (x2, y2)
            cx, cy = nx, ny
        elif cmd in ("A", "a"):
            rx, ry, rot, la, sw, nx, ny = map(float, tokens[i : i + 7])
            i += 7
            if cmd == "a":
                nx += cx; ny += cy
            pts = svg_arc_to_pts(cx, cy, rx, ry, rot, int(la), int(sw), nx, ny)
            cur.extend([(px * S, py * S) for px, py in pts])
            cx, cy = nx, ny
            last_cp = None
        else:
            i += 1
    if cur:
        subpaths.append((cur, False))
    return subpaths


def render_svg_glyph(svg_inner: str) -> bytes:
    cleaned = svg_inner.replace("${fg}", "#ffffff")
    root = ET.fromstring(f"<g>{cleaned}</g>")
    img = Image.new("L", (SZ * S, SZ * S), 0)
    draw = ImageDraw.Draw(img)

    for el in root.iter():
        tag = el.tag
        if tag == "g":
            continue
        fill_a = parse_color_alpha(el.attrib.get("fill"))
        stroke_a = parse_color_alpha(el.attrib.get("stroke"))
        sw = float(el.attrib.get("stroke-width", "2.5")) * S

        if tag == "rect":
            x = float(el.attrib["x"]) * S
            y = float(el.attrib["y"]) * S
            w = float(el.attrib["width"]) * S
            h = float(el.attrib["height"]) * S
            rx = float(el.attrib.get("rx", "0")) * S
            if fill_a:
                draw.rounded_rectangle([x, y, x + w, y + h], radius=rx, fill=fill_a)
            if stroke_a:
                draw.rounded_rectangle([x, y, x + w, y + h], radius=rx, outline=stroke_a, width=max(1, int(round(sw))))
        elif tag == "circle":
            cx = float(el.attrib["cx"]) * S
            cy = float(el.attrib["cy"]) * S
            r = float(el.attrib["r"]) * S
            if fill_a:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill_a)
            if stroke_a:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=stroke_a, width=max(1, int(round(sw))))
        elif tag == "ellipse":
            cx = float(el.attrib["cx"]) * S
            cy = float(el.attrib["cy"]) * S
            rx = float(el.attrib["rx"]) * S
            ry = float(el.attrib["ry"]) * S
            if fill_a:
                draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill_a)
            if stroke_a:
                draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=stroke_a, width=max(1, int(round(sw))))
        elif tag == "line":
            x1, y1, x2, y2 = (float(el.attrib[k]) * S for k in ("x1", "y1", "x2", "y2"))
            if stroke_a:
                draw_thick_polyline(draw, [(x1, y1), (x2, y2)], sw, stroke_a, closed=False)
        elif tag in ("polygon", "polyline"):
            nums = [float(v) * S for v in re.findall(r"[-+]?\d*\.?\d+", el.attrib["points"])]
            pts = [(nums[j], nums[j + 1]) for j in range(0, len(nums), 2)]
            if tag == "polygon" and fill_a and len(pts) >= 3:
                draw.polygon(pts, fill=fill_a)
            if stroke_a:
                draw_thick_polyline(draw, pts, sw, stroke_a, closed=(tag == "polygon"))
        elif tag == "path":
            for pts, closed in parse_path_subpaths(el.attrib["d"]):
                if fill_a and len(pts) >= 3:
                    draw.polygon(pts, fill=fill_a)
                if stroke_a:
                    draw_thick_polyline(draw, pts, sw, stroke_a, closed=closed)
        elif tag == "text":
            txt_s = (el.text or "").strip()
            x = float(el.attrib.get("x", "48")) * S
            y = float(el.attrib.get("y", "48")) * S
            fs = float(el.attrib.get("font-size", "28")) * S
            if FONT_PATH and txt_s:
                font = ImageFont.truetype(FONT_PATH, int(round(fs * 1.15)))
                bbox = draw.textbbox((0, 0), txt_s, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((x - tw / 2 - bbox[0], y - th / 2 - bbox[1]), txt_s, fill=fill_a or 255, font=font)

    out = img.resize((SZ, SZ), Image.Resampling.LANCZOS)
    return out.tobytes()


def main():
    glyphs: dict[str, str] = {}
    for hp in HTML_FILES:
        glyphs.update(extract_glyphs(hp))

    # Render all unique glyphs
    lines = [
        "#pragma once",
        "#include <stdint.h>",
        "#include <string.h>",
        "",
        f"#define HUD_ICON_SZ {SZ}",
        "typedef struct { const char *id; uint8_t px[HUD_ICON_SZ * HUD_ICON_SZ]; } hud_icon_t;",
        "",
        "static const hud_icon_t HUD_ICONS[] = {",
    ]
    for k in sorted(glyphs):
        raw = render_svg_glyph(glyphs[k])
        arr = ",".join(str(b) for b in raw)
        lines.append(f'    {{"{k}", {{{arr}}}}},')
    lines.append("};")
    lines.append("")
    lines.append("""static const char *hud_icon_alias(const char *id) {
    if (!id) return NULL;
    if (!strcmp(id, "steerLeft") || !strcmp(id, "steer_left")) return "left";
    if (!strcmp(id, "steerRight") || !strcmp(id, "steer_right")) return "right";
    if (!strcmp(id, "analogStick") || !strcmp(id, "analog_stick") || !strcmp(id, "steerStick")) return "stick";
    if (!strcmp(id, "gyroBadge")) return "gyro";
    if (!strcmp(id, "empWeapon")) return "emp";
    if (!strcmp(id, "spikeStrip")) return "spikes";
    if (!strcmp(id, "lookBack") || !strcmp(id, "look_back")) return "lookback";
    if (!strcmp(id, "musicSkip") || !strcmp(id, "next_track") || !strcmp(id, "music_skip")) return "music";
    if (!strcmp(id, "camera_view")) return "camera";
    if (!strcmp(id, "game_pause")) return "pause";
    if (!strcmp(id, "world_map")) return "worldMap";
    if (!strcmp(id, "reset_track") || !strcmp(id, "reset_car")) return "resetTrack";
    if (!strcmp(id, "actA") || !strcmp(id, "btnA") || !strcmp(id, "nav_select")) return "padA";
    if (!strcmp(id, "actB") || !strcmp(id, "btnB") || !strcmp(id, "nav_back")) return "padB";
    if (!strcmp(id, "actX") || !strcmp(id, "btnX")) return "padX";
    if (!strcmp(id, "actY") || !strcmp(id, "btnY")) return "padY";
    if (!strcmp(id, "btnZL") || !strcmp(id, "rotate_left")) return "padZL";
    if (!strcmp(id, "btnZR") || !strcmp(id, "rotate_right")) return "padZR";
    if (!strcmp(id, "btnL") || !strcmp(id, "nav_tab_prev")) return "padL";
    if (!strcmp(id, "btnR") || !strcmp(id, "nav_tab_next")) return "padR";
    if (!strcmp(id, "btnPlus") || !strcmp(id, "nav_pause")) return "padPlus";
    if (!strcmp(id, "btnMinus")) return "padMinus";
    if (!strcmp(id, "stickLeft")) return "stickL";
    if (!strcmp(id, "stickRight")) return "stickR";
    if (!strcmp(id, "navUp") || !strcmp(id, "nav_up")) return "dpadUp";
    if (!strcmp(id, "navDown") || !strcmp(id, "nav_down")) return "dpadDown";
    if (!strcmp(id, "navLeft") || !strcmp(id, "nav_left")) return "dpadLeft";
    if (!strcmp(id, "navRight") || !strcmp(id, "nav_right")) return "dpadRight";
    return id;
}

static const uint8_t *hud_find_icon(const char *id) {
    const char *key = hud_icon_alias(id);
    if (!key) return NULL;
    for (size_t i = 0; i < sizeof(HUD_ICONS) / sizeof(HUD_ICONS[0]); i++) {
        if (!strcmp(HUD_ICONS[i].id, key)) return HUD_ICONS[i].px;
    }
    return NULL;
}
""")
    OUT_H.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {OUT_H} with {len(glyphs)} icons: {sorted(glyphs.keys())}")


if __name__ == "__main__":
    main()
