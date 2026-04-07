#!/usr/bin/env python3
"""
Test Imagen 4 with the correct Google GenAI API
"""

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from config import GEMINI_API_KEY

def test_imagen4_new_api():
    """Test Imagen 4 with the new Google GenAI client"""
    print("Testing Imagen 4 with new Google GenAI API...")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt='Robot holding a red skateboard',
            config=types.GenerateImagesConfig(
                number_of_images=1,
                imageSize='2K',
                aspectRatio='1:1'
            )
        )
        
        if response.generated_images:
            generated_image = response.generated_images[0]
            image_bytes = generated_image.image.imageBytes
            
            # Convert to PIL Image
            image = Image.open(BytesIO(image_bytes))
            
            # Save the image
            image_path = 'test_imagen4.jpg'
            image.save(image_path)
            
            print(f"SUCCESS: Imagen 4 working! Image saved as {image_path}")
            print(f"Image size: {image.size}")
            print(f"Image mode: {image.mode}")
            
            return True
        else:
            print("No image generated")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_imagen4_new_api()



