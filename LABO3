import re
import datetime
import socket
import ftplib
import sys
from enum import Enum
from typing import List, Protocol

# 1. Перечислитель LogLevel
class LogLevel(Enum):
    INFO = 1
    WARN = 2
    ERROR = 3

# 2. протокол фильтров
class LogFilterProtocol(Protocol):
    def match(self, log_level: LogLevel, text: str) -> bool:
        pass


# 3. Классы фильтров
class SimpleLogFilter:
    """ для фильтрации по вхождению паттерна,
     задаваемого текстом, в текст сообщения"""

    def __init__(self, pattern: str):
        self.pattern = pattern.lower()

    def match(self, log_level: LogLevel, text: str) -> bool:
        return self.pattern in text.lower()


class ReLogFilter:
    """для фильтрации по вхождению паттерна,
     задаваемого регулярным выражением, в текст сообщения"""

    def __init__(self, pattern: str):
        try:
            self.pattern = re.compile(pattern)
        except re.error as e:
            print(f"Ошибка компиляции регулярного выражения '{pattern}': {e}")

    def match(self, log_level: LogLevel, text: str) -> bool:
        return bool(self.pattern.search(text))


class LevelFilter:
    """Для фильтрации по LogLevel"""

    def __init__(self, min_level: LogLevel):
        self.min_level = min_level

    def match(self, log_level: LogLevel, text: str) -> bool:
        return log_level.value >= self.min_level.value


# 4. Протокол обработчиков
class LogHandlerProtocol(Protocol):
    def handle(self, log_level: LogLevel, text: str) -> None:
        pass


# 5. Классы обработчиков
class FileHandler:
    """Запись логов в файл"""

    def __init__(self, filename: str):
        try:
            # Проверяем возможность записи в файл
            with open(filename, 'a', encoding='utf-8') as f:
                f.write('')  # Пробная запись
            self.filename = filename
        except PermissionError as e:
            print(f"Ошибка доступа к файлу '{filename}': {e}")
            self.filename = None
        except OSError as e:
            print(f"Системная ошибка при работе с файлом '{filename}': {e}")
            self.filename = None
        except Exception as e:
            print(f"Неожиданная ошибка при инициализации FileHandler: {e}")
            self.filename = None

    def handle(self, log_level: LogLevel, text: str) -> None:
        if self.filename is None:
            print(f"FileHandler: невозможно записать в файл - {text}")
            return

        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(text + '\n')
        except PermissionError as e:
            print(f"Ошибка доступа при записи в '{self.filename}': {e}")
        except OSError as e:
            print(f"Системная ошибка записи в '{self.filename}': {e}")
        except Exception as e:
            print(f"Неожиданная ошибка при записи в файл: {e}")


