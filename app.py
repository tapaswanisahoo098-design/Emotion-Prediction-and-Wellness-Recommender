from dotenv import load_dotenv
import os
import json
import io
import hashlib
import streamlit as st
from types import SimpleNamespace
from transformers import pipeline
from groq import Groq
from datetime import datetime, timedelta, timezone
import db
import auth_session
import todo_store
import wellbeing
from urllib.parse import quote as _urlquote

load_dotenv()

# Create the database table on first run (safe to call every time)
db.init_db()

# Setup emotion detection model - runs LOCALLY (free, no Hugging Face credits needed)
@st.cache_resource
def load_emotion_model():
    return pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None,
    )

emotion_model = load_emotion_model()


def classify_emotion(text):
    """Return a list of objects with .label and .score (same shape the old API returned)."""
    raw = emotion_model(text, truncation=True)
    if raw and isinstance(raw[0], list):
        raw = raw[0]
    return [SimpleNamespace(label=r["label"], score=r["score"]) for r in raw]

# Setup Groq client (personalized text generation)
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
)


# Recommendations dataset (fallback if Groq fails)
recommendations = {
    "joy": {
        "message": "You're feeling great! Keep the energy up! 🎉",
        "activities": ["Go for a walk", "Call a friend", "Dance freely"],
        "quote": "Happiness is not something ready-made. It comes from your own actions."
    },
    "sadness": {
        "message": "It's okay to feel sad. You're not alone 💙",
        "activities": ["Write in a journal", "Watch a comforting movie", "Take a warm shower"],
        "quote": "Every storm runs out of rain. Hang in there."
    },
    "anger": {
        "message": "Take a deep breath. You got this! 💪",
        "activities": ["Try deep breathing", "Go for a run", "Punch a pillow"],
        "quote": "For every minute you are angry, you lose 60 seconds of happiness."
    },
    "fear": {
        "message": "Courage is feeling fear and doing it anyway! 🌟",
        "activities": ["Talk to someone you trust", "Meditate for 5 minutes", "Write your fears down"],
        "quote": "You gain strength every time you face your fear."
    },
    "disgust": {
        "message": "Take a step back and refresh your mind 🌿",
        "activities": ["Go outside for fresh air", "Clean your space", "Cook something you love"],
        "quote": "A clean space creates a clean mind."
    },
    "surprise": {
        "message": "Life is full of surprises! Embrace it! 🎊",
        "activities": ["Try something new today", "Explore a new place", "Learn a new skill"],
        "quote": "Life is either a daring adventure or nothing at all."
    },
    "neutral": {
        "message": "A calm mind is a powerful mind 🧘",
        "activities": ["Read a book", "Take a nature walk", "Try meditation"],
        "quote": "In the middle of difficulty lies opportunity."
    },
}

# Dynamic YouTube search queries
search_queries = {
    "🇬🇧 English": {
        "joy":      "happy uplifting english songs playlist",
        "sadness":  "sad emotional english songs",
        "anger":    "calming relaxing english music",
        "surprise": "exciting adventure english songs",
        "neutral":  "peaceful calm english music",
    },
    "🇮🇳 Hindi": {
        "joy":      "happy bollywood hindi songs playlist",
        "sadness":  "sad hindi bollywood songs",
        "anger":    "calming peaceful hindi songs",
        "surprise": "fun exciting hindi songs",
        "neutral":  "peaceful hindi meditation music",
    },
    "🇮🇳 Odia": {
        "joy":      "happy odia songs playlist",
        "sadness":  "sad odia songs",
        "anger":    "calming odia devotional songs",
        "surprise": "fun odia dance songs",
        "neutral":  "peaceful odia classical music",
    },
    "🇮🇳 Telugu": {
        "joy":      "happy telugu songs playlist",
        "sadness":  "sad telugu songs",
        "anger":    "calming telugu devotional songs",
        "surprise": "fun exciting telugu songs",
        "neutral":  "peaceful telugu classical carnatic music",
    },
    "🇮🇳 Bengali": {
        "joy":      "happy bengali songs playlist",
        "sadness":  "sad bengali songs rabindra sangeet",
        "anger":    "calming bengali devotional songs",
        "surprise": "fun exciting bengali songs",
        "neutral":  "peaceful rabindra sangeet classical",
    },
    "🇮🇳 Tamil": {
        "joy":      "happy tamil songs playlist",
        "sadness":  "sad tamil songs",
        "anger":    "calming tamil devotional songs",
        "surprise": "fun exciting tamil songs",
        "neutral":  "peaceful tamil classical music",
    },
    "🇮🇳 Kannada": {
        "joy":      "happy kannada songs playlist",
        "sadness":  "sad kannada songs",
        "anger":    "calming kannada devotional songs",
        "surprise": "fun exciting kannada songs",
        "neutral":  "peaceful kannada classical music",
    },
    "🇮🇳 Punjabi": {
        "joy":      "happy punjabi songs playlist bhangra",
        "sadness":  "sad punjabi songs",
        "anger":    "calming peaceful punjabi songs",
        "surprise": "fun exciting punjabi bhangra songs",
        "neutral":  "peaceful punjabi sufi music",
    },
    "🇮🇳 Marathi": {
        "joy":      "happy marathi songs playlist",
        "sadness":  "sad marathi songs",
        "anger":    "calming marathi devotional songs",
        "surprise": "fun exciting marathi lavani songs",
        "neutral":  "peaceful marathi classical music",
    },
    "🇮🇳 Gujarati": {
        "joy":      "happy gujarati garba songs playlist",
        "sadness":  "sad gujarati songs",
        "anger":    "calming gujarati devotional songs",
        "surprise": "fun exciting gujarati garba songs",
        "neutral":  "peaceful gujarati classical music",
    },
     "🇮🇳 Rajasthani": {
        "joy":      "happy rajasthani folk songs playlist",
        "sadness":  "sad rajasthani songs",
        "anger":    "calming rajasthani devotional songs",
        "surprise": "fun exciting rajasthani folk dance songs",
        "neutral":  "peaceful rajasthani classical music",
    },
    "🇮🇳 Malayalam": {
        "joy":      "happy malayalam songs playlist",
        "sadness":  "sad malayalam songs",
        "anger":    "calming malayalam devotional songs",
        "surprise": "fun exciting malayalam songs",
        "neutral":  "peaceful malayalam classical music",
    },
    "🇮🇳 Assamese": {
        "joy":      "happy assamese bihu songs playlist",
        "sadness":  "sad assamese songs",
        "anger":    "calming assamese devotional songs",
        "surprise": "fun exciting assamese bihu songs",
        "neutral":  "peaceful assamese classical music",
    },
    "🇮🇳 Bhojpuri": {
        "joy":      "happy bhojpuri songs playlist",
        "sadness":  "sad bhojpuri songs",
        "anger":    "calming bhojpuri devotional songs",
        "surprise": "fun exciting bhojpuri dance songs",
        "neutral":  "peaceful bhojpuri folk music",
    },
    "🇮🇳 Haryanvi": {
        "joy":      "happy haryanvi songs playlist",
        "sadness":  "sad haryanvi songs",
        "anger":    "calming haryanvi devotional songs",
        "surprise": "fun exciting haryanvi dance songs",
        "neutral":  "peaceful haryanvi folk music",
    },
    "🇮🇳 Kashmiri": {
        "joy":      "happy kashmiri songs playlist",
        "sadness":  "sad kashmiri songs",
        "anger":    "calming kashmiri sufi songs",
        "surprise": "fun exciting kashmiri folk songs",
        "neutral":  "peaceful kashmiri sufi classical music",
    },
    "🇮🇳 Konkani": {
        "joy":      "happy konkani songs playlist",
        "sadness":  "sad konkani songs",
        "anger":    "calming konkani devotional songs",
        "surprise": "fun exciting konkani mandó songs",
        "neutral":  "peaceful konkani classical music",
    },
    "🇮🇳 Maithili": {
        "joy":      "happy maithili songs playlist",
        "sadness":  "sad maithili songs",
        "anger":    "calming maithili devotional songs",
        "surprise": "fun exciting maithili folk songs",
        "neutral":  "peaceful maithili classical music",
    },
     "🇮🇳 Gondi": {
        "joy":      "happy gondi tribal songs playlist",
        "sadness":  "sad gondi songs",
        "anger":    "calming gondi devotional songs",
        "surprise": "fun exciting gondi folk dance songs",
        "neutral":  "peaceful gondi tribal music",
    },
}

