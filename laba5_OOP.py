import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Sequence, TypeVar, Generic, Optional, List, Any
from pathlib import Path
import os
import time


# 1. Класс User
@dataclass(order=True)  # order=True позволяет сортировать по полю name
class User:
    """Класс пользователя системы"""
    id: int = field(compare=False)
    name: str = field(compare=True)
    login: str
    password: str = field(repr=False)  # не показывается при выводе
    email: Optional[str] = None
    address: Optional[str] = None

    def __str__(self) -> str:
        """Строковое представление без пароля"""
        email_str = f", email='{self.email}'" if self.email else ""
        address_str = f", address='{self.address}'" if self.address else ""
        return f"User(id={self.id}, name='{self.name}', login='{self.login}'{email_str}{address_str})"


T = TypeVar('T')


# 2. Протокол для репозитория
class DataRepositoryProtocol(Protocol[T]):
    """Протокол для системы CRUD операций"""

    @abstractmethod
    def get_all(self) -> Sequence[T]:
        """Получить все записи"""
        ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Получить запись по ID"""
        ...

    @abstractmethod
    def add(self, item: T) -> None:
        """Добавить новую запись"""
        ...

    @abstractmethod
    def update(self, item: T) -> None:
        """Обновить существующую запись"""
        ...

    @abstractmethod
    def delete(self, item: T) -> None:
        """Удалить запись"""
        ...


# 2. Протокол для репозитория пользователей
class UserRepositoryProtocol(DataRepositoryProtocol[User]):
    """Протокол для репозитория пользователей"""

    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]:
        """Получить пользователя по логину"""
        ...


# 3. Реализация DataRepository с JSON
class JsonDataRepository(Generic[T]):
    """Репозиторий для хранения данных в JSON файле"""
    def __init__(self, filename: str, data_class: type, auto_sort: bool = False, sort_key: Optional[callable] = None):
        self.filename = filename
        self.data_class = data_class
        self.auto_sort = auto_sort
        self.sort_key = sort_key
        self._ensure_file_exists()
        self._validate_and_fix_data_on_load()

    def _validate_and_fix_data_on_load(self) -> None:
        """Проверить и исправить данные при загрузке репозитория"""
        data = self._read_raw_data()  # Читаем без автоматического исправления
        fixed_data = self._fix_duplicate_ids(data)

        # Если данные изменились - сохраняем исправленные
        if fixed_data != data:
            self._write_data(fixed_data)
            print(f" Файл {self.filename} автоматически исправлен (дубликаты ID)")

    def _write_data(self, data: List[dict]) -> None:
        """Записать данные в файл с возможной сортировкой"""
        # Если задана функция сортировки
        if self.sort_key:
            # Преобразуем в объекты, сортируем, обратно в словари
            items = [self.data_class(**item) for item in data]
            sorted_items = sorted(items, key=self.sort_key)
            data = [self._object_to_dict(item) for item in sorted_items]

        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except FileNotFoundError:
            print("ошибка записи в файл")

    def _read_raw_data(self) -> List[dict]:
        """Прочитать данные из файла без автоматического исправления"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _read_data(self) -> List[dict]:
        """Прочитать данные из файла"""
        return self._read_raw_data()  # Теперь исправление только при загрузке

    @staticmethod
    def _fix_duplicate_ids(data: List[dict]) -> List[dict]:
        """Исправить дублирующиеся ID в данных"""
        if not data:
            return data

        seen_ids = set()
        fixed_data = []

        # Фильтруем None значения и находим максимальный ID
        ids = (item.get('id') for item in data)
        valid_ids = (id for id in ids if id is not None and isinstance(id, (int, float)))
        next_id = max(valid_ids, default=0) + 1

        for item in data:
            item_copy = item.copy()
            item_id = item_copy.get('id')

            if item_id is None or item_id <= 0:
                # Нет ID - назначаем новый
                item_copy['id'] = next_id
                fixed_data.append(item_copy)
                next_id += 1

            elif item_id in seen_ids:
                # Дубликат ID - меняем
                item_copy['id'] = next_id
                fixed_data.append(item_copy)
                next_id += 1

            else:
                # Уникальный ID - оставляем
                seen_ids.add(item_id)
                fixed_data.append(item_copy)

        return fixed_data

    def _ensure_file_exists(self) -> None:
        """Создать файл если он не существует"""
        if not Path(self.filename).exists():
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)

    # def _read_data(self) -> List[dict]:
    #     """Прочитать данные из файла"""
    #     try:
    #         with open(self.filename, 'r', encoding='utf-8') as f:
    #             return json.load(f)
    #     except (json.JSONDecodeError, FileNotFoundError):
    #         return []

    # def _write_data(self, data: List[dict]) -> None:
    #     """Записать данные в файл"""
    #     with open(self.filename, 'w', encoding='utf-8') as f:
    #         json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self) -> Sequence[T]:
        """Получить все записи"""
        data = self._read_data()
        return [self.data_class(**item) for item in data]

    def get_by_id(self, id: int) -> Optional[T]:
        """Получить запись по ID"""
        data = self._read_data()
        for item in data:
            if item.get('id') == id:
                return self.data_class(**item)
        return None

    def add(self, item: T) -> None:
        """Добавить новую запись"""
        data = self._read_data()

        # Проверяем уникальность ID
        existing_ids = {d.get('id') for d in data}

        if item.id in existing_ids:
            # Находим следующий свободный ID
            next_id = max(existing_ids, default=0) + 1
            print(f"  ID {item.id} уже существует. Назначаем ID {next_id}")
            item.id = next_id

        # Преобразуем объект в словарь
        item_dict = self._object_to_dict(item)
        data.append(item_dict)
        self._write_data(data)

    def update(self, item: T) -> None:
        """Обновить существующую запись"""
        data = self._read_data()
        updated = False

        for i, record in enumerate(data):
            if record.get('id') == item.id:
                data[i] = self._object_to_dict(item)
                updated = True
                print(f"Обновлена запись с ID {item.id}")
                break

        if not updated:
            # 2. Если не нашли по ID - НЕ СОЗДАВАЕМ НОВУЮ!
            # Вместо этого ищем по другим критериям или выбрасываем ошибку
            print(f"  Запись с ID {item.id} не найдена")
            print(f"   Пожалуйста, используйте метод add() для создания новой записи")
            return  # Прерываем выполнение

            # ИЛИ если хочешь автоматически создать с новым ID:
            # existing_ids = {d.get('id') for d in data}
            # if item.id in existing_ids:
            #     next_id = max(existing_ids, default=0) + 1
            #     print(f"  ID {item.id} уже существует. Создаем с ID {next_id}")
            #     item.id = next_id
            # data.append(self._object_to_dict(item))

        self._write_data(data)

    def delete(self, item: T) -> None:
        """Удалить запись"""
        data = self._read_data()
        new_data = [record for record in data if record.get('id') != item.id]

        if len(new_data) == len(data):
            raise ValueError(f"Запись с ID {item.id} не найдена")

        self._write_data(new_data)

    @staticmethod
    def _object_to_dict(obj: Any) -> dict:
        """Преобразовать объект в словарь"""
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        elif hasattr(obj, '_asdict'):
            return obj.asdict()
        return {}


