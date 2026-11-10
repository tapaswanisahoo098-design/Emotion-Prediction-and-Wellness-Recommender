"""Extra care features for EmoTalk:
  * crisis_check(): looks for words that may mean someone is in danger
  * daily check-ins (mood + one good thing), saved per person in checkins.db
  * mood_by_day(): turns past chats + check-ins into one simple number per day
  * reach-out message templates ("send this to a friend")
"""
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
_DB_PATH = Path(__file__).with_name("checkins.db")

HELPLINE_TEXT = "Tele-MANAS: 14416 or 1-800-891-4416 (free, 24×7, many languages)"

# ── 1) Safety words ──────────────────────────────────────────────────────────
# Not a complete list - no keyword list can be. It is a safety net on top of the AI check,
# and it is also run on the English translation, which catches other languages.
_CRISIS_PHRASES = [
    # English
    "kill myself", "killing myself", "end my life", "end it all", "want to die", "wanna die",
    "wish i was dead", "wish i were dead", "better off dead", "suicide", "suicidal",
    "don't want to live", "do not want to live", "dont want to live", "no reason to live",
    "take my life", "hurt myself", "harm myself", "self harm", "self-harm", "cut myself",
    "don't want to be alive", "not want to be alive", "can't go on", "cant go on anymore",
    # Hindi / Hinglish
    "आत्महत्या", "मरना चाहता", "मरना चाहती", "मर जाना चाहता", "मर जाना चाहती", "जीना नहीं चाहता",
    "जीना नहीं चाहती", "जीने का मन नहीं", "खुद को खत्म", "खुद को ख़त्म", "जान दे दू", "जान दे दूँ",
    "atmahatya", "marna chahta", "marna chahti", "mar jana chahta", "mar jana chahti",
    "jeena nahi chahta", "jeena nahi chahti", "jeene ka mann nahi", "khud ko khatam", "jaan de dunga", "jaan de dungi",
    # Odia
    "ଆତ୍ମହତ୍ୟା", "ମରିଯିବାକୁ ଚାହୁଁ", "ମରିବାକୁ ଚାହୁଁ", "ବଞ୍ଚିବାକୁ ଚାହୁଁନାହିଁ", "ବଞ୍ଚିବାକୁ ଇଚ୍ଛା ନାହିଁ", "ବଞ୍ଚିବାକୁ ମନ ନାହିଁ",
    "mari jaibaku chahun", "maribaku chahun", "banchibaku chahunni", "banchibaku ichha nahin",
    # Bengali
    "আত্মহত্যা", "মরে যেতে চাই", "মরতে চাই", "বাঁচতে চাই না", "বাঁচতে ইচ্ছে করছে না", "বাঁচতে ইচ্ছা করে না",
    # Tamil
    "தற்கொலை", "சாக வேண்டும்", "சாகணும்", "சாக விரும்புகிறேன்", "வாழ விருப்பம் இல்லை", "வாழ பிடிக்கவில்லை",
    # Telugu
    "ఆత్మహత్య", "చనిపోవాలని", "చచ్చిపోవాలని", "బ్రతకాలని లేదు", "బతకాలని లేదు",
    # Kannada / Malayalam / Gujarati / Punjabi
    "ಆತ್ಮಹತ್ಯೆ", "ಸಾಯಬೇಕು", "ಸಾಯಬೇಕೆಂದು", "ആത്മഹത്യ", "മരിക്കണം", "മരിക്കാൻ ആഗ്രഹം",
    "આત્મહત્યા", "મરી જવું છે", "મરવું છે", "ਖੁਦਕੁਸ਼ੀ", "ਮਰਨਾ ਚਾਹੁੰਦਾ", "ਮਰਨਾ ਚਾਹੁੰਦੀ",
]

_LONELY_WORDS = ["lonely", "loneliness", "alone", "no one", "nobody", "no friends", "isolated", "left out",
                 "अकेला", "अकेली", "अकेलापन", "ଏକୁଟିଆ", "একা", "தனிமை", "ఒంటరి"]


def _norm(text):
    text = (text or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text)


def crisis_check(*texts):
    """True if any of the texts contains words that may mean the person is in danger."""
    for t in texts:
        t = _norm(t)
        if t and any(p.lower() in t for p in _CRISIS_PHRASES):
            return True
    return False


def feels_lonely(*texts):
    for t in texts:
        t = _norm(t)
        if t and any(w in t for w in _LONELY_WORDS):
            return True
    return False


# ── 2) Reach-out messages ────────────────────────────────────────────────────
REACH_OUT = {
    "English": [
        "Hey, I'm having a heavy day. Are you free for a little chat? It would mean a lot.",
        "I've been feeling a bit alone lately. Can we meet or talk on a call this week?",
        "Just thinking of you. How are you doing? I'd love to catch up.",
    ],
    "Hindi": [
        "आज मेरा दिन थोड़ा भारी है। क्या तुम फ्री हो? थोड़ी बात करें?",
        "कुछ दिनों से मुझे अकेलापन लग रहा है। क्या हम इस हफ़्ते मिल सकते हैं या फ़ोन पर बात कर सकते हैं?",
    ],
    "Odia": [
        "ଆଜି ମୋର ମନ ଟିକେ ଭାରି ଲାଗୁଛି। ତୁମେ ଫ୍ରି ଅଛ କି? ଟିକେ କଥା ହେବା?",
        "କିଛି ଦିନ ହେଲା ମୁଁ ଟିକେ ଏକୁଟିଆ ଅନୁଭବ କରୁଛି। ଏ ସପ୍ତାହରେ ଦେଖା ହେବା କିମ୍ବା ଫୋନରେ କଥା ହେବା?",
    ],
    "Bengali": [
        "আজ আমার মনটা একটু ভারী। তুমি কি ফ্রি আছো? একটু কথা বলবে?",
        "কিছুদিন ধরে আমার একটু একা লাগছে। এই সপ্তাহে দেখা বা ফোনে কথা বলা যাবে?",
    ],
}


