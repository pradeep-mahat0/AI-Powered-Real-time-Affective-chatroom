from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Define the new model name
MODEL_NAME = "cirimus/modernbert-base-go-emotions"

# Global variables for the model and tokenizer
tokenizer = None
model = None

print(f"Loading model: {MODEL_NAME}...")
try:
    # Load the tokenizer and model from Hugging Face
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    # Set the model to evaluation mode (disables dropout, etc.)
    model.eval()
    print("✅ Emotion analysis model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")

def analyze_emotion(text: str) -> str:
    """
    Analyzes the emotion of a given text string using the modernBERT model.
    Returns the label of the most likely emotion.
    """
    # Check if the model and tokenizer were loaded successfully
    if not model or not tokenizer:
        return "unknown"
        
    try:
        # Tokenize the input text and convert to PyTorch tensors
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

        # Perform inference without calculating gradients
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get the raw output scores (logits)
        logits = outputs.logits

        # Find the index of the highest score
        predicted_class_id = torch.argmax(logits, dim=1).item()
        
        # Look up the corresponding emotion label from the model's configuration
        return model.config.id2label[predicted_class_id]

    except Exception as e:
        print(f"Error during emotion analysis: {e}")
        return "unknown"

# Example usage:
if __name__ == "__main__":
    text1 = "I am so excited for the party tonight, it's going to be amazing!"
    text2 = "I'm not sure what to do, I feel so lost and confused."
    text3 = "Thank you so much for your help, I really appreciate it."
    
    print(f"'{text1}' -> Emotion: {analyze_emotion(text1)}")
    print(f"'{text2}' -> Emotion: {analyze_emotion(text2)}")
    print(f"'{text3}' -> Emotion: {analyze_emotion(text3)}")