# Preview videos
preview_videos = {
            "🇬🇧 English": {
                "joy":     [{"title": "Happy - Pharrell Williams",       "id": "ZbZSe6N_BXs"},
                             {"title": "Can't Stop the Feeling - JT",    "id": "ru0K8uYEZWw"},
                             {"title": "Good as Hell - Lizzo",           "id": "SmbmeOgWsqE"}],
                "sadness": [{"title": "Fix You - Coldplay",              "id": "k4V3Mo61fJM"},
                             {"title": "Someone Like You - Adele",       "id": "hLQl3WQQoQ0"},
                             {"title": "Let Her Go - Passenger",         "id": "RBumgq5yVrA"}],
                "anger":   [{"title": "Weightless - Marconi Union",      "id": "UfcAVejslrU"},
                             {"title": "Let It Go - Idina Menzel",       "id": "L0MK7qz13bU"},
                             {"title": "Breathe - Télépopmusik",         "id": "vyut3GyQtn0"}],
                "surprise":[{"title": "Adventure of a Lifetime",         "id": "9jK-NcRmVtw"},
                             {"title": "On Top of the World",            "id": "SDTZ7iX4vTQ"},
                             {"title": "Wonderful Life - Hurts",         "id": "wKxEDNFMSaI"}],
                "neutral": [{"title": "Clair de Lune - Debussy",         "id": "UfcAVejslrU"},
                             {"title": "Weightless - Marconi Union",     "id": "hTWKbfoikeg"},
                             {"title": "Peaceful Piano Mix",             "id": "lCOF9LN_Zxs"}],
            },
            "🇮🇳 Hindi": {
                "joy":     [{"title": "Badtameez Dil - YJHD",            "id": "II2EO3Nw4m0"},
                             {"title": "Gallan Goodiyaan - Dil Dhadakne", "id": "jCEdTq3j-0U"},
                             {"title": "London Thumakda - Queen",         "id": "udra3Mfw2oo"}],
                "sadness": [{"title": "Channa Mereya - ADHM",             "id": "284Ov7ysmfA"},
                             {"title": "Tujhe Bhula Diya - Anjaana",      "id": "-Hb2DeHvvEg"},
                             {"title": "Kabira - YJHD",                   "id": "jHNNMj5bNQw"}],
                "anger":   [{"title": "Om Jai Jagdish Hare - Peaceful",   "id": "coU-0b6pxB8"},
                             {"title": "Mahamrityunjaya Mantra",           "id": "XlkIMG2h668"},
                             {"title": "Gayatri Mantra - Calm",            "id": "GEVvyIrQZnA"}],
                "surprise":[{"title": "Dil Dhadakne Do - Title",          "id": "56ZzM4mz4yY"},
                             {"title": "London Thumakda",                  "id": "udra3Mfw2oo"},
                             {"title": "Badtameez Dil",                    "id": "II2EO3Nw4m0"}],
                "neutral": [{"title": "Raag Yaman - Classical Sitar",     "id": "ed4SIvGjqNI"},
                             {"title": "Bansuri Flute Meditation",         "id": "tF4z5kntXAA"},
                             {"title": "Tabla Classical Music",            "id": "RDv4WgU-LAp-0"}],
        },
            "🇮🇳 Odia": {
                "joy":     [{"title": "Rangabati - Classic Odia",        "id": "9AITXSttuLk"},
                             {"title": "Toka Re Toka",                   "id": "pthzZ5vAxUE"},
                             {"title": "Suna Suna - Happy",              "id": "RDZM_5BZbtr2g"}],
                "sadness": [{"title": "Mo Mana Kande",                   "id": "4vgZlMFnayw"},
                             {"title": "Prema Diwana",                   "id": "NqC5_GP42wI"},
                             {"title": "E mona mo mona",                 "id": "rUB8IcQWEE8"}],
                "anger":   [{"title": "Shanti Odia Devotional",          "id": "RDIsA0xtnQf_A"},
                             {"title": "Calm Odia Music",                "id": "RD2OlFVOcaPL0"},
                             {"title": "Ahe Nila Saila",                "id": "jFdymKB8NmM"}],
                "surprise":[{"title": "Chiring Chiring",              "id": "BXzdhkI8E6w"},
                             {"title": "Lal Taha Taha",                "id": "RDZV-ENArlmsI"},
                             {"title": "Mahua Pani Saturi Tanka Aatheni ",     "id": "RDc3XOtUOdxlE"}],
                "neutral": [{"title": "Odissi Classical Music",          "id": "RDgjjrPr4EOlg"},
                             {"title": "Odia Flute Music",               "id": "RDDuZMesxOIIM"},
                             {"title": "Peaceful Odia Music",            "id": "RD9tzrb2bk4iI"}],
            },
            "🇮🇳 Telugu": {
                "joy":     [{"title": "Samajavaragamana",                "id": "RDOCg6BWlAXSw"},
                             {"title": "Dhimi Dhimi Nach",                "id": "4Vl-cSlYt1c"},
                             {"title": "Butta Bomma",                    "id": "YO7rue3nKX0"}],
                "sadness": [{"title": "Manasuna Manasai",                "id": "W34q8Qp7al4"},
                             {"title": "Kannulatho",                     "id": "ZEHwLad2Izo"},
                             {"title": "Priyathama",                     "id": "BpINyS4k7Uw"}],
                "anger":   [{"title": "Carnatic Calm Music",             "id": "LT1dErF6teA"},
                             {"title": "Telugu Devotional - Peace",      "id": "ZePfHmZ1fVQ"},
                             {"title": "Shanti Shanti",                  "id": "Yfwnw8-077I"}],
                "surprise":[{"title": "Dheeme Dheeme",                   "id": "75JsfrRP28M"},
                             {"title": "Telugu Dance Song",              "id": "YAscOYMTgTs"},
                             {"title": "Samajavaragamana",               "id": "OCg6BWlAXSw"}],
                "neutral": [{"title": "Carnatic Classical",              "id": "3QoDpiH8h1M"},
                             {"title": "Telugu Flute Music",             "id": "VdL8lEXCEmo"},
                             {"title": "Peaceful Veena Music",           "id": "KBYSpR8N6pc"}],
            },
            "🇮🇳 Tamil": {
                "joy":     [{"title": "Rowdy Baby - Maari",              "id": "yUoC5stm05o"},
                             {"title": "Kutti Story - Master",           "id": "nCNqPgXDYhY"},
                             {"title": "Vaathi Coming - Master",         "id": "fRD_3vJagxk"}],
                "sadness": [{"title": "Munbe Vaa - Sillunu Oru Kaadhal", "id": "rp3_FhRnIRw"},
                             {"title": "Ennodu Nee Irundhaal",           "id": "EhhiY11Z9-U"},
                             {"title": "Nenjukulle - Kadal",             "id": "XYZwp-WAg6I"}],
                "anger":   [{"title": "Tamil Devotional - Calm",         "id": "D-EtIYcNy6k"},
                             {"title": "Carnatic Music - Peace",         "id": "coxnUNGoRZ0"},
                             {"title": "Tamil Classical Music",          "id": "xdhY-uRL0Gw"}],
                "surprise":[{"title": "Rowdy Baby - Fun",                "id": "yUoC5stm05o"},
                             {"title": "Vaathi Coming",                  "id": "vxzfsBDx590"},
                             {"title": "Kutti Story",                    "id": "nCNqPgXDYhY"}],
                "neutral": [{"title": "Tamil Classical Carnatic",        "id": "PLLyY0VHQdvV8vGtngeR5lHaWjvH2gQtVD"},
                             {"title": "Tamil Flute Music",              "id": "XAL2Xf5ihzM"},
                             {"title": "Peaceful Tamil Music",           "id": "TKeU1bLlAcc"}],
            },
            "🇮🇳 Bengali": {
                "joy":     [{"title": "Amar Sonar Bangla",               "id": "k9JafGCIMKY"},
                             {"title": "Joy Joy Joy",                    "id": "RDznkwSQFtfiM"},
                             {"title": "Komola",                         "id": "5f1O74GwWJM"}],
                "sadness": [{"title": "Amar Shopno Re",                  "id": "bhiS-rVSPqM"},
                             {"title": "Tumi Robe Nirobe",               "id": "qZbdZEFsT3U"},
                             {"title": "Bengali Sad Song",               "id": "-gvT6gKpq50"}],
                "anger":   [{"title": "Ekla Cholo Re",                   "id": "-d9QOzkxMKU"},
                             {"title": "Rabindra Sangeet - Calm",        "id": "4iE_BHAEcDY"},
                             {"title": "Dekhechhi Rupshagore",           "id": "ReBHEyAd2zk"}],
                "surprise":[{"title": "Joy Joy Joy - Bengali",           "id": "RDznkwSQFtfiM"},
                             {"title": "Bengali Dance Song",             "id": "47BOJY1sheQ"},
                             {"title": "Amar Sonar Bangla",              "id": "k9JafGCIMKY"}],
                "neutral": [{"title": "Rabindra Sangeet",                "id": "4iE_BHAEcDY"},
                             {"title": "Bengali Flute Music",            "id": "6F85DwFqiYw"},
                             {"title": "Peaceful Bengali Music",         "id": "39uMLYTh40Q"}],
            },

            "🇮🇳 Kashmiri": {
                "joy":     [{"title": "Top kashmiri song",                "id": "u4jchTQ4EeA"},
                             {"title": "Jaan e Bahara",                   "id": "aF-lyYtoMAI"},
                             {"title": "Hukus Bukus",                     "id": "pA9UPOSh3Ws"}],
                "sadness": [{"title": "Sad Kashmiri Song",                "id": "A7Jx3JjCV0Y"},
                             {"title": "Lolan",                           "id": "yN-XvU3NyYk"},
                             {"title": "Zakham",                          "id": "UMrHPMVmtNQ"}],
                "anger":   [{"title": "Dilshad",                          "id": "rPOn6B6zcGU"},
                             {"title": "Peer Myanio",                     "id": "-HttjLOdpuM"},
                             {"title": "Nigaaro",                         "id": "GEVvyIrQZnA"}],
                "surprise":[{"title": "Hukus Bukus",                      "id": "pA9UPOSh3Ws"},
                             {"title": "Tarki",                           "id": "egQTEUUbzNU"},
                             {"title": "Bhumbro",                         "id": "FsC9gGQ37-4"}],
                "neutral": [{"title": "Dar Zubair",                       "id": "c8YDYjG40hM"},
                             {"title": "Khodaya",                         "id": "c_Rd7P0Sgrs"},
                             {"title": "Bahaar",                          "id": "ChubKc6V3oI"}],
            }, 
            "🇮🇳 Konkani": {
                "joy":     [{"title": "Rosalina",                         "id": "uHIl-n6ZY70"},
                             {"title": "2026 Konkani Song",               "id": "HqOqOgMfUYk"},
                             {"title": "Illo illo Soro Piyelo",           "id": "kgiA1ieStoI"}],
                "sadness": [{"title": "Mogachi Kanni",                    "id": "x6CtUlEVSdE"},
                             {"title": "Tu Maje Go Tu",                   "id": "H8Xri6GCJ6E"},
                             {"title": "Liz Mojea Moga",                  "id": "RW_tw8ijEnc"}],
                "anger":   [{"title": "Tujea Hatant",                     "id": "dDVYZ1W8gI8"},
                             {"title": "Somi Muzo Gouli",                 "id": "ZzsXB8_2UzQ"},
                             {"title": "Sodhun Ailyanv Balka Jezu",       "id": "rMM5kO9yHq4"}],
                "surprise":[{"title": "Konkani Comedy Song",              "id": "jEdSGnoVtV0"},
                             {"title": "Ringa Ringa",                     "id": "OMWpFvk7Q6s"},
                             {"title": "Bebdo",                           "id": "viZZNb8gzL0"}],
                "neutral": [{"title": "Tu Mojhem Sukh",                   "id": "mSNqGoKiaUk"},
                             {"title": "Meu Amor Usha Uthup",             "id": "nctk0fc3LGI"},
                             {"title": "Alfred Rose Konkani Song",        "id": "etf-iwEUvV4"}],
            }, 
            "🇮🇳 Maithili": {
                "joy":     [{"title": "Bekal Bhela Jiyara",               "id": "HivoGnne6mM"},
                             {"title": "pahunbaa raaghab",                "id": "YcGRgKuTY_M"},
                             {"title": "Sundar sajani",                   "id": "MejgYHWILCc"}],
                "sadness": [{"title": "Hay Re Vidhata",                   "id": "BhmaRDLO1fY"},
                             {"title": "Sannu Kumar Sad Song",            "id": "iJ_o9A-WfP8"},
                             {"title": "Kalank",                          "id": "Aq_uEqdLWhA"}],
                "anger":   [{"title": "Sri Ramchandra Krupalu",           "id": "Hi_gyY-mMQo"},
                             {"title": "Most Popular Raam Bhajan",        "id": "YmmWdT8ae5A"},
                             {"title": "Jagadamvea ahei ablab hamr",      "id": "qt2IhKrjHFQ"}],
                "surprise":[{"title": "Jat Jatin",                        "id": "V0myE1vpAXc"},
                             {"title": "Maithili Folk Song",              "id": "pgkXE8ES3Oc"},
                             {"title": "Godna 2.0",                       "id": "hmHLLu7c_rI"}],
                "neutral": [{"title": "Aaju Mithila Nagariya",            "id": "g7NlE2_XkmU"},
                             {"title": "Shankar Mahadevan & Maithili Thakur",  "id": "eXo08uMetgs"},
                             {"title": "Maithili Bhagabati Song",         "id": "TV6K47TY0h4"}],
            },
            "🇮🇳 Gondi": {
                "joy":     [{"title": "Oh Piki",                          "id": "4ggh-_n5TEo"},
                             {"title": "Onday Kunda Landa",               "id": "0SPnUk_FK4I"},
                             {"title": "Mosamtha Maja Gori",              "id": "qt0a7NhR5-Y"}],
                "sadness": [{"title": "Gondi Sad Song",                   "id": "Ovi-2tORGdY"},
                             {"title": "Simne Sikati Nelenje Indare",     "id": "udoE3O8C-JQ"},
                             {"title": "Dhoka Bari Siti",                 "id": "M32uiFq7RPs"}],
                "anger":   [{"title": "Dharvale Nandhithe Vara",          "id": "An1bMmISvqc"},
                             {"title": "Raythad Jangona Mahima",          "id": "__LBnlpRM7Q"},
                             {"title": " Manval Manthabaga",              "id": "7QdLZk0UKH8"}],
                "surprise":[{"title": "Vasundhara",                       "id": "cAG1Pdcux4k"},
                             {"title": "Koyata Dhemsa",                   "id": "hqEEBG1bh0Y"},
                             {"title": "Madmi Manda Hirvale",             "id": "CyeSecMlNAE"}],
                "neutral": [{"title": "Gondwana Tribal Song",             "id": "ZWIdTA8LEIE"},
                             {"title": "Jal",                             "id": "jWPIAyd79SY"},
                             {"title": "Lal Pungar",                      "id": "e70oEUMA1M8"}],
            }, 
            "🇮🇳 Kannada": {
                "joy":     [{"title": "Tajaa Samachara",                  "id": "oFUmyHA1hD4"},
                             {"title": "Party Freak",                     "id": "zJSP3I1lCco"},
                             {"title": "Dwapara",                         "id": "wiur_AGatGU"}],
                "sadness": [{"title": "Karmoda Saridu",                   "id": "hYOXLwqviR8"},
                             {"title": "Madana Mana Mohini",              "id": "Q9dKU_RhJGQ"},
                             {"title": "Bisilu Kudureyondu",              "id": "N4GFIkcp5Wo"}],
                "anger":   [{"title": "Ambareesha",                       "id": "Vrb1yfD_ch8"},
                             {"title": "Bhuvanam Sharanam",               "id": "NujNxgy4CpA"},
                             {"title": " O Yesuve",                       "id": "acn42qBskb8"}],
                "surprise":[{"title": "Golden Sparrow",                   "id": "1seR_ckLXz4"},
                             {"title": "Innunu Bekagide",                 "id": "fclPhO1FsOY"},
                             {"title": "Marali Manasaagide",              "id": "01uRBlLAjFg"}],
                "neutral": [{"title": "Kannada - 80's Soiree Medley",     "id": "m838qBVTe9c"},
                             {"title": "Healing Ragas",                   "id": "TXSb_OIMNQg"},
                             {"title": "Sonu Nigam Instructional",        "id": "jfNZ7IfjP-I"}],
            }, 
            "🇮🇳 Punjabi": {
                "joy":     [{"title": "Best of Bhangra",                  "id": "-oKAgd0gsHE"},
                             {"title": "Laung Laachi",                    "id": "YpkJO_GrCo0"},
                             {"title": "Gallan Goodiyaan",                "id": "jCEdTq3j-0U"}],
                "sadness": [{"title": "Haar Jaani Aa",                    "id": "zpAJbnzxht4"},
                             {"title": "Kade Ta Tu Avenga",               "id": "3X1tNeiz-jI"},
                             {"title": "Main Suneya",                     "id": "9i1dXa13CxA"}],
                "anger":   [{"title": "Distance Love",                    "id": "45PR60pF_6w"},
                             {"title": "Sufna Banke",                     "id": "YDuVz10Z7xU"},
                             {"title": "Pasoori",                         "id": "5Eqb_-j3FDA"}],
                "surprise":[{"title": "Punjabi Bhangra Nonstop Party",    "id": "pohiMw-rqHo"},
                             {"title": "Gidha",                           "id": "UTYnBUaGTcU"},
                             {"title": "Bhangra On Gasolina",             "id": "2pl4_vew1K8"}],
                "neutral": [{"title": "Rooh Da Sajna",                    "id": "_iflet928mg"},
                             {"title": "Rabba Tu Bata",                   "id": "kBkpVS7uLrA"},
                             {"title": "Punjabi Sufi Collection",         "id": "wiwiUtKCOcI"}],
            }, 
            "🇮🇳 Marathi": {
                "joy":     [{"title": "Chandramukhi",                     "id": "mHN9OaevBkg"},
                             {"title": "Gaav Sutana",                     "id": "0SPnUk_FK4I"},
                             {"title": "Shaky",                           "id": "sUf2PtEZris"}],
                "sadness": [{"title": "Saang Na",                         "id": "GfHbIgkeAIs"},
                             {"title": "Dur Dur",                         "id": "JuIfN8F037E"},
                             {"title": "Kaakan",                          "id": "9HNx1NIwdAc"}],
                "anger":   [{"title": "Nazar Kadh Deva",                  "id": "schSLWVM_gA"},
                             {"title": "Man Mandira",                     "id": "nXbQ-dItErg"},
                             {"title": " Rakhumai Rakhumai",              "id": "RVj23ZyTcMY"}],
                "surprise":[{"title": "Mala Pirtichya Jhulyat Jhulwa",    "id": "iYYYwTdPQXw"},
                             {"title": "Madanmanjiri",                    "id": "Sy15iBaba-U"},
                             {"title": "Ishakacha Baan",                  "id": "AOiF4GIVxLY"}],
                "neutral": [{"title": "Chand Tu Nabhatla",                "id": "ERWoyZ-rmHY"},
                             {"title": "Marathi Soft Songs",              "id": "aH-zZ7rIpTg"},
                             {"title": "Morning Flute Music",             "id": "tF4z5kntXAA"}],
            }, 
            "🇮🇳 Gujarati": {
                "joy":     [{"title": "Dhol Re Vagad",                    "id": "j5DtiXWRcHU"},
                             {"title": "Garbo",                           "id": "65o5Q_SmIww"},
                             {"title": "Garba Mashup 2025",               "id": "KC6JoB0NVjY"}],
                "sadness": [{"title": "Bewafa Sanam",                     "id": "9KYOcGDN8RY"},
                             {"title": "Yaad Tari Zindagi Thi Jati Nathi","id": "nq9QUgOKGRk"},
                             {"title": "Nanpan No Nedlo",                 "id": "5ymfRvZrKzo"}],
                "anger":   [{"title": "Prabhate",                         "id": "L2qZtt7fITk"},
                             {"title": "Naagar Nandji Na Laal",           "id": "iraezTzB938"},
                             {"title": " Pankh",                          "id": "QkjGWGjUWfs"}],
                "surprise":[{"title": "Dholida",                          "id": "rz1hAo3Hiy4"},
                             {"title": "Garba Fusion",                    "id": "OWag-Ep06pQ"},
                             {"title": "Zankaar",                         "id": "nL1v4x7rszs"}],
                "neutral": [{"title": "Gujarati Folk Fusion Song",        "id": "GSggK8v-8GI"},
                             {"title": "Dhun Laagi",                      "id": "TxidFkYHDfI"},
                             {"title": "Gujrati Instrumental Music",      "id": "xwEpQjW_eHI"}],
            }, 
            "🇮🇳 Rajasthani": {
                "joy":     [{"title": "Rail Gaadi",                       "id": "wMtSQKWS6V4"},
                             {"title": "Rajasthani Folk Song",            "id": "dDhw0Eq8zJg"},
                             {"title": "Banni",                           "id": "xiOG-kNFqps"}],
                "sadness": [{"title": "Supno",                            "id": "j-2Zb4QP49A"},
                             {"title": "Boli Pyari Lage",                 "id": "4TSxPTfsF6U"},
                             {"title": "Rajasthan Soulful Song",          "id": "pelvDKowyCw"}],
                "anger":   [{"title": "Rajasthani Traditional Song",      "id": "S4kaTxElgnE"},
                             {"title": "Vari Jau Re",                     "id": "An1bMmISvqc"},
                             {"title": " Rajasthani Folk Song",           "id": "bCfrXBBHoA4"}],
                "surprise":[{"title": "Nazar",                            "id": "f0-LSBqzzk4"},
                             {"title": "Ghoomar",                         "id": "cVeMyeTi4gE"},
                             {"title": "Rajasthani Dance",                "id": "xDPwxfhysEg"}],
                "neutral": [{"title": "Rajasthani Flok Relaxing Music",   "id": "j4yWeD_9-Eg"},
                             {"title": "Mumal",                           "id": "Ah1gS3ZtNrg"},
                             {"title": "Resonant Shoonyam",               "id": "bLg9iK3zOo0"}],
            }, 
            "🇮🇳 Malayalam": {
                "joy":     [{"title": "Minnalvala",                       "id": "izbydia9jz4"},
                             {"title": "Malare Manmiziyale",              "id": "PW44b0m-YKY"},
                             {"title": "Arikil Pathiye",                  "id": "VNg556FUOUs"}],
                "sadness": [{"title": "Parayathe Ariyathe",               "id": "T_yoPCXxaBk"},
                             {"title": "Neeyilla Neram",                  "id": "bY_LdUERXjQ"},
                             {"title": "Nanavekathe",                     "id": "qAKy1GVyzqU"}],
                "anger":   [{"title": "Temple Rhythms",                   "id": "eU1r_QOkX-I"},
                             {"title": "O Yesuve",                        "id": "acn42qBskb8"},
                             {"title": "Nee Enne Gaayakanaakki Mayilpeeli","id": "beGrGvLk_F4"}],
                "surprise":[{"title": "Jil Jil Jil",                      "id": "cAG1Pdcux4k"},
                             {"title": "Illuminati",                      "id": "tOM-nWPcR4U"},
                             {"title": "Onam Mood",                       "id": "GJZAcj4P99g"}],
                "neutral": [{"title": "Malayalam Relaxing Music",         "id": "ipJy_25xRrI"},
                             {"title": "Tharuni",                         "id": "fA4W6V8AoAw"},
                             {"title": "Mind Relaxing Malayalam Songs",   "id": "OEOjbUqntIE"}],
            }, 
            "🇮🇳 Assamese": {
                "joy":     [{"title": "Champadoi",                        "id": "e3eCBrq4-Mw"},
                             {"title": "Tumi Baru Janane",                "id": "P2f-ZLfI6Uc"},
                             {"title": "Dule Dule",                       "id": "P2f-ZLfI6Uc"}],
                "sadness": [{"title": "Zubeen Garg Sad Song",             "id": "Ec-KpTA_tfY"},
                             {"title": "Jape Dim Dishangot",              "id": "bqUjwfMKouw"},
                             {"title": "Oi Jaan",                         "id": "yWt4q9L8Tuw"}],
                "anger":   [{"title": "Shyamo Bonomali",                  "id": "yenAcxaWnqE"},
                             {"title": "Kanai Par Kora He",               "id": "p_zqs6jNgtc"},
                             {"title": "Aji Kailashot",                   "id": "bhG6UwYJKko"}],
                "surprise":[{"title": "Khaplang Khuplung",                "id": "giwZcDxIKPc"},
                             {"title": "Sonowal Kachari",                 "id": "GbEbEp4vPvA"},
                             {"title": "Nahor",                           "id": "KwzSN77dwQ4"}],
                "neutral": [{"title": "Xopun Xore",                       "id": "GSqra-d3YkY"},
                             {"title": "Dlganta Chetia",                  "id": "Q0MQcRjE5CI"},
                             {"title": "A Mind Freshing Classical Song",  "id": "eUxtU22vxNA"}],
            },
            "🇮🇳 Bhojpuri": {
                "joy":     [{"title": "tankha lutake Aata Hai",           "id": "Yf2kbvDjGJ5KONUb"},
                             {"title": "Sorry Sorry",                     "id": "lxqCinPZhVGHzgRH"},
                             {"title": "Palang Sagwan ke",                "id": "nnYjCtZb623DphRi"}],
                "sadness": [{"title": "Jab Sath Dewe Ke Na Rahe",         "id": "5MMYGjYC-mvV9rGg"},
                             {"title": " दिल लागे ना केहू अउर",             "id": "lI_5Ys22OAzNQeJR "},
                             {"title": "Gulari Ke Fhulwa",                "id": "BAUOXfwQFwc2AlsV"}],
                "anger":   [{"title": "गंगा जी नहईबो ए मईया",               "id": "VSNOPWucfI5Za8pI"},
                             {"title": "Math Pa Mahadev",                 "id": "ziXT1A4OrETNcWkX"},
                             {"title": "Le Jat Badu Devghar Jagle Jagle", "id": "t4icpcY4zHZy9qtE"}],
                "surprise":[{"title": "Ghutur Ghutur",                    "id": "fOaXiq3Et9bDbEPW"},
                             {"title": "Jayem Dehradun",                  "id": "ksmTEkNKOe8oLDwQ"},
                             {"title": "Shamiyana",                       "id": "fYr0MtG75KLnrih8"}],
                "neutral": [{"title": "Deshwa Ki Lajiya",                 "id": "AiCU0OW19guPFxRD"},
                             {"title": "Piya Nahi Biyogva",               "id": "FrFJ3OVnHj_5B-bj"},
                             {"title": "Pardesi Aail ",                   "id": "OsdkrS8eEzmZSqyq"}],
            },
            "🇮🇳 Haryanvi": {
                "joy":     [{"title": "Rao Sahab Drill",                  "id": "sq8KXF4SAmRZAGlJ"},
                             {"title": "Bullet Pe Gediyan",               "id": "hbrZO4Zh7bZ11umM"},
                             {"title": "Jat Jatni Khasa Aala Chahar",     "id": "_ILouSGq6zA3y-1-"}],
                "sadness": [{"title": "JAANI Gold E Gill",                "id": "OM9xsM4BL17Y-Ph6"},
                             {"title": " Without Me",                     "id": "JW9Z11DUaUSNmgh3"},
                             {"title": "Khamoshi ",                       "id": "cwoxJCvA_IDtnhY1"}],
                "anger":   [{"title": "Dharvale Nandhithe Vara",          "id": "An1bMmISvqc"},
                             {"title": "Raythad Jangona Mahima",          "id": "__LBnlpRM7Q"},
                             {"title": " Manval Manthabaga",              "id": "7QdLZk0UKH8"}],
                "surprise":[{"title": "Fortuner",                         "id": "WMFB4HAVaiQnn1GJ"},
                             {"title": " Jale 2",                         "id": "q3xgHTBStTFKwidX"},
                             {"title": "Yaari ",                          "id": "Ia3udHAqctO2YInC"}],
                "neutral": [{"title": "Kitse",                            "id": "mWEeSZ91AfoNMPP1"},
                             {"title": "Roots",                           "id": "sCQg7IPgCF0"},
                             {"title": "Pahadi Folk Song",                "id": "mxnsYbab08U"}],
            }, 
        }


