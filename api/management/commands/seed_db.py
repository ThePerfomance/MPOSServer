"""
python manage.py seed_db
Заполняет БД тестовыми данными, аналогичными Rust-сиду.
"""
import uuid
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from api.models import (
    User, Group, GroupMember, Subject, Test, Question, Answer, TestResult,
)


GROUPS = [
    "24ИБ(б)БАС-1", "24ИБ(б)БАС-2", "24ИВТ(б)ВМК", "24ИСТ(б)-1", "24ИСТ(б)-2",
    "24КБ(с)РЗПО-1", "24КБ(с)РЗПО-2", "24МКН(б)ЦТ", "24ПИ(б)Эк",
    "24ПИнж(б)-1", "24ПИнж(б)-2", "24ПМ(б)МКМ", "24ПМИ(б)ППКС", "24Ст(б)СУД",
    "24ФИИТ(б)РАИС", "23ИБ(б)БАС-1", "23ИБ(б)БАС-2", "23ИВТ(б)ВМК",
]

USERS = [
    ("Иван", "Иванов", "Иванович", "Ivan@example.com", "student"),
    ("Сергей", "Сергеев", "Сергеевич", "Ser@example.com", "student"),
    ("Петр", "Петров", "Петрович", "Petr@example.com", "student"),
    ("Евгения", "Федорова", "Николаевна", "Evg@example.com", "teacher"),
    ("Нина", "Алексеева", "Васильевна", "Nina@example.com", "teacher"),
]

SUBJECTS = ["Математика", "Программирование", "Базы данных", "Сети"]

TESTS_DATA = [
    ("Введение в Python", "Базовые конструкции языка Python", "Программирование"),
    ("SQL: основы", "SELECT, INSERT, UPDATE, DELETE", "Базы данных"),
    ("Алгоритмы сортировки", "Пузырёк, быстрая, слияние", "Математика"),
    ("Сетевые протоколы", "TCP/IP, HTTP, DNS", "Сети"),
    ("ООП на Python", "Классы, наследование, полиморфизм", "Программирование"),
]

QUESTIONS_DATA = {
    "Введение в Python": [
        ("Что такое переменная?", [
            ("Ячейка памяти с именем", True),
            ("Функция", False),
            ("Модуль", False),
            ("Оператор", False),
        ]),
        ("Как объявить список?", [
            ("[]", True),
            ("{}", False),
            ("()", False),
            ("<>", False),
        ]),
    ],
    "SQL: основы": [
        ("Что делает SELECT?", [
            ("Выбирает данные из таблицы", True),
            ("Удаляет данные", False),
            ("Обновляет данные", False),
            ("Создаёт таблицу", False),
        ]),
        ("Как удалить запись?", [
            ("DELETE FROM table WHERE id=1", True),
            ("REMOVE FROM table WHERE id=1", False),
            ("DROP FROM table WHERE id=1", False),
            ("ERASE FROM table WHERE id=1", False),
        ]),
    ],
    "Алгоритмы сортировки": [
        ("Сложность сортировки пузырьком?", [
            ("O(n²)", True),
            ("O(n)", False),
            ("O(log n)", False),
            ("O(n log n)", False),
        ]),
    ],
    "Сетевые протоколы": [
        ("На каком уровне работает IP?", [
            ("Сетевой", True),
            ("Транспортный", False),
            ("Канальный", False),
            ("Прикладной", False),
        ]),
    ],
    "ООП на Python": [
        ("Что такое наследование?", [
            ("Механизм создания класса на основе другого", True),
            ("Удаление объекта", False),
            ("Копирование объекта", False),
            ("Скрытие полей", False),
        ]),
    ],
}


class Command(BaseCommand):
    help = "Заполнить БД тестовыми данными"

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write("БД уже заполнена, пропускаем seed.")
            return

        self.stdout.write("Заполняем БД...")

        # Subjects
        subjects = {}
        for name in SUBJECTS:
            s, _ = Subject.objects.get_or_create(name=name)
            subjects[name] = s

        # Groups
        groups = {}
        for name in GROUPS:
            g, _ = Group.objects.get_or_create(name=name)
            groups[name] = g

        # Users
        users = []
        for fn, ln, pn, email, role in USERS:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "firstname": fn,
                    "lastname": ln,
                    "patronymic": pn,
                    "password_hash": email,  # в реальном проекте — bcrypt
                    "role": role,
                },
            )
            users.append(u)

        # Add students to first group
        students = [u for u in users if u.role == "student"]
        first_group = groups["24ИБ(б)БАС-1"]
        for s in students:
            GroupMember.objects.get_or_create(user=s, group=first_group)

        # Tests + Questions + Answers
        tests = {}
        for title, desc, subj_name in TESTS_DATA:
            t, _ = Test.objects.get_or_create(
                title=title,
                defaults={"description": desc, "subject": subjects[subj_name]},
            )
            tests[title] = t

            for q_text, answers in QUESTIONS_DATA.get(title, []):
                q, _ = Question.objects.get_or_create(test=t, text=q_text)
                for a_text, is_correct in answers:
                    Answer.objects.get_or_create(question=q, text=a_text, defaults={"is_correct": is_correct})

        # Test Results — несколько результатов для ML
        import random
        random.seed(42)
        now = datetime.now(timezone.utc)
        for student in students:
            for test in tests.values():
                score = random.randint(30, 100)
                TestResult.objects.get_or_create(
                    user=student,
                    test=test,
                    defaults={
                        "score": score,
                        "started_at": now - timedelta(days=random.randint(1, 30)),
                        "completed_at": now - timedelta(days=random.randint(0, 29)),
                    },
                )

        self.stdout.write(self.style.SUCCESS("Сиды успешно добавлены!"))
