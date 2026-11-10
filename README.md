# 🎭 EmoTalk — Emotion Detector & Wellness Recommender

EmoTalk is a calm, private space where you can **write or speak how you feel in your own language**.
It finds your emotion and gently responds with a kind message, small activities, a quote and music.

> ⚠️ EmoTalk is a friendly helper, **not a doctor or a therapist**. If you are in danger or thinking of
> ending your life, call **Tele-MANAS 14416 / 1-800-891-4416** (India, free, 24×7) or **112**.

---

## ✨ Features

- **Voice or text** in English, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Punjabi, Kannada, Malayalam,
  Urdu, Nepali (voice) and Odia (typing only — Odia voice is not supported yet).
- **Emotion detection** with a score for every emotion (`j-hartmann/emotion-english-distilroberta-base`, runs locally).
- **Personal replies** written by Groq AI in the person's own language.
- **Let's try something together** — breathing circle, timers, writing box, messages to send to a friend, with a
  "how do you feel now?" check before and after.
- **Daily check-in**, "one good thing" list, streak and a **weekly mood chart**.
- **Care & safety** — always-visible helpline box, a safety check for words that may mean danger, and ready-made
  "reach out to someone" messages.
- **Music** in 19 languages, **games**, a **to-do list**, private **login** (stays logged in after refresh) and history.

## 🛠️ Tech stack

| Part | Technology |
|---|---|
| App | Python, Streamlit |
| Emotion model | Hugging Face `transformers` (runs on your computer) |
| Replies, translation | Groq API |
| Voice to text | Whisper (via Groq) |
| Data | SQLite files (`*.db`) |

## 📁 Project structure

```
app.py            # the Streamlit app
db.py             # users, login and chat history
auth_session.py   # stay logged in after a page refresh (cookie + sessions.db)
todo_store.py     # to-do list (todos.db)
wellbeing.py      # check-ins, safety words, weekly mood, notes (checkins.db)
logo.png          # banner image
requirements.txt
```

## 🚀 Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Create a `.env` file next to `app.py` (or add it in Streamlit Cloud → Secrets):

```env
GROQ_API_KEY=your_groq_key_here
```

Get a free key at [console.groq.com](https://console.groq.com). Never upload `.env` or `*.db` files to GitHub —
the included `.gitignore` already blocks them.

## ☁️ Deploying

On hosts with a temporary disk (such as Streamlit Community Cloud) the `*.db` files can be erased when the app
restarts. For real users, move the data to a hosted database.

## 📄 License

MIT License.