# 4. Реализация UserRepository
class UserRepository(JsonDataRepository[User], UserRepositoryProtocol):
    """Репозиторий пользователей на основе JSON хранилища"""

    def __init__(self, filename: str = "users_demo.json"):
        super().__init__(filename, User, auto_sort=True, sort_key=lambda u: u.name)

    def get_by_login(self, login: str) -> Optional[User]:
        """Получить пользователя по логину"""
        data = self._read_data()
        for item in data:
            if item.get('login') == login:
                return User(**item)
        return None

    def get_all(self) -> Sequence[User]:
        """Получить всех пользователей (всегда отсортировано по имени)"""
        users = super().get_all()  # Получаем базовый список
        return sorted(users)  # Сортируем по name

    def update(self, item: User) -> None:
        """Обновить пользователя с поиском по ID или логину"""
        data = self._read_data()
        updated = False

        # 1. Ищем по ID (основной способ)
        for i, record in enumerate(data):
            if record.get('id') == item.id:
                data[i] = self._object_to_dict(item)
                updated = True
                print(f"Обновлен пользователь ID {item.id}: {item.name}")
                break

        # 2. Если не нашли по ID, ищем по логину
        if not updated:
            for i, record in enumerate(data):
                if record.get('login') == item.login:
                    # Нашли по логину, но ID другой - меняем ID на найденный
                    old_id = record.get('id')
                    print(f"  Обновление по логину: {item.login} (ID был {item.id}, меняем на {old_id})")
                    item.id = old_id  # Используем ID из файла
                    data[i] = self._object_to_dict(item)
                    updated = True
                    break

        if not updated:
            print(f"  Пользователь не найден (ID: {item.id}, login: {item.login})")
            return  # Не создаем нового!

        self._write_data(data)


