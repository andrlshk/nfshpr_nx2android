#!/usr/bin/env python3
import hashlib, json, os, secrets, shutil, struct, subprocess, sys, zipfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
R8_JAR = ROOT / "tools" / "r8.jar"
ANDROID_JAR = Path(r"C:\Users\Andrew\.gradle\caches\8.14.3\transforms\0e384a7765b6a3b7071cf2123bb437ea\transformed\android.jar")
BASE_APK = REPO / "apks" / "NeedForSpeedHotPursuitRemastered_racing_hud.apk"
BUILD_DIR = ROOT / "build"
CLASSES_DIR = BUILD_DIR / "classes"
DEX_DIR = BUILD_DIR / "dex"
OUT_APK = ROOT / "NFSHPR_Unified.apk"
KEY_JSON = ROOT / "unified-signing-key.json"

PKG = "org.nx2a.nfshpr"
LABEL = "Hot Pursuit Remastered"
MIN_SDK, TARGET_SDK = 29, 36
ICON_ID = 0x7f010000

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ATTR_IDS = {
    "label": 0x01010001, "icon": 0x01010002, "name": 0x01010003,
    "hasCode": 0x0101000c, "debuggable": 0x0101000f, "exported": 0x01010010,
    "process": 0x01010011, "screenOrientation": 0x0101001e,
    "configChanges": 0x0101001f, "value": 0x01010024,
    "minSdkVersion": 0x0101020c, "versionCode": 0x0101021b,
    "versionName": 0x0101021c, "targetSdkVersion": 0x01010270,
    "maxSdkVersion": 0x01010271, "isGame": 0x010103f4,
    "extractNativeLibs": 0x010104ea, "appCategory": 0x01010545,
    "requestLegacyExternalStorage": 0x01010603,
    "enableOnBackInvokedCallback": 0x0101066c,
}
T_REF, T_STRING, T_INT_DEC, T_INT_HEX, T_BOOL = 0x01, 0x03, 0x10, 0x11, 0x12
CONFIG_CHANGES = (
    0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020 | 0x0040 | 0x0080 |
    0x0100 | 0x0200 | 0x0400 | 0x0800 | 0x1000 | 0x2000 | 0x4000 | 0x10000000 | 0x40000000
)

MANIFEST = ("manifest", [(False, "package", PKG), (True, "versionCode", 196647), (True, "versionName", "1.0-beta")], [
    ("uses-sdk", [(True, "minSdkVersion", MIN_SDK), (True, "targetSdkVersion", TARGET_SDK)], []),
    ("uses-permission", [(True, "name", "android.permission.VIBRATE")], []),
    ("uses-permission", [(True, "name", "android.permission.MANAGE_EXTERNAL_STORAGE")], []),
    ("uses-permission", [(True, "name", "android.permission.READ_EXTERNAL_STORAGE"), (True, "maxSdkVersion", 29)], []),
    ("application", [
        (True, "label", LABEL),
        (True, "icon", ("ref", ICON_ID)),
        (True, "hasCode", True),
        (True, "debuggable", False),
        (True, "isGame", True),
        (True, "extractNativeLibs", True),
        (True, "requestLegacyExternalStorage", True),
        (True, "appCategory", 0),
        (True, "enableOnBackInvokedCallback", False),
    ], [
        ("activity", [
            (True, "name", "org.nx2a.nfshpr.launcher.MainActivity"),
            (True, "exported", True),
            (True, "screenOrientation", 6),
            (True, "configChanges", ("hex", CONFIG_CHANGES)),
        ], [
            ("intent-filter", [], [
                ("action", [(True, "name", "android.intent.action.MAIN")], []),
                ("category", [(True, "name", "android.intent.category.LAUNCHER")], []),
            ])
        ]),
        ("activity", [
            (True, "name", "android.app.NativeActivity"),
            (True, "exported", False),
            (True, "process", ":game"),
            (True, "screenOrientation", 6),
            (True, "configChanges", ("hex", CONFIG_CHANGES)),
        ], [
            ("meta-data", [(True, "name", "android.app.lib_name"), (True, "value", "dmhost")], []),
        ])
    ])
])

