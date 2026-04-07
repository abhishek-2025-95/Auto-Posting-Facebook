Scene stills: Cursor image tool only (no local diffusion / no scripted image backends).

1. Open CURSOR_IMAGE_PROMPTS_PASTE.txt. Use each scene block in Cursor's image generator (10 images).
2. Export into this folder as scene0.png … scene9.png in order (match aspect ratio if your template specifies one).
3. From the project root, stitch the final MP4:

Example (defaults: Kokoro + pycaps kinetic + branding; no static paragraph):
  python scripts/render_manual_cursor_video.py render --images "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene0.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene1.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene2.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene3.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene4.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene5.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene6.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene7.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene8.png" "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/scene9.png" --output "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run/final.mp4" --article "C:\Users\user\Documents\Auto Posting Facebook\cursor_video_cursor_workflow_run\article.json"

Legacy static full-summary only (no Kokoro/pycaps):
  ... same --images/--output/--article ... --no-premium-voice-subtitles --no-pycaps-kinetic-subtitles --static-full-summary-subtitles
