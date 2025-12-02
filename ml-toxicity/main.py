from fastapi import FastAPI
from pydantic import BaseModel
from content_moderation import is_toxic # Your existing file

# import uvicorn
# import os
# from dotenv import load_dotenv
# load_dotenv()

app = FastAPI(title="Toxicity Analysis Service")

class TextIn(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"status": "Toxicity analysis service is running"}

@app.post("/analyze")
def analyze(data: TextIn):
    # Run the analysis from your original file
    toxic = is_toxic(data.text)
    return {"is_toxic": toxic}

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)