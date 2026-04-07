import argparse
import json
from facebook_poster import load_settings, FacebookPoster
from facebook_poster.calendar import load_calendar
from facebook_poster.scheduler import run_scheduler
from facebook_poster.folder_ingest import post_from_folder
from facebook_poster.utm import build_utm_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Facebook Page posting CLI")
    parser.add_argument("--env", dest="env_path", default=None, help="Path to .env file (optional)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    post_text = subparsers.add_parser("post-text", help="Post a text status")
    post_text.add_argument("message", help="Text content to post")

    post_link = subparsers.add_parser("post-link", help="Post a link with optional message")
    post_link.add_argument("url", help="URL to share")
    post_link.add_argument("--message", default=None, help="Optional message")
    # UTM parameters
    for arg in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"):
        post_link.add_argument(f"--{arg}", default=None)

    post_image = subparsers.add_parser("post-image", help="Post an image from a file path")
    post_image.add_argument("path", help="Path to image file")
    post_image.add_argument("--caption", default=None, help="Optional caption")

    post_image_url = subparsers.add_parser("post-image-url", help="Post an image from a URL")
    post_image_url.add_argument("url", help="Image URL")
    post_image_url.add_argument("--caption", default=None, help="Optional caption")

    from_folder = subparsers.add_parser("post-from-folder", help="Post all images in a folder")
    from_folder.add_argument("directory", help="Folder with images")
    from_folder.add_argument("--caption-source", default="filename", choices=["filename", "txt", "none"], help="Caption source")
    from_folder.add_argument("--pattern", action="append", help="Glob patterns (can repeat)")
    from_folder.add_argument("--limit", type=int, default=None, help="Max number of images to post")
    from_folder.add_argument("--prefix", default=None, help="Prefix text for caption")
    from_folder.add_argument("--suffix", default=None, help="Suffix text for caption")

    calendar_post = subparsers.add_parser("post-from-calendar", help="Run due posts from a CSV/JSON calendar and exit")
    calendar_post.add_argument("path", help="Path to calendar file (CSV/JSON)")
    calendar_post.add_argument("--dry-run", action="store_true", help="Print actions without posting")
    calendar_post.add_argument("--max", type=int, default=None, help="Max posts to execute")

    calendar_daemon = subparsers.add_parser("run-scheduler", help="Continuously check a calendar and post when due")
    calendar_daemon.add_argument("path", help="Path to calendar file (CSV/JSON)")
    calendar_daemon.add_argument("--dry-run", action="store_true")
    calendar_daemon.add_argument("--interval", type=int, default=60, help="Polling interval seconds")

    args = parser.parse_args()

    settings = load_settings(args.env_path)
    poster = FacebookPoster(settings)

    if args.command == "post-text":
        result = poster.post_text(args.message)
        print(json.dumps(result, indent=2))
        return

    if args.command == "post-link":
        url = build_utm_url(
            args.url,
            utm_source=args.utm_source,
            utm_medium=args.utm_medium,
            utm_campaign=args.utm_campaign,
            utm_term=args.utm_term,
            utm_content=args.utm_content,
        )
        result = poster.post_link(url, args.message)
        print(json.dumps(result, indent=2))
        return

    if args.command == "post-image":
        result = poster.post_image_from_path(args.path, args.caption)
        print(json.dumps(result, indent=2))
        return

    if args.command == "post-image-url":
        result = poster.post_image_from_url(args.url, args.caption)
        print(json.dumps(result, indent=2))
        return

    if args.command == "post-from-folder":
        results = post_from_folder(
            poster,
            args.directory,
            caption_source=args.caption_source,
            patterns=args.pattern,
            limit=args.limit,
            prefix=args.prefix,
            suffix=args.suffix,
        )
        print(json.dumps(results, indent=2))
        return

    if args.command == "post-from-calendar":
        items = load_calendar(args.path)
        from facebook_poster.calendar import run_due_items
        results = run_due_items(poster, items, dry_run=args.dry_run, max_count=args.max)
        print(json.dumps(results, indent=2))
        return

    if args.command == "run-scheduler":
        items = load_calendar(args.path)
        run_scheduler(poster, items, interval_seconds=args.interval, dry_run=args.dry_run)
        return

    raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()
