import framebuf

from .base_config import *
from . import fb_chars


def get_bytearr_size(w, h):
    return (w + 7) // 8 * h


def draw_text_scaled(fb, text, x, y, color, scale, max_x):
    is_compressed = (scale <= 1)

    glyph_buf = bytearray(get_bytearr_size(CH_SZ_X, CH_SZ_Y))
    ch_temp = framebuf.FrameBuffer(glyph_buf, CH_SZ_X, CH_SZ_Y, framebuf.MONO_HLSB)

    h = int(round(CH_SZ_Y * scale))
    w = int(round(CH_SZ_X * scale))
    cx = x
    cy = y
    for ch in text:
        ch_temp.fill(1)
        fb_chars.write_ch(ch_temp, ch)

        if is_compressed:
            for px in range(CH_SZ_X):
                for py in range(CH_SZ_Y):
                    if ch_temp.pixel(px, py) == 1:
                        continue
                    
                    px_scaled = int(round(px * scale))
                    py_scaled = int(round(py * scale))
                    size_scaled = max(1, int(round(scale)))

                    fb.fill_rect(
                        cx + px_scaled,
                        cy + py_scaled,
                        size_scaled,
                        size_scaled,
                        color
                    )
        else:
            for px in range(w):
                for py in range(h):
                    px_base = int(round(px / scale))
                    py_base = int(round(py / scale))
                    if px_base >= CH_SZ_X or py_base >= CH_SZ_Y:
                        continue
                    if ch_temp.pixel(px_base, py_base) == 1:
                        continue
                    
                    fb.fill_rect(
                        cx + px,
                        cy + py,
                        1,
                        1,
                        color
                    )

        cx += w
        if cx + w > max_x:
            break
    return cx


def draw_border(fb, w, h, depth):
    fb.fill_rect(0, 0, w, depth, 0)
    fb.fill_rect(0, h - depth, w, depth, 0)
    fb.fill_rect(0, 0, depth, h, 0)
    fb.fill_rect(w - depth, 0, depth, h, 0)


def frame_buf_rot90(src, w, h) -> bytearray:
    buf = bytearray(get_bytearr_size(h, w))
    dst_fb = framebuf.FrameBuffer(buf, h, w, framebuf.MONO_HLSB)
    dst_fb.fill(1)

    for px in range(w):
        for py in range(h):
            dst_fb.pixel(h - py - 1, px, src.pixel(px, py))

    return buf


def write_logo(fb_b, fb_r, w, h):
    pass
