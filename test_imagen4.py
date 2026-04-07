# test_imagen4.py - Test Imagen 4 after enabling billing
from content_generator import generate_image_with_imagen4
from PIL import Image
import os

def test_imagen4():
    """Test Imagen 4 image generation"""
    print("Testing Imagen 4 image generation...")
    
    # Test prompt
    test_prompt = """
    Professional news photography of a modern data center with dramatic lighting.
    High contrast, cinematic composition, photorealistic style.
    No text in the image, just the visual scene.
    """
    
    try:
        # Generate image with Imagen 4
        image_path = generate_image_with_imagen4(test_prompt)
        
        if image_path and os.path.exists(image_path):
            # Check image properties
            with Image.open(image_path) as img:
                print(f"SUCCESS: Imagen 4 image generated!")
                print(f"Image size: {img.size}")
                print(f"Image mode: {img.mode}")
                print(f"File size: {os.path.getsize(image_path)} bytes")
                print(f"Image saved as: {image_path}")
                return True
        else:
            print("FAILED: No image generated")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_imagen4()