# Groq model used for all text tasks. llama-3.3-70b-versatile was shut down by Groq on 16 Aug 2026,
# so we use the model Groq recommends instead. You can override it with GROQ_MODEL in your .env file.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def groq_chat(prompt, temperature=0.5, max_tokens=500):
    """Send one prompt to Groq and return the raw response."""
    extra = {"reasoning_effort": "low"} if "gpt-oss" in GROQ_MODEL else {}
    return groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        # gpt-oss "thinks" briefly before answering; that thinking also counts as tokens,
        # so we leave extra room so the real answer is never cut off.
        max_completion_tokens=max_tokens + 800,
        **extra,
    )


# ── Groq personalization helpers ────────────────────────────────────────────
def generate_personalized_recommendation(user_text, emotion, score, language="English", english_text=None):
    """
    Uses Groq to write a gentle, context-aware message, activities and quote
    based on what the user ACTUALLY said - in the SAME language they used.
    Falls back to the static `recommendations` dict if Groq fails.
    """
    english_line = f'\n(English meaning: "{english_text}")' if english_text and language.lower() != "english" else ""

    prompt = f"""You are a kind, gentle wellness companion. A user wrote/said this to express their feelings:
"{user_text}"{english_line}

Language of the user: {language}
Our emotion model detected the primary emotion as "{emotion}" (confidence: {score:.0%}).

Write a soft, caring, non-judgmental response based on the SPECIFIC things they said (not just the emotion label).
IMPORTANT: Write "message", "activities" and "quote" in {language}, using the same script the user used
(if they typed {language} in English letters, answer the same way). Keep activities simple, safe and doable today.
ACTIVITIES: make the FIRST one tiny (under 2 minutes, almost no effort) - especially if the person feels sad, afraid, tired or alone.
Match them to what the person actually said. When they feel low, prefer gentle things (drink water, open a window, stretch,
send one message to someone) over hard ones (running, big cleaning). Each "steps" list has 2-3 very short steps in {language}.
Set "needs_support" to true ONLY if the user talks about hurting themselves, not wanting to live, or being in serious danger. Otherwise false.

Respond ONLY with valid JSON in this exact format, no markdown, no preamble, no extra text:
{{
  "message": "1-2 warm sentences that acknowledge what they SPECIFICALLY said",
  "activities": ["short title of activity 1", "short title of activity 2", "short title of activity 3"],
  "activity_plan": [
    {{"title": "same as activity 1", "type": "breathe or move or write or connect or other", "minutes": 1,
      "steps": ["one tiny step", "another tiny step"], "write_prompt": "only if type is write, else empty"}},
    {{"title": "same as activity 2", "type": "...", "minutes": 2, "steps": ["...", "..."], "write_prompt": ""}},
    {{"title": "same as activity 3", "type": "...", "minutes": 2, "steps": ["...", "..."], "write_prompt": ""}}
  ],
  "quote": "A relevant, comforting quote (real or appropriately paraphrased)",
  "needs_support": false
}}"""

    try:
        response = groq_chat(prompt, temperature=0.7, max_tokens=1800)
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)

        # Basic validation so the UI never breaks even on a malformed response
        if not all(k in parsed for k in ("message", "activities", "quote")):
            raise ValueError("Missing expected keys in Groq response")
        if not isinstance(parsed["activities"], list) or len(parsed["activities"]) == 0:
            raise ValueError("Activities must be a non-empty list")
        parsed["needs_support"] = bool(parsed.get("needs_support", False))

        return parsed
    except Exception as e:
        st.warning(f"⚠️ Personalized recommendation unavailable right now — showing a general one instead. ({type(e).__name__}: {str(e)[:200]})")
        return recommendations.get(emotion, recommendations["neutral"])


def pick_best_video(user_text, emotion, videos_list):
    """
    Asks Groq to pick which curated video (from your existing static list)
    best matches the SPECIFIC nuance of what the user wrote.
    Groq only sees/returns titles (not IDs) so there's no risk of hallucinated IDs.
    Falls back to the original order if anything goes wrong.
    """
    titles = [v["title"] for v in videos_list]

    prompt = f"""A user wrote: "{user_text}"
Detected emotion: {emotion}

Here is a list of song titles:
{json.dumps(titles)}

Pick the ONE title from this exact list that best matches the specific feeling behind what the user wrote. Respond with ONLY the exact title text from the list, nothing else."""

    try:
        response = groq_chat(prompt, temperature=0.3, max_tokens=50)
        chosen_title = response.choices[0].message.content.strip().strip('"')

        for v in videos_list:
            if v["title"].strip().lower() == chosen_title.strip().lower():
                rest = [x for x in videos_list if x is not v]
                return [v] + rest
        return videos_list  # no match found, keep original order
    except Exception:
        return videos_list  # Groq failed, keep original order


def get_music_mood_keyword(user_text, emotion):
    """
    Asks Groq for a short mood descriptor based on the specific text,
    used to refine the YouTube search query beyond the generic emotion.
    Returns None on failure (caller should fall back to the static query).
    """
    prompt = f"""User wrote: "{user_text}"
Detected emotion: {emotion}

In 2-4 words, describe the specific musical mood that would help them (e.g. "gentle heartbreak comfort", "longing nostalgic", "energetic celebration"). Respond with ONLY those words, nothing else, no quotes, no punctuation."""
    try:
        response = groq_chat(prompt, temperature=0.7, max_tokens=20)
        keyword = response.choices[0].message.content.strip()
        return keyword if keyword else None
    except Exception:
        return None


# ── Voice + multi-language helpers ──────────────────────────────────────────
# "hindi" -> "🇮🇳 Hindi", "english" -> "🇬🇧 English" ... (used to auto-select the music language)
LANG_KEY_BY_NAME = {key.split(" ", 1)[1].lower(): key for key in search_queries}


def match_music_language(language_name):
    """Return the matching key of `search_queries` for a language name, or None."""
    if not language_name:
        return None
    return LANG_KEY_BY_NAME.get(language_name.strip().lower())


# Whisper (the voice-to-text model) was only trained on these Indian languages. It does
# NOT know Odia at all, so for Odia it silently guesses a language it does know (usually
# Hindi) - that is why voice came out wrong. Forcing one of THESE codes fixes mix-ups like
# Hindi being heard as Urdu, because Whisper really knows both - it just has to be told
# which one instead of guessing.
WHISPER_SUPPORTED_LANGUAGES = {
    "Hindi": "hi", "Urdu": "ur", "Bengali": "bn", "Tamil": "ta", "Telugu": "te",
    "Marathi": "mr", "Gujarati": "gu", "Punjabi": "pa", "Kannada": "kn",
    "Malayalam": "ml", "Nepali": "ne", "English": "en",
}
# Shown in the dropdown, but Whisper has no real support - we tell the person to type.
VOICE_LIMITED_LANGUAGES = {"Odia"}

ODIA_VOICE_NOTICE = (
    "🙏 **I can't understand Odia voice yet.** If you are comfortable in Odia, "
    "please **write it in the text box** below.  \n"
    "ମୁଁ ଏବେ ଓଡ଼ିଆ ସ୍ୱର ବୁଝିପାରୁନାହିଁ। ଯଦି ଆପଣ ଓଡ଼ିଆରେ ସହଜ, ଦୟାକରି ତଳେ ଥିବା ବକ୍ସରେ ଲେଖନ୍ତୁ।"
)
# Whisper often mistakes Odia speech for these. "assamese" is not in our dropdown at all, so when
# Whisper says it, the person was very likely speaking Odia - we do not trust the (wrong) text.
LIKELY_ODIA_MISHEARD = {"assamese"}
MAYBE_ODIA_MISHEARD = {"bengali", "nepali"}


def transcribe_audio(audio_bytes, language_code=None):
    """
    Turns the user's recorded voice into text with Groq Whisper.
    If `language_code` is given, Whisper is told which language to expect instead of
    guessing. Returns (text, language_name) - or ("", None) if something goes wrong.
    """
    try:
        kwargs = {"language": language_code} if language_code else {}
        result = groq_client.audio.transcriptions.create(
            file=("recording.wav", audio_bytes),
            model="whisper-large-v3",
            response_format="verbose_json",
            temperature=0.0,
            **kwargs,
        )
        text = (getattr(result, "text", "") or "").strip()
        language = getattr(result, "language", None)
        return text, language
    except Exception:
        return "", None


def translate_known_language(user_text, language_name):
    """
    Translate to English when we already KNOW the language (the person picked it),
    instead of asking Groq to guess it again from the text.
    """
    prompt = f"""This text is in {language_name}:
"{user_text}"

Translate it into natural English, keeping the emotion and tone exactly as the person felt it.
Respond with ONLY the English translation - no quotes, no labels, no extra text."""
    try:
        response = groq_chat(prompt, temperature=0.0, max_tokens=500)
        english = response.choices[0].message.content.strip()
        return english or user_text
    except Exception as e:
        st.warning(f"⚠️ I couldn't translate your words, so I'll read them as they are. ({type(e).__name__}: {str(e)[:200]})")
        return user_text


def understand_text(user_text):
    """
    The emotion model only understands English, so we first ask Groq to
    (1) detect the language and (2) translate the meaning into English.
    Works for Hindi, Odia, Bengali, Tamil ... and also 'Hinglish' typed in English letters.
    Returns {"language": "Hindi", "english": "..."}; falls back to the original text.
    """
    prompt = f"""A user wrote/said this (it may be in any Indian language, in English, or a mix such as Hinglish):
"{user_text}"

1. Detect the main language (use its English name, e.g. "Hindi", "Odia", "Bengali", "Tamil", "English").
2. Translate the meaning into natural English, keeping the emotion and tone exactly as the user felt it.

Respond ONLY with valid JSON, no markdown, no extra text:
{{"language": "Hindi", "english": "the English translation"}}"""
    try:
        response = groq_chat(prompt, temperature=0.0, max_tokens=500)
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        english = (parsed.get("english") or "").strip()
        language = (parsed.get("language") or "").strip()
        if not english:
            raise ValueError("empty translation")
        return {"language": language or "English", "english": english}
    except Exception as e:
        st.warning(f"⚠️ I couldn't translate your words, so I'll read them as they are. ({type(e).__name__}: {str(e)[:200]})")
        return {"language": "English", "english": user_text}


# ── Your companion character ─────────────────────────────────────────────────
# One little "friend" (emoji + colour + what it calls itself) per emotion.
COMPANION = {
    "joy":      {"emoji": "🥳", "color": "#FFD166", "does": "celebrate with you"},
    "sadness":  {"emoji": "🤗", "color": "#8EC6FF", "does": "sit with you"},
    "anger":    {"emoji": "😌", "color": "#B6E2A1", "does": "breathe with you"},
    "fear":     {"emoji": "🫂", "color": "#C9B6FF", "does": "stay close to you"},
    "surprise": {"emoji": "😮", "color": "#FFB6C1", "does": "figure it out with you"},
    "disgust":  {"emoji": "🙂", "color": "#B6E2A1", "does": "reset with you"},
    "neutral":  {"emoji": "🙂", "color": "#D8D8D8", "does": "hang out with you"},
}

# Best-effort language codes for the browser's built-in voice (availability depends on
# the user's device — if a language has no installed voice, the browser falls back to
# its default voice automatically).
TTS_LANG_CODES = {
    "english": "en-IN", "hindi": "hi-IN", "odia": "or-IN", "bengali": "bn-IN",
    "tamil": "ta-IN", "telugu": "te-IN", "kannada": "kn-IN", "malayalam": "ml-IN",
    "marathi": "mr-IN", "gujarati": "gu-IN", "punjabi": "pa-IN", "urdu": "ur-IN",
}


