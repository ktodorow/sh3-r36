#!/usr/bin/env python3
"""Extract owner shader assembly/declaration; emit private D3D8 token samples.

Deliberately small assembler for selected instructions, not general D3DX replacement.
Unknown grammar fails build. Original text/tokens never enter tracked source.
"""
import hashlib
from pathlib import Path
import re
import struct
import sys


def operand(text, destination=False):
    modifier = 0
    if text.startswith("-"):
        modifier, text = 1 << 24, text[1:]
    relative = re.fullmatch(r"c\[a0\.x\+(\d+)\]", text)
    if relative:
        return operand("c" + relative[1]) | 1 << 13
    match = re.fullmatch(r"(a0|oPos|oD[01]|oT[0-7]|[rvct]\d+)(?:\.([xyzwrgba]+))?", text)
    if not match:
        raise ValueError("Unsupported sample operand")
    name, swizzle = match.groups()
    kinds = {"r": 0, "v": 1, "c": 2, "t": 3, "a": 3, "oPos": 4, "oD": 5, "oT": 6}
    kind = "oPos" if name == "oPos" else name[:2] if name.startswith("o") else name[0]
    index = 0 if name == "oPos" else int(name[len(kind):])
    swizzle = (swizzle or "xyzw").translate(str.maketrans("rgba", "xyzw"))
    if destination:
        bits = sum(1 << "xyzw".index(c) for c in swizzle)
    else:
        swizzle = swizzle.ljust(4, swizzle[-1])
        if len(swizzle) != 4:
            raise ValueError("Invalid sample swizzle")
        bits = sum("xyzw".index(c) << (2 * i) for i, c in enumerate(swizzle))
    return 0x80000000 | modifier | kinds[kind] << 28 | bits << 16 | index


def assemble(text):
    lines = text.splitlines()
    tokens = [0xfffe0101 if lines[0] == "vs.1.1" else 0xffff0101]
    for line in lines[1:]:
        if not line.strip():
            continue
        operation, arguments = line.strip().split(None, 1)
        coissue = operation.startswith("+")
        operation = operation.removeprefix("+")
        opcode, count = {"mov": (1, 2), "add": (2, 3), "mad": (4, 4), "mul": (5, 3),
                         "dp3": (8, 3), "m4x4": (20, 3), "m4x3": (21, 3), "tex": (66, 1),
                         "cnd": (80, 4)}[operation]
        args = [x.strip() for x in arguments.split(",")]
        if len(args) != count:
            raise ValueError("Invalid sample operand count")
        tokens.append(opcode | (1 << 30 if coissue else 0))
        tokens.extend(operand(arg, i == 0) for i, arg in enumerate(args))
    return tokens + [0xffff]


source = Path(sys.argv[1]).read_bytes()
sha1 = hashlib.sha1(source).hexdigest()
if sha1 not in {"d851669ef609b3164e3581aa8dcfbfaec866cb79", "aa2aca6dba19bf510c9c2e92eefdc15e98266581"}:
    raise ValueError("Shader samples require recognized original input")
output = [f'#define SAMPLE_INPUT_SHA1 "{sha1}"']
for name, offset, prefix in [("vs", 0x2b6af4, "vs.1.1"), ("ps", 0x28f300, "ps.1.1"),
                             ("skin", 0x2b6b70, "vs.1.1"), ("color", 0x28f31c, "ps.1.1"),
                             ("precision", 0x28fedc, "ps.1.1")]:
    text = source[offset:source.index(0, offset)].decode("ascii")
    if not text.startswith(prefix + "\n"):
        raise ValueError("Shader sample provenance mismatch")
    words = assemble(text)
    output += [f'#define SAMPLE_{name.upper()}_OFFSET 0x{offset:08x}u',
               f'static const uint32_t sample_{name}[] = {{' + ",".join(f"0x{x:08x}u" for x in words) + "};"]
# Game's declaration selected at CreateVertexShader call 0x463250, table 0x6b6e48, index 2.
decl_va = struct.unpack_from("<I", source, 0x2b6e50)[0]
decl = []
for offset in range(decl_va - 0x400000, decl_va - 0x400000 + 128, 4):
    word = struct.unpack_from("<I", source, offset)[0]
    decl.append(word)
    if word == 0xffffffff:
        break
else:
    raise ValueError("Unterminated game declaration")
output += [f'#define SAMPLE_DECL_VA 0x{decl_va:08x}u',
           'static const uint32_t sample_decl[] = {' + ",".join(f"0x{x:08x}u" for x in decl) + "};"]
skin_decl_va = struct.unpack_from("<I", source, 0x2b6e4c)[0]
skin_decl = struct.unpack_from("<7I", source, skin_decl_va - 0x400000)
if skin_decl[-1] != 0xffffffff:
    raise ValueError("Skin declaration provenance mismatch")
output += ['static const uint32_t sample_skin_decl[] = {' + ",".join(f"0x{x:08x}u" for x in skin_decl) + "};"]
# Original pretransformed quad: DrawPrimitiveUP at 0x41e0a9, FVF 0x104,
# triangle strip, two primitives, 24-byte stride. Keep bytes unchanged.
geometry = struct.unpack_from("<24I", source, 0x2b0d00)
output += ['#define SAMPLE_GEOMETRY_VA 0x006b0d00u',
           'static const uint32_t sample_geometry[] = {' + ",".join(f"0x{x:08x}u" for x in geometry) + "};"]
# Render-target dimensions read by original CreateTexture wrappers 0x427c70/ce0.
for name, offset in [("widths", 0x2b1434), ("heights", 0x2b1444)]:
    sizes = struct.unpack_from("<4I", source, offset)
    if sizes != (64, 512, 256, 256):
        raise ValueError("Resource sample provenance mismatch")
    output += [f'static const uint32_t sample_rt_{name}[] = {{' + ",".join(map(str,sizes)) + "};"]
target = Path(sys.argv[2])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(output) + "\n")
