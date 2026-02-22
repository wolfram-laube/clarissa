"""
Audio Capture Module — Handles microphone input, buffering, and VAD integration.

Issue: #67 — WebAudio Capture with VAD
ADR-028 Reference: Section 1 — Voice Activity Detection

Provides:
  - AudioConfig: sampling parameters
  - AudioChunk: timestamped raw PCM fragment
  - AudioBuffer: accumulates chunks, produces WAV bytes
  - AudioFormat: encoding enum (PCM16, FLOAT32)
  - AudioCapture: orchestrates chunk processing with energy calculation
"""

import io
import math
import wave
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class AudioFormat(Enum):
    """Audio encoding format."""
    PCM16 = "pcm16"
    FLOAT32 = "float32"


@dataclass
class AudioConfig:
    """Configuration for audio capture and buffering."""
    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16
    chunk_duration_ms: int = 100
    min_duration_s: float = 0.5
    max_duration_s: float = 30.0
    format: AudioFormat = AudioFormat.PCM16

    @property
    def bytes_per_sample(self) -> int:
        return self.bit_depth // 8

    @property
    def chunk_size_samples(self) -> int:
        return int(self.sample_rate * self.chunk_duration_ms / 1000)

    @property
    def chunk_size_bytes(self) -> int:
        return self.chunk_size_samples * self.bytes_per_sample


@dataclass
class AudioChunk:
    """A timestamped fragment of raw PCM audio."""
    data: bytes
    timestamp_ms: int = 0
    is_speech: Optional[bool] = None
    energy_db: Optional[float] = None


class AudioBuffer:
    """
    Accumulates AudioChunks and produces WAV output.

    Tracks total duration and enforces min/max boundaries
    defined by the associated AudioConfig.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.chunks: List[AudioChunk] = []

    @property
    def duration_s(self) -> float:
        total_bytes = sum(len(c.data) for c in self.chunks)
        if total_bytes == 0:
            return 0.0
        return total_bytes / (
            self.config.sample_rate * self.config.bytes_per_sample * self.config.channels
        )

    @property
    def has_minimum(self) -> bool:
        return self.duration_s >= self.config.min_duration_s

    @property
    def is_full(self) -> bool:
        return self.duration_s >= self.config.max_duration_s

    def add_chunk(self, chunk: AudioChunk) -> None:
        self.chunks.append(chunk)

    def clear(self) -> None:
        self.chunks.clear()

    def to_wav_bytes(self) -> bytes:
        """Return accumulated audio as an in-memory WAV file."""
        raw = b"".join(c.data for c in self.chunks)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(self.config.bytes_per_sample)
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(raw)
        return buf.getvalue()


class AudioCapture:
    """
    Orchestrates audio chunk processing with energy calculation.

    Usage (synchronous / push-based):
        capture = AudioCapture()
        chunk = capture.process_chunk(raw_pcm, timestamp_ms)
        if capture.should_transcribe():
            wav = capture.get_wav_for_transcription()
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.buffer = AudioBuffer(config=self.config)
        self._speech_active: bool = False

    def process_chunk(
        self,
        raw_data: bytes,
        timestamp_ms: int,
        is_speech: Optional[bool] = None,
    ) -> AudioChunk:
        """Accept raw PCM bytes, compute energy, buffer the chunk."""
        energy = self._compute_energy_db(raw_data)
        chunk = AudioChunk(
            data=raw_data,
            timestamp_ms=timestamp_ms,
            is_speech=is_speech,
            energy_db=energy,
        )
        self.buffer.add_chunk(chunk)
        if is_speech is not None:
            self._speech_active = is_speech
        return chunk

    def should_transcribe(self) -> bool:
        """True when the buffer has accumulated enough audio."""
        return self.buffer.has_minimum

    def get_wav_for_transcription(self) -> bytes:
        """Export the buffer as WAV and clear it."""
        wav = self.buffer.to_wav_bytes()
        self.buffer.clear()
        return wav

    def reset(self) -> None:
        """Reset capture state completely."""
        self.buffer.clear()
        self._speech_active = False

    @staticmethod
    def _compute_energy_db(raw_data: bytes) -> float:
        """Compute RMS energy in dB (relative to int16 full-scale)."""
        if len(raw_data) < 2:
            return -100.0

        import struct

        n_samples = len(raw_data) // 2
        if n_samples == 0:
            return -100.0

        samples = struct.unpack(f"<{n_samples}h", raw_data[: n_samples * 2])
        sum_sq = sum(s * s for s in samples)
        rms = math.sqrt(sum_sq / n_samples)

        if rms > 0:
            return 20 * math.log10(rms / 32768.0)
        return -100.0


# WebAudio browser configuration
WEBAUDIO_CONFIG = """
const audioConfig = {
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    sampleRate: 16000,
    channelCount: 1
  }
};
"""