def render_companion(emotion, message, language="English", key="companion", height=200):
    """
    An animated little character that 'says' `message` in a speech bubble (typed out
    letter by letter) and can speak it out loud in the browser using the free, built-in
    Web Speech API — no extra API key or audio file needed.
    """
    look = COMPANION.get(emotion, COMPANION["neutral"])
    lang_code = TTS_LANG_CODES.get((language or "English").strip().lower(), "en-IN")
    safe_message = json.dumps(message or "")
    safe_lang = json.dumps(lang_code)

    st.iframe(f"""
    <style>
      body {{ margin: 0; font-family: 'Segoe UI', sans-serif; }}
      .wrap {{ display: flex; align-items: flex-start; gap: 14px; }}
      .avatar {{
        font-size: 54px; line-height: 1; flex-shrink: 0;
        animation: breathe 2.6s ease-in-out infinite;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));
      }}
      @keyframes breathe {{
        0%, 100% {{ transform: translateY(0) scale(1); }}
        50%      {{ transform: translateY(-6px) scale(1.05); }}
      }}
      .bubble {{
        position: relative; background: {look['color']}33; border: 2px solid {look['color']};
        border-radius: 18px; padding: 14px 18px; flex: 1; min-height: 40px;
        font-size: 16px; color: #222; line-height: 1.5;
      }}
      .bubble::before {{
        content: ""; position: absolute; left: -10px; top: 18px;
        border-width: 8px 10px 8px 0; border-style: solid;
        border-color: transparent {look['color']} transparent transparent;
      }}
      .speak-btn {{
        margin-top: 8px; border: none; border-radius: 20px; padding: 6px 14px;
        background: {look['color']}; cursor: pointer; font-size: 13px; color: #222;
      }}
      .speak-btn:hover {{ filter: brightness(0.95); }}
      .cursor {{ display: inline-block; width: 2px; background: #444; margin-left: 1px;
                 animation: blink 0.8s step-end infinite; }}
      @keyframes blink {{ 50% {{ opacity: 0; }} }}
    </style>
    <div class="wrap">
      <div class="avatar">{look['emoji']}</div>
      <div>
        <div class="bubble"><span id="msg-{key}"></span><span class="cursor">&nbsp;</span></div>
        <button class="speak-btn" onclick="speak_{key}()">🔊 Hear me say it</button>
      </div>
    </div>
    <script>
      const fullText_{key} = {safe_message};
      const el_{key} = document.getElementById("msg-{key}");
      let i_{key} = 0;
      (function type_{key}() {{
        if (i_{key} <= fullText_{key}.length) {{
          el_{key}.textContent = fullText_{key}.slice(0, i_{key});
          i_{key}++;
          setTimeout(type_{key}, 18);
        }}
      }})();
      function speak_{key}() {{
        try {{
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(fullText_{key});
          u.lang = {safe_lang};
          u.rate = 0.95;
          window.speechSynthesis.speak(u);
        }} catch (e) {{ /* speech isn't supported on this browser - the bubble text still shows */ }}
      }}
    </script>
    """, height=height, width="stretch")


# ── "Let's try something together": typed activities, breathing, feelings before/after ──
FEEL_FACES = {1: "😞", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}
TYPE_EMOJI = {"breathe": "🌬️", "move": "🚶", "write": "✍️", "connect": "💬", "other": "🌼"}
_ACTIVITY_TYPES = ("breathe", "move", "write", "connect", "other")
BREATHE_STEP = {"title": "Breathe with me", "type": "breathe", "minutes": 1,
                "steps": ["Sit or stand comfortably.", "Follow the circle: in for 4, hold for 4, out for 6."],
                "write_prompt": ""}


def _infer_activity_type(text):
    """Guess the type of a plain-text activity (used for older history and the backup list)."""
    t = (text or "").lower()
    if any(w in t for w in ("breath", "meditat", "relax")):
        return "breathe"
    if any(w in t for w in ("journal", "write", "gratitude", "diary")):
        return "write"
    if any(w in t for w in ("call ", "talk to", "friend", "family", "message", "reach out", "someone you trust")):
        return "connect"
    if any(w in t for w in ("walk", "run", "dance", "stretch", "exercise", "yoga", "outside", "fresh air",
                            "clean", "shower", "cook", "water", "punch", "explore", "nature")):
        return "move"
    return "other"


def _clean_plan_item(it):
    """Make one AI-written activity safe to show. Returns a dict, or None if unusable."""
    if not isinstance(it, dict):
        return None
    title = str(it.get("title") or "").strip()
    if not title:
        return None
    typ = str(it.get("type") or "").lower().strip()
    if typ not in _ACTIVITY_TYPES:
        typ = _infer_activity_type(title)
    try:
        minutes = max(1, min(5, int(it.get("minutes", 1))))
    except (TypeError, ValueError):
        minutes = 1
    raw_steps = it.get("steps") if isinstance(it.get("steps"), list) else []
    steps = [str(x).strip() for x in raw_steps if str(x).strip()][:3]
    wp = str(it.get("write_prompt") or "").strip()
    if typ == "write" and not wp:
        wp = "What is on your mind right now? Write a few lines."
    return {"title": title, "type": typ, "minutes": minutes, "steps": steps, "write_prompt": wp}


def build_activity_plan(activities, plan_raw=None):
    """Typed activity list. Uses the AI's detailed plan when we have it, otherwise builds one
    from the plain activity texts. A guided breathing step is always included."""
    plan = []
    if isinstance(plan_raw, list):
        plan = [x for x in (_clean_plan_item(i) for i in plan_raw) if x]
    if not plan:
        for a in activities or []:
            title = (a.get("title", "") if isinstance(a, dict) else str(a)).strip()
            if title:
                plan.append(_clean_plan_item({"title": title}))
    if plan and not any(x["type"] == "breathe" for x in plan):
        plan.insert(0, dict(BREATHE_STEP))
    return plan


def generate_extra_activity(context_text, emotion, language, existing_titles):
    """'Give me another idea' - one more small activity, different from the ones already shown."""
    prompt = f"""A user feels "{emotion}" and wrote this: "{context_text}"
Language of the user: {language}
Already suggested: {json.dumps(existing_titles, ensure_ascii=False)}

Suggest ONE different, very small, safe activity the person can do today. Write "title", "steps" and
"write_prompt" in {language}. "type" must be one of: breathe, move, write, connect, other.
Respond ONLY with valid JSON, no markdown:
{{"title": "...", "type": "other", "minutes": 2, "steps": ["tiny step 1", "tiny step 2"], "write_prompt": ""}}"""
    try:
        response = groq_chat(prompt, temperature=0.9, max_tokens=500)
        content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
        return _clean_plan_item(json.loads(content))
    except Exception:
        return None


def render_breathing(rounds=3, emoji="🙂"):
    """Guided breathing: a circle grows (in 4), holds (4) and shrinks (out 6)."""
    page = """
    <style>
      body { margin:0; font-family:'Segoe UI',sans-serif; text-align:center; }
      .wrap { height:230px; display:flex; flex-direction:column; align-items:center; justify-content:center; }
      .circle { width:90px; height:90px; border-radius:50%; display:flex; align-items:center; justify-content:center;
                font-size:34px; background:radial-gradient(circle at 35% 30%, #e6f2ff, #8EC6FF);
                box-shadow:0 6px 20px rgba(110,150,255,.35); transition:transform 4s ease-in-out; }
      .label { margin-top:26px; font-size:17px; color:#333; min-height:24px; }
      .count { font-size:14px; color:#777; min-height:20px; }
    </style>
    <div class="wrap"><div id="c" class="circle">__EMOJI__</div><div id="l" class="label">Get ready…</div><div id="n" class="count"></div></div>
    <script>
      const ROUNDS = __ROUNDS__;
      const phases = [["Breathe in…", 4, 1.7], ["Hold…", 4, 1.7], ["Breathe out…", 6, 1]];
      const sleep = ms => new Promise(r => setTimeout(r, ms));
      async function go() {
        const c = document.getElementById('c'), l = document.getElementById('l'), n = document.getElementById('n');
        await sleep(900);
        for (let r = 1; r <= ROUNDS; r++) {
          for (const [txt, secs, scale] of phases) {
            l.textContent = txt + '  (' + r + '/' + ROUNDS + ')';
            c.style.transition = 'transform ' + (txt.startsWith('Hold') ? 0.2 : secs) + 's ease-in-out';
            c.style.transform = 'scale(' + scale + ')';
            for (let s = secs; s >= 1; s--) { n.textContent = s; await sleep(1000); }
          }
        }
        l.textContent = 'Well done 🌿 Keep going if you like.'; n.textContent = '';
        c.style.transition = 'transform 1s'; c.style.transform = 'scale(1)';
      }
      go();
    </script>
    """.replace("__EMOJI__", emoji).replace("__ROUNDS__", str(rounds))
    st.iframe(page, height=270, width="stretch")


def render_activity_step(emoji, text, seconds, key):
    """A simple countdown ring with the character, for activities like a walk or a stretch."""
    import html as _html
    st.iframe(f"""
    <style>
      body {{ margin: 0; font-family: 'Segoe UI', sans-serif; }}
      .row {{ display: flex; align-items: center; gap: 16px; }}
      .ring {{ position: relative; width: 64px; height: 64px; flex-shrink: 0; }}
      .ring svg {{ transform: rotate(-90deg); width: 64px; height: 64px; }}
      .ring circle {{ fill: none; stroke-width: 6; }}
      .ring .bg {{ stroke: #eee; }}
      .ring .fg {{ stroke: #8EC6FF; stroke-linecap: round;
                   stroke-dasharray: 176; stroke-dashoffset: 176;
                   animation: countdown_{key} {seconds}s linear forwards; }}
      @keyframes countdown_{key} {{ to {{ stroke-dashoffset: 0; }} }}
      .ring .face {{ position: absolute; inset: 0; display: flex; align-items: center;
                     justify-content: center; font-size: 26px; animation: sway 2s ease-in-out infinite; }}
      @keyframes sway {{ 0%,100% {{ transform: rotate(-4deg); }} 50% {{ transform: rotate(4deg); }} }}
      .text {{ font-size: 15px; color: #222; }}
    </style>
    <div class="row">
      <div class="ring">
        <svg><circle class="bg" cx="32" cy="32" r="28"/><circle class="fg" cx="32" cy="32" r="28"/></svg>
        <div class="face">{emoji}</div>
      </div>
      <div class="text">{_html.escape(text)}</div>
    </div>
    """, height=90, width="stretch")


def _wk(prefix, name):
    return f"{prefix}_{name}"


def _wk_start(prefix, queue):
    ss = st.session_state
    ss[_wk(prefix, "before_val")] = ss.get(_wk(prefix, "before"), 3)      # how they felt BEFORE
    ss[_wk(prefix, "queue")] = queue
    ss[_wk(prefix, "pos")] = 0
    ss[_wk(prefix, "done_count")] = 0
    ss[_wk(prefix, "phase")] = "run"


def _wk_next(prefix, did_it, note_key=None, item=None):
    ss = st.session_state
    if did_it:
        ss[_wk(prefix, "done_count")] += 1
        if note_key and item:
            wellbeing.save_note(user["id"], item.get("write_prompt") or item["title"], ss.get(note_key, ""))
    ss[_wk(prefix, "pos")] += 1
    if ss[_wk(prefix, "pos")] >= len(ss[_wk(prefix, "queue")]):
        ss[_wk(prefix, "after")] = ss.get(_wk(prefix, "before_val"), 3)
        ss[_wk(prefix, "phase")] = "after"


def _wk_finish(prefix):
    ss = st.session_state
    after = ss.get(_wk(prefix, "after"), 3)
    ss[_wk(prefix, "after_val")] = after
    try:
        wellbeing.save_activity_result(user["id"], ss.get(_wk(prefix, "before_val"), 3), after,
                                       ss.get(_wk(prefix, "done_count"), 0))
    except Exception:
        pass
    ss[_wk(prefix, "phase")] = "done"


def _wk_again(prefix):
    st.session_state[_wk(prefix, "phase")] = "pick"
    st.session_state[_wk(prefix, "before")] = 3


def _render_add_idea_button(prefix, plan, emotion, context_text, language):
    if context_text and st.button("💡 Give me another idea", key=_wk(prefix, "idea_btn")):
        with st.spinner("Thinking of something small and kind..."):
            item = generate_extra_activity(context_text, emotion, language, [x["title"] for x in plan])
        if item:
            plan.append(item)
            st.session_state[_wk(prefix, "plan")] = plan
            st.rerun()
        else:
            st.warning("I couldn't think of a new one just now — please try again in a moment.")


def render_activity_walkthrough(activities, emotion, key_prefix, plan_raw=None, context_text="", language="English"):
    """
    Pick one activity (or do them all) -> each one is shown the right way for its type
    (breathing circle, timer, writing box, or messages to send) -> 'how do you feel now?'.
    """
    look = COMPANION.get(emotion, COMPANION["neutral"])
    ss = st.session_state
    if _wk(key_prefix, "plan") not in ss:
        ss[_wk(key_prefix, "plan")] = build_activity_plan(activities, plan_raw)
    plan = ss[_wk(key_prefix, "plan")]
    if not plan:
        return
    phase = ss.get(_wk(key_prefix, "phase"), "pick")

    # ── 1) choose ──
    if phase == "pick":
        st.caption("Which one feels doable right now? Pick one, or do them all with me.")
        ss.setdefault(_wk(key_prefix, "before"), 3)
        st.caption("First, how do you feel right now?")
        st.select_slider("Feeling now", options=[1, 2, 3, 4, 5], key=_wk(key_prefix, "before"),
                         label_visibility="collapsed", format_func=lambda m: FEEL_FACES[m])
        for i, item in enumerate(plan):
            st.button(f"{TYPE_EMOJI[item['type']]}  {item['title']}   ·  about {item['minutes']} min",
                      key=_wk(key_prefix, f"pick_{i}"), use_container_width=True,
                      on_click=_wk_start, args=(key_prefix, [i]))
        st.button(f"{look['emoji']} Let's do them all together", key=_wk(key_prefix, "all"), type="primary",
                  on_click=_wk_start, args=(key_prefix, list(range(len(plan)))))
        _render_add_idea_button(key_prefix, plan, emotion, context_text, language)
        return

    # ── 2) doing the activities ──
    if phase == "run":
        queue, pos = ss[_wk(key_prefix, "queue")], ss[_wk(key_prefix, "pos")]
        item = plan[queue[pos]]
        st.caption(f"Step {pos + 1} of {len(queue)} — {look['does']}")
        st.markdown(f"**{TYPE_EMOJI[item['type']]} {item['title']}**")

        note_key = None
        if item["type"] == "breathe":
            render_breathing(rounds=3, emoji=look["emoji"])
        elif item["type"] == "write":
            note_key = _wk(key_prefix, f"note_{pos}_{queue[pos]}")
            st.text_area(item["write_prompt"], key=note_key, height=110)
        elif item["type"] == "connect":
            st.caption("Pick a message, copy it, and send it to someone you trust:")
            for msg in wellbeing.reach_out_messages(language)[:3]:
                st.code(msg, language=None)
                st.markdown(f"[📱 Open in messages](sms:?&body={_urlquote(msg)})")
        elif item["type"] == "move":
            render_activity_step(look["emoji"], item["title"], seconds=min(item["minutes"] * 60, 120),
                                 key=_wk(key_prefix, f"t{pos}"))
        else:
            render_activity_step(look["emoji"], item["title"], seconds=30, key=_wk(key_prefix, f"t{pos}"))

        for tip in item["steps"]:
            st.markdown(f"- {tip}")

        col_next, col_skip = st.columns(2)
        col_next.button("Done, next ➜", key=_wk(key_prefix, f"next_{pos}"), use_container_width=True,
                        on_click=_wk_next, args=(key_prefix, True, note_key, item))
        col_skip.button("Skip this one", key=_wk(key_prefix, f"skip_{pos}"), use_container_width=True,
                        on_click=_wk_next, args=(key_prefix, False))
        return

    # ── 3) how do you feel now? ──
    if phase == "after":
        st.markdown("**How do you feel now?**")
        st.select_slider("Feeling after", options=[1, 2, 3, 4, 5], key=_wk(key_prefix, "after"),
                         label_visibility="collapsed", format_func=lambda m: FEEL_FACES[m])
        st.button("Show me", key=_wk(key_prefix, "finish"), type="primary", on_click=_wk_finish, args=(key_prefix,))
        return

    # ── 4) result + small reward ──
    before, after = ss.get(_wk(key_prefix, "before_val"), 3), ss.get(_wk(key_prefix, "after_val"), 3)
    done = ss.get(_wk(key_prefix, "done_count"), 0)
    if after > before:
        st.success(f"{FEEL_FACES[before]} ➜ {FEEL_FACES[after]}  You moved from {before} to {after}. "
                   "That is real progress, and you did it 💛")
    elif after == before:
        st.info(f"{FEEL_FACES[after]} You stayed steady — and that is okay. Small steps still count 🌱")
    else:
        st.warning(f"{FEEL_FACES[before]} ➜ {FEEL_FACES[after]}  I'm sorry it still feels heavy. You tried, and that matters. "
                   "Please think about reaching out to someone you trust today.")
        if after <= 2:
            show_help_box()
    if done:
        st.success(f"🌟 {'⭐' * min(done, 5)}  You did {done} with me — I'm proud of you 💛")
    stars = wellbeing.weekly_activity_count(user["id"])
    if stars:
        st.caption(f"⭐ {stars} activities done in the last 7 days")
    col_a, col_b = st.columns(2)
    col_a.button("Do it again", key=_wk(key_prefix, "again"), on_click=_wk_again, args=(key_prefix,),
                 use_container_width=True)
    with col_b:
        _render_add_idea_button(key_prefix, plan, emotion, context_text, language)


