#!/usr/bin/env python3
"""
The Unseen Economy - Viral Content Pipeline
Generates complete content packages with AI text and images
"""

import os
import random
import json
import urllib.parse
from datetime import datetime
from openai import OpenAI


def setup_constants():
    """Initialize all constants and OpenAI client"""
    
    # Engagement hooks for viral content
    ENGAGEMENT_HOOKS = [
        "Your thoughts?",
        "Share if this makes you angry.",
        "Share if you're tired of being blamed.",
        "Share if you're ready for change.",
        "Is this the 'opportunity' they promised?",
        "What do they hide? This."
    ]
    
    # Hashtag categories for strategic mixing
    HASHTAG_CATEGORIES = {
        'viral': ['#ViralTake', '#TruthBomb', '#DataBomb', '#MindBlown', '#TheUnseenEconomy'],
        'controversial': ['#EconomicReality', '#WealthInequality', '#CorporateGreed', '#LateStageCapitalism'],
        'problem_focused': ['#HousingCrisis', '#DebtCrisis', '#Healthcare', '#GigEconomy', '#Inflation']
    }
    
    # UTM content tags for tracking
    UTM_CONTENT_TAGS = ['ShockingData', 'RealityCheck', 'Controversial', 'DataBomb', 'TruthBomb']
    
    # Base configuration
    BASE_URL = 'https://theunseeneconomy.com/report'
    CAMPAIGN = 'ViralOctober'
    SOURCE = 'Facebook'
    MEDIUM = 'Social'
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'utm_content_tags': UTM_CONTENT_TAGS,
        'base_url': BASE_URL,
        'campaign': CAMPAIGN,
        'source': SOURCE,
        'medium': MEDIUM,
        'client': client
    }


def generate_viral_economic_take(client):
    """Generate a shocking, viral economic statement using GPT-4"""
    
    system_prompt = """You are an AI assistant for 'The Unseen Economy' Facebook page. Your job is to generate one short, shocking, and highly shareable economic fact or controversial statement for a US/European Millennial/Gen Z audience. The tone should be angry, provocative, and focused on economic justice, inequality, corporate greed, or the housing/debt crisis. The statement must be 280 characters or less."""
    
    user_prompt = "Generate a new viral economic take."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.9
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating economic take: {e}")
        return "The top 1% captured 82% of all new wealth created last year, while the bottom 50% saw zero increase."


def generate_image_prompt(economic_take):
    """Create a DALL-E 3 prompt for the economic take"""
    
    base_prompt = f"""Create a DALL-E 3 prompt that visually represents the following idea: {economic_take}. 
    
    The style should be 'high-end graphic,' 'dramatic data visualization,' 'minimalist infographic,' or 'symbolic photorealism.' 
    The image must be cinematic, high-contrast, and emotionally impactful. 
    Do not include any text in the image itself.
    
    Focus on visual metaphors, dramatic contrasts, or symbolic representations that convey the economic inequality or injustice."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "user", "content": base_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        return f"A dramatic, minimalist infographic showing a single gold bar on one side of a scale, weighing more than a massive pile of rubble labeled 'The Bottom 50%' on the other side. Dark, cinematic lighting."


def generate_image(client, image_prompt):
    """Generate image using DALL-E 3"""
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )
        
        return response.data[0].url
    
    except Exception as e:
        print(f"Error generating image: {e}")
        return "https://example.com/placeholder-image.jpg"


def build_post_content(economic_take, utm_link, constants):
    """Build the complete post content with hooks and hashtags"""
    
    # Select random engagement hook
    hook = random.choice(constants['engagement_hooks'])
    
    # Select hashtags (2 viral, 2 controversial, 1 problem-focused)
    hashtags = []
    hashtags.extend(random.sample(constants['hashtag_categories']['viral'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['controversial'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['problem_focused'], 1))
    
    # Build final post text
    post_text = f"{economic_take}\n\n{hook}\n\n{utm_link}\n\n{' '.join(hashtags)}"
    
    return post_text


def generate_utm_link(constants):
    """Generate UTM-tracked link"""
    
    # Select random content tag
    content_tag = random.choice(constants['utm_content_tags'])
    
    # Build UTM parameters
    utm_params = {
        'utm_source': constants['source'],
        'utm_medium': constants['medium'],
        'utm_campaign': constants['campaign'],
        'utm_content': content_tag
    }
    
    # Build full URL
    base_url = constants['base_url']
    query_string = urllib.parse.urlencode(utm_params)
    full_url = f"{base_url}?{query_string}"
    
    return full_url


def main():
    """Main orchestrator function"""
    
    print("The Unseen Economy - Viral Content Pipeline")
    print("=" * 50)
    
    # Setup constants and client
    constants = setup_constants()
    client = constants['client']
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Step 1: Generate viral economic take
        print("Generating viral economic take...")
        economic_take = generate_viral_economic_take(client)
        print(f"Generated: {economic_take}")
        
        # Step 2: Generate image prompt
        print("Creating image prompt...")
        image_prompt = generate_image_prompt(economic_take)
        print("Image prompt created")
        
        # Step 3: Generate image
        print("Generating image with DALL-E 3...")
        image_url = generate_image(client, image_prompt)
        print(f"Image generated: {image_url}")
        
        # Step 4: Generate UTM link
        print("Creating UTM-tracked link...")
        utm_link = generate_utm_link(constants)
        print(f"UTM link: {utm_link}")
        
        # Step 5: Build final post content
        print("Building final post content...")
        final_post_text = build_post_content(economic_take, utm_link, constants)
        print("Post content ready")
        
        # Step 6: Assemble final output
        output = {
            "page_name": "The Unseen Economy",
            "generated_at": datetime.now().isoformat(),
            "viral_take": economic_take,
            "dalle_image_prompt": image_prompt,
            "image_url": image_url,
            "utm_link": utm_link,
            "final_post_text": final_post_text
        }
        
        print("\nCONTENT PACKAGE READY!")
        print("=" * 50)
        print(json.dumps(output, indent=2))
        
        # Save to file
        with open('generated_content.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nContent saved to: generated_content.json")
        
    except Exception as e:
        print(f"Error in main pipeline: {e}")
        return


if __name__ == "__main__":
    main()
