import openai
from config import Config
import tempfile
import os

openai.api_key = Config.OPENAI_API_KEY

class VoiceService:
    def __init__(self):
        self.model = Config.WHISPER_MODEL
    
    async def transcribe_audio(self, audio_file):
        """
        Transcribe audio file to text using OpenAI Whisper
        
        Args:
            audio_file: FileStorage object from Flask request
            
        Returns:
            str: Transcribed text
        """
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_file.save(temp_audio.name)
                temp_path = temp_audio.name
            
            # Transcribe using Whisper
            with open(temp_path, 'rb') as audio:
                transcript = openai.audio.transcriptions.create(
                    model=self.model,
                    file=audio,
                    language='hi'  # Hindi/Hinglish support
                )
            
            # Cleanup
            os.unlink(temp_path)
            
            return transcript.text
            
        except Exception as e:
            raise Exception(f"Voice transcription failed: {str(e)}")
    
    async def transcribe_audio_stream(self, audio_data):
        """
        Transcribe audio from byte stream
        
        Args:
            audio_data: bytes - audio data
            
        Returns:
            str: Transcribed text
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name
            
            with open(temp_path, 'rb') as audio:
                transcript = openai.audio.transcriptions.create(
                    model=self.model,
                    file=audio,
                    language='hi'
                )
            
            os.unlink(temp_path)
            return transcript.text
            
        except Exception as e:
            raise Exception(f"Voice transcription failed: {str(e)}")