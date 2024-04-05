import struct

import bpy
import numpy as np
from PIL import Image


def pil_to_image(pil_image: Image, name="NewImage"):
    width, height = pil_image.width, pil_image.height
    normalized = 1.0 / 255.0
    bpy_image = bpy.data.images.new(name, width=width, height=height)
    # ...
    pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
    bpy_image.pixels[:] = (np.asarray(pil_image.convert("RGBA"), dtype=np.float32) * normalized).ravel()
    return bpy_image


def image_to_pil(bpy_image):
    pixels = [int(px * 255) for px in bpy_image.pixels[:]]
    bytes = struct.pack("%sB" % len(pixels), *pixels)
    pil_image = Image.frombytes("RGBA", (bpy_image.size[0], bpy_image.size[1]), bytes)
    return pil_image
