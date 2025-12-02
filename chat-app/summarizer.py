

import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
# from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool

# Load environment variables from .env file
# load_dotenv()
llm = ChatGroq(
        temperature=0, 
        model_name="llama-3.3-70b-versatile"
    )

# --- Summarization Chain ---
def get_summary_chain() -> LLMChain:
    """
    Initializes and returns a LangChain LLMChain for summarization using Groq and Llama.
    """
    # llm = ChatGroq(temperature=0, model_name="llama3-8b-8192")
    prompt_template = """
    You are an expert in summarizing conversations. Your task is to provide a concise, neutral summary of the following chat transcript.
    Focus on the main topics and decisions, ignoring small talk.

    CONTEXT:
    {chat_transcript}

    SUMMARY:
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_transcript"]
    )
    return LLMChain(prompt=prompt, llm=llm)

# --- NEW: Mood Analysis Chain ---
def get_mood_chain() -> LLMChain:
    """
    Initializes a new LangChain LLMChain specifically for mood analysis.
    """
    # llm = ChatGroq(temperature=0.2, model_name="llama3-8b-8192")
    
    # This detailed prompt guides the LLM to return a single, clean word
    # that matches the emotions our frontend already knows how to display.
    prompt_template = """
    You are a mood analysis expert for a live chatroom. Your task is to analyze the following chat transcript and determine the single, dominant, overall mood of the conversation.
    
    Please respond with ONLY a single word from the following list:
    'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 'relief', 'remorse', 'sadness', 'surprise', 'neutral'.

    CHAT TRANSCRIPT:
    {chat_transcript}

    DOMINANT MOOD:
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_transcript"]
    )
    return LLMChain(prompt=prompt, llm=llm)


# Create reusable instances of our chains
summary_chain = get_summary_chain()
mood_chain = get_mood_chain() # NEW mood chain instance

async def generate_summary_async(chat_transcript: str) -> str:
    """
    Asynchronously generates a summary from a chat transcript.
    """
    try:
        response = await run_in_threadpool(summary_chain.invoke, {"chat_transcript": chat_transcript})
        return response.get("text", "Sorry, the summary could not be generated.").strip()
    except Exception as e:
        print(f"❌ Error during summarization: {e}")
        return "An error occurred while generating the summary."

# NEW: Async function for generating mood
async def generate_mood_async(chat_transcript: str) -> str:
    """
    Asynchronously generates a mood analysis from a chat transcript.
    """
    try:
        response = await run_in_threadpool(mood_chain.invoke, {"chat_transcript": chat_transcript})
        # We strip whitespace and convert to lower to ensure a clean response
        return response.get("text", "neutral").strip().lower()
    except Exception as e:
        print(f"❌ Error during mood analysis: {e}")
        return "neutral"

# import os
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# # from dotenv import load_dotenv
# # # --- Initialization ---
# # load_dotenv()
# # This will read the GOOGLE_API_KEY you provide in the deploy command
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",  # Use the fast and cheap model
#     temperature=0.7,
#     convert_system_message_to_human=True # Helps with older models
# )

# output_parser = StrOutputParser()

# # --- Summarizer Function ---

# # Define the prompt for summarizing
# summary_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful assistant. Your job is to provide a brief, fluent summary of the following chat transcript."),
#     ("human", "Please summarize this chat:\n\n{transcript}")
# ])

# # Create the summarizer chain
# summarizer_chain = summary_prompt | llm | output_parser

# async def generate_summary_async(transcript: str) -> str:
#     """
#     Generates a summary of the transcript using Gemini.
#     """
#     if not transcript:
#         return "No transcript provided."
        
#     try:
#         # Use .ainvoke() for an asynchronous call
#         summary = await summarizer_chain.ainvoke({"transcript": transcript})
#         return summary
#     except Exception as e:
#         print(f"Error during summary generation: {e}")
#         return "Could not generate a summary at this time."

# # --- Mood Analysis Function ---

# # Define the prompt for mood analysis
# mood_prompt = ChatPromptTemplate.from_messages([
#     ("system", (
#         "You are a mood analysis expert for a live chatroom. Your task is to analyze the following chat transcript and determine the single, dominant, overall mood of the conversation."
#         "Respond with *only a single word* from this list:"
#         " ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 'relief', 'remorse', 'sadness', 'surprise', 'neutral']"
#     )),
#     ("human", "Analyze this chat:\n\n{transcript}")
# ])

# # Create the mood chain
# mood_chain = mood_prompt | llm | output_parser

# async def generate_mood_async(transcript: str) -> str:
#     """
#     Generates the dominant mood of the transcript using Gemini.
#     """
#     if not transcript:
#         return "neutral"
        
#     try:
#         # Use .ainvoke() for an asynchronous call
#         mood = await mood_chain.ainvoke({"transcript": transcript})
        
#         # Clean the output, just in case
#         cleaned_mood = mood.strip().lower().replace(".", "")
        
#         # Validate the output
#         valid_moods = ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 'relief', 'remorse', 'sadness', 'surprise', 'neutral']
#         if cleaned_mood in valid_moods:
#             return cleaned_mood
#         else:
#             return "neutral" # Default if LLM gives bad output
            
#     except Exception as e:
#         print(f"Error during mood generation: {e}")
#         return "neutral"