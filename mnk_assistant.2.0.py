# MNK Universal OpenRouter AI Assistant - Cleaned for Public Sharing

# Import required libraries
import pvporcupine
import pyaudio
import struct
import vosk
import sounddevice as sd
import queue
import json
import pyttsx3
import speech_recognition as sr
import requests
import pyautogui
import os
import threading
import tkinter as tk
from PIL import Image, ImageTk
import imapclient
import email
import smtplib

# ================================
# CONFIG SECTION - SET YOUR OWN KEYS HERE BEFORE USE
# ================================

OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324:free"
PORCUPINE_ACCESS_KEY = "YOUR_PORCUPINE_ACCESS_KEY"
GMAIL_USER = "YOUR_EMAIL@gmail.com"
GMAIL_APP_PASSWORD = "YOUR_APP_PASSWORD"

# ================================

# TTS Setup
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# GUI Setup
app = tk.Tk()
app.title("MNK AI Assistant v4.1 PRO")
app.geometry("600x700")
app.configure(bg="#1E1E1E")

# Load Logo (Optional)
try:
    img = Image.open("mnk_logo.png")
    img = img.resize((150, 150))
    photo = ImageTk.PhotoImage(img)
    logo = tk.Label(app, image=photo, bg="#1E1E1E")
    logo.pack(pady=10)
except:
    pass

title = tk.Label(app, text="MNK AI Assistant", font=("Arial", 24), fg="white", bg="#1E1E1E")
title.pack(pady=10)

output_text = tk.Text(app, height=25, width=70, bg="#2E2E2E", fg="white", font=("Arial", 12))
output_text.pack(pady=10)

# Global Flags for Interruption
stop_speaking_flag = False
pause_speaking_flag = False
interrupt_thread_running = False

# Speak Function with interruption support
def speak(text):
    global stop_speaking_flag, pause_speaking_flag, interrupt_thread_running
    output_text.insert(tk.END, "MNK: " + text + "\n")
    output_text.see(tk.END)
    engine.setProperty('rate', 170)
    stop_speaking_flag = False
    pause_speaking_flag = False

    if not interrupt_thread_running:
        threading.Thread(target=interrupt_listener, daemon=True).start()
        interrupt_thread_running = True

    def speak_thread():
        global stop_speaking_flag, pause_speaking_flag
        chunks = text.split(". ")
        for chunk in chunks:
            if stop_speaking_flag:
                break
            while pause_speaking_flag:
                pass
            engine.say(chunk)
            engine.runAndWait()
        stop_speaking_flag = False
        pause_speaking_flag = False

    threading.Thread(target=speak_thread).start()

# Interruption Listener (background)
def interrupt_listener():
    global stop_speaking_flag, pause_speaking_flag
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        while True:
            try:
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                print(f"Interruption heard: {command}")

                if "stop" in command:
                    stop_speaking_flag = True
                elif "wait" in command:
                    pause_speaking_flag = True
                elif "continue" in command:
                    pause_speaking_flag = False
                elif "listen" in command:
                    stop_speaking_flag = True

            except sr.WaitTimeoutError:
                continue
            except:
                continue

# Listen function
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        output_text.insert(tk.END, "Listening...\n")
        output_text.see(tk.END)
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio)
        output_text.insert(tk.END, "You: " + query + "\n")
        output_text.see(tk.END)
        return query
    except:
        speak("Sorry, I didn't understand.")
        return ""

# OpenRouter API integration
def ask_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response_json = response.json()
        print("=== FULL OPENROUTER RESPONSE ===")
        print(json.dumps(response_json, indent=4))

        if 'choices' in response_json:
            answer = response_json['choices'][0]['message']['content']
            return answer.strip()
        else:
            return "Sorry, I could not generate a response."
    except Exception as e:
        print("API ERROR:", e)
        return "Sorry, there was an error connecting to OpenRouter."

# Translation Function
def ai_translate(text, target_lang):
    prompt = f"Translate this sentence into {target_lang}: {text}"
    translation = ask_openrouter(prompt)
    return translation

# System Commands
def system_commands(command):
    cmd = command.lower()
    if "open notepad" in cmd:
        speak("Opening Notepad")
        os.system("notepad")
    elif "shutdown" in cmd:
        speak("Shutting down")
        os.system("shutdown /s /t 1")
    elif "screenshot" in cmd:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        speak("Screenshot saved")
    else:
        speak("Unknown system command")

# Email Reader
def read_email():
    speak("Checking your inbox.")
    try:
        imap_server = imapclient.IMAPClient('imap.gmail.com', ssl=True)
        imap_server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        imap_server.select_folder('INBOX', readonly=True)
        messages = imap_server.search(['UNSEEN'])
        if not messages:
            speak("No unread emails found.")
        else:
            for uid in messages[:3]:
                raw_message = imap_server.fetch([uid], ['BODY[]', 'FLAGS'])
                msg = email.message_from_bytes(raw_message[uid][b'BODY[]'])
                subject = msg.get('Subject')
                from_email = msg.get('From')
                speak(f"Email from {from_email}. Subject: {subject}")
    except Exception as e:
        speak("Error accessing email.")

# Email Sender
def send_email():
    speak("To whom do you want to send email?")
    to = listen()
    speak("What is the subject?")
    subject = listen()
    speak("What is the message?")
    body = listen()

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        message = f'Subject: {subject}\n\n{body}'
        server.sendmail(GMAIL_USER, to, message)
        server.quit()
        speak("Email sent successfully.")
    except:
        speak("Failed to send email.")

# AI Core Loop
def run_mnk():
    while True:
        query = listen()
        if query == "":
            continue

        if "stop" in query.lower():
            speak("Goodbye boss!")
            break

        if any(word in query.lower() for word in ["open", "shutdown", "screenshot"]):
            system_commands(query)
            continue

        if "read email" in query.lower():
            read_email()
            continue

        if "send email" in query.lower():
            send_email()
            continue

        if "translate" in query.lower():
            speak("Say the sentence.")
            text = listen()
            speak("Which language?")
            lang = listen().lower()

            lang_dict = {
                "urdu": "Urdu", "hindi": "Hindi", "russian": "Russian", "chinese": "Chinese",
                "arabic": "Arabic", "english": "English"
            }

            target_lang = lang_dict.get(lang, 'English')
            translated = ai_translate(text, target_lang)
            speak(f"Translation: {translated}")
            continue

        answer = ask_openrouter(query)
        speak(answer)

# Wakeword Listener
def wakeword_listener():
    porcupine = pvporcupine.create(access_key=PORCUPINE_ACCESS_KEY, keywords=["jarvis"])
    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    speak("Wakeword listener activated. Say 'Jarvis' to activate.")

    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            speak("Yes boss, I am ready.")
            run_mnk()

# Start AI Thread
def start_ai():
    threading.Thread(target=wakeword_listener).start()

# Start Button
start_button = tk.Button(app, text="Start MNK Assistant", font=("Arial", 16), bg="#00A8E8", fg="white", command=start_ai)
start_button.pack(pady=10)

# Start GUI Loop
app.mainloop()
