import math
from typing import Union


def normalize(radians: float) -> float:
    """Нормализовать угол в диапазон [0, 2π)"""
    two_pi = 2 * math.pi
    normalized = radians % two_pi
    if normalized < 0:
        normalized += two_pi
    return normalized


class Angle:
    """Класс для хранения и работы с углами"""
    def __init__(self, radians: float) -> None:
        self._radians = radians

    @classmethod
    def from_degrees(cls, degrees: int) -> 'Angle':
        return cls(math.radians(degrees))

    @property
    def radians(self) -> float:
        """Получить угол в радианах"""
        return self._radians

    @radians.setter
    def radians(self, value: float) -> None:
        """Установить угол в радианах"""
        self._radians = value

    @property
    def degrees(self) -> float:
        """Получить угол в градусах"""
        return math.degrees(self._radians)

    @degrees.setter
    def degrees(self, value: float) -> None :
        """Установить угол в градусах"""
        self._radians = math.radians(value)

    def __float__(self) -> float:
        """Преобразование в float (в радианах)"""
        return self._radians

    def __int__(self) -> int:
        """Преобразование в int (в радианах, округление)"""
        return int(round(self._radians))

    def __str__(self) -> str:
        """Строковое представление"""
        return f"{self.degrees:.2f}°"

    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Angle(radians={self._radians:.6f})"

    def __eq__(self, other) -> bool:
        """Сравнение на равенство"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return abs(normalize(self._radians) - normalize(other._radians)) < 1e-10
        return NotImplemented

    def __lt__(self, other) -> bool:
        """Меньше"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return normalize(self._radians) < normalize(other._radians)
        return NotImplemented

    def __le__(self, other) -> bool:
        """Меньше или равно"""
        if isinstance(other, (int, float)):
            other = Angle(other)
        if isinstance(other, Angle):
            return normalize(self._radians) <= normalize(other._radians)
        return NotImplemented

    def __gt__(self, other) -> bool:
        """Больше"""
        return not self <= other

    def __ge__(self, other) -> bool:
        """Больше или равно"""
        return not self < other

    def __add__(self, other) -> 'Angle':
        """Сложение"""
        if isinstance(other, (int, float)):
            return Angle(self._radians + other)
        if isinstance(other, Angle):
            return Angle(self._radians + other._radians)
        return NotImplemented

    def __radd__(self, other) -> 'Angle':
        """Правое сложение"""
        return self.__add__(other)

    def __sub__(self, other) -> 'Angle':
        """Вычитание"""
        if isinstance(other, (int, float)):
            return Angle(self._radians - other)
        if isinstance(other, Angle):
            return Angle(self._radians - other._radians)
        return NotImplemented

    def __rsub__(self, other: Union['Angle', float]):
        """Правое вычитание"""
        if isinstance(other, (int, float)):
            return Angle(other - self._radians)
        return NotImplemented

    def __mul__(self, scalar: float) -> 'Angle':
        """Умножение на число"""
        if isinstance(scalar, (int, float)):
            return Angle(self._radians * scalar)
        return NotImplemented

    def __rmul__(self, scalar: float) -> 'Angle':
        """Правое умножение на число"""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Angle':
        """Деление на число"""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Division by zero")
            return Angle(self._radians / scalar)
        return NotImplemented

    def __abs__(self) -> 'Angle':
        """Абсолютное значение"""
        return Angle(abs(self._radians))


def to_angle(value: Angle) -> Angle:
    """Преобразование в Angle"""
    if isinstance(value, Angle):
        return value
    elif isinstance(value, (int, float)):
        return Angle(value)
    else:
        raise TypeError("Value must be Angle, int or float")