def walk_attrs(n):
    for a in n[1]: yield a
    for k in n[2]: yield from walk_attrs(k)

def axml(root):
    res_names = sorted({n for _, n, _ in walk_attrs(root) if n in ATTR_IDS}, key=lambda n: ATTR_IDS[n])
    strings = list(res_names)
    def s(x):
        if x not in strings: strings.append(x)
        return strings.index(x)
    s("android"); s(ANDROID_NS)
    body = []
    def chunk(t, hsize, payload): return struct.pack("<HHI", t, hsize, 8 + len(payload)) + payload
    def node(n, line=[1]):
        tag, attrs, kids = n
        enc = []
        for is_ns, name, v in attrs:
            ns = s(ANDROID_NS) if is_ns else 0xffffffff
            if isinstance(v, bool): raw, dt, data = 0xffffffff, T_BOOL, 0xffffffff if v else 0
            elif isinstance(v, int): raw, dt, data = 0xffffffff, T_INT_DEC, v
            elif isinstance(v, tuple): raw, dt, data = 0xffffffff, T_REF if v[0] == "ref" else T_INT_HEX, v[1]
            else: raw, dt, data = s(v), T_STRING, s(v)
            enc.append((ATTR_IDS.get(name, 0xffffffff) if is_ns else 0xffffffff, struct.pack("<IIIHBBI", ns, s(name), raw, 8, 0, dt, data)))
        enc.sort(key=lambda a: a[0])
        a = b"".join(e for _, e in enc)
        body.append(chunk(0x0102, 16, struct.pack("<II", line[0], 0xffffffff) + struct.pack("<IIHHHHHH", 0xffffffff, s(tag), 20, 20, len(attrs), 0, 0, 0) + a))
        line[0] += 1
        for k in kids: node(k)
        body.append(chunk(0x0103, 16, struct.pack("<IIII", line[0], 0xffffffff, 0xffffffff, s(tag)))); line[0] += 1
    ns = struct.pack("<IIII", 1, 0xffffffff, s("android"), s(ANDROID_NS))
    node(root)
    nodes = chunk(0x0100, 16, ns) + b"".join(body) + chunk(0x0101, 16, ns)
    offs, data = [], b""
    for x in strings:
        offs.append(len(data)); u = x.encode("utf-16-le"); data += struct.pack("<H", len(x)) + u + b"\0\0"
    data += b"\0" * (-len(data) % 4)
    hdr = struct.pack("<IIIII", len(strings), 0, 0, 28 + 4 * len(strings), 0)
    pool = chunk(0x0001, 28, hdr + b"".join(struct.pack("<I", o) for o in offs) + data)
    rmap = chunk(0x0180, 8, b"".join(struct.pack("<I", ATTR_IDS[n]) for n in res_names))
    return chunk(0x0003, 8, pool + rmap + nodes)

