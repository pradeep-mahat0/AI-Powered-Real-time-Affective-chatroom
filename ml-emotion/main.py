from fastapi import FastAPI
from pydantic import BaseModel
from ml_model import analyze_emotion # Your existing file

#for local
# import uvicorn
# import os
# from dotenv import load_dotenv
# load_dotenv()

app = FastAPI(title="Emotion Analysis Service")

class TextIn(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"status": "Emotion analysis service is running"}

@app.post("/analyze")
def analyze(data: TextIn):
    # Run the analysis from your original file
    emotion = analyze_emotion(data.text)
    return {"emotion": emotion}

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)