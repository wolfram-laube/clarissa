"""
Voice Activity Detection (VAD) Module for CLARISSA

Uses Silero VAD for speech detection:
- Lightweight (< 1MB model)
- Real-time capable
- Works in browser via ONNX.js and on server via PyTorch

ADR-028 Reference: Section 1 - Voice Activity Detection
Issue: #67 - WebAudio Capture with VAD
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class VADMode(Enum):
    """VAD sensitivity modes."""
    AGGRESSIVE = "aggressive"  # Low false positives (miss some speech)
    NORMAL = "normal"  # Balanced
    SENSITIVE = "sensitive"  # Low false negatives (more false positives)


@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection."""
    mode: VADMode = VADMode.NORMAL
    sample_rate: int = 16000
    frame_duration_ms: int = 30  # 30ms frames work well with Silero
    threshold: float = 0.5  # Speech probability threshold
    
    # Smoothing to avoid rapid on/off
    min_speech_duration_ms: int = 250  # Minimum speech segment
    min_silence_duration_ms: int = 500  # Silence before speech ends
    
    # Pre-roll: keep audio before speech starts
    speech_pad_ms: int = 300

    @property
    def frame_size_samples(self) -> int:
        return int(self.sample_rate * self.frame_duration_ms / 1000)
    
    @property
    def threshold_for_mode(self) -> float:
        """Get threshold based on mode."""
        mode_thresholds = {
            VADMode.AGGRESSIVE: 0.7,
            VADMode.NORMAL: 0.5,
            VADMode.SENSITIVE: 0.3,
        }
        return mode_thresholds.get(self.mode, self.threshold)


@dataclass
class VADResult:
    """Result of voice activity detection on a frame."""
    is_speech: bool
    probability: float
    timestamp_ms: int
    energy_db: Optional[float] = None


