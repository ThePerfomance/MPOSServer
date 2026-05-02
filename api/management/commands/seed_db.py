# api/management/commands/seed_db.py
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from api.models import (
    User, Group, GroupMember, TeacherGroup, GroupSubject,
    Subject, Block, Lesson, Test, Question, Answer,
    TestResult, UserAnswer, VideoType, Video
)


def create_test_result(user, test_obj, correct_answers_count, start_time):
    """
    Helper to create a TestResult with a mix of correct and incorrect answers.
    """
    questions = list(test_obj.questions.all())
    total_questions = len(questions)

    if total_questions == 0:
        print(f"Skipping result for test '{test_obj.title}' as it has no questions.")
        return

    # Ensure correct_answers_count is valid
    correct_answers_count = min(correct_answers_count, total_questions)

    # Shuffle questions to randomize which ones are answered correctly/incorrectly
    random.shuffle(questions)

    test_result = TestResult.objects.create(
        user=user,
        test=test_obj,  # Correctly associate the test with the result
        started_at=start_time,
        completed_at=start_time + timedelta(minutes=random.randint(5, 20))
    )

    earned_points = 0

    # Process correct answers
    for q in questions[:correct_answers_count]:
        correct_answer = q.answers.filter(is_correct=True).first()
        if correct_answer:
            UserAnswer.objects.create(
                test_result=test_result,
                question=q,
                chosen_answer=correct_answer,
                points_earned=q.points
            )
            earned_points += q.points

    # Process incorrect answers
    for q in questions[correct_answers_count:]:
        incorrect_answer = q.answers.filter(is_correct=False).first()
        if incorrect_answer:
            UserAnswer.objects.create(
                test_result=test_result,
                question=q,
                chosen_answer=incorrect_answer,
                points_earned=0
            )

    # Finalize the result with calculated points
    test_result.earned_points = earned_points
    test_result.total_points = test_obj.questions.aggregate(Sum('points'))['points__sum'] or 0
    test_result.save()


