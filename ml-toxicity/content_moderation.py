from transformers import pipeline

print("Loading content moderation model...")
try:
    # Load the pipeline for the binary toxicity classifier
    moderator = pipeline(
        "text-classification", 
        model="garak-llm/roberta_toxicity_classifier"
    )
    print("✅ Content moderation model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading moderation model: {e}")
    moderator = None

# A threshold of 0.8 is a good starting point. 
# You can lower it to be more strict or raise it to be more lenient.
TOXICITY_THRESHOLD = 0.8

def is_toxic(text: str) -> bool:
    """
    Analyzes text for toxicity using a binary classifier. Returns True if the 
    'toxic' label has a score above the threshold, False otherwise.
    """
    if not moderator:
        return False # Fail safe if the model didn't load

    try:
        # Use top_k=None to get the scores for ALL labels ('toxic' and 'non-toxic')
        results = moderator(text, top_k=None)
        
        # Find the result for the 'toxic' label specifically
        for result in results:
            if result['label'] == 'toxic' and result['score'] > TOXICITY_THRESHOLD:
                print(f"Toxic content detected: (Score: {result['score']:.2f})")
                return True
                
    except Exception as e:
        print(f"Error during toxicity analysis: {e}")
    
    return False

# Example usage to show how it works now:
if __name__ == "__main__":
    clean_message = "I am having a wonderful day, the weather is lovely!"
    toxic_message = "You are a complete idiot."

    print(f"'{clean_message}' -> Is Toxic: {is_toxic(clean_message)}") # Expected: False
    print(f"'{toxic_message}' -> Is Toxic: {is_toxic(toxic_message)}") # Expected: True

