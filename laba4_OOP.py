from typing import Protocol, TypeVar, Any, Generic

# Generic тип для аргументов события
TEventArgs = TypeVar('TEventArgs')


class EventHandler(Protocol[TEventArgs]):
    """Протокол для обработчиков событий"""

    def handle(self, sender: Any, args: TEventArgs) -> None:
        """
        Обработать событие
        Args:
            sender: объект, который вызвал событие
            args: аргументы события
        """
        ...


class Event(Generic[TEventArgs]):

    def __init__(self):
        self._observers = []

    def __iadd__(self, observer):
        self._observers.append(observer)
        return self

    def __isub__(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)
        return self

    def invoke(self, sender, args):
        observers_copy = self._observers[:]
        for observer in observers_copy:
            try:
                observer.handle(sender, args)
            except Exception as e:
                handler_name = getattr(observer, 'name', observer.__class__.__name__)
                print(f"Ошибка в обработчике '{handler_name}': {e}")


class TestHandler:
    def __init__(self, name):
        self.name = name
        self.received_messages = []

    def handle(self, sender, args):
        message = f"{self.name} получил от {sender}: {args}"
        self.received_messages.append(message)
        print(message)


class TestEventArgs:
    def __init__(self, data: str):
        self.data = data

    def __str__(self):
        return f"TestEventArgs(data='{self.data}')"


def test_basic_event_system():
    print("=== ТЕСТ БАЗОВОЙ СИСТЕМЫ СОБЫТИЙ ===")

    # 1. Создаем событие и обработчики
    event = Event[str]()  # Событие для строковых аргументов
    handler1 = TestHandler("Обработчик 1")
    handler2 = TestHandler("Обработчик 2")

    print("\n1. Тест подписки:")
    event += handler1
    event += handler2
    print(f"   Подписано обработчиков: {len(event._observers)}")

    print("\n2. Тест вызова события:")
    event.invoke("Отправитель", "Тестовое сообщение")

    print("\n3. Тест отписки:")
    event -= handler1
    print(f"   Осталось обработчиков: {len(event._observers)}")

    print("\n4. Тест вызова после отписки:")
    event.invoke("Другой отправитель", "Второе сообщение")

    print("\n5. Проверка полученных сообщений:")
    print(f"   Handler1 получил: {len(handler1.received_messages)} сообщений")
    print(f"   Handler2 получил: {len(handler2.received_messages)} сообщений")

    print("\n6. Тест безопасной отписки (несуществующий обработчик):")
    nonexistent_handler = TestHandler("Несуществующий")
    event -= nonexistent_handler  # Не должно упасть с ошибкой
    print("   Отписка несуществующего обработчика прошла безопасно")


def test_error_handling():
    print("\n=== ТЕСТ ОБРАБОТКИ ОШИБОК ===")

    class ErrorHandler:
        def handle(self, sender, args):
            raise ValueError("Искусственная ошибка в обработчике")

    class GoodHandler:
        @staticmethod
        def handle(sender, args):
            print(f"Хороший обработчик получил: {args}")

    event = Event[str]()
    event += ErrorHandler()
    event += GoodHandler()  # Должен выполниться, даже если первый упал

    print("Тест: вызов события с 'падающим' обработчиком...")
    event.invoke("Тест", "Сообщение")  # Не должно прервать выполнение
    print("Программа продолжила работу после ошибки в обработчике!")


# 3. PropertyChangedEventArgs Хранит информацию об изменении свойства
class PropertyChangedEventArgs:
    """Аргументы события после изменения свойства"""
    def __init__(self, property_name: str):
        self.property_name = property_name

    def __str__(self):
        return f"PropertyChangedEventArgs(property='{self.property_name}')"


