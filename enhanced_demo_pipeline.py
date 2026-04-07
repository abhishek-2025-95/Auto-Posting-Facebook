#!/usr/bin/env python3
"""
The Unseen Economy - Enhanced Demo Pipeline
Shows sophisticated visual strategy without requiring OpenAI API key
"""

import os
import random
import json
import urllib.parse
from datetime import datetime


def setup_constants():
    """Initialize all constants with enhanced strategy"""
    
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
    """Generate a shocking, viral economic statement (enhanced demo version)"""
    
    # Enhanced viral takes with more emotional impact
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
        "The 'American Dream' is now a subscription service. Everything became a monthly payment, and you're paying more for less.",
        "The 'trickle-down economics' experiment has been running for 40 years. Here's the data on what actually trickled down (spoiler: it's not money).",
        "The 'sharing economy' isn't about sharing - it's about extracting value from people who own nothing.",
        "The 'invisible hand' of the market is actually just 3 companies controlling 80% of everything you buy.",
        "The 'middle class' is disappearing not because of technology, but because of policy. Here's the data that proves it's intentional.",
        "The 'free market' created the most expensive healthcare system in the world. Here's how America's healthcare became a profit center instead of a public good."
    ]
    
    return random.choice(viral_takes)


def generate_image_prompt(economic_take):
    """Generate sophisticated DALL-E 3 prompts with professional graphic design strategy (demo version)"""
    
    # Enhanced image prompts with professional graphic design elements
    image_prompts = [
        "A surreal, hyper-realistic depiction of a single, colossal, perfectly polished golden hand reaching down from a dark, stormy sky, effortlessly plucking a massive, glowing sphere of wealth from a vast, barren landscape where countless tiny, struggling figures stand silhouetted against a dim horizon. The hand casts an immense shadow over the landscape. Style: dramatic, Gothic Cyberpunk meets Surreal Photorealism. Cinematic lighting, high contrast, deep shadows. Dominant colors: muted grays, deep blues, with striking golden accents.",
        
        "A stark, neo-brutalist composition showing a towering skyscraper made entirely of stacked dollar bills, with tiny, faceless figures at the base looking up in despair. The building casts a dark shadow over a neighborhood of small, crumbling houses. High contrast black and white with a single red accent. Dramatic, low-angle perspective. Cinematic lighting with deep shadows.",
        
        "A dystopian, cyberpunk cityscape where massive corporate logos glow in neon against a dark, rainy sky. In the foreground, a crowd of silhouetted figures holds up signs, but their voices are drowned out by the towering advertisements. Style: Gothic Cyberpunk with neon accents. High contrast, dramatic lighting, rain effects.",
        
        "An abstract, minimalist representation of wealth inequality: a single, massive golden coin on one side of a scale, weighing down against a pile of broken dreams, empty wallets, and discarded hopes on the other side. Clean lines, stark contrast, limited color palette of gold, black, and white. Dramatic, cinematic lighting.",
        
        "A surreal, hyper-realistic scene of a person trapped inside a transparent cube made of money, while outside, a crowd of people reaches toward them but cannot break through. The cube floats in a vast, empty space. Style: Surreal Photorealism with dramatic, volumetric lighting. High contrast, emotional resonance.",
        
        "A dramatic, sci-fi dystopian scene showing a massive, glowing data visualization in the sky, displaying wealth distribution as a towering bar chart. Below, a crowd of people looks up in horror as the visualization shows the extreme inequality. Style: High-Tech Infographic meets Dramatic Sci-Fi. Glowing elements, motion blur, cinematic composition.",
        
        "A neo-brutalist, concrete-textured composition showing a single, massive percentage symbol (1%) carved into a wall, with a tiny percentage (99%) barely visible in the corner. Raw, industrial textures. High contrast, dramatic shadows. Monochromatic with a single red accent.",
        
        "A surreal, impossible scene where a person stands on a mountain of debt papers, reaching up toward a golden hand that holds a single dollar bill just out of reach. The background is a vast, empty landscape. Style: Surreal Photorealism with dramatic, cinematic lighting. High contrast, emotional impact."
    ]
    
    return random.choice(image_prompts)


def generate_image():
    """Generate image URL (demo version)"""
    return "https://example.com/enhanced-dalle-generated-image.jpg"


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
    """Main orchestrator function with enhanced visual strategy (demo version)"""
    
    print("The Unseen Economy - Enhanced Viral Content Pipeline (DEMO)")
    print("=" * 70)
    
    # Setup constants
    constants = setup_constants()
    
    try:
        # Step 1: Generate viral economic take
        print("Generating viral economic take...")
        economic_take = generate_viral_economic_take()
        print(f"Generated: {economic_take}")
        
        # Step 2: Generate sophisticated image prompt
        print("Creating professional image prompt...")
        image_prompt = generate_image_prompt(economic_take)
        print("Image prompt created")
        
        # Step 3: Generate high-quality image
        print("Generating professional image with DALL-E 3...")
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




