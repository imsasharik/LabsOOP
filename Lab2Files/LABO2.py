import json
from enum import Enum
from typing import Dict, List, Optional, ClassVar


class Color(Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97


class ANSI:
    """ANSI escape codes только для цветов"""
    RESET = '\033[0m'

    @staticmethod
    def set_color(color: Color) -> str:
        return f'\033[{color.value}m'


class FontLoader:
    @staticmethod
    def load_font(filename: str) -> Dict[str, List[str]]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Font file {filename} not found!")


class Printer:
    _current_font: ClassVar[Optional[Dict[str, List[str]]]] = None
    _font_height: ClassVar[int] = 0

    def __init__(self, color: Color = Color.WHITE, symbol: str = '*', font_file: str = None):
        self.color = color
        self.symbol = symbol

        if font_file:
            self.load_font(font_file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(ANSI.RESET, end='')

    @classmethod
    def load_font(cls, font_file: str) -> None:
        cls._current_font = FontLoader.load_font(font_file)
        if cls._current_font:
            first_char = next(iter(cls._current_font.values()))
            cls._font_height = len(first_char)

    @classmethod
    def print(cls, text: str, color: Color = Color.WHITE, symbol: str = '*') -> None:

        lines = [''] * cls._font_height

        for char in text.upper():

            if char in cls._current_font:
                char_pattern = cls._current_font[char]

                for i, line in enumerate(char_pattern):
                    rendered_line = line.replace('*', symbol)
                    padded_line = rendered_line.center(cls._font_height)
                    lines[i] += padded_line + ' '

        for line in lines:
            print(ANSI.set_color(color) + line + ANSI.RESET)

    def print_text(self, text: str) -> None:
        self.__class__.print(text, self.color, self.symbol)
        print()


def demonstrate_printer() -> None:
    print("(шрифт 5x5):")
    Printer.load_font('font5x5.json')
    Printer.print("SLENDER", Color.BRIGHT_WHITE, '#')
    print()
    Printer.print("MAN", Color.BLACK, '@')

    print("\n" + "=" * 50 + "\n")

    print("контекстный менеджер:")

    with Printer(Color.MAGENTA, '$', 'font5x5.json') as printer:
        printer.print_text("CHUPA")
        printer.print_text("CHUPS")

    print("\n" + "=" * 50 + "\n")

    print("шрифт 7x7:")
    Printer.load_font('font7x7.json')

    Printer.print("WOW", Color.BRIGHT_YELLOW, '.')
    print()
    Printer.print("SO", Color.BRIGHT_CYAN, ':')
    print()
    Printer.print("BIG", Color.BRIGHT_CYAN, '$')

    print("\n" + "=" * 50 + "\n")

    Printer.load_font('font7x7.json')
    Printer.print("tri", Color.BRIGHT_WHITE, 'Ё')
    print()
    Printer.print("color", Color.BRIGHT_BLUE, '№')
    print()
    Printer.print("yaaay", Color.BRIGHT_RED, '@')

    print("\n" + "=" * 50 + "\n")

    # Статический вызов
    Printer.load_font('font5x5.json')
    Printer.print("SUPER", Color.BRIGHT_MAGENTA, '%')
    print()

    # Контекстный менеджер
    with Printer(Color.BRIGHT_YELLOW, ')', 'font7x7.json') as p:
        p.print_text("SONIC")


if __name__ == "__main__":
    demonstrate_printer()