# 4. ConsoleLoggerHandler - обработчик для вывода в консоль
class ConsoleLoggerHandler:
    """Обработчик для логирования изменений в консоль"""

    def __init__(self, name: str = "ConsoleLogger"):
        self.name = name

    @staticmethod
    def handle(sender: Any, args: PropertyChangedEventArgs) -> None:
        print(f"[ConsoleLogger] Свойство '{args.property_name}' изменено в объекте {sender}")


# 5. PropertyChangingEventArgs
class PropertyChangingEventArgs:
    """Аргументы события до изменения свойства"""

    def __init__(self, property_name: str, old_value: Any, new_value: Any):
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
        self.can_change = True  # По умолчанию разрешаем изменение

    def __str__(self):
        return (f"PropertyChangingEventArgs(property='{self.property_name}', old={self.old_value}, "
                f"new={self.new_value}, "f"can_change={self.can_change})")

# вместо общего валидатора два валидатора для интов и стрингов
# 6. ValidatorHandler - обработчик-валидатор
# class ValidatorHandler:
#     """Обработчик для валидации изменений свойств"""
#
#     def __init__(self, name: str = "Validator"):
#         self.name = name
#
#     @staticmethod
#     def handle(sender: Any, args: PropertyChangingEventArgs) -> None:
#         # Валидация для разных типов свойств
#         if args.property_name == "age" and isinstance(args.new_value, (int, float)):
#             if args.new_value < 0:
#                 print(f"[Validator] Возраст не может быть отрицательным: {args.new_value}")
#                 args.can_change = False
#             elif args.new_value > 150:
#                 print(f"[Validator] Возраст слишком большой: {args.new_value}")
#                 args.can_change = False
#
#         elif args.property_name == "name" and isinstance(args.new_value, str):
#             if len(args.new_value.strip()) == 0:
#                 print(f"[Validator] Имя не может быть пустым")
#                 args.can_change = False
#             elif len(args.new_value) > 32:
#                 print(f"[Validator] Имя слишком длинное: {len(args.new_value)} символов")
#                 args.can_change = False
#
#         elif args.property_name == "price" and isinstance(args.new_value, (int, float)):
#             if args.new_value < 0:
#                 print(f"[Validator] Цена не может быть отрицательной: {args.new_value}")
#                 args.can_change = False
#
#         elif args.property_name == "quantity" and isinstance(args.new_value, int):
#             if args.new_value < 0:
#                 print(f"[Validator] Количество не может быть отрицательным: {args.new_value}")
#                 args.can_change = False


class IntValidatorHandler:
    """Базовый валидатор для целочисленных свойств"""

    def __init__(self, prop_name: str, min_value: int = 0, max_value: int = 100):
        self.name = prop_name
        self.min_value = min_value
        self.max_value = max_value

    def handle(self, sender: Any, args: PropertyChangingEventArgs) -> None:
        """Обработчик валидации"""
        # Проверяем, соответствует ли имя свойства нашему валидатору
        if args.property_name != self.name:
            return

        # Проверяем, является ли значение числом
        if not isinstance(args.new_value, (int, float)):
            print(f"[Validator] {args.property_name} должно быть числом: {args.new_value}")
            args.can_change = False
            return

        # Преобразуем к целому числу, если это float
        value = int(args.new_value)

        # Проверяем минимальное значение
        if value < self.min_value:
            print(f"[Validator] {args.property_name} не может быть меньше {self.min_value}: {value}")
            args.can_change = False
            return

        # Проверяем максимальное значение
        if value > self.max_value:
            print(f"[Validator] {args.property_name} не может быть больше {self.max_value}: {value}")
            args.can_change = False
            return

        # Если все проверки пройдены, можно изменить значение
        print(f"[Validator] {args.property_name} валидация пройдена: {value}")