def reach_out_messages(language):
    """Ready-to-send messages: in the person's language if we have it, plus English."""
    own = REACH_OUT.get(language, [])
    return own + (REACH_OUT["English"] if language != "English" else [])[:2] if own else REACH_OUT["English"]


# ── 3) Daily check-ins ───────────────────────────────────────────────────────
def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS checkins ("
        "user_id TEXT NOT NULL, day TEXT NOT NULL, mood INTEGER NOT NULL, "
        "good_thing TEXT DEFAULT '', PRIMARY KEY (user_id, day))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS activity_results ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, day TEXT NOT NULL, "
        "mood_before INTEGER, mood_after INTEGER, done INTEGER NOT NULL DEFAULT 0)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, day TEXT NOT NULL, "
        "prompt TEXT, text TEXT NOT NULL)"
    )
    return conn


def today_key():
    return datetime.now(IST).strftime("%Y-%m-%d")


def get_today(user_id):
    with _connect() as conn:
        row = conn.execute("SELECT mood, good_thing FROM checkins WHERE user_id = ? AND day = ?",
                           (str(user_id), today_key())).fetchone()
    return dict(row) if row else None


def save_checkin(user_id, mood, good_thing):
    good_thing = " ".join((good_thing or "").split())[:300]
    with _connect() as conn:
        conn.execute(
            "INSERT INTO checkins (user_id, day, mood, good_thing) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, day) DO UPDATE SET mood = excluded.mood, good_thing = excluded.good_thing",
            (str(user_id), today_key(), int(mood), good_thing),
        )


def recent_checkins(user_id, days=30):
    since = (datetime.now(IST) - timedelta(days=days)).strftime("%Y-%m-%d")
    with _connect() as conn:
        rows = conn.execute("SELECT day, mood, good_thing FROM checkins WHERE user_id = ? AND day >= ? "
                            "ORDER BY day DESC", (str(user_id), since)).fetchall()
    return [dict(r) for r in rows]


def streak(user_id):
    """How many days in a row (ending today or yesterday) the person has checked in."""
    days = {c["day"] for c in recent_checkins(user_id, days=60)}
    d = datetime.now(IST).date()
    if d.strftime("%Y-%m-%d") not in days:
        d -= timedelta(days=1)
    count = 0
    while d.strftime("%Y-%m-%d") in days:
        count += 1
        d -= timedelta(days=1)
    return count


# ── 4) Mood trend ────────────────────────────────────────────────────────────
EMOTION_MOOD = {"joy": 5, "surprise": 4, "neutral": 3, "disgust": 2, "anger": 2, "fear": 2, "sadness": 1}


def mood_by_day(history_rows, checkins, days=7):
    """[(label, average mood 1-5 or None), ...] for the last `days` days, oldest first.
    Uses both the emotions found in chats and the mood picked in daily check-ins."""
    buckets = {}
    for row in history_rows:
        try:
            day = datetime.fromisoformat(row["created_at"]).astimezone(IST).strftime("%Y-%m-%d")
        except Exception:
            continue
        buckets.setdefault(day, []).append(EMOTION_MOOD.get(row["emotion"], 3))
    for c in checkins:
        buckets.setdefault(c["day"], []).append(c["mood"])
    out = []
    today = datetime.now(IST).date()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        vals = buckets.get(d.strftime("%Y-%m-%d"))
        out.append((d.strftime("%a %d"), round(sum(vals) / len(vals), 1) if vals else None))
    return out


# ── 5) "Let's try something together": results, stars and notes ──────────────
def save_activity_result(user_id, before, after, done):
    with _connect() as conn:
        conn.execute("INSERT INTO activity_results (user_id, day, mood_before, mood_after, done) VALUES (?,?,?,?,?)",
                     (str(user_id), today_key(), int(before), int(after), int(done)))


def weekly_activity_count(user_id):
    """How many activities the person finished in the last 7 days (the stars)."""
    since = (datetime.now(IST) - timedelta(days=6)).strftime("%Y-%m-%d")
    with _connect() as conn:
        row = conn.execute("SELECT COALESCE(SUM(done), 0) FROM activity_results WHERE user_id = ? AND day >= ?",
                           (str(user_id), since)).fetchone()
    return int(row[0])


def recent_activity_moods(user_id, days=8):
    """How they felt AFTER doing activities, in the same shape as check-ins (for the week chart)."""
    since = (datetime.now(IST) - timedelta(days=days)).strftime("%Y-%m-%d")
    with _connect() as conn:
        rows = conn.execute("SELECT day, mood_after FROM activity_results WHERE user_id = ? AND day >= ?",
                            (str(user_id), since)).fetchall()
    return [{"day": r[0], "mood": r[1]} for r in rows if r[1]]


def save_note(user_id, prompt, text):
    text = (text or "").strip()[:2000]
    if not text:
        return
    with _connect() as conn:
        conn.execute("INSERT INTO notes (user_id, day, prompt, text) VALUES (?,?,?,?)",
                     (str(user_id), today_key(), (prompt or "")[:300], text))


def recent_notes(user_id, n=3):
    with _connect() as conn:
        rows = conn.execute("SELECT day, text FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                            (str(user_id), n)).fetchall()
    return [{"day": r[0], "text": r[1]} for r in rows]