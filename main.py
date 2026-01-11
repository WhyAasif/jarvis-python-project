import speech_recognition as sr
import pyttsx3
import webbrowser
import musicLib
import os
import applist
import subprocess
import platform
from openai import OpenAI

client = OpenAI()

# Initialize/reinit TTS engine once to avoid re-creating it for every utterance
def _init_engine():
    e = pyttsx3.init()
    e.setProperty("rate", 150)
    e.setProperty("volume", 1.0)
    return e

_engine = _init_engine()


# Configuration: backend selection and modes (overridable via env vars)
# TTS_BACKEND: "powershell" or "pyttsx3" (default: powershell on Windows, pyttsx3 otherwise)
# TTS_ALWAYS_INIT: if set to "1"/"true", re-create pyttsx3 engine for every call (more robust, slower)
# TTS_FORCE_POWERSHELL: if set to "1"/"true", force PowerShell backend on Windows

if platform.system() == "Windows":
    TTS_BACKEND = os.environ.get("TTS_BACKEND", "powershell")
else:
    TTS_BACKEND = os.environ.get("TTS_BACKEND", "pyttsx3")

TTS_ALWAYS_INIT = os.environ.get("TTS_ALWAYS_INIT", "0").lower() in ("1", "true", "yes")
TTS_FORCE_POWERSHELL = os.environ.get("TTS_FORCE_POWERSHELL", "0").lower() in ("1", "true", "yes")

if TTS_FORCE_POWERSHELL and platform.system() == "Windows":
    TTS_BACKEND = "powershell"


def _speak_pyttsx3(text):
    """Speak using pyttsx3; returns True on success, False on failure.

    Behavior depends on TTS_ALWAYS_INIT: if True, a fresh engine is created per call and disposed.
    """
    global _engine
    try:
        if TTS_ALWAYS_INIT:
            # always create a fresh engine for this utterance
            e = pyttsx3.init()
            e.setProperty("rate", 150)
            e.setProperty("volume", 1.0)
            e.say(text)
            e.runAndWait()
            try:
                e.stop()
            except Exception:
                pass
            print("TTS: pyttsx3 (init-per-call) done")
            return True

        # normal path: use shared engine with re-init on failure
        _engine.say(text)
        _engine.runAndWait()
        try:
            _engine.stop()
        except Exception:
            pass
        print("TTS: pyttsx3 done")
        return True
    except Exception as e:
        print("TTS: pyttsx3 error:", e)
        # try to reinit once for shared-engine mode
        if not TTS_ALWAYS_INIT:
            try:
                _engine = _init_engine()
                print("TTS: pyttsx3 reinitialized")
            except Exception as e2:
                print("TTS: pyttsx3 reinit failed:", e2)
        return False


def _speak_powershell(text):
    """Fallback TTS using Windows PowerShell System.Speech (synchronous)."""
    try:
        safe = text.replace('"', '\\"')
        cmd = [
            'powershell', '-NoProfile', '-Command',
            f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe}")'
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("TTS: PowerShell done")
        return True
    except Exception as e:
        print("Powershell TTS failed:", e)
        return False


def speak(text):
    """Speak text using the selected backend with sensible fallback behavior."""
    print("TTS: speaking ->", text)

    # If Windows and forced PowerShell, prefer it
    if TTS_BACKEND == "powershell" and platform.system() == "Windows":
        if _speak_powershell(text):
            return
        # fallback to pyttsx3 if PowerShell fails
        print("TTS: PowerShell failed, trying pyttsx3")
        if _speak_pyttsx3(text):
            return
        print("TTS: all backends failed")

    else:
        # primary: pyttsx3 (or init-per-call mode)
        if _speak_pyttsx3(text):
            return
        print("TTS: pyttsx3 failed, trying PowerShell on Windows")
        if platform.system() == "Windows":
            _speak_powershell(text)
        else:
            print("TTS: no fallback available on this OS")

def ask_gpt(text):
    prompt = f"You are a voice assistant. Answer in 2 to 3 short lines. Question: {text}"
    try:
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=prompt,
            store=False,  # don't store by default
        )
        return response.output_text.strip()
    except Exception as e:
        print("Warning: GPT request failed:", e)
        return "Sorry, I couldn't reach the AI service right now." 

# print(ask_gemini("Explain how AI "))

recognizer = sr.Recognizer()

def process_command(raw):
    """Parse and execute a spoken command in a robust way."""
    cmd = raw.strip()
    print("Command:", cmd)
    lower = cmd.lower()

    # simple verb parsing: verb and rest
    verb, _, rest = lower.partition(' ')
    rest = rest.strip()

    if verb == "app" or (verb == "open" and rest.startswith("app ")):
        # support 'app notepad' and 'open app notepad'
        app_name = rest.split(' ', 1)[-1] if rest.startswith('app ') else rest
        app_path = applist.APPS.get(app_name)
        if app_path:
            try:
                os.startfile(app_path)
            except Exception as e:
                print("Failed to start app:", e)
                speak(f"I couldn't start {app_name}.")
        else:
            speak(f"I couldn't find the app {app_name}.")

    elif verb == "open":
        # open a site; allow 'open example.com' or 'open example'
        site = rest.split(' ')[0]
        if site:
            if not site.startswith("http"):
                url = f"https://{site}"
            else:
                url = site
            webbrowser.open(url)
        else:
            speak("Which site should I open?")

    elif verb == "play":
        song = rest
        url = musicLib.music.get(song)
        if url:
            webbrowser.open(url)
        else:
            speak(f"I couldn't find the song {song}.")

    else:
        ai_reply = ask_gpt(cmd)
        print("AI:", ai_reply)
        speak(ai_reply)

if __name__ == "__main__":
    speak("Initializing computer")

    # tune recognizer a bit
    recognizer.pause_threshold = 0.5
    recognizer.energy_threshold = 300

    # warm up microphone to adjust for ambient noise
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception as e:
        print("Warning: microphone initialization failed:", e)

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for wake word 'computer'...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            try:
                command = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                # couldn't understand audio
                continue
            except sr.RequestError as e:
                print("Recognition API error:", e)
                continue

            print("You said:", command)
            if command.strip().lower() == "computer":
                speak("Yes?")
                with sr.Microphone() as source:
                    print("Awaiting command...")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                try:
                    command = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    speak("Sorry, I didn't catch that.")
                    continue
                except sr.RequestError as e:
                    print("Recognition API error:", e)
                    continue

                process_command(command)

        except sr.WaitTimeoutError:
            # no speech detected within timeout; continue listening
            continue
        except KeyboardInterrupt:
            print("Shutting down.")
            break
        except Exception as e:
            print("Error:", e)
            continue