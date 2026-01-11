import speech_recognition as sr
import pyttsx3
import webbrowser
import musicLib
import os
import applist
from openai import OpenAI

client = OpenAI()
# engine = pyttsx3.init()
# engine.setProperty("rate", 180)
def speak(text):
    engine = pyttsx3.init()   # 🔥 re-create engine every time
    engine.stop()
    engine.say(text)
    engine.runAndWait()

def ask_gpt(text):
    prompt = f" You are a voice assistant. Answer in 2 to 3 short lines. Question: {text}"
    try:
      response = client.responses.create(
                      model="gpt-4.1-nano",
                      input= prompt ,
                      store=False,)
      
      return response.output_text
    except Exception as e:
        print("AI server Error: " , e)
        return"Sorry , I am unable to connect with AI, Right now"

# print(ask_gemini("Explain how AI "))

recognizer = sr.Recognizer()

def processCommand(c):
    if "app" in c.lower():
        app = c.lower().split(" ")
        AppLoc = applist.APPS.get(app[1])
        os.startfile(AppLoc)
    elif c.lower().startswith("open"):
        site = c.lower().split(" ")[1]
        webbrowser.open(f"https://www.{site}.com")

    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        webbrowser.open(musicLib.music[song])
    else: 
        ai_replay = ask_gpt(c)
        print("AI: ", ai_replay)
        speak(ai_replay)

if __name__ == "__main__":
    speak("Initializing jarvis")
    while True:
        try:
            # Awake word listining 
            with sr.Microphone() as source:
                # recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                audio = recognizer.listen(source,timeout=4)
            command = recognizer.recognize_google(audio)
            # print(command)
            print("You said:", command)
            if (command.lower().startswith("computer")):
              speak("Ya")
              with sr.Microphone() as source:
                  print("computer Active")
                  audio = recognizer.listen(source,timeout=5,)
                  command = recognizer.recognize_google(audio)
                  print("You said:", command)
                  processCommand(command)

            # speak(command)   # ✅ now works EVERY time

        except Exception as e:
            print("Error:", e)
            