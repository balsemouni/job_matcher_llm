from config import LLM

from config import LLM
import google.generativeai as genai
import json

def call_gemini_for_json(prompt, max_output_tokens=1024, stream_callback=None):
    if not LLM:
        return None
    try:
        if stream_callback:
            # Streaming version
            response = LLM.generate_content(
                prompt,
                stream=True
            )
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    stream_callback(chunk.text)  # Send each chunk to callback
            
            text = full_response.strip()
        else:
            # Non-streaming version (original)
            response = LLM.generate_content(prompt)
            text = response.text.strip()

        # JSON extraction logic
        if text.startswith("```json"):
            return text[7:-3].strip()
        if text.startswith("```"):
            return text[3:-3].strip()
        return text
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        if stream_callback:
            stream_callback(f"Error: {e}")
        return None
# Checks that LLM is available.

# Sends a prompt to the LLM with a max token limit.

# Cleans the output:

# Removes markdown code blocks (json or ```).

# Returns a string ready to be parsed as JSON.

# Returns None on failure.