class Command(BaseCommand):
    help = 'Seed database with initial data for new schema'

    def handle(self, *args, **kwargs):
        if User.objects.filter(email='nikita@mail.ru').exists():
            self.stdout.write('Database already seeded, skipping.')
            return

        self.stdout.write('Seeding database for new schema...')

        # ── USERS ──
        u1 = User.objects.create_user(
            firstname='Никита',
            lastname='Смольников',
            patronymic='Матвеевич',
            email='nikita@mail.ru',
            password='123456n',
            role='student'
        )
        u2 = User.objects.create_user(
            firstname='Александра',
            lastname='Непейн',
            patronymic='Александровна',
            email='nepein@mail.ru',
            password='123456n',
            role='teacher'
        )

        # ── GROUPS ──
        main_group = Group.objects.create(name='22ПИнж(б)РПиС-2')

        # ── GROUP MEMBERS & TEACHERS ──
        GroupMember.objects.create(user=u1, group=main_group)
        TeacherGroup.objects.create(teacher=u2, group=main_group)

        # ── SUBJECTS ──
        Subject.objects.create(name='Программирование и алгоритмизация', creator=u2)
        Subject.objects.create(name='Компьютерные сети', creator=u2)
        sw = Subject.objects.create(name='Программирование WEB-приложений', creator=u2)
        GroupSubject.objects.create(group=main_group, subject=sw)

        # ── BLOCKS ──
        b1 = Block.objects.create(subject=sw, title='HTML Basics', description='Введение в HTML', position=0, is_published=True)
        b2 = Block.objects.create(subject=sw, title='CSS Fundamentals', description='Основы CSS', position=1, is_published=True)
        b3 = Block.objects.create(subject=sw, title='Advanced CSS & Layout', description='Гибкие макеты, сетки, переменные и анимации', position=2, is_published=True)

        # ── LESSONS & TESTS ──
        vt_rutube = VideoType.objects.create(name='Rutube')
        v1 = Video.objects.create(type=vt_rutube, link='https://rutube.ru/video/f19270376ddbd410699f575f9495a07c/?r=wd', duration=910)

        l1 = Lesson.objects.create(block=b1, title='Основы HTML', summary='Изучение основ HTML: теги, атрибуты, структура документа.', duration=1800, video=v1, position=0, is_published=True)
        t1 = Test.objects.create(title='Введение в НTML', duration=1200, is_published=True)
        l1.test = t1
        l1.save()

        l2 = Lesson.objects.create(block=b1, title='Работа с формами в HTML5', summary='Работа с формами в HTML5: элементы ввода, валидация, отправка данных.', duration=2400, position=1, is_published=True)
        t2 = Test.objects.create(title='Работа с формами в HTML5', duration=1200, is_published=True)
        l2.test = t2
        l2.save()

        l3 = Lesson.objects.create(block=b1, title='Семантическая верстка', summary='Семантическая верстка: использование тегов article, section, nav, header, footer.', duration=2100, position=2, is_published=True)
        t3 = Test.objects.create(title='Семантическая верстка страниц в HTML5', duration=1200, is_published=True)
        l3.test = t3
        l3.save()

        l4 = Lesson.objects.create(block=b2, title='Каскадные таблицы стилей', summary='Основы CSS: селекторы, каскад, наследование, свойства оформления текста и фона.', duration=2700, position=0, is_published=True)
        t4 = Test.objects.create(title='Работа с каскадными таблицами стилей', duration=1200, is_published=True)
        l4.test = t4
        l4.save()

        l5 = Lesson.objects.create(block=b2, title='Фильтры в CSS', summary='Использование CSS-фильтров: blur, brightness, contrast, grayscale, hue-rotate.', duration=1800, position=1, is_published=True)
        t5 = Test.objects.create(title='Фильтры в CSS', duration=1200, is_published=True)
        l5.test = t5
        l5.save()

        l6 = Lesson.objects.create(block=b2, title='Блоковые элементы', summary='Блочная модель CSS: margin, padding, border, display, позиционирование.', duration=2400, position=2, is_published=True)
        t6 = Test.objects.create(title='Блоковые элементы в CSS', duration=1200, is_published=True)
        l6.test = t6
        l6.save()

        l7 = Lesson.objects.create(block=b2, title='Трансформации и анимации', summary='CSS-трансформации, переходы и анимации: scale, rotate, translate, skew, transition, keyframes.', duration=2700, position=3, is_published=True)
        t7 = Test.objects.create(title='Трансформации, переходы и анимации', duration=1200, is_published=True)
        l7.test = t7
        l7.save()

        l8 = Lesson.objects.create(block=b2, title='Адаптивная верстка', summary='Адаптивная верстка: media queries, responsive design, мобильная оптимизация.', duration=3000, position=4, is_published=True)
        t8 = Test.objects.create(title='Адаптивная верстка', duration=1200, is_published=True)
        l8.test = t8
        l8.save()

        l9 = Lesson.objects.create(block=b3, title='Flexbox', summary='Создание гибких макетов с помощью CSS Flexbox: оси, выравнивание, упорядочивание.', duration=2400, position=0, is_published=True)
        t9 = Test.objects.create(title='Создание гибкого макета страницы с помощью Flexbox', duration=1200, is_published=True)
        l9.test = t9
        l9.save()

        l10 = Lesson.objects.create(block=b3, title='Grid Layout', summary='Двумерные сетки с CSS Grid: строки, колонки, области, выравнивание элементов.', duration=2700, position=1, is_published=True)
        t10 = Test.objects.create(title='Двумерная система сеток Grid Layout', duration=1200, is_published=True)
        l10.test = t10
        l10.save()

        l11 = Lesson.objects.create(block=b3, title='Переменные в CSS', summary='Использование CSS-переменных: объявление, использование, преимущества.', duration=1800, position=2, is_published=True)
        t11 = Test.objects.create(title='Использование переменных в CSS', duration=1200, is_published=True)
        l11.test = t11
        l11.save()

        t12 = Test.objects.create(title='Итоговый тест', duration=1800, is_published=True)
        b3.final_test = t12
        b3.lessons_count = b3.lessons.count()
        b3.save()

        b1.lessons_count = b1.lessons.count()
        b1.save()
        b2.lessons_count = b2.lessons.count()
        b2.save()

        # ── QUESTIONS & ANSWERS ──
        def qa(test, text, answers, points=1):
            q = Question.objects.create(test=test, text=text, points=points)
            for a_text, correct in answers:
                Answer.objects.create(question=q, text=a_text, is_correct=correct)

        # Tests 1-11 have 1 point per question
        qa(t1,'Элемент … указывает базовый адрес',[('base',True),('head',False),('meta',False),('title',False)])
        qa(t1,'Элемент … структурирует контент на сайте, группирует содержимое в блоки',[('p',False),('div',True),('pre',False),('span',False)])
        qa(t1,'Самый крупный заголовок имеет тег …',[('h1',True),('h2',False),('h4',False),('h6',False)])
        qa(t1,'Тег … выделяет текст курсивом',[('<b>',False),('<del>',False),('<i>',True),('<s>',False)])
        qa(t1,'Атрибут … используется для задания пути к изображению, а … - для описания изображения',[('src, alt',True),('alt, src',False),('img, alt',False),('src, img',False)])
        qa(t1,'Для нумерованного списка используется элемент …',[('ul',False),('ol',True),('demical',False),('li',False)])
        qa(t1,'Элемент … создает раскрываемый блок',[('li',False),('summary',False),('details',True),('head',False)])
        qa(t1,'Строки в таблицах обозначаются элементом…',[('tr',True),('td',False),('ts',False),('dt',False)])
        qa(t1,'Какой атрибут ссылок <a></a> указывает адрес ресурса?',[('rel',False),('media',False),('href',True),('target',False)])
        qa(t1,'Выберите верное сокращение цвета.',[('#FF00FF - #F0F',True),('#DDA0DD - #DA0D',False),('#D8BFD8 - #DBD;',False),('#E6E6FA - #E6FA',False)])

        qa(t2,'Атрибут … задает тип кнопки для button',[('submit',False),('button',False),('type',True),('form',False)])
        qa(t2,'Атрибут … устанавливает текст по умолчанию',[('dir',False),('pattern',False),('placeholder',True),('readonly',False)])
        qa(t2,'Метки представлены элементом …',[('label',True),('input',False),('meta',False),('form',False)])
        qa(t2,'Атрибут … указывает, что поле должно иметь значение',[('step',False),('value',False),('min',False),('required',True)])
        qa(t2,'Флажок создается при помощи элемента …',[('input',True),('button',False),('form',False),('label',False)])
        qa(t2,'Какой тип input используется для выбора цвета?',[('<input type="colorpicker">',False),('<input type="color">',True),('<input type="picker">',False),('<input type="hex">',False)])
        qa(t2,'Какой тип input используется для ввода пароля?',[('<input type="hidden">',False),('<input type="password">',True),('<input type="secret">',False),('<input type="text" secure>',False)])
        qa(t2,'Элемент … создает список',[('select',True),('option',False),('input',False),('label',False)])
        qa(t2,'В чем отличие textarea от <input type="text"/>?',[('отличий нет',False),('textarea создает многострочное поле',True),('<input type="text"/> создает многострочное поле',False),('в textarea можно вставлять картинки',False)])
        qa(t2,'Какой символ в синтаксисе регулярных выражений соответствует концу строки?',[('?',False),('*',False),('$',True),('.',False)])

        qa(t3,'Элемент … объединяет между собой части информации и выполняет их группировку',[('article',False),('section',True),('div',False),('nav',False)])
        qa(t3,'Nav, как правило, представляет из себя …',[('нумерованный список',False),('ненумерованный список',False),('нумерованный список с набором ссылок',False),('ненумерованный список с набором ссылок',True)])
        qa(t3,'Какой элемент может содержать заголовки, навигацию, формы поиска?',[('header',True),('footer',False),('address',False),('section',False)])
        qa(t3,'Какой элемент обычно содержит даты публикации, блок ссылок на похожие ресурсы?',[('header',False),('footer',True),('address',False),('section',False)])
        qa(t3,'Какой элемент предназначен для отображения контактной информации?',[('header',False),('footer',False),('address',True),('section',False)])
        qa(t3,'Какой элемент должен быть идентифицирован с помощью включения в него заголовков?',[('article',True),('section',False),('header',False),('div',False)])
        qa(t3,'Элемент … призван содержать элементы навигации',[('section',False),('address',False),('nav',True),('aside',False)])
        qa(t3,'Какой элемент можно использовать для сайдбаров, рекламных блоков?',[('header',False),('footer',False),('aside',True),('address',False)])
        qa(t3,'Какой элемент представляет основное содержимое страницы?',[('aside',False),('body',False),('main',True),('div',False)])
        qa(t3,'Наличие только одного элемента … допустимо на странице',[('header',False),('footer',False),('nav',False),('main',True)])

        qa(t4,'Для определения селектора класса в CSS перед названием соответствующего класса ставится …',[('-',False),(':',False),('.',True),('#',False)])
        qa(t4,'Для определения селектора идентификатора в CSS перед названием соответствующего идентификатора ставится …',[('-',False),(':',False),('.',False),('#',True)])
        qa(t4,'Универсальный селектор представлен знаком …',[('-',False),('&',False),('*',True),('$',False)])
        qa(t4,'Укажите верное написание при применении стиля к вложенному элементу, где main - родительский элемент (идентификатор), р – вложенный.',[('#p main',False),('#main p',True),('p #main',False),('#main *p',False)])
        qa(t4,'Выберите пример селектора, который выбирает только те параграфы, которые находятся непосредственно в блоке',[('.article p',False),('.article < p',False),('.article > p',True),('.article < > p',False)])
        qa(t4,'Какой псевдокласс представляет элемент, на который наведен указатель мыши?',[(':visited',False),(':active',False),(':hover',True),(':focus',False)])
        qa(t4,'Какой псевдокласс выбирает элемент по умолчанию?',[('::enabled',False),('::default',True),('::valid',False),('::required',False)])
        qa(t4,'Выберите правильное определения стиля в селекторе атрибутов',[('input. [type="text"] {}',False),('input [type="text"] {}',True),('input [*type="text"] {}',False),('input." type="text"" {}',False)])
        qa(t4,'Расположите по возрастанию важность селекторов',[('идентификаторы, классы, теги',True),('теги, идентификаторы, классы',False),('теги, классы, идентификаторы',False),('идентификаторы, теги, классы',False)])
        qa(t4,'На основе баллов важности селекторов, представленных в главе, посчитать баллы следующего селектора: a #menu:not(.links)',[('111',True),('101',False),('11',False),('222',False)])

        qa(t5,'Какой фильтр в CSS делает фотографию размытой?',[('blur',True),('brightness',False),('contrast',False),('grayscale',False)])
        qa(t5,'Какой фильтр в CSS изменяет яркость изображения?',[('blur',False),('brightness',True),('contrast',False),('grayscale',False)])
        qa(t5,'Какой фильтр в CSS регулирует контрастность изображения?',[('blur',False),('brightness',False),('contrast',True),('grayscale',False)])
        qa(t5,'Какой фильтр в CSS извлекает все цвета из изображения, делая результат черно-белым?',[('blur',False),('brightness',False),('contrast',False),('grayscale',True)])
        qa(t5,'Какой фильтр в CSS изменяет цвета изображения в зависимости от угла поворота, указанного в цветовом круге?',[('blur',False),('brightness',False),('contrast',False),('hue-rotate',True)])
        qa(t5,'Какой фильтр в CSS делает изображение негативным, инвертирует цвета?',[('invert',True),('opacity',False),('saturate',False),('sepia',False)])
        qa(t5,'Какой фильтр в CSS работает аналогично свойству opacity, добавляя прозрачность элементу?',[('invert',False),('opacity',True),('saturate',False),('sepia',False)])
        qa(t5,'Какой из следующих CSS-фильтров применяет эффект размытия к элементу?',[('filter: brightness(1.5)',False),('filter: blur(5px)',True),('filter: contrast(200%)',False),('filter: grayscale(100%)',False)])
        qa(t5,'Какой фильтр в CSS создает эффект, имитирующий старину и "ретро" фотографию?',[('invert',False),('opacity',False),('saturate',False),('sepia',True)])
        qa(t5,'Какой фильтр в CSS аналогичен фильтру Гаусса в Photosop?',[('blur',True),('brightness',False),('contrast',False),('grayscale',False)])

        qa(t6,'Какое свойство блоковых элементов задает внешний отступ, то есть расстояние от границы текущего элемента до других соседних элементов или до границ внешнего контейнера?',[('margin',True),('padding',False),('border',False),('content',False)])
        qa(t6,'Какое свойство блоковых элементов определяет внутренний отступ, определяет расстояние от границы элемента до внутреннего содержимого?',[('margin',False),('padding',True),('border',False),('content',False)])
        qa(t6,'При работе с блоковыми элементами какое свойство устанавливает режим повторения фонового изображения по всей поверхности элемента?',[('background-color',False),('background-image',False),('background-repeat',True),('background-clip',False)])
        qa(t6,'При работе с блоковыми элементами какое свойство определяет область, которая вырезается из изображения и используется в качестве фона?',[('background-size',False),('background-image',False),('background-attachment',False),('background-clip',True)])
        qa(t6,'Какой вид позиционирования позволяет зафиксировать блок, независимо от прокрутки веб-страницы?',[('absolute',False),('relative',False),('fixed',True),('static',False)])
        qa(t6,'Значение свойства position … позиционирует элемент относительно границ элемента-контейнера',[('static',False),('absolute',True),('relative',False),('fixed',False)])
        qa(t6,'Свойство … позволяет изменить порядок следования элементов при их наложении',[('position',False),('z-index',True),('opacity',False),('display',False)])
        qa(t6,'Какое значение свойстсва display при статическом позоционировании позволяет преобразовать блоковый элемент в строчный, подобно словам в строке текста?',[('inline',True),('block',False),('inline-block',False),('list-item',False)])
        qa(t6,'Какое значение свойстсва display при статическом позоционировании позволяет преобразовать блоковый элемент?',[('inline',False),('block',True),('inline-block',False),('list-item',False)])
        qa(t6,'Какое значение используют браузеры по умолчанию для свойства box-sizing?',[('content-box',True),('border-box',False),('content',False),('border',False)])

        qa(t7,'Для создания трансформаций применяется свойство …',[('transformed',False),('transform',True),('transition',False),('visibility',False)])
        qa(t7,'Для масштабирования применяется свойство …',[(':rotate',False),(':scale',True),(':translate',False),(':skew',False)])
        qa(t7,'Для наклона объекта применяется свойство …',[(':rotate',False),(':scale',False),(':translate',False),(':skew',True)])
        qa(t7,'Для перемещения применяется свойство …',[(':rotate',False),(':scale',False),(':translate',True),(':skew',False)])
        qa(t7,'Анимация от одного стиля к другому в течение определенного периода времени - это …',[('трансформация',False),('переход',True),('анимация',False),('периодизация',False)])
        qa(t7,'Чтобы указать свойство как анимируемое, его название передается свойству',[('transform-property',False),('transition-property',True),('animation-property',False),('transition-duration',False)])
        qa(t7,'… - функция плавности, при которой анимация ускоряется к середине и замедляется к концу',[('ease-in-out',False),('ease-in',False),('ease-out',False),('ease',True)])
        qa(t7,'Какое свойство определяет задержку перед выполнением перехода?',[('transition-property',False),('transition-duration',False),('transition-timing-function',False),('transition-delay',True)])
        qa(t7,'Какое свойство задает длительность анимации?',[('animation-property',False),('animation-duration',True),('animation-iteration-count',False),('animation-direction',False)])
        qa(t7,'Какое свойство определяет, сколько раз будет повторяться анимация?',[('animation-delay',False),('animation-duration',False),('animation-iteration-count',True),('animation-direction',False)])

        qa(t8,'Концепция адаптивного дизайна возникла на основе …',[('необходимости подстраивать веб-страницы для различных устройств',True),('развития языка html',False),('развития CSS',False),('развития различных технологий',False)])
        qa(t8,'Как происходит тестирование адаптивных веб-страниц?',[('тестирование на различных устройства',True),('тестирование при помощи эмулятора',False),('изменением размеров в коде',False),('тестирование не происходит',False)])
        qa(t8,'Правила … позволяют определить стиль в зависимости от размеров браузера пользователя',[('адаптивного дизайна',False),('Media Query',True),('кей-фреймов',False),('media',False)])
        qa(t8,'Правило … указывает, что стили применяются к мобильным устройствам',[('media="handheld"',True),('media="screen"',False),('media="all"',False),('media="print"',False)])
        qa(t8,'Правило … указывает, что стили будут применяться ко всем устройствам',[('media="handheld"',False),('media="screen"',False),('media="all"',True),('media="print"',False)])
        qa(t8,'При помощи директивы … можно определить css-файл и поместить в него стили для определенных устройств',[('@export',False),('@import',True),('#export',False),('#import',False)])
        qa(t8,'Функция … - отношение ширины к высоте области браузера.',[('aspect-ratio',True),('device-aspect-ratio',False),('orientation',False),('width',False)])
        qa(t8,'Функция … - отношение ширины к высоте экрана устройства.',[('aspect-ratio',False),('device-aspect-ratio',True),('orientation',False),('width',False)])
        qa(t8,'Функция ориентации …',[('aspect-ratio',False),('device-aspect-ratio',False),('orientation',True),('width',False)])
        qa(t8,'Функция … - определение ширины.',[('aspect-ratio',False),('device-aspect-ratio',False),('orientation',False),('width',True)])

        qa(t9,'Начало центральной оси описывает термин …',[('main start',True),('main end',False),('cross start',False),('cross end',False)])
        qa(t9,'Свойство … определяет, будет ли контейнер иметь несколько рядов, чтобы вместить все элементы',[('flex-direction',False),('flex-wrap',True),('flex-flow',False),('flex-basis',False)])
        qa(t9,'Свойство … позволяет установить группу, позволяя переопределить его позицию',[('order',True),('orphans',False),('justify-items',False),('flex-shrink',False)])
        qa(t9,'При указании … элементы равным образом распределяют пространство между левым и правым краями контейнера',[('space-between',True),('space-around',False),('space-evenly',False),('stretch',False)])
        qa(t9,'При указании значения … для align-content строки занимают все свободное место',[('space-between',False),('space-around',False),('space-evenly',False),('stretch',True)])
        qa(t9,'Свойство … определяет, как элемент будет уменьшаться относительно других элементов в контейнере',[('flex-basis',False),('flex-shrink',True),('flex-grow',False),('flex-flow',False)])
        qa(t9,'Свойство … определяет начальный размер контейнера',[('flex-basis',True),('flex-shrink',False),('flex-grow',False),('flex-flow',False)])
        qa(t9,'Укажите правильную последовательность в использовании свойства flex',[('flex: [flex-basis] [flex-grow] [flex-shrink]',False),('flex: [flex-grow] [flex-basis] [flex-shrink]',False),('flex: [flex-grow] [flex-shrink] [flex-basis]',True),('flex: [flex-basis] [flex-shrink] [flex-grow]',False)])
        qa(t9,'… - значение по умолчанию свойства flex-direction',[('row',True),('row-reverse',False),('column',False),('column-reverse',False)])
        qa(t9,'… - значение по умолчанию свойства flex-wrap',[('wrap-reverse',False),('wrap',False),('nowrap',True),('unset',False)])

        qa(t10,'Для создания grid-контейнера указывается свойство …',[('display: inline-grid',True),('display: grid-inline',False),('display: flex-grid',False),('display: block-grid',False)])
        qa(t10,'Укажите, верно, записанное свойство grid',[('grid: grid-template-columns/grid-template-rows',False),('grid: grid-template-rows/grid-template-columns',True),('grid: [grid-template-columns] [grid-template-rows]',False),('grid: [grid-template-rows] [grid-template-columns]',False)])
        qa(t10,'Укажите правильный вариант сокращения строки grid-template-rows: 5em 5em 5em 5em',[('grid-template-rows: 4 * 5em',False),('grid-template-rows: 5em * 4',False),('grid-template-rows: repeat(5em, 4)',False),('grid-template-rows: repeat(4, 5em)',True)])
        qa(t10,'Для установки пропорциональных размеров в grid применяется единица измерения …',[('pt',False),('rem',False),('fr',True),('px',False)])
        qa(t10,'В grid указаны столбцы: 2fr 25px 1fr, ширина grid равна 100px. Вычислите ширину первого столбца',[('50px',True),('37.5px',False),('75px',False),('25px',False)])
        qa(t10,'По умолчанию каждый элемент в grid позиционируется …',[('в одну ячейку по порядку',True),('в несколько ячеек по порядку',False),('с нижнего левого угла',False),('с правого верхнего угла',False)])
        qa(t10,'Укажите правильное определение свойства grid-column',[('grid-column: [grid-column-start] [grid-column-end]',False),('grid-column: grid-column-start / grid-column-end',True),('grid-column: [grid-column-end] [grid-column-start]',False),('grid-column: grid-column-end / grid-column-start',False)])
        qa(t10,'Укажите правильное определение свойства grid-area',[('grid-area: row-start / column-start / row-end / column-end',True),('grid-area: row-start / row-end / column-start / column-end',False),('grid-area: column-start / row-start / column-end / row-end',False),('grid-area: column-start / column-end / row-start / row-end',False)])
        qa(t10,'Свойство … позволяет изменить направление элементов',[('grid-auto-flow',True),('grid-template',False),('grid-area',False),('grid',False)])
        qa(t10,'Как будут располагаться ячейки при указании свойства grid-template-areas: "1 1" "2 3" "2 4"? В ответе указано расположение слева направо сверху вниз, пробелом разделены строки grid',[('12 21 34',False),('11 23 24',True),('11 32 42',False),('24 23 11',False)])

        qa(t11,'Переменные в CSS могут хранить …',[('теги',False),('атрибуты',False),('свойства',False),('значения свойств',True)])
        qa(t11,'Определение переменных начинается с …',[('&',False),('--',True),('$',False),('@',False)])
        qa(t11,'С помощью какого выражения можно ссылаться на переменные?',[('let',False),('var',True),('variables',False),('properties',False)])
        qa(t11,'Как использовать переменные глобально для всех элементов?',[('* {…}',False),(': all {…}',False),(': root {…}',True),('{...}',False)])
        qa(t11,'Официальное название переменных в CSS - …',[('кастомные свойства',True),('переменные',False),('настраиваемые переменные',False),('css-переменные',False)])
        qa(t11,'Как можно избежать ошибок при определении переменных?',[('Задать резервное значение первым параметром в var',False),('Задать резервное значение вторым параметром в var',True),('Указать резервное значение после указания переменной',False),('Указать резервное значение до указания переменной',False)])
        qa(t11,'Что, помимо стилизации, могут хранить переменные в CSS?',[('таблицы',False),('файлы',False),('состояния',True),('код CSS/HTML',False)])
        qa(t11,'Укажите правильное задание переменной в свойстве',[('color: --col',False),('color: var (col)',False),('color: var (--col)',True),('color: (--col)var',False)])
        qa(t11,'Укажите правильное задание резервного значения переменной',[('color: var (--col_1, var (--col_2))',True),('color: var(col_1) var (col_2)',False),('color: (var (col_1), var(col_2))',False),('color: (var(--col_1), var(--col_2))',False)])
        qa(t11,'Укажите правильное задание присвоения текстовых значений для последующего вывода их на страницу',[('.user {content: var(--name);}',False),('.user:after {content:var (--name);}',True),('.user {content: var(name);}',False),('.user:after {content:var (name);}',False)])

        # Final Test (t12) with varied points
        qa(t12,'Элемент … указывает базовый адрес',[('base',True),('head',False),('meta',False),('title',False)], points=1)
        qa(t12,'Элемент … структурирует контент на сайте, группирует содержимое в блоки',[('p',False),('div',True),('pre',False),('span',False)], points=1)
        qa(t12,'Атрибут … задает тип кнопки для button',[('submit',False),('button',False),('type',True),('form',False)], points=1)
        qa(t12,'Атрибут … устанавливает текст по умолчанию',[('dir',False),('pattern',False),('placeholder',True),('readonly',False)], points=1)
        qa(t12,'Элемент … объединяет между собой части информации и выполняет их группировку',[('article',False),('section',True),('div',False),('nav',False)], points=2)
        qa(t12,'Nav, как правило, представляет из себя …',[('нумерованный список',False),('ненумерованный список',False),('нумерованный список с набором ссылок',False),('ненумерованный список с набором ссылок',True)], points=1)
        qa(t12,'Для определения селектора класса в CSS перед названием соответствующего класса ставится …',[('-',False),(':',False),('.',True),('#',False)], points=1)
        qa(t12,'Для определения селектора идентификатора в CSS перед названием соответствующего идентификатора ставится …',[('-',False),(':',False),('.',False),('#',True)], points=1)
        qa(t12,'Какой фильтр в CSS делает фотографию размытой?',[('blur',True),('brightness',False),('contrast',False),('grayscale',False)], points=1)
        qa(t12,'Какой фильтр в CSS изменяет яркость изображения?',[('blur',False),('brightness',True),('contrast',False),('grayscale',False)], points=1)
        qa(t12,'Какое свойство блоковых элементов задает внешний отступ...',[('margin',True),('padding',False),('border',False),('content',False)], points=2)
        qa(t12,'Какое свойство блоковых элементов определяет внутренний отступ...',[('margin',False),('padding',True),('border',False),('content',False)], points=2)
        qa(t12,'Для создания трансформаций применяется свойство …',[('transformed',False),('transform',True),('transition',False),('visibility',False)], points=1)
        qa(t12,'Для масштабирования применяется свойство …',[(':rotate',False),(':scale',True),(':translate',False),(':skew',False)], points=1)
        qa(t12,'Концепция адаптивного дизайна возникла на основе …',[('необходимости подстраивать веб-страницы для различных устройств',True),('развития языка html',False),('развития CSS',False),('развития различных технологий',False)], points=1)
        qa(t12,'Как происходит тестирование адаптивных веб-страниц?',[('тестирование на различных устройства',True),('тестирование при помощи эмулятора',False),('изменением размеров в коде',False),('тестирование не происходит',False)], points=1)
        qa(t12,'Начало центральной оси описывает термин …',[('main start',True),('main end',False),('cross start',False),('cross end',False)], points=3)
        qa(t12,'Свойство … определяет, будет ли контейнер иметь несколько рядов...',[('flex-direction',False),('flex-wrap',True),('flex-flow',False),('flex-basis',False)], points=2)
        qa(t12,'Для создания grid-контейнера указывается свойство …',[('display: inline-grid',True),('display: grid-inline',False),('display: flex-grid',False),('display: block-grid',False)], points=1)
        qa(t12,'Укажите, верно, записанное свойство grid',[('grid: grid-template-columns/grid-template-rows',False),('grid: grid-template-rows/grid-template-columns',True),('grid: [grid-template-columns] [grid-template-rows]',False),('grid: [grid-template-rows] [grid-template-columns]',False)], points=3)
        qa(t12,'Переменные в CSS могут хранить …',[('теги',False),('атрибуты',False),('свойства',False),('значения свойств',True)], points=1)
        qa(t12,'Определение переменных начинается с …',[('&',False),('--',True),('$',False),('@',False)], points=1)

        # ── TEST RESULTS ──
        dt_start = timezone.make_aware(datetime(2026, 3, 1, 10, 0, 0))

        # Create 4 test results using the helper function
        create_test_result(user=u1, test_obj=t1, correct_answers_count=8, start_time=dt_start)
        create_test_result(user=u1, test_obj=t1, correct_answers_count=10, start_time=dt_start + timedelta(days=1))
        create_test_result(user=u1, test_obj=t2, correct_answers_count=5, start_time=dt_start + timedelta(days=2))
        create_test_result(user=u1, test_obj=t12, correct_answers_count=18, start_time=dt_start + timedelta(days=5))

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
            f'{UserAnswer.objects.count()} user_answers, '
            f'{TestResult.objects.count()} test_results.'
        ))
