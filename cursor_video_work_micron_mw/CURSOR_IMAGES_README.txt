Micron / MarketWatch story — Cursor image tool only.
Open CURSOR_IMAGE_PROMPTS_PASTE.txt; generate 5 images in Cursor; save scene0.png … scene4.png here.

Then:
  python scripts/render_manual_cursor_video.py render --images "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/scene0.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/scene1.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/scene2.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/scene3.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/scene4.png" --output "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw/final.mp4" --article "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_work_micron_mw\article.json"