# ── Play with me: a small set of self-contained games ───────────────────────
GAMES = {
    "tictactoe": {"title": "Tic-Tac-Toe",        "emoji": "❌⭕", "desc": "Choose Low, Medium or High - can you beat me?"},
    "memory":    {"title": "Memory Match",        "emoji": "🧠",  "desc": "Find all the matching pairs."},
    "bubblepop": {"title": "Bubble Pop",          "emoji": "🫧",  "desc": "Pop as many as you can in 30 seconds - 3 levels."},
    "rps":       {"title": "Rock Paper Scissors", "emoji": "✊✋✌️", "desc": "First to win the match is the champion!"},
}


def open_games_hub():
    st.session_state.active_game = "hub"


def open_game(game_id):
    st.session_state.active_game = game_id


def close_games():
    st.session_state.active_game = None


def render_games_hub():
    render_companion("joy", "Let's play! Which game sounds fun right now?", key="games_companion", height=170)
    cols = st.columns(2)
    for i, (game_id, info) in enumerate(GAMES.items()):
        with cols[i % 2]:
            st.button(
                f"{info['emoji']} {info['title']}\n\n{info['desc']}",
                key=f"pick_{game_id}", on_click=open_game, args=(game_id,), use_container_width=True,
            )


def render_tictactoe():
    st.iframe("""
    <style>
      body { margin:0; font-family:'Segoe UI',sans-serif; text-align:center; }
      .level-btn { border:2px solid #C9B6FF; background:#fff; color:#6B4FBF; border-radius:16px;
                   padding:6px 16px; margin:0 4px; cursor:pointer; font-size:13px; }
      .level-btn.active { background:#C9B6FF; color:#fff; }
      #hint { font-size:13px; color:#777; margin-top:8px; min-height:18px; }
      #board { display:grid; grid-template-columns:repeat(3,80px); grid-gap:8px; justify-content:center; margin-top:10px; }
      .cell { width:80px; height:80px; background:#F4F1FF; border:2px solid #C9B6FF; border-radius:12px;
              font-size:34px; display:flex; align-items:center; justify-content:center; cursor:pointer; }
      .cell:hover { background:#EAE3FF; }
      #status { font-size:16px; margin-top:14px; min-height:22px; }
      #tally { font-size:13px; color:#666; margin-top:6px; min-height:18px; }
      #reset { margin-top:8px; border:none; border-radius:20px; padding:8px 18px; background:#C9B6FF; cursor:pointer; }
    </style>
    <div id="levels">
      <button class="level-btn" data-lvl="low" onclick="setLevel('low')">🟢 Low</button>
      <button class="level-btn" data-lvl="medium" onclick="setLevel('medium')">🟡 Medium</button>
      <button class="level-btn" data-lvl="high" onclick="setLevel('high')">🔴 High</button>
    </div>
    <div id="hint"></div>
    <div id="board"></div>
    <div id="status"></div>
    <div id="tally"></div>
    <button id="reset" onclick="reset()">Play again</button>
    <script>
      const HINTS = {
        low:    "Low: I play random moves - a gentle warm-up.",
        medium: "Medium: I win when I can and block you - can you outsmart me?",
        high:   "High: I play perfectly. A draw is a great result!"
      };
      const NAMES = { low: "Low", medium: "Medium", high: "High" };
      // Wins / losses / draws for THIS visit, kept separately for each level
      const tally = { low: {you:0, me:0, draw:0}, medium: {you:0, me:0, draw:0}, high: {you:0, me:0, draw:0} };
      const LINES = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
      const boardEl = document.getElementById("board");
      const statusEl = document.getElementById("status");
      const tallyEl = document.getElementById("tally");
      const hintEl = document.getElementById("hint");
      const YOUR_TURN = "Your turn - you're ❌";
      let level = "low", board, gameOver, thinking;

      function winner(b) {
        for (const [a,c,d] of LINES) if (b[a] && b[a]===b[c] && b[a]===b[d]) return b[a];
        return b.includes("") ? null : "draw";
      }
      function emptyCells(b) { return [0,1,2,3,4,5,6,7,8].filter(i => !b[i]); }
      function pick(list) { return list[Math.floor(Math.random() * list.length)]; }

      // LOW: any empty square
      function randomMove(b) { return pick(emptyCells(b)); }

      // MEDIUM: win if possible, else block you, else centre, else a corner, else anywhere
      function smartMove(b) {
        for (const mark of ["O","X"]) {
          for (const i of emptyCells(b)) { b[i]=mark; const w = winner(b); b[i]=""; if (w===mark) return i; }
        }
        if (!b[4]) return 4;
        const corners = [0,2,6,8].filter(i => !b[i]);
        if (corners.length) return pick(corners);
        return randomMove(b);
      }

      // HIGH: perfect play. It looks at every possible way the game could continue (minimax)
      // and picks a move that can never lose - the best you can get is a draw.
      function minimax(b, turn) {
        const w = winner(b);
        if (w === "O") return 1;
        if (w === "X") return -1;
        if (w === "draw") return 0;
        let best = turn === "O" ? -2 : 2;
        for (const i of emptyCells(b)) {
          b[i] = turn;
          const s = minimax(b, turn === "O" ? "X" : "O");
          b[i] = "";
          best = turn === "O" ? Math.max(best, s) : Math.min(best, s);
        }
        return best;
      }
      function perfectMove(b) {
        let bestScore = -2, moves = [];
        for (const i of emptyCells(b)) {
          b[i] = "O"; const s = minimax(b, "X"); b[i] = "";
          if (s > bestScore) { bestScore = s; moves = [i]; } else if (s === bestScore) moves.push(i);
        }
        return pick(moves);
      }
      function computerMove(b) {
        if (level === "low") return randomMove(b);
        if (level === "medium") return smartMove(b);
        return perfectMove(b);
      }

      function draw() {
        boardEl.innerHTML = "";
        board.forEach((v,i) => {
          const c = document.createElement("div"); c.className = "cell"; c.textContent = v;
          c.onclick = () => play(i); boardEl.appendChild(c);
        });
      }
      function showTally() {
        const t = tally[level];
        tallyEl.textContent = NAMES[level] + " level this visit - You: " + t.you + "  Me: " + t.me + "  Draws: " + t.draw;
      }
      function play(i) {
        if (gameOver || thinking || board[i]) return;
        board[i] = "X";
        let w = winner(board);
        draw();
        if (w) { finish(w); return; }
        thinking = true;
        statusEl.textContent = "My turn...";
        setTimeout(() => {
          board[computerMove(board)] = "O";
          thinking = false;
          w = winner(board);
          draw();
          if (w) finish(w); else statusEl.textContent = YOUR_TURN;
        }, 400);
      }
      function finish(w) {
        gameOver = true;
        const t = tally[level];
        if (w === "X") { t.you++; statusEl.textContent = "🎉 You won!"; }
        else if (w === "O") { t.me++; statusEl.textContent = "I got this one - good game!"; }
        else {
          t.draw++;
          statusEl.textContent = level === "high" ? "It's a draw - that's the best anyone can do against me!" : "It's a draw!";
        }
        showTally();
      }
      function reset() {
        board = Array(9).fill(""); gameOver = false; thinking = false;
        statusEl.textContent = YOUR_TURN; draw(); showTally();
      }
      function setLevel(l) {
        level = l;
        document.querySelectorAll(".level-btn").forEach(b => b.classList.toggle("active", b.dataset.lvl === l));
        hintEl.textContent = HINTS[l];
        reset();
      }
      setLevel("low");
    </script>
    """, height=560, width="stretch")


def render_memory_match():
    st.iframe("""
    <style>
      body { margin:0; font-family:'Segoe UI',sans-serif; text-align:center; overflow:hidden; }
      #levels { margin-top:4px; }
      .level-btn { border:2px solid #8EC6FF; background:#fff; color:#4A7FB5; border-radius:16px;
                   padding:6px 14px; margin:0 4px; cursor:pointer; font-size:13px; }
      .level-btn.active { background:#8EC6FF; color:#fff; }
      #grid { display:grid; grid-gap:8px; justify-content:center; margin:14px auto 0; }
      .card { border-radius:10px; background:#8EC6FF; display:flex; align-items:center;
              justify-content:center; cursor:pointer; transform-style:preserve-3d;
              transition:transform .25s; }
      .card.flipped, .card.matched { background:#EAF3FF; transform:rotateY(180deg) scale(1.06); }
      .card.matched { opacity:0.55; cursor:default; }
      .card.wrong { animation:shake .3s; }
      @keyframes shake { 25%{transform:translateX(-4px);} 75%{transform:translateX(4px);} }
      #hud { display:flex; justify-content:center; gap:18px; font-size:14px; margin-top:12px; color:#333; }
      #reset { margin-top:10px; border:none; border-radius:20px; padding:8px 18px; background:#8EC6FF;
               color:#fff; cursor:pointer; }
      #best { font-size:12px; color:#888; margin-top:4px; min-height:16px; }
      #confetti { position:fixed; inset:0; pointer-events:none; overflow:hidden; }
      .confetti-piece { position:absolute; top:-20px; font-size:22px;
                         animation:fall linear forwards; }
      @keyframes fall { to { transform:translateY(420px) rotate(360deg); opacity:0.3; } }
      #banner { font-size:17px; font-weight:600; margin-top:10px; min-height:24px; }
    </style>

    <div id="levels">
      <button class="level-btn" data-lvl="easy" onclick="setLevel('easy')">🟢 Easy · 6 pairs</button>
      <button class="level-btn" data-lvl="medium" onclick="setLevel('medium')">🟡 Medium · 8 pairs</button>
      <button class="level-btn" data-lvl="hard" onclick="setLevel('hard')">🔴 Hard · 12 pairs</button>
    </div>

    <div id="grid"></div>
    <div id="hud"><span id="moves">Moves: 0</span><span id="timer">Time: 0s</span></div>
    <div id="banner"></div>
    <button id="reset" onclick="setup()">🔄 Shuffle again</button>
    <div id="best"></div>
    <div id="confetti"></div>

    <script>
      const EMOJIS = ["🌸","🐚","🍀","⭐","🌙","🦋","🍄","🐝","🍉","🌺","🐢","🎈"];
      const LEVELS = {
        easy:   { pairs: 6,  cols: 4 },
        medium: { pairs: 8,  cols: 4 },
        hard:   { pairs: 12, cols: 6 },
      };
      // Best result reached THIS visit, per difficulty (starts fresh each time you open the page)
      const best = { easy: null, medium: null, hard: null };

      let level = "easy";
      let cards, flipped, matchedCount, moves, lock, startTime, timerId;
      const grid = document.getElementById("grid");
      const movesEl = document.getElementById("moves");
      const timerEl = document.getElementById("timer");
      const bannerEl = document.getElementById("banner");
      const bestEl = document.getElementById("best");

      // ── tiny sound effects, generated on the fly (no sound files needed) ──
      let audioCtx;
      function tone(freq, duration, type, delay) {
        try {
          audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
          const t0 = audioCtx.currentTime + (delay || 0);
          const osc = audioCtx.createOscillator(), gain = audioCtx.createGain();
          osc.type = type || "sine"; osc.frequency.setValueAtTime(freq, t0);
          gain.gain.setValueAtTime(0.001, t0);
          gain.gain.exponentialRampToValueAtTime(0.18, t0 + 0.01);
          gain.gain.exponentialRampToValueAtTime(0.001, t0 + duration);
          osc.connect(gain); gain.connect(audioCtx.destination);
          osc.start(t0); osc.stop(t0 + duration + 0.02);
        } catch (e) {}
      }
      const sfx = {
        flip:     () => tone(520, 0.08, "triangle"),
        match:    () => { tone(660, 0.12, "sine"); tone(880, 0.16, "sine", 0.08); },
        mismatch: () => tone(180, 0.18, "sawtooth"),
        win:      () => [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.22, "sine", i * 0.12)),
      };

      function confettiBurst() {
        const layer = document.getElementById("confetti");
        const bits = ["🎉","✨","🌟","💛","🎊"];
        for (let i = 0; i < 24; i++) {
          const s = document.createElement("span");
          s.className = "confetti-piece";
          s.textContent = bits[Math.floor(Math.random() * bits.length)];
          s.style.left = Math.random() * 100 + "%";
          s.style.animationDuration = (1.2 + Math.random()) + "s";
          layer.appendChild(s);
          setTimeout(() => s.remove(), 2400);
        }
      }

      function setLevel(l) {
        level = l;
        document.querySelectorAll(".level-btn").forEach(b => b.classList.toggle("active", b.dataset.lvl === l));
        setup();
      }

      function setup() {
        const cfg = LEVELS[level];
        grid.style.gridTemplateColumns = "repeat(" + cfg.cols + ", " + (level === "hard" ? 48 : 64) + "px)";
        const pool = EMOJIS.slice(0, cfg.pairs);
        const deck = [...pool, ...pool].sort(() => Math.random() - 0.5);
        cards = deck.map(e => ({ emoji: e, open: false, done: false, wrong: false }));
        flipped = []; matchedCount = 0; moves = 0; lock = false; startTime = null;
        clearInterval(timerId); timerId = null;
        movesEl.textContent = "Moves: 0"; timerEl.textContent = "Time: 0s"; bannerEl.textContent = "";
        renderBest();
        render();
      }

      function renderBest() {
        const b = best[level];
        bestEl.textContent = b ? ("Your best this visit: " + b.moves + " moves in " + b.time + "s") : "";
      }

      function render() {
        const cfg = LEVELS[level];
        grid.innerHTML = "";
        cards.forEach((c, i) => {
          const d = document.createElement("div");
          const size = level === "hard" ? 48 : 64;
          d.style.width = d.style.height = size + "px";
          d.style.fontSize = (size === 48 ? 22 : 28) + "px";
          d.className = "card" + (c.open || c.done ? " flipped" : "") + (c.done ? " matched" : "") + (c.wrong ? " wrong" : "");
          d.textContent = (c.open || c.done) ? c.emoji : "❓";
          d.onclick = () => flip(i);
          grid.appendChild(d);
        });
      }

      function tick() {
        timerEl.textContent = "Time: " + Math.floor((Date.now() - startTime) / 1000) + "s";
      }

      function flip(i) {
        if (lock || cards[i].open || cards[i].done) return;
        if (!startTime) { startTime = Date.now(); timerId = setInterval(tick, 500); }
        cards[i].open = true; flipped.push(i); sfx.flip(); render();
        if (flipped.length === 2) {
          moves++; movesEl.textContent = "Moves: " + moves; lock = true;
          const [a, b] = flipped;
          if (cards[a].emoji === cards[b].emoji) {
            sfx.match();
            cards[a].done = cards[b].done = true; matchedCount++;
            flipped = []; lock = false; render();
            if (matchedCount === LEVELS[level].pairs) finish();
          } else {
            sfx.mismatch();
            cards[a].wrong = cards[b].wrong = true; render();
            setTimeout(() => {
              cards[a].open = cards[b].open = false; cards[a].wrong = cards[b].wrong = false;
              flipped = []; lock = false; render();
            }, 700);
          }
        }
      }

      function finish() {
        clearInterval(timerId);
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        sfx.win(); confettiBurst();
        const prev = best[level];
        const isBest = !prev || moves < prev.moves || (moves === prev.moves && seconds < prev.time);
        if (isBest) best[level] = { moves: moves, time: seconds };
        bannerEl.textContent = "🎉 All matched in " + moves + " moves, " + seconds + "s!" + (isBest ? "  New best! 🌟" : "");
        renderBest();
      }

      setLevel("easy");
    </script>
    """, height=600, width="stretch")


