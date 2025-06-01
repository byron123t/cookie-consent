"""Utils for handling images."""

import base64
import re
from io import BytesIO

from PIL import Image


def encode_to_base64(img_bytes, new_size=None):
    image = Image.open(BytesIO(img_bytes))

    if new_size is not None:
        try:
            image.thumbnail(new_size)
            # image = image.resize(new_size) # resize does not keep aspect ratio
        except IOError as e:
            print(f"Cannot resize: {str(e)}")

    # Convert to JPEG
    # Remove Alpha layer, JPEG does not support transparency.
    image = image.convert('RGB')
    img_byte_arr = BytesIO()
    # Somehow after converting the image.format becomes None, so set manually.
    img_format = 'JPEG'
    image.save(img_byte_arr, format=img_format)
    # img_base64 = f'data:image/jpg;base64,' + base64.b64encode(img_byte_arr.getvalue()).decode('ascii')

    # Save as PNG, but the size is big like
    # image.save(img_byte_arr, format=image.format, optimize=True)

    img_base64 = f'data:image/{img_format.lower()};base64,' + base64.b64encode(img_byte_arr.getvalue()).decode('ascii')

    return img_base64

def base64_to_image(base64_str, image_path=None):
    """Save base64 to file. From https://www.programmersought.com/article/8497913323/"""
    base64_data = re.sub('^data:image/.+;base64,', '', base64_str)
    byte_data = base64.b64decode(base64_data)
    image_data = BytesIO(byte_data)
    img = Image.open(image_data)
    if image_path:
        img.save(image_path)
    return img
