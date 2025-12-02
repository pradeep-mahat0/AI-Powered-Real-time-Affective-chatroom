# 🎭 AI-Powered Real-Time Affective Chatroom

![Project Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg)
![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?\&logo=google-cloud\&logoColor=white)

A modern, intelligent chat platform that goes beyond text by understanding the emotional tone of conversations in real-time. This project uses a microservices architecture to detect emotions, moderate toxic content, and generate conversation summaries using advanced AI models.

<img width="1024" height="1024" alt="Gemini_Generated_Image_tdl1g7tdl1g7tdl1" src="https://github.com/user-attachments/assets/54622292-0924-4218-a64b-e9b8c891d729" />
<img width="1895" height="1116" alt="Screenshot 2025-12-02 231152" src="https://github.com/user-attachments/assets/f2e3136a-9b65-41ea-b749-1bb8ab7605fa" />
<img width="1901" height="1140" alt="Screenshot 2025-12-02 231232" src="https://github.com/user-attachments/assets/5267e0a9-ad0b-4493-b8ab-f67ae918cca8" />
<img width="1902" height="1091" alt="Screenshot 2025-12-02 231308" src="https://github.com/user-attachments/assets/747b4aa7-20db-4f18-b651-000dcb6b69a7" />

<img width="1902" height="1073" alt="Screenshot 2025-12-02 231322" src="https://github.com/user-attachments/assets/50d896eb-3417-4154-bd3a-e3d40cd04b8a" />



---

## 🚀 Features

* **💬 Real-Time Messaging:** Instant communication using WebSockets with zero latency.
* **🤩 Real-Time Emotion Detection:** Messages are automatically annotated with emojis representing 27 distinct emotions (e.g., Joy, Admiration, Fear) using the `modernbert-base-go-emotions` model.
* **🛡️ AI-Powered Moderation:** Automatically detects and blocks toxic content using `roberta_toxicity_classifier`, keeping the community safe.
* **📊 Smart Insights:** Generates on-demand chat summaries and analyzes the overall "Room Mood" using **Google Gemini 1.5 Flash**.
* **⚡ Asynchronous Architecture:** Uses a "Broadcast-First, Update-Later" pattern to ensure the chat feels instant even while AI processing happens in the background.

---

## 🏗️ System Architecture

The system is built as a set of decoupled microservices deployed on **Google Cloud Run**, connected to a **Google Cloud SQL (MySQL)** database.

### Microservices

1. **`chat-app-service` (FastAPI):** The core orchestrator. Handles WebSockets, user authentication, database management, and calls other AI services.
2. **`ml-emotion-service` (FastAPI + Transformers):** A dedicated high-memory service that runs the Emotion Analysis model.
3. **`ml-toxicity-service` (FastAPI + Transformers):** A dedicated high-memory service that runs the Toxicity Detection model.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10, FastAPI, Uvicorn, Gunicorn
* **Frontend:** HTML5, JavaScript (ES6), Tailwind CSS
* **Database:** MySQL (Google Cloud SQL), SQLAlchemy (ORM)
* **AI & ML:**

  * Hugging Face Transformers (`modernbert`, `roberta`)
  * LangChain + Google Gemini (LLM)
  * PyTorch
* **DevOps:** Docker, Google Cloud Run, Google Artifact Registry

---

## ⚙️ Local Development Setup

Follow these steps to run the project locally.

### **Prerequisites**

* Python 3.10+
* Docker (optional)
* MySQL Server (local or cloud)

### **1. Clone the Repository**

```bash
git clone https://github.com/your-username/affective-chatroom.git
cd affective-chatroom
```

### **2. Set Up Virtual Environment**

```bash
python -m venv chat_env
# Windows
./chat_env/Scripts/activate
# Mac/Linux
source chat_env/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r chat-app/requirements.txt
pip install -r ml-emotion/requirements.txt
pip install -r ml-toxicity/requirements.txt
```

### **4. Configuration (.env)**

Create a `.env` file in the `chat-app/` directory:

```ini
DB_USER=root
DB_PASS=your_local_password
DB_HOST=127.0.0.1
DB_NAME=chatroom
SECRET_KEY=your_secret_key
GOOGLE_API_KEY=your_gemini_api_key

EMOTION_API_URL=http://127.0.0.1:8001
TOXICITY_API_URL=http://127.0.0.1:8002
```

### **5. Run the Services (3 Terminals)**

#### Terminal 1 — Emotion Service

```bash
cd ml-emotion
python main.py  # Runs on port 8001
```

#### Terminal 2 — Toxicity Service

```bash
cd ml-toxicity
python main.py  # Runs on port 8002
```

#### Terminal 3 — Main Chat App

```bash
cd chat-app
uvicorn main:app --reload --port 8000
```

Access the app at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## ☁️ Deployment (Google Cloud)

### **1. Deploy AI Services (High Memory)**

```bash
gcloud run deploy ml-emotion-service --source ./ml-emotion --allow-unauthenticated --memory=4Gi --region=asia-south1
gcloud run deploy ml-toxicity-service --source ./ml-toxicity --allow-unauthenticated --memory=4Gi --region=asia-south1
```

### **2. Deploy Chat App (Standard Memory)**

```bash
gcloud run deploy chat-app-service \
  --source ./chat-app \
  --allow-unauthenticated \
  --memory=1Gi \
  --region=asia-south1 \
  --set-env-vars="DB_USER=root,DB_PASS=YourDBPass,DB_NAME=chatroom,DB_HOST=YOUR_CLOUD_SQL_PUBLIC_IP,SECRET_KEY=secure-key,GOOGLE_API_KEY=your-key,TOXICITY_API_URL=https://url-to-toxicity-service,EMOTION_API_URL=https://url-to-emotion-service"
```

---

## 🔮 Future Scope

* Mobile App using React Native
* Voice emotion recognition
* End-to-end encrypted private chatrooms

---

## 📄 License

This project is open-source and available under the **MIT License**.
