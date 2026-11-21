# main.py — entry for make.fun "The Passport Page of a Country That Isn't There".
#
# Writes one image to /output/entry.png: an invented passport spread for
# the Republic of Vestmara, a North Atlantic island republic that does not
# exist. The image is drawn locally by render_passport.py (Pillow, fixed
# seed, no network, no timestamps), so both of the grader's runs write
# exactly the same file.
#
# If rendering fails in the sandbox (no Pillow, no fonts), it falls back to
# the pre-rendered entry.png committed beside this file, which the same
# script produced — so the output is valid either way.
#
# Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
#   python3 render_passport.py && mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
OUT_PATH = os.path.join(OUT_DIR, "entry.png")
PRE_RENDERED = os.path.join(HERE, "entry.png")
MAX_BYTES = 1048576


def validate(path):
    """Check the output is a whole JPEG, 1024x640, under the 1 MiB gate."""
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 2 or data[0] != 0xFF or data[1] != 0xD8:
        raise ValueError("not a JPEG")
    if data[-2] != 0xFF or data[-1] != 0xD9:
        raise ValueError("not a whole JPEG (no end marker)")
    if len(data) > MAX_BYTES:
        raise ValueError("entry.png is %d bytes, over the 1 MiB gate"
                         % len(data))
    # Walk the JPEG markers to the frame header (SOF0/SOF2) and read size.
    i = 2
    width = height = 0
    while i + 9 < len(data):
        if data[i] != 0xFF:
            raise ValueError("broken JPEG marker")
        marker = data[i + 1]
        length = (data[i + 2] << 8) | data[i + 3]
        if marker in (0xC0, 0xC2):
            height = (data[i + 5] << 8) | data[i + 6]
            width = (data[i + 7] << 8) | data[i + 8]
            break
        i += 2 + length
    if (width, height) != (1024, 640):
        raise ValueError("entry.png is %dx%d, expected 1024x640"
                         % (width, height))
    os.chmod(path, 0o644)
    return len(data)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        sys.path.insert(0, HERE)
        import render_passport
        render_passport.render(OUT_PATH)
        nbytes = validate(OUT_PATH)
        print("rendered /output/entry.png (%d bytes)" % nbytes)
    except Exception as exc:  # noqa: BLE001 - sandbox may lack Pillow/fonts
        print("render failed (%s); using pre-rendered entry.png" % exc,
              file=sys.stderr)
        shutil.copyfile(PRE_RENDERED, OUT_PATH)
        nbytes = validate(OUT_PATH)
        print("copied pre-rendered entry.png (%d bytes)" % nbytes)


if __name__ == "__main__":
    main()
