# 🎭 Emotion Detector & Wellness Recommender

A Streamlit web application that detects emotions from text input and provides personalized wellness recommendations, activities, motivational quotes, and curated music videos in multiple Indian and English languages.

---

## ✨ Features

- **🧠 Emotion Detection** — Analyzes your text using the `j-hartmann/emotion-english-distilroberta-base` model via Hugging Face Inference API
- **📊 Emotion Breakdown** — Visual progress bars showing confidence scores for all detected emotions
- **🏃 Activity Suggestions** — Personalized activities based on your current emotional state
- **💬 Motivational Quotes** — Curated quotes matching your mood
- **🎵 Music Recommendations** — Curated YouTube video previews in **19 languages**:
  - 🇬🇧 English
  - 🇮🇳 Hindi, Odia, Telugu, Tamil, Bengali, Kannada, Punjabi, Marathi, Gujarati
  - 🇮🇳 Malayalam, Assamese, Bhojpuri, Haryanvi, Kashmiri, Konkani, Maithili, Gondi, Rajasthani

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Emotion Model | `j-hartmann/emotion-english-distilroberta-base` |
| Inference API | Hugging Face `huggingface_hub` |
| Environment Config | `python-dotenv` |

---

## 📁 Project Structure

```
emotion-detector/
│
├── app.py                  # Main Streamlit application
├── .env                    # Environment variables (HF_TOKEN)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/emotion-detector.git
cd emotion-detector
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
HF_TOKEN=your_huggingface_api_token_here
```

> 💡 Get your free API token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 5. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🎯 Supported Emotions

| Emotion | Message |
|---|---|
| 😄 Joy | Uplifting activities and happy music |
| 😢 Sadness | Comforting suggestions and soothing music |
| 😠 Anger | Calming techniques and relaxing music |
| 😨 Fear | Grounding exercises and supportive music |
| 🤢 Disgust | Refreshing activities and neutral music |
| 😲 Surprise | Adventure-themed suggestions and energetic music |
| 😐 Neutral | Mindfulness activities and peaceful music |

---

## 🌍 Music Languages

The app supports curated video previews and YouTube search for **19 languages**, making it accessible across India and beyond. Each language has emotion-matched playlists, mixes, and direct video thumbnails with watch links.

---

## 📝 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `HF_TOKEN` | Hugging Face API token for inference | ✅ Yes |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

- [Hugging Face](https://huggingface.co/) for the emotion classification model
- [Streamlit](https://streamlit.io/) for the web framework
- All regional music artists and YouTube creators featured in recommendations
