#!/usr/bin/env python3
"""
Proof of Concept: Speeches.ai Transcription Integration

Tests transcription of mic.flac using Systran/faster-whisper-large-v3
via Speeches.ai's OpenAI-compatible API.

Uses default temperature fallback to handle hallucinations.

Usage:
    uv run python experiments/speeches_poc.py
"""

import httpx
from openai import OpenAI
from pathlib import Path

# Configuration
SPEECHES_BASE_URL = "http://localhost:8000/v1"
MODEL_ID = "Systran/faster-whisper-medium"  # Medium model - stable, no hallucinations
INPUT_FILE = Path("mic.flac")
OUTPUT_FILE = Path("mic.attempt2.txt")


def check_model_loaded(base_url: str, model_id: str) -> bool:
    """Check if model is already loaded in Speeches.ai."""
    try:
        response = httpx.get(f"{base_url.replace('/v1', '')}/v1/audio/models")
        response.raise_for_status()
        models = response.json()
        loaded = any(m.get("id") == model_id for m in models.get("data", []))
        print(f"Model {model_id}: {'loaded' if loaded else 'not loaded'}")
        return loaded
    except Exception as e:
        print(f"Error checking models: {e}")
        return False


def download_model(base_url: str, model_id: str) -> bool:
    """Download and load model into Speeches.ai."""
    try:
        print(f"Downloading model {model_id}... (this may take several minutes)")
        # Remove /v1 suffix for model management endpoints
        response = httpx.post(
            f"{base_url.replace('/v1', '')}/v1/models/{model_id}",
            timeout=600.0  # 10 minutes for large model download
        )
        response.raise_for_status()
        print(f"Model {model_id} downloaded successfully")
        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False


def transcribe_audio(client: OpenAI, audio_file: Path, model_id: str) -> str:
    """Transcribe audio file using Speeches.ai via OpenAI client."""
    print(f"Transcribing {audio_file}...")

    with open(audio_file, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model=model_id,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            temperature=0.2  # Balanced: prevents hallucinations while maintaining consistency
        )

    return transcription


def format_output_with_timestamps(transcription) -> str:
    """Format transcription with segment timestamps."""
    lines = []

    # Add metadata
    lines.append(f"Duration: {transcription.duration:.2f}s")
    lines.append(f"Language: {transcription.language}")
    lines.append(f"Model: {MODEL_ID}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    # Add segments with timestamps
    if hasattr(transcription, 'segments') and transcription.segments:
        for segment in transcription.segments:
            start = getattr(segment, 'start', 0)
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            text = getattr(segment, 'text', '').strip()
            lines.append(f"{timestamp} {text}")
    else:
        # Fallback if no segments
        lines.append(transcription.text)

    return "\n".join(lines)


def main():
    """Main execution flow."""
    print("Speeches.ai Transcription PoC")
    print("=" * 80)

    # Verify input file exists
    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found")
        return

    print(f"Input: {INPUT_FILE} ({INPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Model: {MODEL_ID}")
    print("")

    # Check and download model if needed
    if not check_model_loaded(SPEECHES_BASE_URL, MODEL_ID):
        if not download_model(SPEECHES_BASE_URL, MODEL_ID):
            print("Failed to download model. Exiting.")
            return

    # Initialize OpenAI client pointing to Speeches.ai
    client = OpenAI(
        base_url=SPEECHES_BASE_URL,
        api_key="dummy"  # Speeches.ai doesn't require real API key
    )

    # Transcribe
    try:
        transcription = transcribe_audio(client, INPUT_FILE, MODEL_ID)

        # Format and save output
        output_text = format_output_with_timestamps(transcription)
        OUTPUT_FILE.write_text(output_text)

        print("")
        print(f"Success! Transcription saved to {OUTPUT_FILE}")
        print(f"Duration: {transcription.duration:.2f}s")
        print(f"Language: {transcription.language}")

        # Print first few lines as preview
        print("\nPreview:")
        print("-" * 80)
        preview_lines = output_text.split("\n")[:15]
        print("\n".join(preview_lines))
        if len(output_text.split("\n")) > 15:
            print("...")

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise


if __name__ == "__main__":
    main()
