import code
import calendar
import flask
import psycopg2
import feedparser
# pip install qrcode
import qrcode
from flask import Flask, request, render_template
import sys
import csv
import json
import datetime

#
# connect info for conn = psycopg2.connect(dbname=DATABASE, user=DB_USER, password=PASSWORD, host=HOST, port=PORT)
DATABASE = "prof2025"
DB_USER = "postgres"
PASSWORD = "root"
HOST = "192.168.2.202"
PORT = "5432"
KEY_WORD = "12345"
RSS_HOST = "127.0.0.1"

current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
print(current_month)


def job():
    # param = {}
    # param['username'] = "Пользователь"
    # param['title'] = 'Домашняя страница'
    # staff = get_staff()
    # news = get_news()
    # return render_template('index.html', staff=staff, **param)
    print("hello")


app = Flask(__name__)

month = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь',
         'декабрь', ]

month_eng = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
             'November', 'December']


@app.route('/')
@app.route('/index')
def index():
    param = {}
    param['username'] = "Пользователь"
    param['title'] = 'Домашняя страница'
    # получаем нажатую кнопку next или prev
    is_change_month = request.args.get('submit_button', None)
    param['calendar'] = get_calendar(is_change_month)
    staff = get_staff()
    news = get_news()
    events = get_events()
    return render_template('index.html', staff=staff, news=news, events=events, **param)


@app.route('/', methods=['POST'])
@app.route('/index', methods=['POST'])
def search_data():
    text = request.form['text']
    print(text)
    param = {}
    param['username'] = "Пользователь"
    param['title'] = 'Домашняя страница'
    param['calendar'] = get_calendar(None)
    staff = get_staff(text)
    news = get_news()
    events = get_events()
    return render_template('index.html', staff=staff, news=news, events=events, **param)

# вернет рабочие номера дней кроме дней воскресных и субботних
def get_work_days():
    # calendar.monthrange(current_year, current_month)
    # возвращает кортеж вида (1, 31) диапазон дней для указанного года и месяца
    result = []
    for day in range(1, calendar.monthrange(current_year, current_month)[1] + 1):
        current_day = datetime.datetime(current_year, current_month, day)
        day_of_week = current_day.weekday()
        if day_of_week in {0, 1, 2, 3, 4}:
            result.append(day)
    return result


def get_calendar(is_change_month):
    global current_year
    global current_month

    # рабочие дни
    work_days = get_work_days()

    # смена месяцев
    if is_change_month == 'next':
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

    if is_change_month == 'prev':
        if current_month == 1:
            current_month = 12
            current_year -= 1
        else:
            current_month -= 1

    cl = calendar.HTMLCalendar(firstweekday=0)
    # в строке s будет лежать html таблица календаря
    s = cl.formatmonth(current_year, current_month)
    # эта часть для внешнего оформления. там просто анг названия, меняем на русские
    days = {"Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт",
            "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"}
    me = month_eng[current_month - 1]
    second_line = f'<tr><th colspan="7" class="month">{me} {current_year}</th></tr>'
    s = s.replace(f'<tr><th colspan="7" class="month">{month_eng[current_month]}'
                  f' {current_year}</th></tr>', second_line)
    s = s.replace(me, month[current_month - 1].capitalize())
    # меняем англ названия на русские
    for key, value in days.items():
        s = s.replace(key, value)


    try:
        # запрос к БД на получение праздничных дней за текущий месяц и год
        conn = psycopg2.connect(dbname=DATABASE, user=DB_USER,
                                password=PASSWORD, host=HOST, port=PORT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT EXTRACT(DAY FROM exception_date), is_working_day "
                       f"FROM working_calendar "
                       f"WHERE EXTRACT(MONTH FROM exception_date) = {current_month} "
                       f"and EXTRACT(YEAR FROM exception_date) = {current_year}")

        results = cursor.fetchall()
        cursor.close()

        days = []
        for day in results:
            d = int(day[0])
            days.append({'num': int(day[0]), 'is_work': day[1]})
            # в строках добаляем для дня класс holiday
            if not day[1]:
                # добавляем в тег td для данного дня класс holiday
                s = s.replace(f'">{d}<', f' holiday">{d}<')
                # удаляем день из списка рабочих дней праздничный
                if d in work_days:
                    work_days.remove(d)

        # запрос возвращает количество мероприятий в указанный день для текущего месяца и года
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT EXTRACT(DAY FROM date_start), count(*), date_start "
            f"FROM events e "
            f"WHERE EXTRACT(MONTH FROM date_start) = {current_month} "
            f"and EXTRACT(YEAR FROM date_start) = {current_year}"
            f" GROUP BY date_start")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        days = []
        for day in results:
            d = int(day[0])
            days.append({'num': int(day[0]), 'count': day[1]})
            # добавляем в теги классы five или two или none
            # если в этот день пять и более мероприятий, то добавляем
            # в тег td класс five
            if day[1] >= 5:
                s = s.replace(f'">{d}<', f' five">{d}<')
                # удаляем его из списка рабочих дней
                if d in work_days:
                    work_days.remove(d)
            # если в этот день от 2 до 5
            # в тег td класс two
            elif day[1] >= 2:
                s = s.replace(f'">{d}<', f' two">{d}<')
                # удаляем его из списка рабочих дней
                if d in work_days:
                    work_days.remove(d)

        # оставшиеся дни в месяце красим желтым. код цвета указан в задании
        for day in work_days:
            s = s.replace(f'">{day}<', f' none">{day}<')

    except Exception as e:
        print(f"Ошибка {e}")

    return s