class AngleRange:
    """Класс для хранения промежутков углов"""
    def __init__(self, start: Union[int, float, Angle], end: Union[int, float, Angle], start_inclusive=True, end_inclusive=True) -> None:

        self.start = to_angle(start)
        self.end = to_angle(end)
        self.start_inclusive = start_inclusive
        self.end_inclusive = end_inclusive

    @classmethod
    def from_degrees(cls, start_deg: int, end_deg: int, start_inclusive=True, end_inclusive=True) -> 'AngleRange':
        start = Angle.from_degrees(start_deg)
        end = Angle.from_degrees(end_deg)
        return cls(start, end, start_inclusive, end_inclusive)

    def __eq__(self, other) -> bool:
        """Сравнение на равенство"""
        if not isinstance(other, AngleRange):
            return False
        return (self.start == other.start and
                self.end == other.end and
                self.start_inclusive == other.start_inclusive and
                self.end_inclusive == other.end_inclusive)

    def __str__(self) -> str:
        """Строковое представление"""
        start_bracket = '[' if self.start_inclusive else '('
        end_bracket = ']' if self.end_inclusive else ')'
        return f"{start_bracket}{self.start}, {self.end}{end_bracket}"

    def __repr__(self) -> str:
        """Представление для отладки"""
        return (f"AngleRange(start={self.start!r}, end={self.end!r}, "
                f"start_inclusive={self.start_inclusive}, end_inclusive={self.end_inclusive})")

    def __abs__(self) -> Angle:
        """Длина промежутка"""
        if self.start <= self.end:
            return Angle(self.end.radians - self.start.radians)

        # Промежуток проходит через 0
        return Angle(2 * math.pi - self.start.radians + self.end.radians)

    def __contains__(self, item: Union['AngleRange', Angle]) -> bool:
        """Проверка принадлежности угла или промежутка"""
        if isinstance(item, (Angle, int, float)):
            angle = to_angle(item)
            return self._contains_angle(angle)
        elif isinstance(item, AngleRange):
            return self._contains_range(item)
        return False

    def _contains_angle(self, angle: Angle) -> bool:
        """Проверка принадлежности угла"""
        if self.start <= self.end:
            # Обычный промежуток
            left_ok = (angle > self.start) or (angle == self.start and self.start_inclusive)
            right_ok = (angle < self.end) or (angle == self.end and self.end_inclusive)
            return left_ok and right_ok

        # Промежуток проходит через 0
        left_ok = (angle > self.start) or (angle == self.start and self.start_inclusive)
        right_ok = (angle < self.end) or (angle == self.end and self.end_inclusive)
        return left_ok or right_ok

    def _contains_range(self, other: 'AngleRange') -> bool:
        """Проверка вхождения промежутка в другой"""
        # Упрощенная проверка - точное совпадение границ
        return (self.start <= other.start and self.end >= other.end and
                (not other.start_inclusive or self.start_inclusive) and
                (not other.end_inclusive or self.end_inclusive))

    def __add__(self, other: 'AngleRange') -> Union['AngleRange', str]:
        """Объединение промежутков"""
        if not isinstance(other, AngleRange):
            return NotImplemented

        if self._intersects(other):
            new_start = min(self.start, other.start)
            new_end = max(self.end, other.end)
            if new_start == self.start:
                new_start_inclusive = self.start_inclusive
            else:
                new_start_inclusive = other.start_inclusive
            if new_end == self.end:
                new_end_inclusive = self.end_inclusive
            else:
                new_end_inclusive = other.end_inclusive
            return AngleRange(new_start, new_end, new_start_inclusive, new_end_inclusive)

        return f"{self} ∪ {other}"

    def __sub__(self, other: 'AngleRange') -> str:
        """Разность промежутков"""
        if not isinstance(other, AngleRange):
            return NotImplemented
        if (self.start_inclusive and not other.start_inclusive) and \
                (self.end_inclusive and not other.end_inclusive) and self._intersects(other):
            return f'{self.start} ∪ {self.end}'
        elif self.start_inclusive and not other.start_inclusive:
            return str(self.start)
        elif self.end_inclusive and not other.end_inclusive:
            return str(self.end)
        elif self == other:
            return "∅"
        elif self._intersects(other):
            new_start = min(self.start, other.start)
            new_end = max(self.end, other.end)
            if self.end > other.end:
                return f"{AngleRange(new_start, other.start, start_inclusive=True, end_inclusive=False)} ∪ " \
                       f"{AngleRange(other.end, new_end, start_inclusive=False, end_inclusive=True)}"
            else:
                return "The first corner range should be larger than the second range."
        else:
            return str(self)


    def _intersects(self, other: 'AngleRange') -> bool:
        """Проверяет, пересекаются ли промежутки"""

        if self.start <= self.end and other.start <= other.end:
            return not (self.end < other.start or other.end < self.start)

        return True


