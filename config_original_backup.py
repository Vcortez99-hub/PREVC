import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações base da aplicação"""
    
    # Configurações Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configurações de banco de dados
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///mvp.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'data/uploads'
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or 'data/outputs'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    
    # Extensões permitidas
    ALLOWED_TRANSCRIPTION_EXTENSIONS = {'txt', 'vtt'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Configurações OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Configurações OCR
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD')  # Caminho para tesseract se necessário
    
    # Configurações de processamento
    MAX_PROCESSING_TIME = int(os.environ.get('MAX_PROCESSING_TIME', 600))  # 10 minutos
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 3))
    
    # Configurações de segurança
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hora
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        # Criar diretórios necessários
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        os.makedirs('data/samples', exist_ok=True)

class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    DEBUG = False
    TESTING = False
    
    # Em produção, usar configurações mais restritivas
    MAX_CONTENT_LENGTH = 20971520  # 20MB
    MAX_CONCURRENT_SESSIONS = 2
    SESSION_TIMEOUT = 1800  # 30 minutos

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = 'tests/uploads'
    OUTPUT_FOLDER = 'tests/outputs'

# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}