def render_bubble_pop():
    st.iframe("""
    <style>
      body { margin:0; font-family:'Segoe UI',sans-serif; text-align:center; }
      .level-btn { border:2px solid #8EC6FF; background:#fff; color:#4A7FB5; border-radius:16px;
                   padding:6px 16px; margin:0 4px; cursor:pointer; font-size:13px; }
      .level-btn.active { background:#8EC6FF; color:#fff; }
      #hint { font-size:13px; color:#777; margin-top:8px; min-height:18px; }
      #wrap { position:relative; margin-top:8px; }
      #stage { position:relative; width:100%; height:340px; overflow:hidden; border-radius:14px;
                background:linear-gradient(180deg,#EAF6FF,#F7FBFF); }
      #overlay { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
                 font-size:17px; color:#4A7FB5; padding:20px; pointer-events:none; }
      .bubble { position:absolute; bottom:-90px; border-radius:50%; cursor:pointer;
                background:radial-gradient(circle at 30% 30%, #ffffffcc, #8EC6FF88);
                border:1px solid #ffffffaa; animation:rise linear forwards; }
      @keyframes rise { to { transform: translateY(-460px); } }
      #hud { display:flex; justify-content:center; gap:22px; font-size:15px; margin-top:8px; }
      #msg { font-size:15px; font-weight:600; margin-top:6px; min-height:22px; }
      #best { font-size:12px; color:#888; min-height:16px; }
      #start { margin-top:6px; border:none; border-radius:20px; padding:8px 20px; background:#8EC6FF; color:#fff; cursor:pointer; }
    </style>
    <div id="levels">
      <button class="level-btn" data-lvl="low" onclick="setLevel('low')">🟢 Low</button>
      <button class="level-btn" data-lvl="medium" onclick="setLevel('medium')">🟡 Medium</button>
      <button class="level-btn" data-lvl="high" onclick="setLevel('high')">🔴 High</button>
    </div>
    <div id="hint"></div>
    <div id="wrap"><div id="stage"></div><div id="overlay"></div></div>
    <div id="hud"><span id="score">Popped: 0</span><span id="time">⏱ 30s</span></div>
    <div id="msg"></div>
    <div id="best"></div>
    <button id="start" onclick="startRound()">▶ Start</button>
    <script>
      const ROUND_SECONDS = 30;
      // size = bubble size in pixels, rise = seconds a bubble takes to float up, every = ms between new bubbles
      const LEVELS = {
        low:    { size: [52, 80], rise: [6, 9],     every: 950, hint: "Low: big, slow bubbles - nice and easy." },
        medium: { size: [34, 62], rise: [4, 6.5],   every: 620, hint: "Medium: medium bubbles at a steady pace." },
        high:   { size: [22, 42], rise: [2.2, 3.8], every: 330, hint: "High: small, fast bubbles - quick fingers!" }
      };
      const NAMES = { low: "Low", medium: "Medium", high: "High" };
      const best = { low: null, medium: null, high: null };   // best score THIS visit, per level
      const stage = document.getElementById("stage"), overlay = document.getElementById("overlay");
      const scoreEl = document.getElementById("score"), timeEl = document.getElementById("time");
      const msgEl = document.getElementById("msg"), bestEl = document.getElementById("best");
      const hintEl = document.getElementById("hint"), startBtn = document.getElementById("start");
      let level = "low", score = 0, timeLeft = ROUND_SECONDS, playing = false, spawner = null, ticker = null;

      function rand(a, b) { return a + Math.random() * (b - a); }
      function renderHud() {
        scoreEl.textContent = "Popped: " + score;
        timeEl.textContent = "⏱ " + timeLeft + "s";
        bestEl.textContent = best[level] === null ? "" : "Best on " + NAMES[level] + " this visit: " + best[level];
      }
      function stopTimers() { clearInterval(spawner); clearInterval(ticker); spawner = null; ticker = null; }

      function spawnBubble() {
        const cfg = LEVELS[level];
        const b = document.createElement("div");
        const size = rand(cfg.size[0], cfg.size[1]);
        b.className = "bubble";
        b.style.width = size + "px"; b.style.height = size + "px";
        b.style.left = Math.random() * Math.max(1, stage.clientWidth - size) + "px";
        b.style.animationDuration = rand(cfg.rise[0], cfg.rise[1]) + "s";
        b.onclick = () => { if (!playing) return; score++; renderHud(); b.remove(); };
        b.addEventListener("animationend", () => b.remove());
        stage.appendChild(b);
      }

      function idle() {
        stopTimers(); playing = false; stage.innerHTML = ""; score = 0; timeLeft = ROUND_SECONDS;
        overlay.style.display = "flex"; overlay.textContent = "Pick a level, then press Start - you have 30 seconds!";
        msgEl.textContent = ""; startBtn.textContent = "▶ Start"; renderHud();
      }
      function setLevel(l) {
        level = l;
        document.querySelectorAll(".level-btn").forEach(b => b.classList.toggle("active", b.dataset.lvl === l));
        hintEl.textContent = LEVELS[l].hint;
        idle();
      }
      function startRound() {
        stopTimers(); stage.innerHTML = ""; score = 0; timeLeft = ROUND_SECONDS; playing = true;
        overlay.style.display = "none"; msgEl.textContent = ""; startBtn.textContent = "🔄 Restart"; renderHud();
        spawner = setInterval(spawnBubble, LEVELS[level].every);
        ticker = setInterval(() => { timeLeft--; renderHud(); if (timeLeft <= 0) endRound(); }, 1000);
      }
      function endRound() {
        stopTimers(); playing = false; stage.innerHTML = "";
        const isBest = best[level] === null || score > best[level];
        if (isBest) best[level] = score;
        overlay.style.display = "flex"; overlay.textContent = "⏰ Time's up!";
        msgEl.textContent = "You popped " + score + (score === 1 ? " bubble" : " bubbles") + (isBest && score > 0 ? " - a new best for this level! 🌟" : ".");
        startBtn.textContent = "▶ Play again"; renderHud();
      }
      setLevel("low");
    </script>
    """, height=620, width="stretch")


def render_rock_paper_scissors():
    st.iframe("""
    <style>
      body { margin:0; font-family:'Segoe UI',sans-serif; text-align:center; }
      .mode-btn { border:2px solid #FFB6C9; background:#fff; color:#C2547A; border-radius:16px;
                  padding:6px 14px; margin:0 4px; cursor:pointer; font-size:13px; }
      .mode-btn.active { background:#FFB6C9; color:#fff; }
      #scoreboard { font-size:26px; font-weight:700; margin-top:12px; }
      #roundinfo { font-size:13px; color:#777; margin-top:2px; min-height:18px; }
      .choice { font-size:34px; border:none; background:#FFE3EC; border-radius:16px; padding:14px 18px;
                margin:6px; cursor:pointer; }
      .choice:hover { background:#FFD1E0; }
      .choice:disabled { opacity:0.4; cursor:default; }
      #vs { font-size:40px; margin-top:8px; white-space:pre; min-height:50px; }
      #result { font-size:16px; margin-top:6px; min-height:22px; }
      #banner { font-size:20px; font-weight:800; margin-top:8px; min-height:30px; }
      #again { margin-top:8px; border:none; border-radius:20px; padding:8px 20px; background:#FFB6C9; color:#fff; cursor:pointer; }
      #record { font-size:12px; color:#888; margin-top:8px; }
    </style>
    <div id="modes">
      <span style="font-size:13px;color:#777">Match length:</span>
      <button class="mode-btn" data-n="3" onclick="setBestOf(3)">Best of 3</button>
      <button class="mode-btn" data-n="5" onclick="setBestOf(5)">Best of 5</button>
      <button class="mode-btn" data-n="7" onclick="setBestOf(7)">Best of 7</button>
    </div>
    <div id="scoreboard"></div>
    <div id="roundinfo"></div>
    <div>
      <button class="choice" onclick="play('✊')">✊</button>
      <button class="choice" onclick="play('✋')">✋</button>
      <button class="choice" onclick="play('✌️')">✌️</button>
    </div>
    <div id="vs"></div>
    <div id="result"></div>
    <div id="banner"></div>
    <button id="again" onclick="newMatch()">🔄 New match</button>
    <div id="record"></div>
    <script>
      const beats = { "✊": "✌️", "✋": "✊", "✌️": "✋" };
      const options = ["✊", "✋", "✌️"];
      const record = { you: 0, me: 0 };            // matches won THIS visit
      const scoreEl = document.getElementById("scoreboard"), infoEl = document.getElementById("roundinfo");
      const vsEl = document.getElementById("vs"), resultEl = document.getElementById("result");
      const bannerEl = document.getElementById("banner"), recordEl = document.getElementById("record");
      let bestOf = 5, you = 0, me = 0, round = 1, over = false;

      function target() { return Math.ceil(bestOf / 2); }     // wins needed to take the match
      function setChoicesDisabled(flag) { document.querySelectorAll(".choice").forEach(b => { b.disabled = flag; }); }
      function renderScore() {
        scoreEl.textContent = "🧑 You " + you + "  -  " + me + " Me 🤖";
        infoEl.textContent = over ? "Match finished" : "Round " + round + " - first to " + target() + " wins the match";
        recordEl.textContent = "Matches won this visit - You: " + record.you + "  Me: " + record.me;
      }
      function newMatch() {
        you = 0; me = 0; round = 1; over = false;
        vsEl.textContent = ""; resultEl.textContent = "Pick one to start!"; bannerEl.textContent = "";
        setChoicesDisabled(false); renderScore();
      }
      function setBestOf(n) {
        bestOf = n;
        document.querySelectorAll(".mode-btn").forEach(b => b.classList.toggle("active", Number(b.dataset.n) === n));
        newMatch();
      }
      function endMatch(winnerName) {
        over = true; setChoicesDisabled(true);
        if (winnerName === "you") {
          record.you++;
          bannerEl.textContent = "🏆 You are the winner! (" + you + " - " + me + ")";
        } else {
          record.me++;
          bannerEl.textContent = "🤖 I win the match! (" + me + " - " + you + ") Good game!";
        }
        renderScore();
      }
      function play(choice) {
        if (over) return;
        const mine = options[Math.floor(Math.random() * 3)];
        vsEl.textContent = choice + "    vs    " + mine;
        if (choice === mine) {
          resultEl.textContent = "It's a tie - let's play this round again!";
        } else if (beats[choice] === mine) {
          you++; resultEl.textContent = "🎉 You win round " + round + "!"; round++;
        } else {
          me++; resultEl.textContent = "I win round " + round + " - good try!"; round++;
        }
        renderScore();
        if (you >= target()) endMatch("you");
        else if (me >= target()) endMatch("me");
      }
      setBestOf(5);
    </script>
    """, height=470, width="stretch")


GAME_RENDERERS = {
    "tictactoe": render_tictactoe,
    "memory": render_memory_match,
    "bubblepop": render_bubble_pop,
    "rps": render_rock_paper_scissors,
}


def render_games_page():
    st.title("🎮 Play with me")
    col_back, _ = st.columns([1, 3])
    col_back.button("⬅ Back to chat", on_click=close_games)

    if st.session_state.active_game == "hub":
        render_games_hub()
    else:
        info = GAMES[st.session_state.active_game]
        st.subheader(f"{info['emoji']} {info['title']}")
        st.button("🎲 Choose a different game", on_click=open_games_hub)
        GAME_RENDERERS[st.session_state.active_game]()


# ── Session state init ──────────────────────────────────────────────────────
if "emotion_result" not in st.session_state:
    st.session_state.emotion_result = None
if "result_scores" not in st.session_state:
    st.session_state.result_scores = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "personalized_rec" not in st.session_state:
    st.session_state.personalized_rec = None
if "user_text" not in st.session_state:
    st.session_state.user_text = ""
if "mood_keyword" not in st.session_state:
    st.session_state.mood_keyword = None
if "reordered_videos" not in st.session_state:
    st.session_state.reordered_videos = {}
if "english_text" not in st.session_state:
    st.session_state.english_text = ""
if "detected_language" not in st.session_state:
    st.session_state.detected_language = "English"
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "selected_entry_id" not in st.session_state:
    st.session_state.selected_entry_id = None
if "active_game" not in st.session_state:
    st.session_state.active_game = None   # None = chat, "hub" = game menu, or a game's id
if "user" not in st.session_state:
    st.session_state.user = None          # None = nobody is logged in

# ── Login / sign-up page ─────────────────────────────────────────────────────
EMOTION_EMOJI = {
    "joy": "😊", "sadness": "😢", "anger": "😠", "fear": "😨",
    "surprise": "😲", "disgust": "🤢", "neutral": "😐",
}
IST = timezone(timedelta(hours=5, minutes=30))     # times are stored in UTC, shown in Indian time


def format_when(iso_time, short=False):
    try:
        moment = datetime.fromisoformat(iso_time).astimezone(IST)
    except Exception:
        return iso_time
    return moment.strftime("%d %b, %I:%M %p") if short else moment.strftime("%d %b %Y, %I:%M %p") + " IST"


# ── Look & feel: fonts, sizes and the top banner ─────────────────────────────
# Nunito for English + a Noto Sans font for each Indian script, so Hindi / Odia / Bengali ...
# text looks as clean as the English text. If the fonts can't be downloaded, the browser
# simply falls back to its normal fonts.
FONT_STACK = ("'Nunito', 'Noto Sans Devanagari', 'Noto Sans Oriya', 'Noto Sans Bengali', "
              "'Noto Sans Tamil', 'Noto Sans Telugu', 'Noto Sans Kannada', 'Noto Sans Malayalam', "
              "'Noto Sans Gujarati', 'Noto Sans Gurmukhi', 'Segoe UI', sans-serif")

TYPOGRAPHY_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;600&family=Noto+Sans+Oriya:wght@400;600&family=Noto+Sans+Bengali:wght@400;600&family=Noto+Sans+Tamil:wght@400;600&family=Noto+Sans+Telugu:wght@400;600&family=Noto+Sans+Kannada:wght@400;600&family=Noto+Sans+Malayalam:wght@400;600&family=Noto+Sans+Gujarati:wght@400;600&family=Noto+Sans+Gurmukhi:wght@400;600&display=swap');

html { font-size: 17px; }                       /* scales the whole UI a little */
.stApp { font-family: FONT_STACK; }
.stApp :is(p, li, label, input, textarea, button, h1, h2, h3, h4, h5, h6,
           [data-testid="stMarkdownContainer"], [data-baseweb="select"] div) {
    font-family: FONT_STACK !important;
}
.stApp p, .stApp li { line-height: 1.6; }