class StringValidatorHandler:
    """Валидатор для строковых свойств Person и Product"""

    def __init__(self, prop_name: str, min_length: int = 1, max_length: int = 32):
        """
        Args:
            prop_name: Имя свойства для валидации
            min_length: Минимальная длина строки (по умолчанию 1 - не пустая)
            max_length: Максимальная длина строки (по умолчанию 32)
        """
        self.name = prop_name
        self.min_length = min_length
        self.max_length = max_length

    def handle(self, sender: Any, args: PropertyChangingEventArgs) -> None:
        """Обработчик валидации строк"""
        # Проверяем, соответствует ли имя свойства нашему валидатору
        if args.property_name != self.name:
            return

        # Проверяем, является ли значение строкой
        if not isinstance(args.new_value, str):
            print(f"[StringValidator] {args.property_name} должно быть строкой: {args.new_value}")
            args.can_change = False
            return

        # Очищаем строку (удаляем пробелы по краям)
        value = args.new_value.strip()

        # Проверяем минимальную длину (не пустая строка)
        if len(value) < self.min_length:
            print(f"[StringValidator] {args.property_name} не может быть пустым")
            args.can_change = False
            return

        # Проверяем максимальную длину
        if len(value) > self.max_length:
            print(f"[StringValidator] {args.property_name} слишком длинное "
                  f"(максимум {self.max_length} символов): '{value}'")
            args.can_change = False
            return

        # Дополнительные проверки для email
        if args.property_name == "email" and "@" not in value:
            print(f"[StringValidator] Email должен содержать символ '@': '{value}'")
            args.can_change = False
            return

        # Если все проверки пройдены, можно изменить значение
        print(f"[StringValidator] {args.property_name} валидация пройдена: '{value}'")
        # Обновляем значение в args (очищенная строка)
        args.new_value = value


