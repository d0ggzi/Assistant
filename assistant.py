from __future__ import print_function
import datetime
import pickle
import os.path
import random

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz
import subprocess
import webbrowser
import pyowm
import config

owm = pyowm.OWM("0c7cb189167666cb7ffbbe3906203557")


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio, language="ru-RU")
            print('Вы сказали: ', said)
        except Exception as e:
            print('Ошибка: ' + str(e))

    return said.lower()


def authenticate_google():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', config.SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_events(day, service_calc):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())

    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service_calc.events().list(calendarId='primary', timeMin=date.isoformat(),
                                               timeMax=end_date.isoformat(),
                                               singleEvents=True,
                                               orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('Событий в этот день нет')
    else:
        speak(f'У вас есть {len(events)} событий в этот день')

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split('T')[1].split("-")[0])
            start_time_h = str(int(start_time.split(":")[0]) + 9)
            start_time_m = str(start_time.split(":")[1])

            speak(event["summary"] + 'at' + start_time_h + ' ' + start_time_m)


def get_date(text):
    text = text.lower()
    today = datetime.date.today()

    if text.count("сегодня") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in config.MONTHS:
            month = config.MONTHS.index(word) + 1
        elif word in config.DAYS:
            day_of_week = config.DAYS.index(word)
        elif word.isdigit():
            day = int(word)

    if text.count('завтра') > 0:
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        day = tomorrow.day
        month = tomorrow.month
        year = tomorrow.year
    else:
        if month < today.month and month != -1:
            year = year + 1
        if day < today.day and month == -1 and day != -1:
            month = month + 1
        if month == -1 and day == -1 and day_of_week != -1:
            current_day_of_week = today.weekday()  # 0-6
            dif = day_of_week - current_day_of_week

            if dif < 0:
                dif += 7
                if text.count("следующий") >= 1:
                    dif += 7

            return today + datetime.timedelta(dif)
    return datetime.date(month=month, day=day, year=year)


def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + '-note.txt'
    with open(file_name, 'w') as f:
        f.write(text)

    subprocess.Popen(["notepad.exe", file_name])


def recognize_cmd(text):
    for c, v in config.opts['cmds'].items():
        for x in v:
            if x in text:
                return c
    return None


def execute_cmd(cmd):
    global text
    if cmd == "kto":
        speak('Меня зовут маруся')
    elif cmd == "time":
        speak(f'Время сейчас - {datetime.datetime.now().hour} {datetime.datetime.now().minute}')
    elif cmd == "open":
        for exe in config.opts['open_list']:
            if exe in text:
                if exe == 'steam':
                    subprocess.call(["C:\\Program Files (x86)\\Steam\\Steam.exe"])
                elif exe == 'discord':
                    subprocess.call(["C:\\Users\\koval\\AppData\\Local\\Discord\\app-0.0.306\\Discord.exe"])
                elif exe == 'opera':
                    subprocess.call(["C:\\Users\\koval\\AppData\\Local\\Programs\\Opera GX\\launcher.exe"])
                elif exe == 'вконтакте':
                    webbrowser.open('https://vk.com', new=2)
                elif exe == 'youtube':
                    webbrowser.open('https://youtu.be', new=2)
                speak(f'Открываю {exe}')
    elif cmd == "CALENDAR_STRS":
        date = get_date(text)
        if date:
            get_events(date, service_calc)
    elif cmd == "weather":
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place('Yakutsk, Russia')
        w = observation.weather
        temp = int(w.temperature('celsius')['temp'])
        speak(f"Температура сейчас {temp}")
    elif cmd == "NOTE_STRS":
        speak('Что надо записать?')
        note_text = get_audio()
        note(note_text)
        speak("Запись сделана")
    elif cmd == "destiny":
        speak(random.choice(config.responses))
    else:
        speak("Что-то я ничего не поняла")


r = sr.Recognizer()
m = sr.Microphone(device_index=1)

with m as source:
    r.adjust_for_ambient_noise(source)

service_calc = authenticate_google()
print('Start')

while True:
    print('Слушаю Вас')
    text = get_audio()
    for name in config.opts['alias']:
        if name in text:
            speak('Слушаю вас, господин')
            text = get_audio()
            cmd = recognize_cmd(text)
            execute_cmd(cmd)
    time.sleep(0.1)
