from dotenv import load_dotenv
import os
import streamlit as st
from huggingface_hub import InferenceClient

load_dotenv()

# Setup client
client = InferenceClient(
    provider="auto",
    api_key=os.getenv("HF_TOKEN"),
)

# Recommendations dataset
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



# ── Session state init ──────────────────────────────────────────────────────
if "emotion_result" not in st.session_state:
    st.session_state.emotion_result = None
if "result_scores" not in st.session_state:
    st.session_state.result_scores = None
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

# App UI
st.title("🎭 Emotion Detector & Wellness Recommender")
st.write("Tell me how you feel and I'll help you feel better!")

# Text input
text = st.text_area(
    "Express yourself here:",
    placeholder="I am feeling really down today..."
)

# ── Session state init ──────────────────────────────────────────────────────
if st.button("Analyze & Recommend"):
    if text.strip() == "":
        st.warning("Please enter some text!")
    else:
        with st.spinner("Analyzing your emotions..."):
            result = client.text_classification(
                text,
                model="j-hartmann/emotion-english-distilroberta-base",
            )
        st.session_state.emotion_result = max(result, key=lambda x: x.score)
        st.session_state.result_scores = result

        # Get top emotion
if st.session_state.emotion_result is not None:
    top_emotion = st.session_state.emotion_result
    result      = st.session_state.result_scores

    emotion = top_emotion.label.lower()
    rec     = recommendations.get(emotion, recommendations["neutral"])

    # Show emotion
    st.subheader(f"Detected Emotion: {emotion.upper()} — {top_emotion.score:.2%}")
    st.info(rec["message"])

    # Emotion breakdown
    st.subheader("📊 Emotion Breakdown:")
    for item in result:
        st.progress(item.score, text=f"{item.label} — {item.score:.2%}")

        # Activities
    st.subheader("🏃 Activities to try:")
    for activity in rec["activities"]:
        st.write(f"• {activity}")

    # Quote
    st.subheader("💬 Quote for you:")
    st.success(rec["quote"])

# Language selector
    st.divider()
    language = st.selectbox(
             "🌍 Select your preferred language for music:",
            list(search_queries.keys())
        )

 # YouTube section
    st.subheader(f"🎵 Recommended {language} Videos for you:")
    query = search_queries[language][emotion]
    youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"


        # Show 3 preview videos if available
    if language in preview_videos:
            videos = preview_videos[language].get(emotion, preview_videos[language]["neutral"])
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