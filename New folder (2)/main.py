"""
Main orchestrator for the AI Comic Generator pipeline.
Takes a news URL and generates a mobile-friendly comic strip.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from extractor import extract_news_content
from director import generate_comic_script
from artist import generate_all_panels
from publisher import generate_mobile_html
from comic_combiner import combine_panels_into_comic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('comic_generator.log')
    ]
)

logger = logging.getLogger(__name__)


def get_api_keys():
    """Get API keys from environment variables or config file.
    
    Returns:
        tuple: (gemini_api_key, openai_api_key) or (None, None) if not found
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Try to read from config file
    config_path = Path("config.txt")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") and not gemini_key:
                        gemini_key = line.split("=", 1)[1].strip()
                    elif line.startswith("OPENAI_API_KEY=") and not openai_key:
                        openai_key = line.split("=", 1)[1].strip()
        except Exception as e:
            logger.warning(f"Could not read config file: {e}")
    
    if not gemini_key:
        logger.error("Gemini API key not found. Set GEMINI_API_KEY environment variable or add it to config.txt")
    
    if not openai_key:
        logger.warning("OpenAI API key not found. Images won't be generated. Set OPENAI_API_KEY for DALL-E image generation.")
    
    return gemini_key, openai_key


def generate_comic_from_url(url, output_dir="output", gemini_api_key=None, openai_api_key=None):
    """
    Main pipeline function: Extract -> Direct -> Generate Images -> Publish
    
    Args:
        url (str): News article URL
        output_dir (str): Directory for output files
        gemini_api_key (str): Google Gemini API key (optional, will try to get from env/config)
        openai_api_key (str): Not used anymore - kept for backward compatibility
        
    Returns:
        str: Path to generated HTML file, or None if generation fails
    """
    if not gemini_api_key:
        gemini_key, _ = get_api_keys()
        gemini_api_key = gemini_key
    
    if not gemini_api_key:
        logger.error("Gemini API key required for script generation")
        return None
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("Starting AI Comic Generator Pipeline")
    logger.info("=" * 60)
    
    # Step 1: Extract news content
    logger.info("\n[Step 1/4] Extracting news content...")
    news_data = extract_news_content(url)
    if not news_data:
        logger.error("Failed to extract news content")
        return None
    
    logger.info(f"[OK] Extracted: {news_data['title'][:60]}...")
    
    # Step 2: Generate comic script
    logger.info("\n[Step 2/4] Generating comic script with Google Gemini...")
    script_data = generate_comic_script(
        news_data["title"],
        news_data["text"],
        gemini_api_key
    )
    if not script_data:
        logger.error("Failed to generate comic script")
        return None
    
    logger.info(f"[OK] Script generated: {script_data['comic_title']}")
    
    # Step 3: Generate panel images
    logger.info("\n[Step 3/4] Generating panel images using free image generation API...")
    # Use Gemini API key (though image generation uses free alternatives)
    # Save images to the specified FB Page Manager folder
    fb_images_folder = r"C:\Users\user\Documents\Auto Posting Facebook\FB Page Manager\Content Maker\images"
    image_paths = generate_all_panels(script_data, gemini_api_key, fb_images_folder)
    if not image_paths or len(image_paths) != 4:
        logger.error(f"Failed to generate all panels. Got {len(image_paths)} images")
        return None
    
    logger.info(f"[OK] Generated {len(image_paths)} panel images")
    
    # Step 4: Combine panels into single comic image
    logger.info("\n[Step 4/5] Combining panels into single comic image...")
    fb_images_folder = r"C:\Users\user\Documents\Auto Posting Facebook\FB Page Manager\Content Maker\images"
    combined_comic_path = os.path.join(fb_images_folder, "comic_strip.png")
    combined_image = combine_panels_into_comic(image_paths, script_data, combined_comic_path)
    if combined_image:
        logger.info(f"[OK] Combined comic saved: {combined_image}")
    else:
        logger.warning("Failed to create combined comic, but individual panels are available")
    
    # Step 5: Generate HTML
    logger.info("\n[Step 5/5] Generating mobile-friendly HTML...")
    html_path = os.path.join(output_dir, "comic.html")
    html_file = generate_mobile_html(script_data, image_paths, html_path)
    if not html_file:
        logger.error("Failed to generate HTML")
        return None
    
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info(f"Output: {html_file}")
    logger.info("=" * 60)
    
    return html_file


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate a mobile-friendly comic strip from a news article URL"
    )
    parser.add_argument(
        "url",
        help="URL of the news article to convert into a comic"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for generated files (default: output)"
    )
    parser.add_argument(
        "--gemini-key",
        help="Google Gemini API key (or set GEMINI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--openai-key",
        help="(Deprecated) No longer needed - image generation uses free APIs"
    )
    
    args = parser.parse_args()
    
    html_file = generate_comic_from_url(
        args.url, 
        args.output, 
        gemini_api_key=args.gemini_key,
        openai_api_key=args.openai_key
    )
    
    if html_file:
        print(f"\n[SUCCESS] Comic generated: {html_file}")
        print(f"Open this file in a web browser to view the comic.")
        sys.exit(0)
    else:
        print("\n[ERROR] Failed to generate comic. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