/* headings */
.stApp h2 { font-size: 1.45rem !important; font-weight: 800 !important; }
.stApp h3 { font-size: 1.3rem !important;  font-weight: 700 !important; }
[data-testid="stSidebar"] h2 { font-size: 1.25rem !important; }
[data-testid="stSidebar"] h3 { font-size: 1.05rem !important; }

/* small helper text */
[data-testid="stCaptionContainer"], .stApp small { font-size: 0.85rem !important; opacity: 0.75; }

/* labels above inputs */
.stApp label p { font-size: 0.95rem !important; font-weight: 600; }

/* inputs */
.stApp textarea, .stApp input { font-size: 1rem !important; }
.stApp [data-baseweb="select"] > div, .stApp textarea, .stApp [data-baseweb="input"] > div {
    border-radius: 12px !important;
}

/* Merged composer card: text box + microphone live inside ONE rounded box */
.stApp .st-key-composer {
    background: #ffffff;
    border: 1px solid #e3e1da;
    border-radius: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, .06);
    padding: 6px 10px 10px 10px;
    gap: 0 !important;
    transition: box-shadow .2s ease, border-color .2s ease;
}
.stApp .st-key-composer:hover { box-shadow: 0 4px 18px rgba(0, 0, 0, .09); }
.stApp .st-key-composer:focus-within { border-color: #b9b5a8; box-shadow: 0 4px 22px rgba(0, 0, 0, .10); }

/* text area: no box of its own */
.st-key-composer [data-testid="stTextArea"] [data-baseweb="textarea"],
.st-key-composer [data-testid="stTextArea"] [data-baseweb="base-input"] {
    background: transparent !important; border: none !important; box-shadow: none !important;
}
.st-key-composer [data-testid="stTextArea"] textarea {
    background: transparent !important; border: none !important; box-shadow: none !important;
    padding: 14px 14px 6px 14px !important; font-size: 1.05rem !important;
    line-height: 1.55 !important; color: #1f1e1d !important;
}
.st-key-composer [data-testid="stTextArea"] textarea::placeholder { color: #9a978d !important; }

/* microphone: a slim pill at the bottom of the card, no separate box */
.st-key-composer [data-testid="stAudioInput"] { max-width: 300px; }
.st-key-composer [data-testid="stAudioInput"] > div {
    background: #f4f3ee !important; border: none !important; box-shadow: none !important;
    border-radius: 999px !important; min-height: 2.6rem;
}
.st-key-composer [data-testid="stCaptionContainer"] { margin: 2px 0 0 14px; }

/* buttons */
.stApp .stButton button, .stApp [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stLinkButton"] a {
    border-radius: 12px; font-weight: 600; font-size: 0.92rem;
    transition: transform .08s ease, box-shadow .15s ease;
}
.stApp .stButton button:hover, .stApp [data-testid="stLinkButton"] a:hover {
    transform: translateY(-1px); box-shadow: 0 3px 10px rgba(60, 80, 200, .15);
}

/* sidebar: tidy, left-aligned buttons, history entries a bit smaller */
[data-testid="stSidebar"] .stButton button { justify-content: flex-start; text-align: left; }
[data-testid="stSidebar"] .stButton button p { font-size: 0.88rem !important; line-height: 1.35; }

/* emotion breakdown bars */
.stApp [data-testid="stProgress"] p { font-size: 0.9rem !important; }
/* welcome text under the banner (no fixed colours, so it works in light AND dark mode) */
.emo-intro { text-align: center; max-width: 46rem; margin: 0.4rem auto 0.8rem; }
.emo-hello { font-size: 1.3rem; font-weight: 700; line-height: 1.5; margin: 0 0 0.35rem; }
.emo-sub   { font-size: 0.92rem; opacity: 0.7; line-height: 1.5; margin: 0; }

/* main action buttons use the logo's purple -> blue gradient */
.stApp .st-key-analyze_btn button, .stApp [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #7c4dff 0%, #2f7bff 55%, #1fc8ff 100%);
    color: #ffffff; border: none; padding: 0.55rem 1.6rem; font-size: 1rem;
}
.stApp .st-key-analyze_btn button p, .stApp [data-testid="stFormSubmitButton"] button p { color: #ffffff !important; }
.stApp .st-key-analyze_btn button:hover, .stApp [data-testid="stFormSubmitButton"] button:hover {
    filter: brightness(1.08); color: #ffffff; border: none;
}

/* Deploy / menu sit on top of the banner, so give them a light pill to stay readable */
header[data-testid="stHeader"] [data-testid="stToolbar"] {
    background: rgba(255, 255, 255, 0.85); border-radius: 999px; padding: 0 0.6rem; margin: 0.4rem 0.6rem 0 0;
}
header[data-testid="stHeader"] [data-testid="stToolbar"] * { color: #1f2a44 !important; }
""".replace("FONT_STACK", FONT_STACK)


BANNER_FILES = ["banner.png", "banner.jpg", "banner.jpeg", "banner.webp", "logo.png"]
APP_DIR = os.path.dirname(os.path.abspath(__file__))


@st.cache_data(show_spinner=False)
def load_banner():
    """Find the banner image next to app.py, shrink it a little and return
    (base64 jpeg, background colour, is_wide). Returns None if no image is found."""
    import base64
    import io
    from PIL import Image

    for name in BANNER_FILES:
        path = os.path.join(APP_DIR, name)
        if not os.path.exists(path):
            continue
        img = Image.open(path).convert("RGB")
        if img.width > 1600:
            img = img.resize((1600, round(img.height * 1600 / img.width)))
        bg = "#%02x%02x%02x" % img.getpixel((2, 2))        # colour of the image corner
        wide = img.width / img.height >= 2                   # banner-shaped image?
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88, optimize=True)
        return base64.b64encode(buf.getvalue()).decode(), bg, wide
    return None


def render_logo(full_width=True):
    """Apply the fonts/sizes and show the banner at the top of the page.
    full_width=True  -> banner stretches across the whole page (chat, history, games)
    full_width=False -> banner is only as wide as the text column below it (login page)"""
    banner_css, banner_html = "", ""
    banner = load_banner()
    if banner is not None:
        data, bg, wide = banner
        if full_width:
            if wide:   # banner-shaped image: show it whole, full width (only very tall ones get trimmed)
                img_css = "height: auto; max-height: 380px; object-fit: cover;"
                box_css = ""
            else:      # square-ish logo: keep it uncropped inside a strip
                img_css = "height: 100%; object-fit: contain;"
                box_css = "height: clamp(150px, 26cqw, 300px);"
            banner_css = (
                '[data-testid="stMain"], section.main { container-type: inline-size; }'
                '.block-container, [data-testid="stMainBlockContainer"] { padding-top: 0 !important; }'
                'header[data-testid="stHeader"] { background: transparent !important; }'
                '.emo-banner { width: 100vw; width: 100cqw; margin-left: calc(50% - 50vw);'
                ' margin-left: calc(50% - 50cqw); background: ' + bg + ';'
                ' margin-bottom: 0.75rem; overflow: hidden; ' + box_css + ' }'
                '.emo-banner img { width: 100%; display: block; object-position: center; ' + img_css + ' }'
            )
        else:
            # same width as the text column (the "line length"), with soft rounded corners
            if wide:
                img_css = "height: auto; object-fit: cover;"
                box_css = ""
            else:
                img_css = "height: 100%; object-fit: contain;"
                box_css = "height: 220px;"
            banner_css = (
                '.block-container, [data-testid="stMainBlockContainer"] { padding-top: 3rem !important; }'
                '.emo-banner { width: 100%; background: ' + bg + '; border-radius: 16px;'
                ' margin: 0 0 1rem; overflow: hidden; ' + box_css + ' }'
                '.emo-banner img { width: 100%; display: block; object-position: center; ' + img_css + ' }'
            )
        banner_html = ('<div class="emo-banner"><img src="data:image/jpeg;base64,'
                       + data + '" alt="EmoTalk"></div>')
    # ONE st.markdown call: a separate call just for CSS would add an empty row above the banner
    st.markdown("<style>" + TYPOGRAPHY_CSS + banner_css + "</style>" + banner_html,
                unsafe_allow_html=True)


def show_auth_page():
    render_logo(full_width=False)
    st.write("Welcome 🌸 This is your calm, personal space. Please log in, or create an account, "
             "so your chats and history belong only to you.")

    login_tab, signup_tab = st.tabs(["🔑 Log in", "📝 Create account"])

    with login_tab:
        with st.form("login_form"):
            identifier = st.text_input("Email or phone number", key="login_id")
            password = st.text_input("Password", type="password", key="login_pw")
            submitted = st.form_submit_button("Log in")
        if submitted:
            found, error = db.authenticate(identifier, password)
            if error:
                st.error(error)
            else:
                start_login_session(found)
                st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("Your name", key="su_name")
            email = st.text_input("Email", key="su_email")
            phone = st.text_input("Phone number", key="su_phone")
            st.caption("Give at least one of email or phone number — you can use it to log in.")
            password = st.text_input("Password (at least 8 characters)", type="password", key="su_pw")
            confirm = st.text_input("Confirm password", type="password", key="su_pw2")
            submitted = st.form_submit_button("Create my account")
        if submitted:
            if password != confirm:
                st.error("The two passwords do not match.")
            else:
                created, error = db.create_user(name, email, phone, password)
                if error:
                    st.error(error)
                else:
                    start_login_session(created)
                    st.rerun()
        st.caption("🔒 Your password is saved in a scrambled (hashed) form, never as plain text, "
                   "and other people cannot see your history.")


# ── Stay logged in after a page refresh ──────────────────────────────────────
def _browser_token():
    """The login cookie the browser sent with this page load (None if there isn't one)."""
    try:
        return st.context.cookies.get(auth_session.COOKIE_NAME)
    except Exception:          # very old Streamlit without st.context
        return None


def start_login_session(person):
    """Log this person in, and ask the browser to remember them."""
    token = auth_session.create_session(person)
    st.session_state.user = person
    st.session_state.session_token = token
    st.session_state.cookie_action = ("set", token)


def _apply_cookie_action():
    """Write or delete the login cookie in the browser (runs a tiny invisible script)."""
    action = st.session_state.pop("cookie_action", None)
    if not action:
        return
    kind, token = action
    if kind == "set":
        cookie = f"{auth_session.COOKIE_NAME}={token}; max-age={auth_session.SESSION_DAYS * 86400}; path=/; SameSite=Lax"
    else:
        cookie = f"{auth_session.COOKIE_NAME}=; max-age=0; path=/; SameSite=Lax"
    script = f"<script>window.parent.document.cookie = {json.dumps(cookie)};</script>"
    if hasattr(st, "iframe"):
        st.iframe(script, height=1)
    else:                                   # older Streamlit
        import streamlit.components.v1 as components
        components.html(script, height=0)


if st.session_state.user is None:
    _saved_user = auth_session.get_user(_browser_token())
    if _saved_user and hasattr(db, "get_user"):       # make sure that account still exists (and is the same person)
        _fresh = db.get_user(_saved_user.get("id"))
        if not _fresh or _fresh.get("email") != _saved_user.get("email") or _fresh.get("phone") != _saved_user.get("phone"):
            auth_session.delete_session(_browser_token())
            _saved_user = None
        else:
            _saved_user = _fresh
    if _saved_user:                                   # refreshed page -> welcome them back
        st.session_state.user = _saved_user
        st.session_state.session_token = _browser_token()

_apply_cookie_action()

if st.session_state.user is None:
    show_auth_page()
    st.stop()          # nothing below this line is shown until someone is logged in

user = st.session_state.user


# ── History helpers (used by the sidebar buttons) ────────────────────────────
def select_history_entry(entry_id):
    st.session_state.selected_entry_id = entry_id


def close_history_entry():
    st.session_state.selected_entry_id = None


def delete_one_entry(entry_id):
    db.delete_entry(st.session_state.user["id"], entry_id)
    st.session_state.selected_entry_id = None


def delete_all_history():
    db.delete_history(st.session_state.user["id"])
    st.session_state.selected_entry_id = None


def logout():
    auth_session.delete_session(st.session_state.get("session_token") or _browser_token())
    st.session_state.clear()      # forget everything, including the previous person's results
    st.session_state.cookie_action = ("clear", "")


def show_history_entry(entry):
    """The page you see after clicking a history button in the sidebar."""
    emoji = EMOTION_EMOJI.get(entry["emotion"], "💭")
    st.subheader(f"{emoji} {entry['emotion'].upper()} — {entry['score']:.2%}")
    when = f"🕒 {format_when(entry['created_at'])}"
    if entry.get("language"):
        when += f"  ·  🌐 {entry['language']}"
    st.caption(when)

    st.markdown("**You said:**")
    st.write(entry["user_text"])
    if entry.get("english_text") and (entry.get("language") or "English").lower() != "english":
        st.caption(f"In English: “{entry['english_text']}”")

    if entry["message"]:
        render_companion(entry["emotion"], entry["message"], language=entry.get("language") or "English",
                          key=f"hist_companion_{entry['id']}")

    if entry["all_scores"]:
        st.subheader("📊 Emotion Breakdown:")
        for label, score in sorted(entry["all_scores"].items(), key=lambda kv: kv[1], reverse=True):
            st.progress(min(max(float(score), 0.0), 1.0), text=f"{label} — {score:.2%}")

    if entry["activities"]:
        st.subheader("🏃 Let's try something together:")
        render_activity_walkthrough(entry["activities"], entry["emotion"], key_prefix=f"hist_{entry['id']}",
                                    context_text=entry.get("user_text", ""), language=entry.get("language") or "English")

    if entry["quote"]:
        st.subheader("💬 Quote for you:")
        st.success(entry["quote"])

    col_back, col_delete = st.columns(2)
    col_back.button("⬅ Back to new chat", on_click=close_history_entry, use_container_width=True)
    col_delete.button("🗑️ Delete this entry", on_click=delete_one_entry, args=(entry["id"],),
                      use_container_width=True)


def render_history_sidebar():
    """History as buttons in the sidebar. Called at the END of the script so a brand-new
    analysis shows up in the list straight away."""
    with st.sidebar:
        st.divider()
        all_rows = db.get_history(user["id"], limit=200)
        render_mood_trend(all_rows)
        st.subheader("📜 Your history")
        history = all_rows[:30]
        if not history:
            st.caption("Your past chats will appear here 🌱")
        for row in history:
            emoji = EMOTION_EMOJI.get(row["emotion"], "💭")
            snippet = " ".join(row["user_text"].split())
            snippet = snippet[:18] + "…" if len(snippet) > 18 else snippet
            is_open = st.session_state.selected_entry_id == row["id"]
            st.button(
                f"{emoji} {format_when(row['created_at'], short=True)} · {snippet}",
                key=f"hist_{row['id']}",
                on_click=select_history_entry,
                args=(row["id"],),
                use_container_width=True,
                type="primary" if is_open else "secondary",
            )
        if history:
            with st.expander("🗑️ Delete all my history"):
                confirm = st.checkbox("Yes, delete everything permanently", key="confirm_delete_all")
                st.button("Delete all", disabled=not confirm, on_click=delete_all_history)


# ── To-do list (sidebar, under "Play with me") ───────────────────────────────
def _add_todo():
    todo_store.add_todo(user["id"], st.session_state.get("new_todo", ""))
    st.session_state.new_todo = ""


def _toggle_todo(todo_id):
    todo_store.set_done(user["id"], todo_id, st.session_state.get(f"todo_{todo_id}", False))


def _delete_todo(todo_id):
    todo_store.delete_todo(user["id"], todo_id)


def render_todo_sidebar():
    with st.expander("📝 My to-do list", expanded=True):
        st.text_input("New task", key="new_todo", placeholder="Add a small task… press Enter",
                      label_visibility="collapsed", on_change=_add_todo)
        todos = todo_store.list_todos(user["id"])
        if not todos:
            st.caption("Nothing here yet. Small steps count 🌱")
        for t in todos:
            c_task, c_del = st.columns([6, 1], vertical_alignment="center")
            c_task.checkbox(f"~~{t['text']}~~" if t["done"] else t["text"], value=bool(t["done"]),
                            key=f"todo_{t['id']}", on_change=_toggle_todo, args=(t["id"],))
            c_del.button("✕", key=f"todo_del_{t['id']}", on_click=_delete_todo, args=(t["id"],),
                         help="Delete this task")
        if todos:
            done = sum(1 for t in todos if t["done"])
            st.progress(done / len(todos), text=f"{done} of {len(todos)} done")
            if done:
                st.button("Clear completed", key="todo_clear_done", use_container_width=True,
                          on_click=todo_store.clear_done, args=(user["id"],))


# ── Care features: help box, daily check-in, week mood chart, reach-out ──────
def show_help_box():
    """Always-visible small help box in the sidebar."""
    st.info("💛 **Need to talk to someone?**  \n"
            "Call **[14416](tel:14416)** or **[1-800-891-4416](tel:18008914416)** — Tele-MANAS, "
            "free, 24×7, many languages.")


def show_crisis_help():
    """Shown on the result page when the words may mean the person is in danger."""
    st.error(
        "💛 **You matter, and you don't have to carry this alone.**  \n"
        "If you are thinking about hurting yourself or ending your life, please talk to someone **right now**:  \n"
        "📞 **[14416](tel:14416)** or **[1-800-891-4416](tel:18008914416)** — Tele-MANAS (free, 24×7, many languages)  \n"
        "🚑 If you are in immediate danger, call **[112](tel:112)**, or go to the nearest hospital.  \n"
        "Please also tell a person you trust — a family member or a friend — how you are feeling today."
    )


MOOD_FACES = {1: "😞", 2: "😕", 3: "😐", 4: "🙂", 5: "😊"}


def _save_checkin():
    wellbeing.save_checkin(user["id"], st.session_state.checkin_mood, st.session_state.checkin_good)
    st.session_state.checkin_saved = True


def render_checkin_sidebar():
    today = wellbeing.get_today(user["id"])
    if "checkin_mood" not in st.session_state:
        st.session_state.checkin_mood = today["mood"] if today else 3
    if "checkin_good" not in st.session_state:
        st.session_state.checkin_good = today["good_thing"] if today else ""
    with st.expander("🌙 Today's check-in", expanded=today is None):
        st.caption("How was today, overall?")
        st.select_slider("Mood", options=[1, 2, 3, 4, 5], key="checkin_mood", label_visibility="collapsed",
                         format_func=lambda m: MOOD_FACES[m])
        st.text_input("One good thing today", key="checkin_good", max_chars=300,
                      placeholder="One good thing today (even a small one) 🌼")
        st.button("Save check-in", key="checkin_save_btn", on_click=_save_checkin, use_container_width=True)
        if st.session_state.pop("checkin_saved", False):
            st.success("Saved 💛")
        n = wellbeing.streak(user["id"])
        if n >= 2:
            st.caption(f"🔥 {n} days in a row — well done for showing up for yourself.")
        stars = wellbeing.weekly_activity_count(user["id"])
        if stars:
            st.caption(f"⭐ {stars} activities done this week")
        goods = [c for c in wellbeing.recent_checkins(user["id"], days=30) if c["good_thing"]][:5]
        if goods:
            st.markdown("**✨ Your good things**")
            for c in goods:
                st.caption(f"{c['day'][5:]} · {c['good_thing']}")
        notes = wellbeing.recent_notes(user["id"], 3)
        if notes:
            st.markdown("**📝 Your notes**")
            for n_ in notes:
                st.caption(f"{n_['day'][5:]} · {n_['text'][:80]}")


def render_mood_trend(history):
    """Small weekly chart: one mood number (1-5) per day, from chats + check-ins."""
    import pandas as pd
    points = wellbeing.mood_by_day(
        history,
        wellbeing.recent_checkins(user["id"], days=8) + wellbeing.recent_activity_moods(user["id"], days=8),
        days=7)
    with st.expander("📈 My week", expanded=False):
        if all(v is None for _, v in points):
            st.caption("Chat or do a daily check-in and your week will show up here 🌱")
            return
        df = pd.DataFrame({"Mood": [v if v is not None else 0 for _, v in points]},
                          index=[d for d, _ in points])
        st.bar_chart(df, height=170)
        st.caption("1 = very low · 3 = okay · 5 = great  (a day with no chat or check-in shows 0)")
        vals = [v for _, v in points if v is not None]
        if len(vals) >= 2:
            first, last = sum(vals[: len(vals) // 2]) / (len(vals) // 2), sum(vals[len(vals) // 2:]) / (len(vals) - len(vals) // 2)
            if last - first >= 0.5:
                st.caption("🌱 Your recent days look a little brighter than earlier this week.")
            elif first - last >= 0.5:
                st.caption("💛 This week has been heavier lately. Be extra gentle with yourself — and consider reaching out to someone.")


def show_reach_out(language, key_prefix="reach"):
    """Ready-to-send messages for a friend or family member."""
    with st.expander("💬 Reach out to someone you trust", expanded=True):
        st.caption("Talking to a real person can help. Copy a message below, or tap the link to open it in your messages app.")
        for i, msg in enumerate(wellbeing.reach_out_messages(language)):
            st.code(msg, language=None)
            st.markdown(f"[📱 Open in messages](sms:?&body={_urlquote(msg)})")


# ── Sidebar (top part): who is logged in ─────────────────────────────────────
with st.sidebar:
    st.header(f"👤 {user['name']}")
    show_help_box()
    save_to_db = st.checkbox("Save my results to history", value=True, key="save_to_db")
    st.button("➕ New chat", on_click=close_history_entry, use_container_width=True)
    st.button("🎮 Play with me", on_click=open_games_hub, use_container_width=True)
    render_todo_sidebar()
    render_checkin_sidebar()
    st.button("🚪 Log out", on_click=logout, use_container_width=True)

# ── If "Play with me" was clicked, show the games page instead of everything else ─
if st.session_state.active_game is not None:
    render_games_page()
    render_history_sidebar()
    st.stop()

# ── If a history button was clicked, show that entry instead of the chat page ─
if st.session_state.selected_entry_id is not None:
    entry = db.get_entry(user["id"], st.session_state.selected_entry_id)   # only YOUR entries
    if entry is None:
        st.session_state.selected_entry_id = None
    else:
        render_logo()
        show_history_entry(entry)
        render_history_sidebar()
        st.stop()

# App UI
render_logo()
st.markdown(
    '<div class="emo-intro">'
    '<p class="emo-hello">Hi there 🌸 Take a deep breath. Tell me how you feel — I\'m here to listen, gently.</p>'
    '<p class="emo-sub">You can speak or write in English, Hindi, Odia, Bengali, Tamil, Telugu '
    'and many other Indian languages.</p>'
    '</div>',
    unsafe_allow_html=True,
)

if wellbeing.get_today(user["id"]) is None:
    st.caption("🌙 Haven't checked in today? Open **Today's check-in** in the sidebar — it takes 10 seconds.")

# 🌐 Which language? Auto-detect works for many people - pick one if it gets it wrong for you.
chosen_language = st.selectbox(
    "Which language are you using? (optional — pick it if detection seems wrong)",
    ["Auto-detect (recommended)"] + sorted(WHISPER_SUPPORTED_LANGUAGES) + sorted(VOICE_LIMITED_LANGUAGES),
    key="chosen_language",
)
if chosen_language in VOICE_LIMITED_LANGUAGES:
    st.info(ODIA_VOICE_NOTICE)

# Messages about the voice (listening..., errors) appear here, above the text box.
voice_status = st.container()

# ONE merged card (like a chat composer): text on top, microphone inside the bottom of the same box.
st.markdown("**Write it here, or speak (any language):**")
with st.container(key="composer"):
    col_text = st.container()
    col_mic = st.container()

# 🎙️ Voice input: record -> transcribe -> put the words in the text box (so you can still edit them).
# This code runs BEFORE the text box is drawn, so the words it hears can be placed inside the box.
with col_mic:
    audio = st.audio_input("🎙️ Or speak:", label_visibility="collapsed")
    st.caption("🎙️ Tap the mic, talk, then tap stop.")
if audio is not None:
    audio_bytes = audio.getvalue()
    audio_id = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_id != audio_id:      # only transcribe a new recording once
        force_code = WHISPER_SUPPORTED_LANGUAGES.get(chosen_language)   # None = let Whisper guess
        odia_voice = chosen_language in VOICE_LIMITED_LANGUAGES          # no voice engine for Odia -> ask to type
        voice_error = ""
        transcript, spoken_language = "", None
        if odia_voice:
            voice_error = ODIA_VOICE_NOTICE
        else:
            with voice_status:
                with st.spinner("Listening carefully..."):
                    transcript, spoken_language = transcribe_audio(audio_bytes, language_code=force_code)
        st.session_state.last_audio_id = audio_id
        heard = (spoken_language or "").lower()
        if transcript and not force_code and heard in LIKELY_ODIA_MISHEARD:
            transcript, voice_error = "", ODIA_VOICE_NOTICE          # probably Odia: don't fill the box with wrong words
        elif transcript and not force_code and heard in MAYBE_ODIA_MISHEARD:
            voice_status.info("If you were speaking **Odia**, these words may be wrong — I can't understand Odia voice. "
                              "Please write it in the text box instead.")
        if transcript:
            st.session_state.user_input = transcript
            st.toast(f"I heard you 💛 ({chosen_language if (force_code or odia_voice) else (spoken_language or 'language detected')})")
        else:
            if voice_error == ODIA_VOICE_NOTICE:
                voice_status.info(voice_error)
            else:
                voice_status.warning(voice_error or "I couldn't hear that clearly. Could you try again, or type it in the box?")

# ✍️ Text input (also shows the transcript of your voice, so you can fix any word)
with col_text:
    text = st.text_area(
        "Write it here (any language):",
        label_visibility="collapsed",
        key="user_input",
        height=120,
        placeholder="I am feeling really down today... / मुझे आज बहुत उदास लग रहा है... / ମୋତେ ଆଜି ବହୁତ ଦୁଃଖ ଲାଗୁଛି..."
    )

# ── Analyze button ───────────────────────────────────────────────────────────
if st.button("Analyze & Recommend", key="analyze_btn"):
    if text.strip() == "":
        st.warning("Please write or say something first 🌱")
    else:
        # 1) Which language is it, and what does it mean in English?
        with st.spinner("Understanding your words..."):
            if chosen_language != "Auto-detect (recommended)":
                # We already know the language - translate directly instead of re-guessing it
                # from the text (that re-guessing caused the Hindi -> Urdu mix-ups).
                detected_language = chosen_language
                english_text = translate_known_language(text, chosen_language)
            else:
                understood = understand_text(text)
                english_text = understood["english"]
                detected_language = understood["language"]

        # Safety net: look for words that may mean the person is in danger (any language / its translation)
        st.session_state.crisis_flag = wellbeing.crisis_check(text, english_text)

        # 2) Detect the emotion (the model reads the English meaning)
        with st.spinner("Feeling what you feel..."):
            result = classify_emotion(english_text)
        st.session_state.emotion_result = max(result, key=lambda x: x.score)
        st.session_state.result_scores = result
        st.session_state.user_text = text
        st.session_state.english_text = english_text
        st.session_state.detected_language = detected_language

        emotion_label = st.session_state.emotion_result.label.lower()

        # 3) Dynamic, gentle recommendation - written in the user's own language
        with st.spinner("Preparing something gentle for you..."):
            st.session_state.personalized_rec = generate_personalized_recommendation(
                text, emotion_label, st.session_state.emotion_result.score,
                language=detected_language, english_text=english_text,
            )
            st.session_state.mood_keyword = get_music_mood_keyword(english_text, emotion_label)

        # Songs are picked lazily (only for the language you choose) - see below
        st.session_state.reordered_videos = {}
        for _k in [k for k in st.session_state if k.startswith("live_")]:   # start the activities fresh each time
            del st.session_state[_k]

        # Songs: start with the language the user used (if we have songs for it)
        matched = match_music_language(detected_language)
        if matched:
            st.session_state["music_language"] = matched
            st.session_state.matched_music_language = matched

        # 4) Save to the database
        if save_to_db:
            try:
                db.save_analysis(
                    user_id=user["id"],
                    user_name=user["name"],
                    user_text=text,
                    emotion=emotion_label,
                    score=st.session_state.emotion_result.score,
                    all_scores={item.label: item.score for item in result},
                    recommendation=st.session_state.personalized_rec,
                    mood_keyword=st.session_state.mood_keyword,
                    language=detected_language,
                    english_text=english_text,
                )
                st.toast("Saved to your history ✅")
            except Exception as e:
                st.warning(f"Couldn't save to the database: {e}")

# Get top emotion
if st.session_state.emotion_result is not None:
    top_emotion = st.session_state.emotion_result
    result      = st.session_state.result_scores

    emotion = top_emotion.label.lower()
    rec     = st.session_state.personalized_rec or recommendations.get(emotion, recommendations["neutral"])

    # Show emotion
    st.subheader(f"Detected Emotion: {emotion.upper()} — {top_emotion.score:.2%}")
    if st.session_state.detected_language.lower() != "english":
        st.caption(f"🌐 Language: {st.session_state.detected_language} · I understood: “{st.session_state.english_text}”")

    # Your companion says the message, in your language, with a voice
    render_companion(emotion, rec["message"], language=st.session_state.detected_language, key="live_companion")

    if rec.get("needs_support") or st.session_state.get("crisis_flag"):
        show_crisis_help()

    if (emotion in ("sadness", "fear", "anger") or st.session_state.get("crisis_flag")
            or wellbeing.feels_lonely(st.session_state.user_text, st.session_state.english_text)):
        show_reach_out(st.session_state.detected_language)

    # Emotion breakdown
    st.subheader("📊 Emotion Breakdown:")
    for item in result:
        st.progress(item.score, text=f"{item.label} — {item.score:.2%}")

    # Activities — your companion does them together with you, one at a time
    st.subheader("🏃 Let's try something together:")
    render_activity_walkthrough(rec["activities"], emotion, key_prefix="live", plan_raw=rec.get("activity_plan"),
                                context_text=st.session_state.user_text,
                                language=st.session_state.detected_language)

    # Quote
    st.subheader("💬 Quote for you:")
    st.success(rec["quote"])

# Language selector
    st.divider()
    if "music_language" not in st.session_state and st.session_state.get("matched_music_language"):
        st.session_state["music_language"] = st.session_state["matched_music_language"]
    language = st.selectbox(
        "🌍 Select your preferred language for music:",
        list(search_queries.keys()),
        key="music_language",
    )

 # YouTube section
    st.subheader(f"🎵 Recommended {language} Videos for you:")
    base_query = search_queries[language].get(emotion, search_queries[language]["neutral"])
    mood_keyword = st.session_state.mood_keyword
    query = f"{mood_keyword} {base_query}" if mood_keyword else base_query
    youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"


        # Show 3 preview videos if available
    if language in preview_videos:
            if language not in st.session_state.reordered_videos:
                base_videos = preview_videos[language].get(emotion, preview_videos[language]["neutral"])
                with st.spinner("Choosing songs that match your mood..."):
                    st.session_state.reordered_videos[language] = pick_best_video(
                        st.session_state.english_text or st.session_state.user_text,
                        emotion, base_videos,
                    )
            videos = st.session_state.reordered_videos[language]
            for video in videos:
                col1, col2 = st.columns([1, 2])
                with col1:
                    thumbnail = f"https://img.youtube.com/vi/{video['id']}/mqdefault.jpg"
                    st.image(thumbnail)
                with col2:
                    st.write(f"🎵 **{video['title']}**")
                    url = f"https://www.youtube.com/watch?v={video['id']}"
                    st.link_button("▶ Watch on YouTube", url)
                st.divider()
    else:
            st.info(f"🔍 Searching: **{query}**")

        # More videos button
    st.markdown("🔎 Want more videos?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("🎵 More Songs", youtube_url)
        with col2:
            playlist_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+playlist"
            st.link_button("📋 Playlists", playlist_url)
        with col3:
            mix_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+mix"
            st.link_button("🎧 Mix", mix_url)


# ── History buttons in the sidebar ───────────────────────────────────────────
render_history_sidebar()
