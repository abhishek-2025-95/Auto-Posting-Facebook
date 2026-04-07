"""
The Director: AI scriptwriting module using Google Gemini.
Converts news articles into structured 4-panel comic scripts.
"""

import google.generativeai as genai
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert comic book writer and storyboard artist. Your job is to take a news article and convert it into a compelling, accurate, 4-panel comic strip script.

You must output strictly valid JSON format with the following structure:
{
  "comic_title": "A catchy title for the comic",
  "panels": [
    {
      "panel_number": 1,
      "visual_prompt": "A detailed description of the scene for an AI image generator. Specify the art style (watercolor-ink on textured paper). Mention key characters and setting. Ensure visual consistency for subsequent panels.",
      "caption": "A short, punchy caption summarizing this part of the news story (max 2 sentences)."
    }
  ]
}

Rules:
1. The art style must always be "watercolor-ink comic style on textured paper".
2. Maintain factual accuracy to the news source.
3. Ensure visual continuity. If Panel 1 establishes a character wearing a red tie, Panel 2 should mention the same character in a red tie if they are present.
4. Create exactly 4 panels that tell a complete story arc.
5. Each visual_prompt should be detailed enough for consistent image generation (mention character appearances, clothing, setting details).
6. Keep captions concise and engaging."""


def generate_comic_script(news_title, news_text, api_key):
    """
    Generate a 4-panel comic script from news content using Google Gemini.
    
    Args:
        news_title (str): The title of the news article
        news_text (str): The full text content of the news article
        api_key (str): Google Gemini API key
        
    Returns:
        dict: JSON object containing comic_title and panels array, or None if generation fails
    """
    try:
        logger.info("Generating comic script with Google Gemini...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash model (faster and free tier available)
        # Model names need to include 'models/' prefix or use short name
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            try:
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except:
                model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Combine system prompt and user input
        full_prompt = f"""{SYSTEM_PROMPT}

Now, convert the following news article into a comic script:

News Title: {news_title}

News Text:
{news_text}

Remember to output ONLY valid JSON with the exact structure specified above."""
        
        # Generate response
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2000,
            )
        )
        
        script_text = response.text.strip()
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in script_text:
            script_text = script_text.split("```json")[1].split("```")[0].strip()
        elif "```" in script_text:
            script_text = script_text.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object in the text if it's not clean JSON
        if not script_text.startswith("{"):
            # Look for JSON object boundaries
            start_idx = script_text.find("{")
            end_idx = script_text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                script_text = script_text[start_idx:end_idx + 1]
        
        script_data = json.loads(script_text)
        
        # Validate structure
        if "comic_title" not in script_data or "panels" not in script_data:
            logger.error("Invalid script structure returned from Gemini")
            return None
            
        if len(script_data["panels"]) != 4:
            logger.warning(f"Expected 4 panels, got {len(script_data['panels'])}")
        
        logger.info(f"Successfully generated script: {script_data['comic_title']}")
        return script_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Response text: {script_text[:500] if 'script_text' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Error generating comic script: {e}")
        return None

