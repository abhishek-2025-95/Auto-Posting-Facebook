#!/usr/bin/env python3
"""
The Unseen Economy - Enhanced Viral Content Pipeline
Professional-grade visual strategy with sophisticated DALL-E 3 prompts
"""

import os
import random
import json
import urllib.parse
from datetime import datetime
from openai import OpenAI


def setup_constants():
    """Initialize all constants and OpenAI client with enhanced strategy"""
    
    # Enhanced engagement hooks for maximum viral potential
    ENGAGEMENT_HOOKS = [
        "Your thoughts?",
        "Share if this makes you angry.",
        "Share if you're tired of being blamed.",
        "Share if you're ready for change.",
        "Is this the 'opportunity' they promised?",
        "What do they hide? This.",
        "This is why we're angry.",
        "The math doesn't lie.",
        "Wake up.",
        "They don't want you to see this."
    ]
    
    # Enhanced hashtag strategy with more categories
    HASHTAG_CATEGORIES = {
        'viral': ['#ViralTake', '#TruthBomb', '#DataBomb', '#MindBlown', '#TheUnseenEconomy', '#WakeUp', '#RealityCheck'],
        'controversial': ['#EconomicReality', '#WealthInequality', '#CorporateGreed', '#LateStageCapitalism', '#SystemRigged', '#EliteCapture'],
        'problem_focused': ['#HousingCrisis', '#DebtCrisis', '#Healthcare', '#GigEconomy', '#Inflation', '#StudentDebt', '#WageStagnation'],
        'emotional': ['#Angry', '#Frustrated', '#FedUp', '#Enough', '#FightBack', '#Resistance']
    }
    
    # Enhanced UTM content tags
    UTM_CONTENT_TAGS = ['ShockingData', 'RealityCheck', 'Controversial', 'DataBomb', 'TruthBomb', 'WakeUp', 'ViralTake']
    
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
    """Generate a shocking, viral economic statement using GPT-4 with enhanced prompts"""
    
    system_prompt = """You are an AI assistant for 'The Unseen Economy' Facebook page. Your job is to generate one short, shocking, and highly shareable economic fact or controversial statement for a US/European Millennial/Gen Z audience. 

The tone should be angry, provocative, and focused on economic justice, inequality, corporate greed, or the housing/debt crisis. The statement must be 280 characters or less.

Focus on:
- Shocking statistics that make people angry
- Controversial takes that challenge mainstream narratives
- Data points that expose systemic problems
- Statements that make people want to share immediately

Make it punchy, memorable, and designed to go viral."""
    
    user_prompt = "Generate a new viral economic take that will make people angry and want to share it immediately."
    
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
    """Generate sophisticated DALL-E 3 prompts with professional graphic design strategy"""
    
    system_prompt = """You are an expert graphic designer for a viral social media page called 'The Unseen Economy'. Your goal is to create a stunning, high-impact DALL-E 3 image prompt that perfectly visualizes a controversial economic data point, designed to grab attention and evoke strong emotion.

The image should not just *represent* the data; it should *transform* it into an arresting visual narrative.

Here's what to include in the DALL-E 3 prompt:

Core Idea: Clearly communicate the economic_take through symbolic imagery, metaphor, or abstract representation.

Style & Aesthetics (Choose 1-2 primary, and others as supporting):
- Neo-Brutalism: Bold, stark, concrete textures, often monochromatic with a single powerful accent color. Raw and impactful.
- Gothic Cyberpunk: Dark, futuristic, dystopian, with neon accents, rain, industrial elements, and a sense of decay or oppression.
- Abstract Minimalism: Clean lines, strong geometric shapes, limited color palette, deep symbolism, often with a sense of stark contrast.
- Surreal Photorealism: Hyper-realistic elements combined in a dreamlike, impossible, or unsettling way to create a powerful metaphor.
- High-Tech Infographic/Data-Art: Elegant, sophisticated data visualization, but rendered in a highly artistic, almost architectural way, not just a chart. Think glowing lines, 3D elements, motion blur (implied).
- Dramatic Sci-Fi/Dystopian: Sweeping, cinematic scenes depicting the future consequences or current struggle related to the economic issue.

Composition & Mood:
- High Contrast: Essential for drama and impact.
- Cinematic Lighting: Volumetric light, deep shadows, spotlights.
- Emotional Resonance: The image must evoke anger, frustration, injustice, shock, or a sense of urgency.
- Focal Point: A clear visual anchor that immediately communicates the core message.
- Dynamic Angles: Low angles, wide shots, or unique perspectives to add drama.
- Color Palette: Suggest a dominant mood (e.g., desaturated, monochrome with a single vibrant accent, dark and moody, stark reds and grays).

Forbidden: No visible text, no specific numbers unless abstractly integrated into a graphic element (e.g., a towering percentage bar, not a text label).

The output should be *only* the DALL-E 3 prompt text, highly descriptive of the visual elements, style, mood, and composition. Aim for a captivating, viral aesthetic."""
    
    user_prompt = f"Create a DALL-E 3 image prompt for the following economic take: \"{economic_take}\"\n\nThe output should be *only* the DALL-E 3 prompt text, highly descriptive of the visual elements, style, mood, and composition. Aim for a captivating, viral aesthetic."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error generating image prompt: {e}")
        return f"A surreal, hyper-realistic depiction of a single, colossal, perfectly polished golden hand reaching down from a dark, stormy sky, effortlessly plucking a massive, glowing sphere of wealth from a vast, barren landscape where countless tiny, struggling figures stand silhouetted against a dim horizon. The hand casts an immense shadow over the landscape. Style: dramatic, Gothic Cyberpunk meets Surreal Photorealism. Cinematic lighting, high contrast, deep shadows. Dominant colors: muted grays, deep blues, with striking golden accents."


def generate_image(client, image_prompt):
    """Generate image using DALL-E 3 with enhanced settings"""
    
    try:
        print(f"Generating image with DALL-E 3. Prompt: {image_prompt[:100]}...")
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
    """Build the complete post content with enhanced hooks and hashtags"""
    
    # Select random engagement hook
    hook = random.choice(constants['engagement_hooks'])
    
    # Enhanced hashtag selection (3 viral, 2 controversial, 2 problem-focused, 1 emotional)
    hashtags = []
    hashtags.extend(random.sample(constants['hashtag_categories']['viral'], 3))
    hashtags.extend(random.sample(constants['hashtag_categories']['controversial'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['problem_focused'], 2))
    hashtags.extend(random.sample(constants['hashtag_categories']['emotional'], 1))
    
    # Build final post text
    post_text = f"{economic_take}\n\n{hook}\n\n{utm_link}\n\n{' '.join(hashtags)}"
    
    return post_text


def generate_utm_link(constants):
    """Generate UTM-tracked link with enhanced tracking"""
    
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
    """Main orchestrator function with enhanced visual strategy"""
    
    print("The Unseen Economy - Enhanced Viral Content Pipeline")
    print("=" * 60)
    
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
        
        # Step 2: Generate sophisticated image prompt
        print("Creating professional image prompt...")
        image_prompt = generate_image_prompt(economic_take)
        print("Image prompt created")
        
        # Step 3: Generate high-quality image
        print("Generating professional image with DALL-E 3...")
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
        
        print("\nENHANCED CONTENT PACKAGE READY!")
        print("=" * 50)
        print(json.dumps(output, indent=2))
        
        # Save to file
        with open('enhanced_content.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nContent saved to: enhanced_content.json")
        
    except Exception as e:
        print(f"Error in main pipeline: {e}")
        return


if __name__ == "__main__":
    main()




