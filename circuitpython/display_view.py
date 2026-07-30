import displayio
import terminalio
import time

from adafruit_display_text import label


WHITE = 0xFFFFFF
LIGHT_GRAY = 0xAAAAAA
DARK_GRAY = 0x555555
BLACK = 0x000000


class MagTagDisplayView:
    def __init__(self, display, max_sections=2, max_rows=3):
        self.display = display
        self.max_sections = max_sections
        self.max_rows = max_rows
        self.last_signature = None
        self.root = displayio.Group()
        self.display.root_group = self.root

        background_bitmap = displayio.Bitmap(
            self.display.width // 8,
            self.display.height // 8,
            1,
        )
        background_palette = displayio.Palette(1)
        background_palette[0] = WHITE
        background = displayio.TileGrid(
            background_bitmap,
            pixel_shader=background_palette,
        )
        background_group = displayio.Group(scale=8)
        background_group.append(background)
        self.root.append(background_group)

        separator_bitmap = displayio.Bitmap(self.display.width, 1, 1)
        separator_palette = displayio.Palette(1)
        separator_palette[0] = LIGHT_GRAY
        self.root.append(
            displayio.TileGrid(
                separator_bitmap,
                pixel_shader=separator_palette,
                x=0,
                y=24,
            )
        )

        self.temperature = label.Label(terminalio.FONT, text="", color=BLACK, x=10, y=12)
        self.clock = label.Label(terminalio.FONT, text="", color=DARK_GRAY, x=220, y=12)
        self.root.append(self.temperature)
        self.root.append(self.clock)

        self.section_titles = []
        self.section_rows = []
        for section_index in range(max_sections):
            top = 34 + section_index * 45
            if section_index:
                self.root.append(
                    displayio.TileGrid(
                        separator_bitmap,
                        pixel_shader=separator_palette,
                        x=0,
                        y=top - 10,
                    )
                )
            title = label.Label(terminalio.FONT, text="", color=BLACK, x=12, y=top)
            self.section_titles.append(title)
            self.root.append(title)
            rows = []
            for row_index in range(max_rows):
                row = label.Label(
                    terminalio.FONT,
                    text="",
                    color=DARK_GRAY,
                    x=12,
                    y=top + 12 + row_index * 10,
                )
                rows.append(row)
                self.root.append(row)
            self.section_rows.append(rows)

    def update(self, state, now=None):
        signature = state.visible_signature(now)
        if signature == self.last_signature:
            return False
        self.temperature.text = signature[0]
        self.clock.text = signature[1]
        sections = signature[2]
        for index in range(self.max_sections):
            if index < len(sections):
                title, rows = sections[index]
                self.section_titles[index].text = title
            else:
                rows = ()
                self.section_titles[index].text = ""
            for row_index, row_label in enumerate(self.section_rows[index]):
                row_label.text = rows[row_index][:42] if row_index < len(rows) else ""

        wait = getattr(self.display, "time_to_refresh", 0)
        if wait:
            time.sleep(wait)
        self.display.refresh()
        self.last_signature = signature
        return True
