#!/usr/bin/env python3
"""
Proof of Concept: whisper-asr-webservice Transcription

Tests transcription of mic.flac using whisper-asr-webservice API (port 9000).

API uses native Whisper endpoint format (not OpenAI-compatible like Speeches.ai).
Compares against previous results (Speeches.ai, faster-whisper direct).

Usage:
    uv run python experiments/whisper_asr_webservice_poc.py
"""

from pathlib import Path
import httpx
import structlog

logger = structlog.get_logger()

# Configuration
WHISPER_ASR_BASE_URL = "http://localhost:9000"
INPUT_FILE = Path("mic.flac")
OUTPUT_FILE = Path("mic.whisper_asr_webservice.txt")

# Test configuration (matching previous tests)
TASK = "transcribe"  # transcribe vs translate
OUTPUT_FORMAT = "json"  # txt, vtt, srt, tsv, json
LANGUAGE = None  # None = auto-detect (like faster-whisper large-v3)
ENCODE = True  # Pre-encode with ffmpeg


def transcribe_audio(audio_path: Path) -> dict:
    """Transcribe audio using whisper-asr-webservice API"""
    logger.info(
        "whisper_asr.transcribing",
        audio_path=str(audio_path),
        base_url=WHISPER_ASR_BASE_URL,
        task=TASK,
        output_format=OUTPUT_FORMAT,
        language=LANGUAGE or "auto",
    )

    # Build query parameters
    params = {
        "task": TASK,
        "output": OUTPUT_FORMAT,
        "encode": str(ENCODE).lower(),
    }
    if LANGUAGE:
        params["language"] = LANGUAGE

    # Send transcription request
    with open(audio_path, "rb") as audio_file:
        files = {"audio_file": (audio_path.name, audio_file, "audio/flac")}

        with httpx.Client(timeout=1800.0) as client:  # 30 minute timeout
            logger.info("whisper_asr.sending_request", size_mb=audio_path.stat().st_size / 1024 / 1024)
            response = client.post(
                f"{WHISPER_ASR_BASE_URL}/asr",
                params=params,
                files=files,
            )
            logger.info("whisper_asr.received_response", status_code=response.status_code)
            response.raise_for_status()

    result = response.json()

    logger.info(
        "whisper_asr.transcribed",
        audio_path=str(audio_path),
        segments=len(result.get("segments", [])) if "segments" in result else "N/A",
        detected_language=result.get("language", "unknown"),
    )

    return result


def format_output_with_timestamps(result: dict) -> str:
    """Format transcription with segment timestamps (matching previous PoC format)"""
    lines = []

    # Add metadata
    detected_language = result.get("language", "unknown")
    segments = result.get("segments", [])

    # Calculate duration from last segment
    total_duration = 0.0
    if segments:
        last_segment = segments[-1]
        total_duration = last_segment.get("end", 0.0)

    lines.append(f"Duration: {total_duration:.2f}s")
    lines.append(f"Language: {detected_language}")
    lines.append(f"Service: whisper-asr-webservice")
    lines.append(f"Task: {TASK}")
    lines.append(f"Auto-detect: {LANGUAGE is None}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    # Add segments with timestamps
    for segment in segments:
        start = segment.get("start", 0.0)
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = segment.get("text", "").strip()
        lines.append(f"{timestamp} {text}")

    return "\n".join(lines)


def main():
    """Main execution flow"""
    print("whisper-asr-webservice Transcription PoC")
    print("=" * 80)

    # Verify input file exists
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found")
        return

    print(f"Input: {INPUT_FILE} ({INPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Service: {WHISPER_ASR_BASE_URL}")
    print(f"Task: {TASK}")
    print(f"Output format: {OUTPUT_FORMAT}")
    print(f"Language: {LANGUAGE or 'auto-detect'}")
    print("")

    # Transcribe
    try:
        result = transcribe_audio(INPUT_FILE)

        # Format and save output
        output_text = format_output_with_timestamps(result)
        OUTPUT_FILE.write_text(output_text)

        segments = result.get("segments", [])
        print("")
        print(f"Success! Transcription saved to {OUTPUT_FILE}")
        print(f"Total segments: {len(segments)}")
        print(f"Detected language: {result.get('language', 'unknown')}")

        # Print first few lines as preview
        print("\nPreview:")
        print("-" * 80)
        preview_lines = output_text.split("\n")[:15]
        print("\n".join(preview_lines))
        if len(output_text.split("\n")) > 15:
            print("...")

        # Comparison note
        print("\n" + "=" * 80)
        print("Comparison files:")
        print(f"  - mic.whisper_asr_webservice.txt (this run)")
        print(f"  - mic.faster_whisper_large_v3.txt (faster-whisper direct, large-v3)")
        print(f"  - mic.faster_whisper.txt (faster-whisper direct, medium)")
        print(f"  - mic.attempt2.txt (Speeches.ai, medium)")
        print(f"  - mic.reference.txt (reference transcription)")
        print("\nUse diff to compare outputs")

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise


if __name__ == "__main__":
    main()
