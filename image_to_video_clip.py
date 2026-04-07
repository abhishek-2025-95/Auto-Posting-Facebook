"""
Convert a single image into a short video clip (Ken Burns style: subtle zoom/pan).
Uses ffmpeg for best compatibility. No AI required.
Useful for turning your approval_preview.jpg or post_image.jpg into a 5–8 second clip for Reels/Stories.
"""
import os
import subprocess
import sys


def image_to_video_clip(
    image_path,
    output_path=None,
    duration_seconds=6,
    width=720,
    height=900,
    effect="zoom",
    fps=30,
):
    """
    Convert an image to a short MP4 clip.

    Args:
        image_path: Path to input image (e.g. approval_preview.jpg, post_image.jpg).
        output_path: Output MP4 path. Default: same name as image with .mp4.
        duration_seconds: Clip length in seconds (default 6).
        width, height: Output size (default 720x900 for 4:5 portrait).
        effect: "zoom" (slow zoom in), "zoom_out" (slow zoom out), or "static" (no motion).
        fps: Frame rate (default 30).

    Returns:
        Path to the created video file, or None on failure.
    """
    if not image_path or not os.path.isfile(image_path):
        print(f"Image not found: {image_path}")
        return None

    if output_path is None:
        base = os.path.splitext(image_path)[0]
        output_path = base + "_clip.mp4"

    total_frames = int(duration_seconds * fps)

    # Ken Burns: zoompan filter. z goes from 1.0 to 1.08 over the clip for subtle zoom in.
    if effect == "zoom":
        # zoom in: z increases from 1.0 to ~1.08
        zoompan = f"zoompan=z='min(1.0+0.08*on/{total_frames},1.08)':d=1:s={width}x{height}:fps={fps}"
    elif effect == "zoom_out":
        zoompan = f"zoompan=z='max(1.08-0.08*on/{total_frames},1.0)':d=1:s={width}x{height}:fps={fps}"
    else:
        # static: scale to output size, no motion
        zoompan = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", zoompan,
        "-t", str(duration_seconds),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        if os.path.isfile(output_path):
            print(f"Video clip saved: {output_path}")
            return output_path
    except FileNotFoundError:
        print("ffmpeg not found. Install ffmpeg and add it to PATH:")
        print("  https://ffmpeg.org/download.html")
        print("  Or: winget install ffmpeg")
        return None
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr.decode() if e.stderr else e}")
        return None
    except Exception as e:
        print(f"Error creating video: {e}")
        return None
    return None


def main():
    image = "approval_preview.jpg"
    if len(sys.argv) > 1:
        image = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    path = image_to_video_clip(image, output_path=out, duration_seconds=6)
    if path:
        print(f"Done. Use: {path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
