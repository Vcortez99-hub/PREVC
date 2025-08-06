"""
Configurações otimizadas para estabilidade
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class StableConfig:
    """Configurações ultra-estáveis"""
    
    # Flask básico
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ultra-stable-secret-key-2025'
    FLASK_ENV = 'production'  # Sempre produção para estabilidade
    DEBUG = False             # Sem debug para evitar problemas
    TESTING = False
    
    # Threading otimizado
    THREADED = True
    USE_RELOADER = False      # Nunca auto-reload
    PROCESSES = 1             # Single process apenas
    
    # Database com pool otimizado
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///mvp_stable.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {
            'check_same_thread': False,
            'timeout': 30
        }
    }
    
    # Upload com limites conservadores
    UPLOAD_FOLDER = 'data/uploads'
    OUTPUT_FOLDER = 'data/outputs'
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB max
    
    # Extensões permitidas
    ALLOWED_TRANSCRIPTION_EXTENSIONS = {'txt', 'vtt'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # API Keys
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Processamento otimizado
    MAX_PROCESSING_TIME = 300      # 5 minutos max
    MAX_CONCURRENT_SESSIONS = 1    # Uma sessão por vez
    SESSION_TIMEOUT = 1800         # 30 minutos
    
    # Timeouts para estabilidade
    REQUEST_TIMEOUT = 30
    AI_TIMEOUT = 60
    OCR_TIMEOUT = 30
    
    # Logging seguro
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app_stable.log'
    
    @staticmethod
    def init_app(app):
        """Inicializar com configurações seguras"""
        # Criar diretórios
        os.makedirs(StableConfig.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(StableConfig.OUTPUT_FOLDER, exist_ok=True)
        os.makedirs('data/samples', exist_ok=True)
        
        # Configurar logging seguro
        import logging
        logging.basicConfig(
            level=getattr(logging, StableConfig.LOG_LEVEL),
            format=StableConfig.LOG_FORMAT,
            handlers=[
                logging.FileHandler(StableConfig.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Configurações específicas do Flask
        app.config.update({
            'SEND_FILE_MAX_AGE_DEFAULT': 3600,
            'PERMANENT_SESSION_LIFETIME': StableConfig.SESSION_TIMEOUT,
            'SESSION_COOKIE_SECURE': False,    # HTTP local
            'SESSION_COOKIE_HTTPONLY': True,
            'WTF_CSRF_ENABLED': False,         # Desabilitar CSRF para simplicidade
        })

# Configuração padrão para estabilidade
config = {
    'default': StableConfig,
    'stable': StableConfig,
    'production': StableConfig
}