# 5. Протокол сервиса авторизации
class AuthServiceProtocol(Protocol):
    """Протокол для сервиса авторизации"""

    @property
    @abstractmethod
    def is_authorized(self) -> bool:
        """Проверка авторизации текущего пользователя"""
        ...

    @property
    @abstractmethod
    def current_user(self) -> Optional[User]:
        """Текущий авторизованный пользователь"""
        ...

    @abstractmethod
    def sign_in(self, login: str, password: str) -> bool:
        """Вход пользователя в систему"""
        ...

    @abstractmethod
    def sign_out(self) -> None:
        """Выход пользователя из системы"""
        ...


# 6. Реализация сервиса авторизации
class FileAuthService(AuthServiceProtocol):
    """Сервис авторизации с хранением сессии в файле"""

    def __init__(self, user_repository: UserRepositoryProtocol, session_file: str = "session.dat"):
        self.user_repository = user_repository
        self.session_file = session_file
        self._current_user: Optional[User] = None
        self._load_session()

    def _load_session(self) -> None:
        """Загрузить сессию из файла (автоматическая авторизация)"""
        try:
            if Path(self.session_file).exists():
                with open(self.session_file, 'rb') as f:
                    session_data = pickle.load(f)
                    user_id = session_data.get('user_id')

                    if user_id:
                        user = self.user_repository.get_by_id(user_id)
                        if user:
                            self._current_user = user
                            print(f"Автоматически авторизован пользователь: {user.name}")
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")

    def _save_session(self) -> None:
        """Сохранить сессию в файл"""
        try:
            session_data = {'user_id': self._current_user.id if self._current_user else None}
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")

    def _clear_session(self) -> None:
        """Очистить файл сессии"""
        try:
            if Path(self.session_file).exists():
                os.remove(self.session_file)
        except Exception as e:
            print(f"Ошибка очистки сессии: {e}")

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def sign_in(self, login: str, password: str) -> bool:
        """Вход пользователя в систему"""
        user = self.user_repository.get_by_login(login)

        if not user:
            print(f"Пользователь с логином '{login}' не найден")
            return False

        if user.password != password:
            print("Неверный пароль")
            return False

        self._current_user = user
        self._save_session()
        print(f"Успешный вход! Добро пожаловать, {user.name}!")
        return True

    def sign_out(self) -> None:
        """Выход пользователя из системы"""
        if self._current_user:
            print(f"До свидания, {self._current_user.name}!")
            self._current_user = None
        self._clear_session()


