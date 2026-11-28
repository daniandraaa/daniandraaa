#!/usr/bin/env python3
"""Rebuild the decorative hero. Requires Pillow; daily analytics do not."""
from math import sin, pi
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(name, size)


def main():
    frames = []
    for index in range(48):
        image = Image.new('RGB', (1200, 330), '#080f18')
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((1, 1, 1198, 328), radius=20, outline='#233445', width=2)
        draw.text((48, 36), 'YUDIAZ CREATIVE STUDIO  /  FOUNDER’S FIELD NOTES', font=font(15), fill='#55dce5')
        draw.text((45, 90), 'Daniandra', font=font(66, True), fill='#e7f0f6')
        draw.text((48, 174), 'Prayudisty Ilham', font=font(31), fill='#b4c8d7')
        draw.text((48, 269), 'PRODUCT ARCHITECTURE   /   AI ORCHESTRATION   /   CREATIVE ENGINEERING', font=font(14), fill='#9aaebe')
        # Abstract signal, deliberately not presented as activity data.
        for line in range(5):
            points = [(x, 156 + line * 18 + 26*sin((x-790)/80 + index*pi/24 + line*.32)) for x in range(810, 1154)]
            draw.line(points, fill=['#17404e', '#226675', '#3298a6', '#55dce5', '#a2edf1'][line], width=2)
        x = 810 + int(index/47 * 343)
        draw.ellipse((x-4, 237, x+4, 245), fill='#55dce5')
        frames.append(image)
    frames[0].save(ROOT/'assets/hero.gif', save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True, disposal=2)
    print('Created assets/hero.gif: 48 frames, 1200 × 330')


if __name__ == '__main__':
    main()