def is_prime(n):
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for _ in range(40):
        x = pow(secrets.randbelow(n - 3) + 2, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True
def gen_prime(bits):
    while True:
        p = secrets.randbits(bits) | (3 << (bits - 2)) | 1
        if p % 65537 != 1 and is_prime(p): return p
def gen_key():
    p, q = gen_prime(1024), gen_prime(1024)
    n, e = p * q, 65537
    return {"n": n, "e": e, "d": pow(e, -1, (p - 1) * (q - 1))}
def der(tag, body):
    l = len(body)
    ln = bytes([l]) if l < 0x80 else (lambda b: bytes([0x80 | len(b)]) + b)(l.to_bytes((l.bit_length() + 7) // 8, "big"))
    return bytes([tag]) + ln + body
def der_int(v): return der(0x02, v.to_bytes(v.bit_length() // 8 + 1, "big"))
def der_seq(*xs): return der(0x30, b"".join(xs))
def der_oid(s):
    a = [int(x) for x in s.split(".")]; out = bytes([a[0] * 40 + a[1]])
    for v in a[2:]:
        b = [v & 0x7f]; v >>= 7
        while v: b.append(0x80 | (v & 0x7f)); v >>= 7
        out += bytes(reversed(b))
    return der(0x06, out)
NULL = b"\x05\x00"
ALG_SHA256_RSA = der_seq(der_oid("1.2.840.113549.1.1.11"), NULL)
def spki(k): return der_seq(der_seq(der_oid("1.2.840.113549.1.1.1"), NULL), der(0x03, b"\0" + der_seq(der_int(k["n"]), der_int(k["e"]))))
def rsa_sign(k, msg):
    di = bytes.fromhex("3031300d060960864801650304020105000420") + hashlib.sha256(msg).digest()
    kl = (k["n"].bit_length() + 7) // 8
    em = b"\x00\x01" + b"\xff" * (kl - len(di) - 3) + b"\x00" + di
    return pow(int.from_bytes(em, "big"), k["d"], k["n"]).to_bytes(kl, "big")
def cert(k):
    name = der_seq(der(0x31, der_seq(der_oid("2.5.4.3"), der(0x0c, b"nfshpr unified"))))
    validity = der_seq(der(0x17, b"260101000000Z"), der(0x18, b"20560101000000Z"))
    tbs = der_seq(der(0xa0, der_int(2)), der_int(secrets.randbits(62) | 1), ALG_SHA256_RSA, name, validity, name, spki(k))
    return der_seq(tbs, ALG_SHA256_RSA, der(0x03, b"\0" + rsa_sign(k, tbs)))

def build_zip(entries):
    out, cd = bytearray(), bytearray()
    dos_time, dos_date = 0, (2026 - 1980) << 9 | 1 << 5 | 1
    for name, data, align in entries:
        nb = name.encode(); crc = zlib.crc32(data)
        pad = -(len(out) + 30 + len(nb)) % align
        if 0 < pad < 4: pad += align
        extra = struct.pack("<HH", 0xd935, pad - 4) + b"\0" * (pad - 4) if pad else b""
        off = len(out)
        out += struct.pack("<IHHHHHIIIHH", 0x04034b50, 10, 0, 0, dos_time, dos_date, crc, len(data), len(data), len(nb), len(extra)) + nb + extra + data
        cd += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014b50, 10, 10, 0, 0, dos_time, dos_date, crc, len(data), len(data), len(nb), 0, 0, 0, 0, 0, off) + nb
    eocd = struct.pack("<IHHHHIIH", 0x06054b50, 0, 0, len(entries), len(entries), len(cd), len(out), 0)
    return bytes(out), bytes(cd), eocd

def lp(b): return struct.pack("<I", len(b)) + b
def chunked_sha256(sections):
    digests = []
    for sec in sections:
        for i in range(0, len(sec), 1 << 20):
            c = sec[i:i + (1 << 20)]
            digests.append(hashlib.sha256(b"\xa5" + struct.pack("<I", len(c)) + c).digest())
    return hashlib.sha256(b"\x5a" + struct.pack("<I", len(digests)) + b"".join(digests)).digest()
def sign_v2(zip_entries, cd, eocd, k, crt):
    ALG = 0x0103
    digest = chunked_sha256([zip_entries, cd, eocd])
    signed = lp(lp(struct.pack("<I", ALG) + lp(digest))) + lp(lp(crt)) + lp(b"")
    signer = lp(signed) + lp(lp(struct.pack("<I", ALG) + lp(rsa_sign(k, signed)))) + lp(spki(k))
    value = lp(lp(signer))
    pair = struct.pack("<QI", 4 + len(value), 0x7109871a) + value
    size = len(pair) + 8 + 16
    block = struct.pack("<Q", size) + pair + struct.pack("<Q", size) + b"APK Sig Block 42"
    new_eocd = eocd[:16] + struct.pack("<I", len(zip_entries) + len(block)) + eocd[20:]
    return zip_entries + block + cd + new_eocd

def main():
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    CLASSES_DIR.mkdir(parents=True)
    DEX_DIR.mkdir(parents=True)

    java_files = [str(p) for p in (ROOT / "src").rglob("*.java")]
    subprocess.run(["javac", "--release", "11", "-cp", str(ANDROID_JAR), "-d", str(CLASSES_DIR)] + java_files, check=True)
    class_files = [str(p) for p in CLASSES_DIR.rglob("*.class")]
    subprocess.run(["java", "-cp", str(R8_JAR), "com.android.tools.r8.D8", "--min-api", str(MIN_SDK), "--lib", str(ANDROID_JAR), "--output", str(DEX_DIR)] + class_files, check=True)

    if KEY_JSON.exists():
        jd = json.loads(KEY_JSON.read_text())
        k = {a: int(v) for a, v in jd.items() if a != "cert"}
        crt = bytes.fromhex(jd["cert"])
    else:
        k = gen_key(); crt = cert(k)
        KEY_JSON.write_text(json.dumps({**{a: str(v) for a, v in k.items()}, "cert": crt.hex()}))

    entries = [
        ("AndroidManifest.xml", axml(MANIFEST), 4),
        ("classes.dex", (DEX_DIR / "classes.dex").read_bytes(), 4),
    ]
    for asset_file in sorted((ROOT / "assets").rglob("*")):
        if asset_file.is_file():
            rel = asset_file.relative_to(ROOT).as_posix()
            entries.append((rel, asset_file.read_bytes(), 4))

    gamedata_dir = REPO / "nx2android" / ".gamedump" / "NFSHPR" / "NeedForSpeedHotPursuitRemastered-data"
    if gamedata_dir.exists():
        manifest_lines = []
        for sub in ("mods",):
            sub_dir = gamedata_dir / sub
            if sub_dir.is_dir():
                for f in sorted(sub_dir.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(gamedata_dir).as_posix()
                        data = f.read_bytes()
                        entries.append((f"assets/gamedata/{rel}", data, 4))
                        manifest_lines.append(f"{rel}|{len(data)}")
        for fname in ("shaders.dmsv", "nintendo_ext.ttf"):
            f = gamedata_dir / fname
            if f.is_file():
                data = f.read_bytes()
                entries.append((f"assets/gamedata/{fname}", data, 4))
                manifest_lines.append(f"{fname}|{len(data)}")
        if manifest_lines:
            entries.append(("assets/gamedata/manifest.txt", ("\n".join(manifest_lines) + "\n").encode("utf-8"), 4))
            print(f"Embedded {len(manifest_lines)} gamedata files into assets/gamedata/")

    custom_dmhost = REPO / "nx2android" / "nxnative" / "dm" / "android" / "out" / "010029B0118E8000" / "libdmhost.so"
    with zipfile.ZipFile(BASE_APK) as zf:
        for name in zf.namelist():
            if name in ("AndroidManifest.xml", "lib/arm64-v8a/libvulkan.ad07xx.so"):
                continue
            if name == "lib/arm64-v8a/libdmhost.so" and custom_dmhost.exists():
                entries.append((name, custom_dmhost.read_bytes(), 16384))
                print(f"Using built {custom_dmhost}")
                continue
            align = 16384 if name.endswith(".so") else 4
            entries.append((name, zf.read(name), align))

    extra_dir = ROOT / "extra_libs"
    if extra_dir.exists():
        for so in sorted(extra_dir.glob("*.so")):
            if so.name != "libvulkan.purple.so":
                continue
            entries.append((f"lib/arm64-v8a/{so.name}", so.read_bytes(), 16384))

    z, cd, eocd = build_zip(entries)
    apk = sign_v2(z, cd, eocd, k, crt)
    OUT_APK.write_bytes(apk)
    print(f"Built {OUT_APK} ({len(apk)} bytes)")

if __name__ == "__main__":
    main()