def generate_qrcode(name, surname, position, work_phone, phone, work_email, ind):
    data = f'''BEGIN:VCARD
    
    VERSION:3.0
    
    N:{name}
    
    FN:{surname}
    
    ORG:ГК Дороги России
    
    TITLE:{position}
    
    TEL;WORK;VOICE:{work_phone}
    
    TEL;CELL:{phone}
    
    EMAIL;WORK;INTERNET:{work_email}
    
    END:VCARD'''

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img.save(f"static/images/qrcodes/{ind}.jpg")
    return f'images/qrcodes/{ind}.jpg'


def get_news():
    feed_items = []
    ## распарсить ответ веб-сервера
    feed_data = feedparser.parse(f"http://{RSS_HOST}:5000/swagger")
    print(feed_data)
    for entry in feed_data.entries:
        print(entry)
        dates = entry.published.split()
        feed_items.append({
            'title': entry.title,
            'link': entry.link,
            'description': entry.description,
            'published': ' '.join(dates[1:5])
        })
    feed_items.sort(key=lambda x: x['published'], reverse=True)
    return feed_items


def get_events():
    try:
        conn = psycopg2.connect(dbname=DATABASE, user=DB_USER,
                                password=PASSWORD, host=HOST, port=PORT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT e.title, e.date_start, e.info, s.surname, "
                       f"s.name, s.patronymic "
                       f"FROM events e left join staff s on e.employee_id = s.id ")

        results = cursor.fetchall()
        cursor.close()
        conn.close()
        events = []
        for event in results:
            events.append({
                'title': event[0],
                'date': event[1].strftime('%d.%m.%Y'),
                'description': event[2],
                'author': f"{event[3]} {event[4][:1]}.{event[5][:1]}."
            })
        result = {"events": events}
        return result
    except Exception as e:
        print(f"Ошибка {e}")


def get_staff(name=None):
    try:
        conn = psycopg2.connect(dbname=DATABASE, user=DB_USER,
                                password=PASSWORD, host=HOST, port=PORT)
        cursor = conn.cursor()
        results = []
        if name:
            cursor.execute(f"SELECT s.id, s.surname, "
                           f"s.name, s.patronymic,"
                           f" s.work_phone, s.phone, s.work_email, s.birthday, "
                           f" p.title, "
                           f" e.title, u.title "
                           f"FROM staff s join positions p on"
                           f" s.position_id = p.id "
                           f" left join education_levels e on s.education_level_id = e.id "
                           f" join units u on s.unit_id = u.id WHERE LOWER(s.surname) LIKE '%{name.lower()}%' OR"
                           f" LOWER(s.name) LIKE '%{name.lower()}%' OR "
                           f" LOWER(s.patronymic) LIKE '%{name.lower()}%'")
        else:
            cursor.execute(f"SELECT s.id, s.surname, "
                           f"s.name, s.patronymic,"
                           f" s.work_phone, s.phone, s.work_email, s.birthday, "
                           f" p.title, "
                           f" e.title, u.title "
                           f"FROM staff s join positions p on"
                           f" s.position_id = p.id "
                           f" left join education_levels e on s.education_level_id = e.id "
                           f" join units u on s.unit_id = u.id ")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        result = {"staff": []}
        staff = []
        ind = 1
        for employee in results:
            ind += 1
            unit = {
                'id': employee[0],
                'fio': f"{employee[1]} {employee[2]} {employee[3]}",
                'work_phone': employee[4],
                'phone': employee[5] if employee[5] else "-",
                'email': employee[6] if employee[6] else "-",
                'birthday': f"{employee[7].day} {month[employee[7].month - 1]}",
                'position': employee[8],
                'education': employee[9] if employee[5] else "-",
                'unit': ' '.join(employee[10].split()[1:]),
                'qrcode': generate_qrcode(employee[2], employee[1], employee[8], employee[4],
                                          employee[5] if employee[5] else "-", employee[6] if employee[6] else "-", ind)
            }

            staff.append(unit)
        result = {"staff": staff}
        return result
    except Exception as e:
        print(f"Ошибка {e}")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
