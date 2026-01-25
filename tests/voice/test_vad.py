"""
Tests for CLARISSA Voice Input Module

Issue: #67 - WebAudio Capture with VAD
"""

import pytest
import numpy as np
import io
import wave

from clarissa.voice.audio_capture import (
    AudioCapture,
    AudioConfig,
    AudioChunk,
    AudioBuffer,
    AudioFormat,
)
from clarissa.voice.vad import (
    VoiceActivityDetector,
    VADConfig,
    VADMode,
    VADResult,
    SimpleVAD,
)


class TestAudioConfig:
    """Tests for AudioConfig dataclass."""

    def test_default_config(self):
        config = AudioConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.bit_depth == 16

    def test_bytes_per_sample(self):
        config = AudioConfig(bit_depth=16)
        assert config.bytes_per_sample == 2

    def test_chunk_size(self):
        config = AudioConfig(sample_rate=16000, chunk_duration_ms=100)
        assert config.chunk_size_samples == 1600
        assert config.chunk_size_bytes == 3200  # 1600 * 2 bytes


class TestAudioBuffer:
    """Tests for AudioBuffer."""

    def test_add_chunk(self):
        config = AudioConfig()
        buffer = AudioBuffer(config=config)
        
        chunk = AudioChunk(
            data=b'\x00' * 3200,  # 100ms of silence
            timestamp_ms=0,
        )
        buffer.add_chunk(chunk)
        
        assert len(buffer.chunks) == 1
        assert buffer.duration_s == pytest.approx(0.1, rel=0.01)

    def test_duration_calculation(self):
        config = AudioConfig()
        buffer = AudioBuffer(config=config)
        
        # Add 1 second of audio (16000 samples * 2 bytes)
        chunk = AudioChunk(
            data=b'\x00' * 32000,
            timestamp_ms=0,
        )
        buffer.add_chunk(chunk)
        
        assert buffer.duration_s == pytest.approx(1.0, rel=0.01)

    def test_has_minimum(self):
        config = AudioConfig(min_duration_s=0.5)
        buffer = AudioBuffer(config=config)
        
        # Not enough audio
        chunk = AudioChunk(data=b'\x00' * 8000, timestamp_ms=0)  # 0.25s
        buffer.add_chunk(chunk)
        assert not buffer.has_minimum
        
        # Add more
        buffer.add_chunk(chunk)
        assert buffer.has_minimum

    def test_is_full(self):
        config = AudioConfig(max_duration_s=1.0)
        buffer = AudioBuffer(config=config)
        
        # Add 1 second
        chunk = AudioChunk(data=b'\x00' * 32000, timestamp_ms=0)
        buffer.add_chunk(chunk)
        
        assert buffer.is_full

    def test_to_wav_bytes(self):
        config = AudioConfig()
        buffer = AudioBuffer(config=config)
        
        # Add some audio
        chunk = AudioChunk(data=b'\x00\x01' * 1600, timestamp_ms=0)
        buffer.add_chunk(chunk)
        
        wav_bytes = buffer.to_wav_bytes()
        
        # Verify WAV header
        assert wav_bytes[:4] == b'RIFF'
        assert wav_bytes[8:12] == b'WAVE'
        
        # Verify it's valid WAV
        wav_io = io.BytesIO(wav_bytes)
        with wave.open(wav_io, 'rb') as wav:
            assert wav.getnchannels() == 1
            assert wav.getframerate() == 16000
            assert wav.getsampwidth() == 2

    def test_clear(self):
        config = AudioConfig()
        buffer = AudioBuffer(config=config)
        
        chunk = AudioChunk(data=b'\x00' * 3200, timestamp_ms=0)
        buffer.add_chunk(chunk)
        buffer.clear()
        
        assert len(buffer.chunks) == 0
        assert buffer.duration_s == 0


class TestAudioCapture:
    """Tests for AudioCapture class."""

    def test_process_chunk(self):
        capture = AudioCapture()
        
        # Create some audio data
        audio_data = b'\x00\x10' * 1600  # 100ms
        
        chunk = capture.process_chunk(
            raw_data=audio_data,
            timestamp_ms=0,
            is_speech=False,
        )
        
        assert chunk.data == audio_data
        assert chunk.timestamp_ms == 0
        assert chunk.is_speech is False
        assert chunk.energy_db is not None

    def test_energy_calculation(self):
        capture = AudioCapture()
        
        # Silence should have very low energy
        silence = b'\x00\x00' * 1600
        chunk = capture.process_chunk(silence, 0)
        assert chunk.energy_db < -60
        
        # Loud signal should have higher energy
        loud = b'\x00\x7f' * 1600  # ~half max amplitude
        chunk = capture.process_chunk(loud, 100)
        assert chunk.energy_db > -20

    def test_should_transcribe(self):
        config = AudioConfig(min_duration_s=0.5, max_duration_s=1.0)
        capture = AudioCapture(config=config)
        
        # Not enough audio
        chunk = AudioChunk(data=b'\x00' * 8000, timestamp_ms=0)
        capture.buffer.add_chunk(chunk)
        assert not capture.should_transcribe()
        
        # Enough audio
        capture.buffer.add_chunk(chunk)
        assert capture.should_transcribe()

    def test_get_wav_for_transcription(self):
        capture = AudioCapture()
        
        # Add some audio
        audio_data = b'\x00\x10' * 16000  # 1 second
        capture.process_chunk(audio_data, 0)
        
        wav_data = capture.get_wav_for_transcription()
        
        # Buffer should be cleared
        assert capture.buffer.duration_s == 0
        
        # WAV should be valid
        assert wav_data[:4] == b'RIFF'

    def test_reset(self):
        capture = AudioCapture()
        
        capture.process_chunk(b'\x00' * 3200, 0)
        capture.reset()
        
        assert capture.buffer.duration_s == 0
        assert not capture._speech_active


