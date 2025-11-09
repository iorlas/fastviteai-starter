import asyncio
import argparse
import sys
from pathlib import Path
import structlog

from tactiq_transcriber import TactiqTranscriber

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

logger = structlog.get_logger()


async def main():
    parser = argparse.ArgumentParser(description="Test YouTube transcript extraction via tactiq.io")
    parser.add_argument("url", help="YouTube URL to transcribe")
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (not headless)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds (default: 30)")

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"YouTube Transcript Extractor - tactiq.io PoC")
    print(f"{'='*80}\n")
    print(f"URL: {args.url}")
    print(f"Headless: {not args.visible}")
    print(f"Timeout: {args.timeout}s\n")

    transcriber = TactiqTranscriber(
        headless=not args.visible,
        timeout_ms=args.timeout * 1000
    )

    print("Starting extraction...\n")

    result = await transcriber.get_transcript(args.url)

    print(f"{'='*80}")
    print(f"RESULT")
    print(f"{'='*80}\n")
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_seconds:.2f}s")

    if result.video_title:
        print(f"Video Title: {result.video_title}")
    if result.channel_name:
        print(f"Channel: {result.channel_name}")
    if result.video_duration:
        print(f"Video Duration: {result.video_duration}")

    if result.success and result.transcript:
        print(f"Transcript length: {len(result.transcript)} characters")
        print(f"\n{'='*80}")
        print(f"TRANSCRIPT")
        print(f"{'='*80}\n")
        print(result.transcript)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(result.transcript)
            print(f"\n{'='*80}")
            print(f"Saved to: {output_path.absolute()}")
            print(f"{'='*80}\n")
    else:
        print(f"Error: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
