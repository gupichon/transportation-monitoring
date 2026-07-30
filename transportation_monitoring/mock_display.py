from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from transportation_monitoring.display_backends import DisplayUpdatePlan, build_update_plan
from transportation_monitoring.display_models import (
    TransitDisplayState,
    clock_label,
    compact_line_rows,
    temperature_label,
)


class MockPngDisplay:
    width = 296
    height = 128

    def __init__(self) -> None:
        self.previous_state: TransitDisplayState | None = None
        self.last_image: Image.Image | None = None

    def _load_font(self, size: int, bold: bool = False) -> ImageFont.ImageFont:
        candidates = [
            "C:/Windows/Fonts/DejaVuSansMono.ttf" if not bold else "C:/Windows/Fonts/DejaVuSansMono-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    def render_image(self, state: TransitDisplayState) -> Image.Image:
        image = Image.new("L", (state.width, state.height), color=243)
        draw = ImageDraw.Draw(image)

        section_font = self._load_font(10, bold=True)
        body_font = self._load_font(8)

        header_height = 24
        body_top = header_height + 4
        body_height = state.height - body_top - 4
        section_height = body_height // max(1, len(state.sections))

        draw.rectangle((0, 0, state.width, state.height), fill=243)
        draw.rectangle((0, 0, state.width, 24), fill=217)

        draw.text((10, 6), temperature_label(state), font=body_font, fill=40)

        time_label = clock_label(state)
        if time_label:
            bbox = draw.textbbox((0, 0), time_label, font=body_font)
            draw.text((state.width - (bbox[2] - bbox[0]) - 10, 6), time_label, font=body_font, fill=40)

        for index, section in enumerate(state.sections):
            top = body_top + index * section_height
            bottom = top + section_height - 2
            draw.rounded_rectangle((6, top, state.width - 6, bottom), radius=4, outline=31, fill=255, width=1)
            draw.text((12, top + 3), section.title, font=section_font, fill=17)

            row_y = top + 17
            for row_text in compact_line_rows(section.line_rows)[:3]:
                clipped = row_text if len(row_text) <= 46 else row_text[:43] + "..."
                draw.text((12, row_y), clipped, font=body_font, fill=34)
                row_y += 10

        self.last_image = image
        return image

    def save_png(self, state: TransitDisplayState, output_path: str | Path) -> Path:
        path = Path(output_path)
        image = self.render_image(state)
        image.save(path, format="PNG")
        return path

    def update(self, state: TransitDisplayState) -> DisplayUpdatePlan:
        plan = build_update_plan(self.previous_state, state)
        self.previous_state = state
        return plan


MockMagTagDisplay = MockPngDisplay
