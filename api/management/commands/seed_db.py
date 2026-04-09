# api/management/commands/seed_db.py
from django.core.management.base import BaseCommand
from api.models import User, Group, GroupMember, Subject, Block, Lesson, Test, Question, Answer, TestResult
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
import uuid

class Command(BaseCommand):
    help = 'Seed database with initial data for new schema (Subject -> Block -> Lesson -> Test)'

    def handle(self, *args, **kwargs):
        if User.objects.filter(email='nikita@mail.ru').exists():
            self.stdout.write('Database already seeded, skipping.')
            return

        self.stdout.write('Seeding database for new schema...')

        # ── USERS ──
        # Хешируем пароли при создании
        u1 = User.objects.create(firstname='Никита',    lastname='Смольников',    patronymic='Матвеевич',   email='nikita@mail.ru', password_hash=make_password('123456n'), role='student')
        u2 = User.objects.create(firstname='Александра',  lastname='Непейн',   patronymic='Александровна',  email='nepein@mail.ru',  password_hash=make_password('123456n'),     role='teacher')
        u3 = User.objects.create(firstname='Петр',    lastname='Петров',    patronymic='Петрович',   email='Petr@example.com', password_hash=make_password('Petr@example.com'),    role='student')
        u4 = User.objects.create(firstname='Евгения', lastname='Федорова',  patronymic='Николаевна', email='Evg@example.com',  password_hash=make_password('Evg@example.com'),     role='teacher')
        u5 = User.objects.create(firstname='Нина',    lastname='Алексеева', patronymic='Васильевна', email='Nina@example.com', password_hash=make_password('Nina@example.com'),    role='teacher')

        # ── GROUPS ──
        group_names = [
            '24ИБ(б)БАС-1','24ИБ(б)БАС-2','24ИВТ(б)ВМК','24ИСТ(б)-1','24ИСТ(б)-2',
            '24КБ(с)РЗПО-1','24КБ(с)РЗПО-2','24МКН(б)ЦТ','24ПИ(б)Эк','24ПИнж(б)-1',
            '24ПИнж(б)-2','24ПМ(б)МКМ','24ПМИ(б)ППКС','24Ст(б)СУД','24ФИИТ(б)РАИС',
            '23ИБ(б)БАС-1','23ИБ(б)БАС-2','23ИВТ(б)ВМК','23ИСТ(б)АДМО','23ИСТ(б)СИЦ',
            '23КБ(с)РЗПО-1','23КБ(с)РЗПО-2','23МКН(б)ЦТ','23ПИ(б)Эк','23ПИнж(б)РПиС-1',
            '23ПИнж(б)РПиС-2','23ПМ(б)МКМ','23ПМИ(б)ППКС','23Ст(б)СУД','23ФИИТ(б)РАИС',
            '22БИ(б)ИСЭ','22ИБ(б)БАС-1','22ИБ(б)БАС-2','22ИВТ(б)ВМК','22ИСТ(б)АДМО',
            '22ИСТ(б)СИЦ','22КБ(с)РЗПО-1','22КБ(с)РЗПО-2','22МКН(б)ЦТ','22ПИ(б)Эк',
            '22ПИнж(б)РПиС-1','22ПИнж(б)РПиС-2','22ПМ(б)МКМ','22ПМИ(б)ППКС','22ПО(б)Ин',
            '22Ст(б)СУД','22ФИИТ(б)РАИС',
            '21ИБ(б)БАС-1','21ИБ(б)БАС-2','21ИВТ(б)ВМК','21ИВТ(б)ПОВТ','21ИСТ(б)АДМО',
            '21ИСТ(б)СИЦ','21КБ(с)РЗПО-1','21КБ(с)РЗПО-2','21МКН(б)ЦТ','21ПИ(б)Эк',
            '21ПИнж(б)РПиС','21ПМ(б)ПММ','21ПМИ(б)ППКС','21Ст(б)СУД','21ФИИТ(б)РАИС',
        ]
        groups = {name: Group.objects.create(name=name) for name in group_names}

        # ── GROUP MEMBERS ──
        GroupMember.objects.create(user=u1, group=groups['22ПИнж(б)РПиС-2'])
        GroupMember.objects.create(user=u2, group=groups['22ПИнж(б)РПиС-2'])
        GroupMember.objects.create(user=u3, group=groups['22ПИнж(б)РПиС-2'])
        GroupMember.objects.create(user=u4, group=groups['22ИБ(б)БАС-1'])
        GroupMember.objects.create(user=u5, group=groups['22ПИнж(б)РПиС-2'])

        # ── SUBJECTS ──
        Subject.objects.create(name='Программирование и алгоритмизация')
        Subject.objects.create(name='Компьютерные сети')
        sw = Subject.objects.create(name='Программирование WEB-приложений')

        # ── BLOCKS ──
        b1 = Block.objects.create(subject=sw, title='HTML Basics', description='Введение в HTML', position=0, is_published=True)
        b2 = Block.objects.create(subject=sw, title='CSS Fundamentals', description='Основы CSS', position=1, is_published=True)
        b3 = Block.objects.create(subject=sw, title='Advanced CSS & Layout', description='Гибкие макеты, сетки, переменные и анимации', position=2, is_published=True)

        # ── LESSONS & TESTS ──
        # Block 1: HTML Basics
        l1 = Lesson.objects.create(
            block=b1,
            title='Основы HTML',
            summary='Изучение основ HTML: теги, атрибуты, структура документа.',
            duration=1800,
            position=0,
            is_published=True
        )  # 30 мин
        t1 = Test.objects.create(title='Введение в НTML', duration=1200, is_published=True)
        l1.test = t1
        l1.save()

        l2 = Lesson.objects.create(
            block=b1,
            title='Работа с формами в HTML5',
            summary='Работа с формами в HTML5: элементы ввода, валидация, отправка данных.',
            duration=2400,
            position=1,
            is_published=True
        )  # 40 мин
        t2 = Test.objects.create(title='Работа с формами в HTML5', duration=1200, is_published=True)
        l2.test = t2
        l2.save()

        l3 = Lesson.objects.create(
            block=b1,
            title='Семантическая верстка',
            summary='Семантическая верстка: использование тегов article, section, nav, header, footer.',
            duration=2100,
            position=2,
            is_published=True
        )  # 35 мин
        t3 = Test.objects.create(title='Семантическая верстка страниц в HTML5', duration=1200, is_published=True)
        l3.test = t3
        l3.save()

        # Block 2: CSS Fundamentals
        l4 = Lesson.objects.create(
            block=b2,
            title='Каскадные таблицы стилей',
            summary='Основы CSS: селекторы, каскад, наследование, свойства оформления текста и фона.',
            duration=2700,
            position=0,
            is_published=True
        )  # 45 мин
        t4 = Test.objects.create(title='Работа с каскадными таблицами стилей', duration=1200, is_published=True)
        l4.test = t4
        l4.save()

        l5 = Lesson.objects.create(
            block=b2,
            title='Фильтры в CSS',
            summary='Использование CSS-фильтров: blur, brightness, contrast, grayscale, hue-rotate.',
            duration=1800,
            position=1,
            is_published=True
        )  # 30 мин
        t5 = Test.objects.create(title='Фильтры в CSS', duration=1200, is_published=True)
        l5.test = t5
        l5.save()

        l6 = Lesson.objects.create(
            block=b2,
            title='Блоковые элементы',
            summary='Блочная модель CSS: margin, padding, border, display, позиционирование.',
            duration=2400,
            position=2,
            is_published=True
        )  # 40 мин
        t6 = Test.objects.create(title='Блоковые элементы в CSS', duration=1200, is_published=True)
        l6.test = t6
        l6.save()

        l7 = Lesson.objects.create(
            block=b2,
            title='Трансформации и анимации',
            summary='CSS-трансформации, переходы и анимации: scale, rotate, translate, skew, transition, keyframes.',
            duration=2700,
            position=3,
            is_published=True
        )  # 45 мин
        t7 = Test.objects.create(title='Трансформации, переходы и анимации', duration=1200, is_published=True)
        l7.test = t7
        l7.save()

        l8 = Lesson.objects.create(
            block=b2,
            title='Адаптивная верстка',  # <-- Добавлено
            summary='Адаптивная верстка: media queries, responsive design, мобильная оптимизация.',
            duration=3000,
            position=4,
            is_published=True
        )  # 50 мин
        t8 = Test.objects.create(title='Адаптивная верстка', duration=1200, is_published=True)
        l8.test = t8
        l8.save()

        # Block 3: Advanced Topics
        l9 = Lesson.objects.create(
            block=b3,
            title='Flexbox',  # <-- Добавлено
            summary='Создание гибких макетов с помощью CSS Flexbox: оси, выравнивание, упорядочивание.',
            duration=2400,
            position=0,
            is_published=True
        )  # 40 мин
        t9 = Test.objects.create(title='Создание гибкого макета страницы с помощью Flexbox', duration=1200,
                                 is_published=True)
        l9.test = t9
        l9.save()

        l10 = Lesson.objects.create(
            block=b3,
            title='Grid Layout',  # <-- Добавлено
            summary='Двумерные сетки с CSS Grid: строки, колонки, области, выравнивание элементов.',
            duration=2700,
            position=1,
            is_published=True
        )  # 45 мин
        t10 = Test.objects.create(title='Двумерная система сеток Grid Layout', duration=1200, is_published=True)
        l10.test = t10
        l10.save()

        l11 = Lesson.objects.create(
            block=b3,
            title='Переменные в CSS',  # <-- Добавлено
            summary='Использование CSS-переменных: объявление, использование, преимущества.',
            duration=1800,
            position=2,
            is_published=True
        )  # 30 мин
        t11 = Test.objects.create(title='Использование переменных в CSS', duration=1200, is_published=True)
        l11.test = t11
        l11.save()

        # Final Test for Block 3
        t12 = Test.objects.create(title='Итоговый тест', duration=1800, is_published=True) # 30 мин
        b3.final_test = t12
        # Update lessons_count automatically
        b3.lessons_count = b3.lessons.count() # This counts lessons linked to the block
        b3.save()

        # Update lessons_count for other blocks too
        b1.lessons_count = b1.lessons.count()
        b1.save()
        b2.lessons_count = b2.lessons.count()
        b2.save()


        # ── QUESTIONS & ANSWERS ──
        def qa(test, text, answers):
            q = Question.objects.create(test=test, text=text)
            for a_text, correct in answers:
                Answer.objects.create(question=q, text=a_text, is_correct=correct)

        # Example for t1
        qa(t1,'Элемент … указывает базовый адрес',[
            ('base',True),('head',False),('meta',False),('title',False)])
        qa(t1,'Элемент … структурирует контент на сайте, группирует содержимое в блоки',[
            ('p',False),('div',True),('pre',False),('span',False)])
        qa(t1,'Самый крупный заголовок имеет тег …',[
            ('h1',True),('h2',False),('h4',False),('h6',False)])
        qa(t1,'Тег … выделяет текст курсивом',[
            ('<b>',False),('<del>',False),('<i>',True),('<s>',False)])
        qa(t1,'Атрибут … используется для задания пути к изображению, а … - для описания изображения',[
            ('src, alt',True),('alt, src',False),('img, alt',False),('src, img',False)])
        qa(t1,'Для нумерованного списка используется элемент …',[
            ('ul',False),('ol',True),('demical',False),('li',False)])
        qa(t1,'Элемент … создает раскрываемый блок',[
            ('li',False),('summary',False),('details',True),('head',False)])
        qa(t1,'Строки в таблицах обозначаются элементом…',[
            ('tr',True),('td',False),('ts',False),('dt',False)])
        qa(t1,'Какой атрибут ссылок <a></a> указывает адрес ресурса?',[
            ('rel',False),('media',False),('href',True),('target',False)])
        qa(t1,'Выберите верное сокращение цвета.',[
            ('#FF00FF - #F0F',True),('#DDA0DD - #DA0D',False),('#D8BFD8 - #DBD;',False),('#E6E6FA - #E6FA',False)])

        # Example for t2
        qa(t2,'Атрибут … задает тип кнопки для button',[
            ('submit',False),('button',False),('type',True),('form',False)])
        qa(t2,'Атрибут … устанавливает текст по умолчанию',[
            ('dir',False),('pattern',False),('placeholder',True),('readonly',False)])
        qa(t2,'Метки представлены элементом …',[
            ('label',True),('input',False),('meta',False),('form',False)])
        qa(t2,'Атрибут … указывает, что поле должно иметь значение',[
            ('step',False),('value',False),('min',False),('required',True)])
        qa(t2,'Флажок создается при помощи элемента …',[
            ('input',True),('button',False),('form',False),('label',False)])
        qa(t2,'Какой тип input используется для выбора цвета?',[
            ('<input type="colorpicker">',False),('<input type="color">',True),
            ('<input type="picker">',False),('<input type="hex">',False)])
        qa(t2,'Какой тип input используется для ввода пароля?',[
            ('<input type="hidden">',False),('<input type="password">',True),
            ('<input type="secret">',False),('<input type="text" secure>',False)])
        qa(t2,'Элемент … создает список',[
            ('select',True),('option',False),('input',False),('label',False)])
        qa(t2,'В чем отличие textarea от <input type="text"/>?',[
            ('отличий нет',False),('textarea создает многострочное поле',True),
            ('<input type="text"/> создает многострочное поле',False),
            ('в textarea можно вставлять картинки',False)])
        qa(t2,'Какой символ в синтаксисе регулярных выражений соответствует концу строки?',[
            ('?',False),('*',False),('$',True),('.',False)])

        # ── TEST RESULTS ──
        dt_start = datetime(2026, 3, 1, 10, 0, 0)  # фиксированное время начала

        # Link results to tests through lessons
        TestResult.objects.create(user=u1, test=t1, score=5, started_at=dt_start,
                                  completed_at=dt_start + timedelta(minutes=7))
        TestResult.objects.create(user=u1, test=t1, score=10, started_at=dt_start + timedelta(days=1),
                                  completed_at=dt_start + timedelta(days=1, minutes=5))
        TestResult.objects.create(user=u1, test=t2, score=5, started_at=dt_start + timedelta(days=2),
                                  completed_at=dt_start + timedelta(days=2, minutes=9))
        TestResult.objects.create(user=u2, test=t1, score=5, started_at=dt_start + timedelta(days=1),
                                  completed_at=dt_start + timedelta(days=1, minutes=6))
        TestResult.objects.create(user=u3, test=t3, score=10, started_at=dt_start + timedelta(days=3),
                                  completed_at=dt_start + timedelta(days=3, minutes=8))


        self.stdout.write(self.style.SUCCESS(
            f'OK: Seeded new schema - '
            f'{User.objects.count()} users, '
            f'{Group.objects.count()} groups, '
            f'{Subject.objects.count()} subjects, '
            f'{Block.objects.count()} blocks, '
            f'{Lesson.objects.count()} lessons, '
            f'{Test.objects.count()} tests, '
            f'{Question.objects.count()} questions, '
            f'{Answer.objects.count()} answers, '
            f'{TestResult.objects.count()} test_results.'
        ))