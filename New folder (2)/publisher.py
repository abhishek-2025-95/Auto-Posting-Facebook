"""
The Publisher: HTML generation module for mobile-friendly comic display.
Assembles images and captions into a responsive HTML page.
"""

import os
import logging

logger = logging.getLogger(__name__)


def generate_mobile_html(script_data, image_paths, output_filename="daily_news_comic.html"):
    """
    Generate a mobile-friendly HTML file from comic script and images.
    
    Args:
        script_data (dict): Comic script containing comic_title and panels
        image_paths (list): List of paths to panel image files
        output_filename (str): Name of the output HTML file
        
    Returns:
        str: Path to the generated HTML file, or None if generation fails
    """
    try:
        logger.info("Generating mobile-friendly HTML...")
        
        comic_title = script_data.get("comic_title", "Daily News Comic")
        panels = script_data.get("panels", [])
        
        # Ensure we have matching panels and images
        if len(panels) != len(image_paths):
            logger.warning(f"Mismatch: {len(panels)} panels but {len(image_paths)} images")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{comic_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px 10px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .comic-container {{
            max-width: 600px;
            width: 100%;
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            font-size: 24px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            font-weight: 700;
        }}
        
        .panel {{
            margin-bottom: 30px;
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .panel img {{
            width: 100%;
            height: auto;
            border: 4px solid #333;
            border-radius: 8px;
            display: block;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .caption {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 15px;
            margin-top: -4px;
            border-left: 4px solid #667eea;
            border-right: 4px solid #333;
            border-bottom: 4px solid #333;
            border-radius: 0 0 8px 8px;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            font-weight: 500;
        }}
        
        .panel-number {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        
        @media (max-width: 480px) {{
            h1 {{
                font-size: 20px;
            }}
            
            .caption {{
                font-size: 14px;
                padding: 12px;
            }}
            
            .comic-container {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="comic-container">
        <h1>{comic_title}</h1>
"""
        
        # Add panels
        for i, panel in enumerate(panels):
            if i >= len(image_paths):
                logger.warning(f"Missing image for panel {i+1}")
                break
            
            panel_num = panel.get("panel_number", i + 1)
            caption = panel.get("caption", "")
            
            # Use absolute path to FB Page Manager images folder
            # Images are saved to the FB Page Manager folder
            fb_images_folder = r"C:\Users\user\Documents\Auto Posting Facebook\FB Page Manager\Content Maker\images"
            image_path = os.path.join(fb_images_folder, f"panel_{panel_num}.png")
            
            # For HTML, use relative path if possible, otherwise use absolute path
            # Check if we can make it relative to the HTML file location
            output_dir = os.path.dirname(output_filename) or "."
            try:
                rel_path = os.path.relpath(image_path, output_dir)
                # If relative path is too long or crosses drives, use absolute
                if ".." in rel_path and len(rel_path) > 50:
                    image_path_for_html = image_path.replace("\\", "/")
                else:
                    image_path_for_html = rel_path.replace("\\", "/")
            except ValueError:
                # Different drives, use absolute path
                image_path_for_html = image_path.replace("\\", "/")
            
            html_content += f"""
        <div class="panel">
            <span class="panel-number">Panel {panel_num}</span>
            <img src="{image_path_for_html}" alt="Panel {panel_num}">
            <div class="caption">{caption}</div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"Successfully generated HTML: {output_filename}")
        return output_filename
        
    except Exception as e:
        logger.error(f"Error generating HTML: {e}")
        return None