class VoiceActivityDetector:
    """
    Voice Activity Detection using Silero VAD.
    
    Silero VAD is a pre-trained model that works with:
    - PyTorch (server-side)
    - ONNX (browser via ONNX.js)
    
    Usage:
        vad = VoiceActivityDetector()
        
        for chunk in audio_stream:
            result = vad.process_chunk(chunk, timestamp_ms)
            if result.is_speech:
                # Process speech
    """

    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self._model = None
        self._model_loaded = False
        self._speech_started_at: Optional[int] = None
        self._silence_started_at: Optional[int] = None
        self._is_speaking = False
        
        # Ring buffer for speech padding
        self._pre_buffer: List[Tuple[bytes, int]] = []
        self._pre_buffer_ms = 0

    def _load_model(self) -> None:
        """Lazy-load the Silero VAD model."""
        if self._model_loaded:
            return
        
        try:
            import torch
            
            # Load Silero VAD from torch hub
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,  # Use PyTorch version
            )
            
            self._model = model
            self._get_speech_timestamps = utils[0]
            self._model_loaded = True
            logger.info("Silero VAD model loaded successfully")
            
        except ImportError:
            logger.warning(
                "PyTorch not available. Using energy-based VAD fallback. "
                "Install torch for better accuracy: pip install torch"
            )
            self._model = None
            self._model_loaded = True

    def process_chunk(
        self,
        audio_data: bytes,
        timestamp_ms: int,
    ) -> VADResult:
        """
        Process an audio chunk and detect speech.
        
        Args:
            audio_data: Raw PCM audio bytes (int16)
            timestamp_ms: Timestamp in milliseconds
        
        Returns:
            VADResult with speech detection info
        """
        self._load_model()
        
        # Convert bytes to numpy array
        samples = np.frombuffer(audio_data, dtype=np.int16)
        samples_float = samples.astype(np.float32) / 32768.0
        
        # Calculate energy for debugging/fallback
        energy_db = self._calculate_energy(samples)
        
        # Get speech probability
        if self._model is not None:
            probability = self._run_model(samples_float)
        else:
            # Fallback: energy-based VAD
            probability = self._energy_vad(energy_db)
        
        # Apply threshold
        is_speech_frame = probability >= self.config.threshold_for_mode
        
        # Apply smoothing
        is_speech = self._apply_smoothing(is_speech_frame, timestamp_ms)
        
        # Update pre-buffer for speech padding
        self._update_pre_buffer(audio_data, timestamp_ms)
        
        return VADResult(
            is_speech=is_speech,
            probability=probability,
            timestamp_ms=timestamp_ms,
            energy_db=energy_db,
        )

    def _run_model(self, samples: np.ndarray) -> float:
        """Run Silero VAD model on samples."""
        import torch
        
        # Silero expects (batch, samples) tensor
        tensor = torch.from_numpy(samples).unsqueeze(0)
        
        with torch.no_grad():
            speech_prob = self._model(tensor, self.config.sample_rate)
        
        return float(speech_prob.item())

    def _calculate_energy(self, samples: np.ndarray) -> float:
        """Calculate energy in dB."""
        if len(samples) == 0:
            return -100.0
        
        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        
        if rms > 0:
            return 20 * np.log10(rms / 32768.0)
        return -100.0

    def _energy_vad(self, energy_db: float) -> float:
        """Fallback energy-based VAD when Silero not available."""
        # Simple energy threshold
        # -40 dB is typical threshold for speech vs silence
        speech_threshold_db = -40.0
        silence_threshold_db = -50.0
        
        if energy_db > speech_threshold_db:
            return 0.9
        elif energy_db > silence_threshold_db:
            # Linear interpolation
            return 0.3 + 0.6 * (energy_db - silence_threshold_db) / (
                speech_threshold_db - silence_threshold_db
            )
        return 0.1

    def _apply_smoothing(self, is_speech_frame: bool, timestamp_ms: int) -> bool:
        """
        Apply temporal smoothing to avoid rapid on/off.
        
        - Speech must be detected for min_speech_duration_ms to start
        - Silence must last min_silence_duration_ms to end speech
        """
        if is_speech_frame:
            self._silence_started_at = None
            
            if not self._is_speaking:
                if self._speech_started_at is None:
                    self._speech_started_at = timestamp_ms
                
                speech_duration = timestamp_ms - self._speech_started_at
                if speech_duration >= self.config.min_speech_duration_ms:
                    self._is_speaking = True
                    logger.debug(f"Speech started at {timestamp_ms}ms")
        else:
            self._speech_started_at = None
            
            if self._is_speaking:
                if self._silence_started_at is None:
                    self._silence_started_at = timestamp_ms
                
                silence_duration = timestamp_ms - self._silence_started_at
                if silence_duration >= self.config.min_silence_duration_ms:
                    self._is_speaking = False
                    logger.debug(f"Speech ended at {timestamp_ms}ms")
        
        return self._is_speaking

    def _update_pre_buffer(self, audio_data: bytes, timestamp_ms: int) -> None:
        """Maintain a rolling buffer of recent audio for speech padding."""
        self._pre_buffer.append((audio_data, timestamp_ms))
        self._pre_buffer_ms += self.config.frame_duration_ms
        
        # Remove old data beyond padding window
        while self._pre_buffer_ms > self.config.speech_pad_ms * 2:
            _, _ = self._pre_buffer.pop(0)
            self._pre_buffer_ms -= self.config.frame_duration_ms

    def get_pre_speech_audio(self) -> bytes:
        """Get audio from before speech started (for padding)."""
        return b''.join(data for data, _ in self._pre_buffer[-10:])

    def reset(self) -> None:
        """Reset VAD state."""
        self._speech_started_at = None
        self._silence_started_at = None
        self._is_speaking = False
        self._pre_buffer.clear()
        self._pre_buffer_ms = 0

    @property
    def is_speaking(self) -> bool:
        """Check if speech is currently active."""
        return self._is_speaking


class SimpleVAD:
    """
    Simple energy-based VAD for environments without PyTorch.
    
    Uses zero-crossing rate and energy for basic speech detection.
    """

    def __init__(
        self,
        energy_threshold_db: float = -40.0,
        zcr_threshold: float = 0.1,
    ):
        self.energy_threshold_db = energy_threshold_db
        self.zcr_threshold = zcr_threshold

    def is_speech(self, audio_data: bytes) -> Tuple[bool, float]:
        """
        Detect if audio contains speech.
        
        Returns:
            Tuple of (is_speech, confidence)
        """
        samples = np.frombuffer(audio_data, dtype=np.int16)
        
        if len(samples) < 100:
            return False, 0.0
        
        # Calculate energy
        samples_float = samples.astype(np.float32)
        rms = np.sqrt(np.mean(samples_float ** 2))
        energy_db = 20 * np.log10(max(float(rms), 1) / 32768.0)
        
        # Calculate zero-crossing rate
        signs = np.sign(samples_float)
        zcr = float(np.mean(np.abs(np.diff(signs))) / 2)
        
        # Speech typically has moderate energy and ZCR
        energy_ok = energy_db > self.energy_threshold_db
        zcr_ok = zcr > self.zcr_threshold and zcr < 0.5
        
        # Energy alone is a strong indicator; ZCR boosts confidence
        is_speech = bool(energy_ok)
        if energy_ok and zcr_ok:
            confidence = 0.9
        elif energy_ok:
            confidence = 0.6
        else:
            confidence = 0.1
        
        return is_speech, confidence
