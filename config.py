import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # MongoDB Atlas
    MONGODB_URI = os.getenv('MONGODB_URI')  # mongodb+srv://username:password@cluster.mongodb.net/
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'cashflow')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-1')
    GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-4-turbo-preview')
    
    # Twilio (WhatsApp)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')  # Format: whatsapp:+14155238886
    
    # Agent Configuration
    LIQUIDITY_ALERT_THRESHOLD_DAYS = 7  # Alert when cash runs out in 7 days
    LOW_STOCK_THRESHOLD = 10  # Alert when stock falls below this
    ANOMALY_THRESHOLD = 0.15  # Isolation Forest contamination rate
    
    # Business Logic
    DEFAULT_CURRENCY = 'INR'
    TIMEZONE = 'Asia/Kolkata'