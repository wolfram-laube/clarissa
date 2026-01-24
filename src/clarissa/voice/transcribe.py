"""
Speech-to-Text Module - Integrates with OpenAI Whisper API.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    text: str
    language: str = "en"
    confidence: float = 1.0
    duration_ms: int = 0


DOMAIN_VOCABULARY = """
Reservoir simulation terms: permeability, porosity, water saturation, 
oil saturation, pressure, BHP, bottomhole pressure, OOIP, original oil in place,
waterflood, injector, producer, PROD1, INJ1, INJ2, INJ3, INJ4,
millidarcy, mD, psi, bar, bbl/day, m3/day, STB, 
FOPT, FOPR, FWPT, FWPR, FWCT, water cut,
layer, grid, cell, timestep, schedule, deck, ECLIPSE
"""


class WhisperTranscriber:
    """Transcribe audio using OpenAI Whisper API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "en"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.language = language
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    async def transcribe(
        self,
        audio_data: bytes,
        prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio data to text."""
        import openai
        
        effective_prompt = prompt or DOMAIN_VOCABULARY
        
        # TODO: Implement actual API call
        raise NotImplementedError("Whisper integration not yet implemented")


class LocalWhisperTranscriber:
    """Transcribe using local Whisper model (air-gapped deployments)."""
    
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cuda",
        compute_type: str = "float16"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    def _load_model(self):
        """Lazy-load Whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model
    
    async def transcribe(self, audio_path: str) -> TranscriptionResult:
        """Transcribe audio file using local model."""
        model = self._load_model()
        segments, info = model.transcribe(audio_path, language="en")
        text = " ".join(segment.text for segment in segments)
        
        return TranscriptionResult(
            text=text.strip(),
            language=info.language,
            confidence=info.language_probability
        )