print("класс Angle")

angle1 = Angle.from_degrees(90)  # 45 градусов
angle2 = Angle(math.pi / 2)  # π/4 радиан
angle3 = Angle.from_degrees(440)

print(f"angle1: {angle1} ({angle1.radians:.4f} рад)")
print(f"angle2: {angle2} ({angle2.radians:.4f} рад)")
print(f"angle3: {angle3} ({angle3.radians:.4f} рад)\n")

print(f"{angle1} == {angle2}: {angle1 == angle2}")
print(f"{angle1} <= {angle3}: {angle1 <= angle3}\n")

sum_angle = angle1 + angle3
diff_angle = angle3 - angle1
scaled_angle = angle1 * 2

print(f"{angle1} + {angle3} = {sum_angle}")
print(f"{angle3} - {angle1} = {diff_angle}")
print(f"{angle1} * 2 = {scaled_angle}\n")

print(f"float(angle1): {float(angle1):.4f}")
print(f"int(angle1): {int(angle1)}")
print(f"str(angle1): {str(angle1)}\n")

print("класс AngleRange")

range1 = AngleRange(0, math.pi / 2)  # [0°, 90°]
range2 = AngleRange.from_degrees(45, 135, True, False)
range3 = AngleRange.from_degrees(270, 90)  # Промежуток через 0
range4 = AngleRange.from_degrees(10, 40)
range5 = AngleRange.from_degrees(45, 135)

print(f"range1: {range1}")
print(f"range2: {range2}")
print(f"range3: {range3}")
print(f"range3: {range4}")
print(f"Длина range1: {abs(range1)}")
print(f"Длина range2: {abs(range2)}")
print(f"Длина range3: {abs(range3)}")
print(f"Длина range3: {abs(range4)}\n")

test_angle = Angle.from_degrees(60)
print(f"{test_angle} in {range1}: {test_angle in range1}")
print(f"{test_angle} in {range4}: {test_angle in range4}\n")
print(f"{test_angle} in {range4}: {test_angle in range4}\n")

print(f"{range1} == {range2}: {range1 == range2}\n")
print(f"{range2} == {range5}: {range2 == range5}\n")

print(f"{range1} + {range2} = {range1 + range2}")
print(f"{range1} - {range4} = {range1 - range4}")

print(f"{range5} - {range2} = {range5 - range2}")
print(f"{range5} - {range5} = {range5 - range5}")

#  [Pi / 6, 7 * Pi] in [Pi / 3,  8 * Pi] = True

range6 = AngleRange(math.pi / 6, 7 * math.pi)
range7 = AngleRange(math.pi / 3, math.pi * 8)

print(f"{range6} in {range7}: {range6 in range7}\n")

range6 = AngleRange.from_degrees(20, 60)
range7 = AngleRange.from_degrees(10, 70)

print(f"{range6} in {range7}: {range6 in range7}\n")


range6 = AngleRange.from_degrees(10, 50)
range7 = AngleRange.from_degrees(10, 50, False, False)

print(f"{range6} - {range7} = {range6 - range7}")

range6 = AngleRange(math.pi / 3, math.pi, False, False)
range7 = AngleRange(math.pi / 2, 7 * math.pi / 6)

print(f"{range6} + {range7} = {range6 + range7}")
