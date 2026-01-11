import speech_recognition as sr
import pyttsx3
import webbrowser
import os
from openai import OpenAI

client = OpenAI()

def speak(text):
    engine = pyttsx3.init()   # 🔥 re-create engine every time
    engine.stop()
    engine.say(text)
    engine.runAndWait()

loopC = True
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
applist = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "Files": "explorer.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "code": r"C:\Users\mohda\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"
}
music = {
  "test": "https://www.youtube.com/watch?v=QpICROpBFI0",
  "ishqa": "https://www.youtube.com/watch?v=j18MRhEfmPk",
  "kaho": "https://www.youtube.com/watch?v=S-z6vyR89Ig",
  "jhol": "https://www.youtube.com/shorts/q8uDiwfs7OA",
  "mala": "https://www.youtube.com/watch?v=eYSaHXXFIBU"
}

def processCommand(c):
    taskL = c.split(" ")
    if not taskL:
        speak("Please speak again")
        return True
    if taskL[0] == "stop":
         return False
    elif "app" == taskL[-1]:
        AppLoc = applist.get(taskL[1])
        if AppLoc:
            os.startfile(AppLoc)
        else: speak(f"{AppLoc} not found")
    elif c.lower().startswith("open"):
        webbrowser.open(f"https://www.{taskL[1]}.com")

    elif c.startswith("play"):
        Pmusic = music.get(taskL[1])
        if Pmusic:
            webbrowser.open(Pmusic)
        else: speak(f"{Pmusic} not found")
    else:
        ai_replay = ask_gpt(c)
        print("AI: ", ai_replay)
        speak(ai_replay)
    return True

if __name__ == "__main__":
    speak("Initializing computer")
    while loopC:
        try:
            # Awake word listining 
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source,timeout=5)
            command = recognizer.recognize_google(audio)
            # print(command)
            command = command.lower().strip()
            print("You said:", command)
            if command.startswith("computer"):
                task = command[len("computer"):].strip()
                loopC =  processCommand(task)

            # speak(command)   # ✅ now works EVERY time

        except Exception as e:
            print("Error:", e)
    speak("Program is stopped")
        
        