# 7. Классы с автообновляющимися свойствами
class Person:
    """Класс Person с отслеживанием изменений свойств"""

    def __init__(self, name: str = "", age: int = 0, email: str = ""):
        self._name = name
        self._age = age
        self._email = email

        # События
        self.property_changing = Event[PropertyChangingEventArgs]()
        self.property_changed = Event[PropertyChangedEventArgs]()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        # Событие ДО изменения
        changing_args = PropertyChangingEventArgs("name", self._name, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._name
            self._name = value
            # Событие ПОСЛЕ изменения
            self.property_changed.invoke(self, PropertyChangedEventArgs("name"))
            print(f"Имя изменено: '{old_value}' -> '{self._name}'")
        else:
            print(f"Изменение имени отменено: '{self._name}' -> '{value}'")

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        changing_args = PropertyChangingEventArgs("age", self._age, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._age
            self._age = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("age"))
            print(f"Возраст изменен: {old_value} -> {self._age}")
        else:
            print(f"Изменение возраста отменено: {self._age} -> {value}")

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        changing_args = PropertyChangingEventArgs("email", self._email, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._email
            self._email = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("email"))
            print(f"Email изменен: '{old_value}' -> '{self._email}'")
        else:
            print(f"Изменение email отменено: '{self._email}' -> '{value}'")

    def __str__(self):
        return f"Person(name='{self.name}', age={self.age}, email='{self.email}')"


class Product:
    """Класс Product с отслеживанием изменений свойств"""

    def __init__(self, title: str = "", price: float = 0.0, quantity: int = 0):
        self._title = title
        self._price = price
        self._quantity = quantity

        # События
        self.property_changing = Event[PropertyChangingEventArgs]()
        self.property_changed = Event[PropertyChangedEventArgs]()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        changing_args = PropertyChangingEventArgs("title", self._title, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._title
            self._title = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("title"))
            print(f"Название товара изменено: '{old_value}' -> '{self._title}'")
        else:
            print(f"Изменение названия отменено: '{self._title}' -> '{value}'")

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        changing_args = PropertyChangingEventArgs("price", self._price, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._price
            self._price = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("price"))
            print(f"Цена изменена: {old_value:.2f} -> {self._price:.2f}")
        else:
            print(f"Изменение цены отменено: {self._price:.2f} -> {value:.2f}")

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        changing_args = PropertyChangingEventArgs("quantity", self._quantity, value)
        self.property_changing.invoke(self, changing_args)

        if changing_args.can_change:
            old_value = self._quantity
            self._quantity = value
            self.property_changed.invoke(self, PropertyChangedEventArgs("quantity"))
            print(f"Количество изменено: {old_value} -> {self._quantity}")
        else:
            print(f"Изменение количества отменено: {self._quantity} -> {value}")

    def __str__(self):
        return f"Product(title='{self.title}', price={self.price:.2f}, quantity={self.quantity})"


# Демонстрация работы системы
def demonstrate_complete_system():
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ ПОЛНОЙ СИСТЕМЫ СОБЫТИЙ И ВАЛИДАЦИИ")
    print("=" * 60)

    # Создаем обработчики
    console_logger = ConsoleLoggerHandler()
    # validator = ValidatorHandler()

    # СОЗДАЕМ ВАЛИДАТОРЫ С КОНКРЕТНЫМИ ПАРАМЕТРАМИ
    person_age_validator = IntValidatorHandler("age", min_value=0, max_value=150)
    person_name_validator = StringValidatorHandler("name", min_length=1, max_length=32)
    person_email_validator = StringValidatorHandler("email", min_length=1, max_length=32)

    product_quantity_validator = IntValidatorHandler("quantity", min_value=0, max_value=1000)
    product_price_validator = IntValidatorHandler("price", min_value=0, max_value=1000000)
    product_title_validator = StringValidatorHandler("title", min_length=1, max_length=32)

    # Создаем объекты
    person = Person("Иван", 25, "ivan@mail.com")
    product = Product("Ноутбук", 50000.0, 10)

    # Подписываем обработчики на события
    print("\nПОДПИСКА НА СОБЫТИЯ PERSON:")
    person.property_changing += person_age_validator
    person.property_changing += person_name_validator
    person.property_changing += person_email_validator
    person.property_changed += console_logger

    # Подписываем обработчики на события Product
    print("ПОДПИСКА НА СОБЫТИЯ PRODUCT:")
    product.property_changing += product_quantity_validator
    product.property_changing += product_price_validator
    product.property_changing += product_title_validator
    product.property_changed += console_logger

    print(f"Person: {person}")
    print(f"Product: {product}")

    # Тестируем валидные изменения
    print("\nТЕСТ ВАЛИДНЫХ ИЗМЕНЕНИЙ:")
    person.name = "Петр"
    person.age = 30
    person.email = "petr@mail.com"

    product.title = "Игровой ноутбук"
    product.price = 45000.0
    product.quantity = 15

    # Тестируем невалидные изменения (должны быть отменены)
    print("\nТЕСТ НЕВАЛИДНЫХ ИЗМЕНЕНИЙ:")
    person.age = -5  # Отрицательный возраст
    person.name = ""  # Пустое имя
    person.age = 200  # Слишком большой возраст

    product.price = -1000  # Отрицательная цена
    product.quantity = -5  # Отрицательное количество

    # Показываем финальное состояние
    print(f"\nФИНАЛЬНОЕ СОСТОЯНИЕ:")
    print(f"Person: {person}")
    print(f"Product: {product}")

    # Тест отписки от событий
    print("\nТЕСТ ОТПИСКИ ОТ СОБЫТИЙ:")
    person.property_changing -= person_age_validator
    person.property_changing -= person_name_validator
    person.property_changing -= person_email_validator
    person.property_changed -= console_logger

    print("Попытка изменения после отписки:")
    person.age = 35  # Должно измениться без валидации и логирования


if __name__ == "__main__":
    # Базовые тесты
    test_basic_event_system()
    test_error_handling()

    # Полная демонстрация системы
    demonstrate_complete_system()

    print("\nВСЕ ТЕСТЫ ПРОЙДЕНЫ! ЛАБОРАТОРНАЯ РАБОТА ЗАВЕРШЕНА!")
