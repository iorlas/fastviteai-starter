#!/usr/bin/env python3
"""
Proof of Concept: Direct faster-whisper Transcription

Tests transcription of mic.flac using faster-whisper library directly
(same approach as dagster_project/core/content_types/youtube.py).

Compares against Speeches.ai results for quality/consistency evaluation.

Usage:
    uv run python experiments/faster_whisper_poc.py
"""

from pathlib import Path
from faster_whisper import WhisperModel
import structlog

logger = structlog.get_logger()

# Configuration
MODEL_ID = "large-v3"  # Shorthand model name (same pattern as YouTubeExtractor)
DEVICE = "cpu"
COMPUTE_TYPE = "int8"  # Same as YouTubeExtractor
INPUT_FILE = Path("mic.flac")
OUTPUT_FILE = Path("mic.faster_whisper_large_v3.txt")
CACHE_DIR = Path("artifacts/cache/whisper_models")


def load_whisper_model() -> WhisperModel:
    """Load Whisper model with same config as YouTubeExtractor"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(
        "whisper.loading_model",
        model=MODEL_ID,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        cache_dir=str(CACHE_DIR),
    )

    model = WhisperModel(
        MODEL_ID,
        device=DEVICE,
        download_root=str(CACHE_DIR),
        compute_type=COMPUTE_TYPE,
    )

    logger.info("whisper.model_loaded", model=MODEL_ID)
    return model


def transcribe_audio(model: WhisperModel, audio_path: Path) -> tuple[list[dict], str]:
    """Transcribe audio file using faster-whisper"""
    logger.info("whisper.transcribing", audio_path=str(audio_path))

    # Transcribe with generator pattern (same as YouTubeExtractor)
    segments_generator, info = model.transcribe(
        str(audio_path),
        vad_filter=True,  # Voice activity detection
        # Note: No temperature parameter - testing default behavior
        # Note: No language parameter - let Whisper auto-detect
    )

    # Collect segments with progress logging
    segments = []
    total_duration = info.duration if hasattr(info, "duration") else None
    detected_language = info.language if hasattr(info, "language") else "unknown"
    last_progress_log = 0.0

    for segment in segments_generator:
        segments.append(
            {
                "start": segment.start,
                "text": segment.text,
                "end": segment.end,
            }
        )

        # Log progress every 15 seconds
        if total_duration and segment.end - last_progress_log >= 15.0:
            progress_pct = (segment.end / total_duration) * 100
            logger.info(
                "whisper.progress",
                audio_path=str(audio_path),
                processed_seconds=round(segment.end, 1),
                total_seconds=round(total_duration, 1),
                progress_pct=round(progress_pct, 1),
            )
            last_progress_log = segment.end

    logger.info(
        "whisper.transcribed",
        audio_path=str(audio_path),
        segments=len(segments),
        duration=round(total_duration, 2) if total_duration else None,
        language=detected_language,
    )

    return segments, detected_language


def format_output_with_timestamps(segments: list[dict], detected_language: str) -> str:
    """Format transcription with segment timestamps (same as Speeches.ai PoC)"""
    lines = []

    # Add metadata
    total_duration = max(seg["end"] for seg in segments) if segments else 0
    lines.append(f"Duration: {total_duration:.2f}s")
    lines.append(f"Language: {detected_language}")
    lines.append(f"Model: {MODEL_ID}")
    lines.append(f"Compute Type: {COMPUTE_TYPE}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    # Add segments with timestamps
    for segment in segments:
        start = segment["start"]
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = segment["text"].strip()
        lines.append(f"{timestamp} {text}")

    return "\n".join(lines)


def main():
    """Main execution flow"""
    print("faster-whisper Direct Transcription PoC")
    print("=" * 80)

    # Verify input file exists
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found")
        return

    print(f"Input: {INPUT_FILE} ({INPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Model: {MODEL_ID}")
    print(f"Device: {DEVICE}")
    print(f"Compute Type: {COMPUTE_TYPE}")
    print(f"Language: auto-detect")
    print("")

    # Load model
    model = load_whisper_model()

    # Transcribe
    try:
        segments, detected_language = transcribe_audio(model, INPUT_FILE)

        # Format and save output
        output_text = format_output_with_timestamps(segments, detected_language)
        OUTPUT_FILE.write_text(output_text)

        print("")
        print(f"Success! Transcription saved to {OUTPUT_FILE}")
        print(f"Total segments: {len(segments)}")

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
        print(f"  - mic.faster_whisper.txt (this run - direct faster-whisper)")
        print(f"  - mic.attempt2.txt (Speeches.ai with medium model)")
        print(f"  - mic.reference.txt (reference transcription)")
        print("\nUse diff to compare outputs")

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise


if __name__ == "__main__":
    main()