# для добавления пользователя с консоли, Сервис для ввода/вывода
class ConsoleService:
    @staticmethod
    def input_user() -> Optional[User]:
        """Ввод данных пользователя с консоли"""
        print("\n" + "=" * 40)
        print("ДОБАВЛЕНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ")
        print("=" * 40)

        # Ввод обязательных полей
        fields = [
            ("имя", True),
            ("логин", True),
            ("пароль", True),
            ("email", False),
            ("адрес", False),
        ]

        data = {}
        for field_name, required in fields:
            while True:
                prompt = f"Введите {field_name}: "
                if not required:
                    prompt = f"Введите {field_name} (необязательно): "

                value = input(prompt).strip()

                if required and not value:
                    print(f"{field_name} не может быть пустым!")
                    continue

                # Преобразуем имя поля для объекта User
                field_map = {
                    "имя": "name",
                    "логин": "login",
                    "пароль": "password",
                    "email": "email",
                    "адрес": "address"
                }

                if value or required:
                    data[field_map[field_name]] = value if value else None
                break

        # Создаем пользователя
        try:
            return User(
                id=0,  # Будет заменен при сохранении
                **data
            )
        except Exception as e:
            print(f"Ошибка создания пользователя: {e}")
            return None

    @staticmethod
    def show_menu() -> str:
        """Показывает меню и возвращает выбор пользователя"""
        print("\n" + "=" * 40)
        print("МЕНЮ СИСТЕМЫ АВТОРИЗАЦИИ")
        print("=" * 40)
        print("1. Добавить нового пользователя")
        print("2. Показать всех пользователей")
        print("3. Найти пользователя по ID")
        print("4. Найти пользователя по логину")
        print("5. Авторизоваться")
        print("6. Выйти чтобы сменить пользователя")
        print("7. Проверить текущую авторизацию")
        print("8. Редактировать пользователя")
        print("9. Удалить пользователя")
        print("0. Завершение программы")
        print("=" * 40)

        return input("Выберите действие: ").strip()

    @staticmethod
    def print_user(user: Optional[User]):
        """Красиво выводит информацию о пользователе"""
        if not user:
            print("Пользователь не найден")
            return

        print("\n" + "-" * 40)
        print("ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
        print("-" * 40)
        print(f"ID: {user.id}")
        print(f"Имя: {user.name}")
        print(f"Логин: {user.login}")
        print(f"Email: {user.email or 'не указан'}")
        print(f"Адрес: {user.address or 'не указан'}")
        print("-" * 40)


class UserValidator:
    @staticmethod
    def validate_email(email: Optional[str]) -> bool:
        if not email:
            return True
        return '@' in email and '.' in email.split('@')[-1]

    @staticmethod
    def validate_login(login: str, existing_logins: List[str]) -> tuple[bool, str]:
        if not login:
            return False, "Логин не может быть пустым"
        if len(login) < 3:
            return False, "Логин должен быть не менее 3 символов"
        if login in existing_logins:
            return False, "Логин уже занят"
        return True, ""


# Улучшенный ввод
class EnhancedConsoleService(ConsoleService):
    @staticmethod
    def input_user_with_validation(user_repo: UserRepository) -> Optional[User]:
        print("\n" + "=" * 40)
        print("РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ")
        print("=" * 40)

        # Получаем существующие логины для проверки
        existing_logins = [user.login for user in user_repo.get_all()]

        # Ввод с валидацией
        name = input("Имя: ").strip()
        while not name:
            print("Имя обязательно!")
            name = input("Имя: ").strip()

        login = input("Логин: ").strip()
        while True:
            is_valid, message = UserValidator.validate_login(login, existing_logins)
            if is_valid:
                break
            print(f"{message}")
            login = input("Логин: ").strip()

        password = input("Пароль: ").strip()
        while len(password) < 4:
            print("Пароль должен быть не менее 4 символов")
            password = input("Пароль: ").strip()

        email = input("Email (необязательно): ").strip() or None
        if email and not UserValidator.validate_email(email):
            print("Email имеет неверный формат, но сохранен")

        address = input("Адрес (необязательно): ").strip() or None

        return User(
            id=0,
            name=name,
            login=login,
            password=password,
            email=email,
            address=address
        )


# Демонстрация работы системы
def first_demonstrate_auth_system():
    """Демонстрация работы системы авторизации"""

    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ СИСТЕМЫ АВТОРИЗАЦИИ")
    print("=" * 60)

    # Создаем репозиторий и сервис авторизации
    user_repo = UserRepository("users_demo.json")
    auth_service = FileAuthService(user_repo, "session_demo.dat")

    # # Очищаем файлы для чистого демо
    # if Path("users_demo.json").exists():
    #     Path("users_demo.json").unlink()
    # if Path("session_demo.dat").exists():
    #     Path("session_demo.dat").unlink()

    # 1. Добавление пользователей
    print("\n1. ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ:")

    users = [
        User(id=1, name="Мария Сидорова", login="maria", password="qwerty",
             email="maria@mail.com"),
        User(id=2, name="Иван Петров", login="ivan", password="12345",
             email="ivan@mail.com", address="Москва, ул. Ленина, 1"),
        User(id=3, name="Алексей Иванов", login="alex", password="password123"),
    ]

    for user in users:
        try:
            user_repo.add(user)
            print(f"   Добавлен: {user.name}")
        except ValueError as e:
            print(f"   Ошибка: {e}")

    # 2. Показать всех пользователей (сортировка по name)
    print("\n2. ВСЕ ПОЛЬЗОВАТЕЛИ:")
    for user in user_repo.get_all():
        print(f"{user}")

    # 3. Авторизация пользователя
    print("\n3. АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЕЙ:")

    # Неуспешная авторизация
    print("   Попытка входа с неверными данными:")
    auth_service.sign_in("ivan", "wrong_password")

    # Успешная авторизация
    print("\n   Успешный вход:")
    auth_service.sign_in("ivan", "12345")
    print(f"   Текущий пользователь: {auth_service.current_user}")
    print(f"   Авторизован: {auth_service.is_authorized}")

    # 4. Редактирование пользователя
    print("\n4. РЕДАКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ:")
    # Ищем по ЛОГИНУ, а не по ID!
    ivan = user_repo.get_by_login("ivan")  # ← Ищем по логину!
    if ivan:
        print(f"   Найден пользователь: {ivan.name} (ID: {ivan.id})")
        ivan.email = "ivan.new@mail.com"
        user_repo.update(ivan)
        print(f"   Email пользователя {ivan.name} обновлен")
    else:
        print("   Пользователь с логином 'ivan' не найден")

    # 5. Смена текущего пользователя
    print("\n5. СМЕНА ПОЛЬЗОВАТЕЛЯ:")
    auth_service.sign_out()
    print(f"   Авторизован после выхода: {auth_service.is_authorized}")

    # Вход другого пользователя
    auth_service.sign_in("maria", "qwerty")
    print(f"   Новый текущий пользователь: {auth_service.current_user}")

    # 6. Демонстрация автоматической авторизации
    print("\n6. АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ ПРИ ПОВТОРНОМ ВХОДЕ:")

    # Создаем новый сервис (имитируем повторный вход в программу)
    print("   Создаем новый экземпляр сервиса (имитация перезапуска программы)...")
    new_auth_service = FileAuthService(user_repo, "session_demo.dat")

    print(f"   Авторизован автоматически: {new_auth_service.is_authorized}")
    if new_auth_service.is_authorized:
        print(f"   Текущий пользователь: {new_auth_service.current_user}")

    # 7. Удаление пользователя
    print("\n7. УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ:")
    try:
        alex = user_repo.get_by_login("alex")
        if alex:
            user_repo.delete(alex)
            print(f"   Пользователь {alex.name} удален")
    except ValueError as e:
        print(f"   Ошибка: {e}")

    # 8. Показать оставшихся пользователей
    print("\n8. ОСТАВШИЕСЯ ПОЛЬЗОВАТЕЛИ:")
    for user in user_repo.get_all():
        print(f"{user}")

    # 9. Поиск пользователя по логину
    print("\n9. ПОИСК ПОЛЬЗОВАТЕЛЯ ПО ЛОГИНУ:")
    found_user = user_repo.get_by_login("ivan")
    if found_user:
        print(f"   Найден: {found_user}")

    # Очистка (выход из системы)
    new_auth_service.sign_out()

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)