class SocketHandler:
    """Отправка логов через сокет"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def handle(self, log_level: LogLevel, text: str) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(f"{text}\n".encode('utf-8'))
        except Exception as e:
            print(f"Socket error: {e}")


class ConsoleHandler:
    """Вывод логов в консоль"""
    @staticmethod
    def handle(log_level: LogLevel, text: str) -> None:
        colors = {
            LogLevel.INFO: '\033[94m',  # синий
            LogLevel.WARN: '\033[93m',  # желтый
            LogLevel.ERROR: '\033[91m'  # красный
        }
        reset = '\033[0m'
        print(f"{colors[log_level]}{text}{reset}")


class SyslogHandler:
    """Запись в системные логи"""
    @staticmethod
    def handle(log_level: LogLevel, text: str) -> None:
        # Принудительный вывод с форматированием и сбросом буфера
        timestamp = datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        formatted_message = f"SYSLOG [{log_level.name}] [{timestamp}] {text}"
        print(formatted_message, file=sys.stderr)
        sys.stderr.flush()  # Принудительно сбросить буфер


class FtpHandler:
    """Запись логов на FTP сервер"""
    def __init__(self, host: str, username: str, password: str, remote_path: str):
        self.host = host
        self.username = username
        self.password = password
        self.remote_path = remote_path

    def handle(self, log_level: LogLevel, text: str) -> None:
        try:
            with ftplib.FTP(self.host) as ftp:
                ftp.login(self.username, self.password)
                # Упрощенная реализация - добавляем в файл на FTP
                temp_file = f"temp_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(text + '\n')

                with open(temp_file, 'rb') as f:
                    ftp.storbinary(f"STOR {self.remote_path}", f)
        except Exception as e:
            print(f"FTP error: {e}")


# 6. Протокол для форматтеров
class LogFormatterProtocol(Protocol):
    def format(self, log_level: LogLevel, text: str) -> str:
        pass


# 7. Класс форматтера
class StandardFormatter:
    """Форматтер с добавлением уровня и времени"""

    def __init__(self, time_format: str = '%Y.%m.%d %H:%M:%S'):
        self.time_format = time_format

    def format(self, log_level: LogLevel, text: str) -> str:
        timestamp = datetime.datetime.now().strftime(self.time_format)
        return f"[{log_level.name}] [{timestamp}] {text}"


# 8. Основной класс Logger
class Logger:
    def __init__(self,
                 filters: List[LogFilterProtocol],
                 formatters: List[LogFormatterProtocol],
                 handlers: List[LogHandlerProtocol]):
        self.filters = filters
        self.formatters = formatters
        self.handlers = handlers

    def log(self, log_level: LogLevel, text: str) -> None:
        # Применяем фильтры
        for filter_obj in self.filters:
            if not filter_obj.match(log_level, text):
                return  # Сообщение не прошло фильтр

        # Применяем форматтеры
        formatted_text = text
        for formatter in self.formatters:
            formatted_text = formatter.format(log_level, formatted_text)

        # Передаем обработчикам
        for handler in self.handlers:
            handler.handle(log_level, formatted_text)

    def log_info(self, text: str) -> None:
        self.log(LogLevel.INFO, text)

    def log_warn(self, text: str) -> None:
        self.log(LogLevel.WARN, text)

    def log_error(self, text: str) -> None:
        self.log(LogLevel.ERROR, text)


def test_filters():
    print("=== ТЕСТ ФИЛЬТРАЦИИ ===")

    # Тест LevelFilter
    level_filter = LevelFilter(LogLevel.WARN)
    print(f"LevelFilter WARN + INFO: {level_filter.match(LogLevel.INFO, 'test')}")  # False
    print(f"LevelFilter WARN + WARN: {level_filter.match(LogLevel.WARN, 'test')}")  # True
    print(f"LevelFilter WARN + ERROR: {level_filter.match(LogLevel.ERROR, 'test')}")  # True

    # Тест SimpleLogFilter
    text_filter = SimpleLogFilter("error")
    print(f"SimpleFilter 'error' in text: {text_filter.match(LogLevel.INFO, 'some error occurred')}")  # True
    print(f"SimpleFilter 'error' not in text: {text_filter.match(LogLevel.INFO, 'normal message')}")  # False

    # Тест ReLogFilter
    relog_filter = ReLogFilter(r"user\d+")
    print(f"ReLogFilter matches: {relog_filter.match(LogLevel.INFO, 'login user123')}")  # True
    print(f"ReLogFilter no match: {relog_filter.match(LogLevel.INFO, 'login admin')}")  # False


def test_formatter():
    print("\n=== ТЕСТ ФОРМАТТЕРА ===")

    # Тестируем разные форматы времени
    test_cases = [
        ('%Y.%m.%d %H:%M:%S', "Стандартный формат"),
        ('%d/%m/%Y %H:%M', "Европейский формат"),
        ('%H:%M:%S', "Только время"),
        ('%Y-%m-%d', "Только дата"),
    ]

    for time_format, description in test_cases:
        formatter = StandardFormatter(time_format)
        formatted = formatter.format(LogLevel.ERROR, f"Тест: {description}")
        print(f"{description}: {formatted}")

    # Тестируем разные уровни логирования
    print("\n--- Тест уровней логирования ---")
    formatter = StandardFormatter()
    for level in LogLevel:
        formatted = formatter.format(level, "Тестовое сообщение")
        print(f"Уровень {level.name}: {formatted}")


def test_handlers():
    print("\n=== ТЕСТ ОБРАБОТЧИКОВ ===")

    # ConsoleHandler
    console = ConsoleHandler()
    console.handle(LogLevel.INFO, "Тест консоли - INFO")
    console.handle(LogLevel.WARN, "Тест консоли - WARN")
    console.handle(LogLevel.ERROR, "Тест консоли - ERROR")

    # FileHandler
    file_handler = FileHandler("test.log")
    file_handler.handle(LogLevel.INFO, "Тест записи в файл")
    print("Проверьте файл 'test.log'")

    # SyslogHandler
    syslog = SyslogHandler()
    syslog.handle(LogLevel.ERROR, "Тест системных логов")


def comprehensive_logger_test():
    print("\n=== КОМПЛЕКСНЫЙ ТЕСТ LOGGER ===")

    # Создаем логгер с разными комбинациями
    filters = [
        LevelFilter(LogLevel.INFO),  # Все уровни
        SimpleLogFilter("test")  # Только сообщения с "test"
    ]

    formatters = [StandardFormatter()]
    handlers = [ConsoleHandler(), FileHandler("detailed_test.log")]

    logger = Logger(filters, formatters, handlers)

    # Тестовые сценарии
    test_cases = [
        (LogLevel.INFO, "Обычное сообщение"),  # Должно быть отфильтровано (нет "test")
        (LogLevel.INFO, "Тестовое сообщение test"),  # Должно пройти
        (LogLevel.WARN, "Предупреждение test"),  # Должно пройти
        (LogLevel.ERROR, "Ошибка test"),  # Должно пройти
    ]

    for level, message in test_cases:
        print(f"\nТест: {level.name} - '{message}'")
        logger.log(level, message)


def test_processing_chain():
    print("\n=== ТЕСТ ЦЕПОЧКИ ОБРАБОТКИ ===")

    class TestHandler(LogHandlerProtocol):
        def __init__(self, name):
            self.name = name
            self.messages = []

        def handle(self, log_level: LogLevel, text: str) -> None:
            self.messages.append(f"{self.name}: {text}")
            print(f"{self.name} получил: {text}")

    # Создаем тестовые обработчики
    handler1 = TestHandler("Handler1")
    handler2 = TestHandler("Handler2")

    logger = Logger(
        filters=[LevelFilter(LogLevel.INFO)],
        formatters=[StandardFormatter()],
        handlers=[handler1, handler2]
    )

    logger.log_info("Сообщение для всех обработчиков")
    print(f"Handler1 получил {len(handler1.messages)} сообщений")
    print(f"Handler2 получил {len(handler2.messages)} сообщений")


def verify_file_output():
    print("\n=== ПРОВЕРКА ФАЙЛОВЫХ ВЫХОДОВ ===")

    # Записываем тестовые данные
    file_handler = FileHandler("verification.log")
    test_messages = [
        (LogLevel.INFO, "Первое сообщение"),
        (LogLevel.WARN, "Второе сообщение"),
        (LogLevel.ERROR, "Третье сообщение")
    ]

    for level, message in test_messages:
        formatted = StandardFormatter().format(level, message)
        file_handler.handle(level, formatted)

    # Читаем и проверяем
    try:
        with open("verification.log", "r", encoding="utf-8") as f:
            content = f.read()
            print("Содержимое файла:")
            print(content)
            lines = content.strip().split('\n')
            print(f"Записано строк: {len(lines)} (ожидается: 3)")
    except FileNotFoundError:
        print("ОШИБКА: Файл не создан!")


def automated_test():
    print("\n=== АВТОМАТИЗИРОВАННАЯ ПРОВЕРКА ===")

    test_results = {
        "LevelFilter": False,
        "SimpleFilter": False,
        "RegexFilter": False,
        "Formatter": False,
        "MultipleHandlers": False
    }

    # Тест LevelFilter
    level_filter = LevelFilter(LogLevel.WARN)
    test_results["LevelFilter"] = (
            not level_filter.match(LogLevel.INFO, "test") and  # INFO < WARN → False
            level_filter.match(LogLevel.WARN, "test") and  # WARN == WARN → True
            level_filter.match(LogLevel.ERROR, "test")  # ERROR > WARN → True
    )

    # Тест SimpleFilter
    text_filter = SimpleLogFilter("secret")
    test_results["SimpleFilter"] = (
            text_filter.match(LogLevel.INFO, "secret data") and
            not text_filter.match(LogLevel.INFO, "public data")
    )

    # Тест RegexFilter
    regex_filter = ReLogFilter(r"\d+")
    test_results["RegexFilter"] = (
            regex_filter.match(LogLevel.INFO, "error 404") and
            not regex_filter.match(LogLevel.INFO, "error text")
    )

    # Тест Formatter
    formatter = StandardFormatter()
    formatted = formatter.format(LogLevel.ERROR, "test")
    test_results["Formatter"] = (
            "[ERROR]" in formatted and
            "test" in formatted and
            "202" in formatted  # год в timestamp
    )

    # Вывод результатов
    print("Результаты тестов:")
    for test_name, passed in test_results.items():
        status = "✓ ПРОЙДЕН" if passed else "✗ НЕ ПРОЙДЕН"
        print(f"  {test_name}: {status}")

    all_passed = all(test_results.values())
    print(f"\nИтог: {'ВСЕ ТЕСТЫ ПРОЙДЕНЫ' if all_passed else 'ЕСТЬ ОШИБКИ'}")


if __name__ == "__main__":
    test_filters()
    test_formatter()
    test_handlers()
    comprehensive_logger_test()
    test_processing_chain()
    verify_file_output()
    automated_test()
