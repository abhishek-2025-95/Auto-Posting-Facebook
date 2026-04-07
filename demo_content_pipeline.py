#!/usr/bin/env python3
"""
The Unseen Economy - Viral Content Pipeline (Demo Version)
Shows the structure without requiring OpenAI API key
"""

import os
import random
import json
import urllib.parse
from datetime import datetime


def setup_constants():
    """Initialize all constants"""
    
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
    
    return {
        'engagement_hooks': ENGAGEMENT_HOOKS,
        'hashtag_categories': HASHTAG_CATEGORIES,
        'utm_content_tags': UTM_CONTENT_TAGS,
        'base_url': BASE_URL,
        'campaign': CAMPAIGN,
        'source': SOURCE,
        'medium': MEDIUM
    }


def generate_viral_economic_take():
    """Generate a shocking, viral economic statement (demo version)"""
    
    # Pre-written viral takes for demo
    viral_takes = [
        "The top 1% captured 82% of all new wealth created last year, while the bottom 50% saw zero increase.",
        "The average CEO makes 350x more than their workers. In 1965, it was 20x. This isn't meritocracy - it's aristocracy with better PR.",
        "The average American spends 40% of their income on housing. In 1970, it was 25%. This isn't inflation - it's a systematic transfer of wealth.",
        "The 'gig economy' isn't the future of work - it's the return of medieval serfdom with better marketing.",
        "The top 1% own more wealth than the bottom 90% combined. This isn't capitalism - it's feudalism with better technology.",
        "The average American has $90,000 in debt but only $8,000 in savings. This isn't personal failure - it's systemic design.",
        "The 'free market' is a myth. 5 companies control 90% of what you consume, and competition died in America.",
        "The minimum wage should be $25/hour, not $15. Here's the math that will make your head explode.",
        "Europe has better healthcare, education, and work-life balance than America, but Americans think they're 'freer.' The propaganda is working perfectly.",
        "The 'American Dream' is now a subscription service. Everything became a monthly payment, and you're paying more for less."
    ]
    
    return random.choice(viral_takes)


def generate_image_prompt(economic_take):
    """Create a DALL-E 3 prompt for the economic take (demo version)"""
    
    # Pre-written image prompts for demo
    image_prompts = [
        "A dramatic, minimalist infographic showing a single gold bar on one side of a scale, weighing more than a massive pile of rubble labeled 'The Bottom 50%' on the other side. Dark, cinematic lighting.",
        "A stark black and white image of a towering skyscraper made of dollar bills, with tiny figures at the base looking up in despair. High contrast, dramatic shadows.",
        "A symbolic representation of wealth inequality: a golden throne on a mountain of coins, with a crowd of faceless people at the bottom reaching up. Cinematic, high-contrast lighting.",
        "A minimalist graphic showing a massive corporate building casting a dark shadow over a neighborhood of small houses. Dramatic, high-contrast black and white.",
        "A symbolic scale with a single diamond on one side and a pile of broken dreams on the other. Dark, cinematic lighting with dramatic shadows."
    ]
    
    return random.choice(image_prompts)


def generate_image():
    """Generate image URL (demo version)"""
    return "https://example.com/dalle-generated-image.jpg"


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
    """Main orchestrator function (demo version)"""
    
    print("The Unseen Economy - Viral Content Pipeline (DEMO)")
    print("=" * 60)
    
    # Setup constants
    constants = setup_constants()
    
    try:
        # Step 1: Generate viral economic take
        print("Generating viral economic take...")
        economic_take = generate_viral_economic_take()
        print(f"Generated: {economic_take}")
        
        # Step 2: Generate image prompt
        print("Creating image prompt...")
        image_prompt = generate_image_prompt(economic_take)
        print("Image prompt created")
        
        # Step 3: Generate image
        print("Generating image with DALL-E 3...")
        image_url = generate_image()
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




