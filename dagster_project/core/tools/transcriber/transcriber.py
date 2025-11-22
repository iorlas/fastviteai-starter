import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import structlog
from faster_whisper import WhisperModel

from dagster_project.core.tools.transcriber.models import TranscriptionResult

logger = structlog.get_logger()


class Transcriber:
    _model_cache: dict[tuple[str, str], WhisperModel] = {}

    def __init__(
        self,
        model: str = "large-v3",
        device: str = "cpu",
        model_cache_dir: Path = Path("artifacts/cache/whisper_models"),
        progress_callback: Callable[[float, float, float], None] | None = None,
    ):
        self.model_name = model
        self.device = device
        self.model_cache_dir = model_cache_dir
        self.progress_callback = progress_callback
        self._model = self._get_model()

    def _get_model(self) -> WhisperModel:
        cache_key = (self.model_name, self.device)

        if cache_key not in self._model_cache:
            self.model_cache_dir.mkdir(parents=True, exist_ok=True)

            logger.info(
                "whisper.loading_model",
                model=self.model_name,
                device=self.device,
                cache_dir=str(self.model_cache_dir),
            )

            self._model_cache[cache_key] = WhisperModel(
                self.model_name,
                device=self.device,
                download_root=str(self.model_cache_dir),
            )

            logger.info("whisper.model_loaded", model=self.model_name)

        return self._model_cache[cache_key]

    async def transcribe(
        self,
        audio_path: Path,
        format: Literal["llm_optimized", "raw"] = "llm_optimized",
    ) -> TranscriptionResult:
        logger.info("transcription.started", audio_path=str(audio_path), format=format)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        segments_generator, info = await asyncio.to_thread(
            self._model.transcribe,
            str(audio_path),
            vad_filter=True,
        )

        segments = []
        total_duration = info.duration if hasattr(info, "duration") else None
        last_progress_log = 0.0

        for segment in segments_generator:
            segment_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            }

            if format == "raw":
                segment_dict.update(
                    {
                        "id": segment.id,
                        "seek": segment.seek,
                        "tokens": segment.tokens,
                        "temperature": segment.temperature,
                        "avg_logprob": segment.avg_logprob,
                        "compression_ratio": segment.compression_ratio,
                        "no_speech_prob": segment.no_speech_prob,
                    }
                )

            segments.append(segment_dict)

            if total_duration and segment.end - last_progress_log >= 15.0:
                progress_pct = (segment.end / total_duration) * 100

                if self.progress_callback:
                    self.progress_callback(segment.end, total_duration, progress_pct)

                logger.info(
                    "whisper.progress",
                    audio_path=str(audio_path),
                    processed_seconds=round(segment.end, 1),
                    total_seconds=round(total_duration, 1),
                    progress_pct=round(progress_pct, 1),
                )
                last_progress_log = segment.end

        result = TranscriptionResult(
            metadata={
                "audio_path": str(audio_path),
                "model": self.model_name,
                "device": self.device,
                "format": format,
                "segments_count": len(segments),
            }
        )

        if format == "raw":
            result.segments = segments
        else:
            result.text = self._format_llm_optimized(segments)

        logger.info("transcription.completed", audio_path=str(audio_path), format=format, segments=len(segments))

        return result

    @staticmethod
    def _format_llm_optimized(segments: list[dict]) -> str:
        if not segments:
            return ""

        max_time = max(seg["start"] for seg in segments)
        is_long_video = max_time >= 3600

        lines = []
        current_minute = None
        current_texts = []

        for segment in segments:
            start_time = segment["start"]
            total_minutes = int(start_time // 60)

            if current_minute is None or total_minutes != current_minute:
                if current_minute is not None and current_texts:
                    lines.append(" ".join(current_texts))

                current_minute = total_minutes
                current_texts = []

                if is_long_video:
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    timestamp = f"[{hours}h{minutes:02d}m]"
                else:
                    timestamp = f"[{total_minutes}m]"

                lines.append(timestamp)

            current_texts.append(segment["text"].strip())

        if current_texts:
            lines.append(" ".join(current_texts))

        return "\n".join(lines)
