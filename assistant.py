import os
import smtplib
import sqlite3
from datetime import datetime, timedelta
import webbrowser
import subprocess
import re
import time

import pyttsx3
import speech_recognition as sr
import requests
import wikipedia
import paho.mqtt.publish as publish
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
import openai

# ================= CONFIG =================
load_dotenv()

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Puneeth")
DB_FILE = os.getenv("ASSISTANT_DB", "assistant.db")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASS = os.getenv("SMTP_PASSWORD")

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "London")

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USERNAME")
MQTT_PASS = os.getenv("MQTT_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# ================= INIT =================
engine = pyttsx3.init()
engine.setProperty('volume', 1.0)  # Max volume
engine.setProperty('rate', 150)    # Clear speech rate

recognizer = sr.Recognizer()
scheduler = BackgroundScheduler()
scheduler.start()

# Database for reminders
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, text TEXT, time DATETIME)")
conn.commit()

# ================= CORE FUNCTIONS =================
def speak(text: str):
    """Speak text clearly and loudly"""
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()  # Wait for speech to finish

def listen(timeout=15):
    """Listen from microphone and return recognized speech"""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            command = recognizer.recognize_google(audio)
            return command.lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            speak("Network error while recognizing speech.")
            return ""

# ================= ACTIONS =================
def send_email():
    speak("Who do you want to send the email to?")
    to_addr = listen()
    if not to_addr:
        speak("Email cancelled.")
        return
    speak("What is the subject?")
    subject = listen()
    if not subject:
        speak("Email cancelled.")
        return
    speak("What is the message?")
    body = listen()
    if not body:
        speak("Email cancelled.")
        return
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail(SMTP_USER, to_addr, msg)
        speak("Email sent successfully.")
    except Exception as e:
        speak(f"Failed to send email: {e}")

def set_reminder(task, delay_seconds):
    remind_time = datetime.now() + timedelta(seconds=delay_seconds)
    cursor.execute("INSERT INTO reminders (text, time) VALUES (?, ?)", (task, remind_time))
    conn.commit()
    scheduler.add_job(lambda: speak(f"Reminder: {task}"), "date", run_date=remind_time)
    speak(f"Reminder set for {remind_time.strftime('%H:%M:%S')}")

def get_weather(city=DEFAULT_CITY):
    if not WEATHER_API_KEY:
        speak("Weather API key is missing.")
        return
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") != 200:
            speak(f"Couldn't fetch weather: {res.get('message', 'Unknown error')}")
            return
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        speak(f"The weather in {city} is {temp}°C with {desc}.")
    except Exception as e:
        speak(f"Error fetching weather: {e}")

def control_device(command):
    if not MQTT_BROKER:
        speak("MQTT broker not configured.")
        return
    try:
        publish.single("home/device", command, hostname=MQTT_BROKER,
                       port=MQTT_PORT, auth={"username": MQTT_USER, "password": MQTT_PASS})
        speak(f"Sent command '{command}' to smart home device.")
    except Exception as e:
        speak(f"Failed to control device: {e}")

def search_wiki(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        speak(summary)
    except Exception:
        speak("I couldn't find information on that.")

def ask_gpt(prompt: str):
    """Ask OpenAI GPT for a conversational response."""
    if not OPENAI_API_KEY:
        speak("OpenAI API key is not configured.")
        return
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        answer = response['choices'][0]['message']['content'].strip()
        speak(answer)
    except Exception as e:
        speak(f"Error contacting OpenAI: {e}")

WEBSITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com"
}

LOCAL_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
}

# ================= COMMAND PARSER =================
def parse_command(cmd: str):
    if not cmd:
        return

    # Repeat question
    speak(f"You said: {cmd}")

    # EXIT
    if any(x in cmd for x in ["exit", "quit", "stop"]):
        speak("Goodbye!")
        scheduler.shutdown()
        exit()

    # TIME
    if "time" in cmd:
        speak(f"The current time is {datetime.now().strftime('%H:%M:%S')}")
        return

    # DATE
    if "date" in cmd or "day" in cmd:
        speak(f"Today is {datetime.now().strftime('%A, %d %B %Y')}")
        return

    # WEATHER
    if "weather" in cmd:
        city_match = re.search(r"in (\w+)", cmd)
        city = city_match.group(1) if city_match else DEFAULT_CITY
        get_weather(city)
        return

    # REMINDERS
    if "remind me to" in cmd:
        match = re.search(r"remind me to (.+?) in (\d+) (seconds?|minutes?|hours?)", cmd)
        if match:
            task, value, unit = match.groups()
            delay = int(value)
            if "minute" in unit:
                delay *= 60
            elif "hour" in unit:
                delay *= 3600
            set_reminder(task, delay)
        else:
            speak("Specify reminder as 'Remind me to [task] in [number] minutes/seconds/hours'.")
        return

    # EMAIL
    if "email" in cmd:
        send_email()
        return

    # SMART HOME
    if "turn on" in cmd or "turn off" in cmd:
        control_device(cmd)
        return

    # OPEN WEBSITE / APP
    if "open" in cmd:
        site = cmd.replace("open", "").strip()
        for app in LOCAL_APPS:
            if fuzz.ratio(site, app) > 80:
                try:
                    subprocess.Popen(LOCAL_APPS[app])
                    speak(f"Opening {app}")
                    return
                except Exception as e:
                    speak(f"Cannot open {app}: {e}")
                    return
        url = WEBSITE_MAP.get(site.lower(), f"https://www.{site.replace(' ', '')}.com")
        try:
            speak(f"Opening {site}")
            webbrowser.open(url)
        except Exception as e:
            speak(f"Couldn't open {site}: {e}")
        return

    # WIKIPEDIA or GPT fallback
    try:
        search_wiki(cmd)
    except Exception:
        ask_gpt(cmd)

# ================= CONTINUOUS LISTENER =================
def callback(recognizer, audio):
    try:
        command = recognizer.recognize_google(audio)
        parse_command(command.lower())
    except sr.UnknownValueError:
        speak("Sorry, I couldn't understand that.")
    except sr.RequestError:
        speak("Network error while recognizing speech.")

def main():
    speak(f"Hello, I'm {ASSISTANT_NAME}. How can I help?")
    stop_listening = recognizer.listen_in_background(sr.Microphone(), callback)
    try:
        while True:
            time.sleep(0.1)  # Keep main thread alive
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=False)
        scheduler.shutdown()
        speak("Goodbye!")

if __name__ == "__main__":
    main()