class TestVADConfig:
    """Tests for VADConfig."""

    def test_default_config(self):
        config = VADConfig()
        assert config.mode == VADMode.NORMAL
        assert config.threshold == 0.5

    def test_threshold_for_mode(self):
        aggressive = VADConfig(mode=VADMode.AGGRESSIVE)
        assert aggressive.threshold_for_mode == 0.7
        
        sensitive = VADConfig(mode=VADMode.SENSITIVE)
        assert sensitive.threshold_for_mode == 0.3


class TestVoiceActivityDetector:
    """Tests for VoiceActivityDetector."""

    def test_silence_detection(self):
        vad = VoiceActivityDetector()
        
        # Create silence
        silence = np.zeros(1600, dtype=np.int16).tobytes()
        
        result = vad.process_chunk(silence, 0)
        
        assert result.is_speech is False
        assert result.probability < 0.5
        assert result.energy_db < -60

    def test_speech_detection_with_energy(self):
        """Test speech detection using energy-based fallback."""
        vad = VoiceActivityDetector()
        vad._model = None  # Force fallback to energy-based VAD
        vad._model_loaded = True
        
        # Create loud signal (simulated speech)
        # Mix of frequencies to get reasonable ZCR
        t = np.linspace(0, 0.1, 1600)
        signal = (np.sin(2 * np.pi * 200 * t) * 10000).astype(np.int16)
        audio_data = signal.tobytes()
        
        result = vad.process_chunk(audio_data, 0)
        
        assert result.energy_db > -40
        # Note: is_speech depends on smoothing, may not trigger immediately

    def test_smoothing(self):
        """Test that smoothing prevents rapid state changes."""
        config = VADConfig(min_speech_duration_ms=100, min_silence_duration_ms=200)
        vad = VoiceActivityDetector(config=config)
        vad._model = None
        vad._model_loaded = True
        
        # Single speech frame shouldn't trigger immediately
        loud = (np.random.randn(1600) * 5000).astype(np.int16).tobytes()
        
        result = vad.process_chunk(loud, 0)
        assert result.is_speech is False  # Not yet, due to smoothing

    def test_reset(self):
        vad = VoiceActivityDetector()
        vad._is_speaking = True
        vad._speech_started_at = 1000
        
        vad.reset()
        
        assert vad._is_speaking is False
        assert vad._speech_started_at is None


class TestSimpleVAD:
    """Tests for SimpleVAD fallback."""

    def test_silence(self):
        vad = SimpleVAD()
        
        silence = np.zeros(1600, dtype=np.int16).tobytes()
        is_speech, confidence = vad.is_speech(silence)
        
        assert is_speech is False
        assert confidence < 0.5

    def test_speech_like_signal(self):
        vad = SimpleVAD(energy_threshold_db=-50)
        
        # Create a signal that looks like speech
        t = np.linspace(0, 0.1, 1600)
        signal = (np.sin(2 * np.pi * 150 * t) * 15000).astype(np.int16)
        audio_data = signal.tobytes()
        
        is_speech, confidence = vad.is_speech(audio_data)
        
        # Should detect as speech due to energy
        assert confidence > 0.3


class TestIntegration:
    """Integration tests for voice pipeline."""

    def test_capture_and_vad_together(self):
        """Test AudioCapture with VAD integration."""
        vad = VoiceActivityDetector()
        vad._model = None
        vad._model_loaded = True
        
        capture = AudioCapture()
        
        # Simulate audio stream with speech
        timestamps = range(0, 1000, 100)  # 1 second in 100ms chunks
        
        for ts in timestamps:
            # Alternating silence and "speech"
            if ts > 300 and ts < 700:
                # Simulated speech
                signal = (np.random.randn(1600) * 8000).astype(np.int16)
            else:
                # Silence
                signal = np.zeros(1600, dtype=np.int16)
            
            audio_data = signal.tobytes()
            vad_result = vad.process_chunk(audio_data, ts)
            capture.process_chunk(audio_data, ts, is_speech=vad_result.is_speech)
        
        # Should have captured audio
        assert capture.buffer.duration_s > 0

    def test_wav_roundtrip(self):
        """Test that WAV encoding/decoding preserves audio."""
        config = AudioConfig()
        buffer = AudioBuffer(config=config)
        
        # Create known audio pattern
        samples = np.array([1000, -1000, 2000, -2000] * 400, dtype=np.int16)
        audio_data = samples.tobytes()
        
        chunk = AudioChunk(data=audio_data, timestamp_ms=0)
        buffer.add_chunk(chunk)
        
        wav_bytes = buffer.to_wav_bytes()
        
        # Read back
        wav_io = io.BytesIO(wav_bytes)
        with wave.open(wav_io, 'rb') as wav:
            frames = wav.readframes(wav.getnframes())
            read_samples = np.frombuffer(frames, dtype=np.int16)
        
        np.testing.assert_array_equal(samples, read_samples)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