def main():
    # Инициализация репозиториев и сервисов
    user_repo = UserRepository("users_demo.json")
    auth_service = FileAuthService(user_repo, "session_demo.dat")

    # Главный цикл программы
    while True:
        time.sleep(2)
        choice = ConsoleService.show_menu()

        if choice == "1":  # Добавить пользователя
            new_user = ConsoleService.input_user()
            if new_user:
                user_repo.add(new_user)
                print(f"Пользователь '{new_user.name}' успешно добавлен!")

        elif choice == "9":  # удалить пользователя
            login = input("Логин: ").strip()
            password = input("Пароль: ").strip()

            # Используем метод sign_in сервиса авторизации (передаем логин и пароль)
            if auth_service.sign_in(login, password):
                # Успешная авторизация уже обработана в методе sign_in
                try:
                    del_user = user_repo.get_by_login(login)
                    if del_user:
                        user_repo.delete(del_user)
                        print(f"   Пользователь {del_user.name} удален")
                except ValueError as e:
                    print(f"   Ошибка: {e}")

        elif choice == "2":  # Показать всех
            users = user_repo.get_all()
            if users:
                print(f"\nВсего пользователей: {len(users)}")
                for user in sorted(users, key=lambda u: u.name):
                    ConsoleService.print_user(user)
            else:
                print("Нет пользователей в системе")

        elif choice == "3":  # Найти по ID
            try:
                user_id = int(input("Введите ID пользователя: "))
                user = user_repo.get_by_id(user_id)
                ConsoleService.print_user(user)
            except ValueError:
                print("Неверный формат ID")

        elif choice == "4":  # Найти по логину
            login = input("Введите логин: ").strip()
            user = user_repo.get_by_login(login)
            ConsoleService.print_user(user)

        elif choice == "5":  # Авторизоваться
            login = input("Логин: ").strip()
            password = input("Пароль: ").strip()

            # Используем метод sign_in сервиса авторизации (передаем логин и пароль)
            if auth_service.sign_in(login, password):
                # Успешная авторизация уже обработана в методе sign_in
                pass
            else:
                print("Неверный логин или пароль")

        elif choice == "6":  # Выйти
            if auth_service.is_authorized:
                print(f"До свидания, {auth_service.current_user.name}!")
                auth_service.sign_out()
            else:
                print("Вы не авторизованы")

        elif choice == "7":  # Проверить авторизацию
            if auth_service.is_authorized:
                print(f"Вы авторизованы как: {auth_service.current_user.name}")
                ConsoleService.print_user(auth_service.current_user)
            else:
                print("Вы не авторизованы")

        elif choice == "8":  # Редактировать пользователя
            if auth_service.is_authorized:
                print(f"Редактирование профиля пользователя {auth_service.current_user.name}")

                # Показываем текущие данные
                ConsoleService.print_user(auth_service.current_user)

                # Запрашиваем новые данные
                print("\nВведите новые данные (оставьте пустым для сохранения текущего значения):")

                new_name = input(f"Имя [{auth_service.current_user.name}]: ").strip()
                new_email = input(f"Email [{auth_service.current_user.email or 'не указан'}]: ").strip()
                new_address = input(f"Адрес [{auth_service.current_user.address or 'не указан'}]: ").strip()

                # Обновляем только если введено значение
                updated_user = User(
                    id=auth_service.current_user.id,
                    name=new_name if new_name else auth_service.current_user.name,
                    login=auth_service.current_user.login,  # Логин не меняем
                    password=auth_service.current_user.password,  # Пароль не меняем
                    email=new_email if new_email else auth_service.current_user.email,
                    address=new_address if new_address else auth_service.current_user.address
                )

                user_repo.update(updated_user)
                print("Профиль обновлен!")
            else:
                print("Вы не авторизованы")

        elif choice == "0":  # Выход без сохранения
            print("Выход без сохранения")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


def should_show_demo(file_path: str = "users_demo.json") -> bool:
    """Показывать демо, если файл репозитория пустой или не существует"""
    path = Path(file_path)

    if path.exists() and path.stat().st_size != 0:
        return False

    # Или проверяем содержимое JSON
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return len(data.get("users", [])) == 0
    except Exception as e:
        print(f"Неизвестная ошибка при чтении {file_path}: {e} - показываем демо")
        return True


if __name__ == "__main__":
    if should_show_demo('users_demo.json'):
        first_demonstrate_auth_system()
    else:
        main()

