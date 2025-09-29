# OIBSIP-PYTHONPROGRAMMING--TASK1
 Developed an advanced voice assistant with natural language processing capabilities. Enable it to perform tasks such as sending emails, setting reminders, providing weather updates, controlling smart home devices, answering general knowledge questions, and even integrating with third-party APIs for more functionality.
Objective

To build a voice-activated personal assistant named Puneeth that can handle everyday tasks like sending emails, setting reminders, fetching weather, controlling smart home devices, searching Wikipedia, and chatting via OpenAI’s GPT.

Steps Involved

Setup Environment

Configure .env with API keys, SMTP, MQTT, and assistant settings.

Install required Python libraries (speech_recognition, pyttsx3, openai, requests, etc.).

Initialize Components

Load environment variables.

Configure text-to-speech engine and speech recognizer.

Setup SQLite database for reminders.

Start a scheduler for timed events.

Implement Core Functions

Text-to-speech (speak) and speech-to-text (listen).

Send emails via SMTP.

Set reminders and fetch them from SQLite.

Fetch weather using OpenWeather API.

Control smart devices via MQTT.

Query Wikipedia or fallback to GPT.

Open websites or local applications.

Command Parsing

Recognize commands like “time”, “date”, “weather”, “remind me”, “email”, “open …”, “turn on/off …”.

Match inputs using regex and fuzzy string matching.

Run Assistant

Start continuous background listener.

Process voice input and execute mapped actions.

Steps Performed in Code

Load .env values into variables.

Create SQLite reminders table.

Implement parse_command() to interpret user input.

Add voice interaction (speaking and listening).

Integrate APIs (OpenWeather, OpenAI GPT, Wikipedia).

Implement smart home control using MQTT publish.

Enable real-time continuous listening with callbacks.

Tools Used

Python Libraries:

speech_recognition, pyttsx3 → Voice input/output.

smtplib → Email sending.

sqlite3, apscheduler → Reminders and scheduling.

requests → API requests (weather).

wikipedia, openai → Information & conversational AI.

paho.mqtt.publish → Smart home device control.

dotenv → Load environment config.

fuzzywuzzy → Command matching.

External Services:

Gmail SMTP server.

OpenWeather API.

MQTT Broker.

OpenAI GPT API.

Outcome

A working voice-controlled assistant that can:
✅ Speak and understand natural voice commands.
✅ Tell date, time, and weather.
✅ Set and announce reminders.
✅ Send emails.
✅ Control IoT/smart devices.
✅ Search Wikipedia or ask GPT for answers.
✅ Open apps and websites.
