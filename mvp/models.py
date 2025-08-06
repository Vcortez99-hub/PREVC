from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Session(db.Model):
    """Modelo para sessões de processamento"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), nullable=False, default='uploading')  # uploading, processing, completed, error
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Arquivos enviados
    transcription_file = db.Column(db.String(255))
    screenshot_files = db.Column(db.Text)  # JSON list of filenames
    transcription_only_mode = db.Column(db.Boolean, default=False, nullable=False)
    
    # Resultados do processamento
    processed_actions = db.Column(db.Text)  # JSON
    ocr_results = db.Column(db.Text)  # JSON
    generated_documentation = db.Column(db.Text)
    
    # Metadados adicionais para histórico
    processing_time = db.Column(db.Float)  # Tempo total de processamento em segundos
    error_message = db.Column(db.Text)  # Mensagem de erro se houver
    files_count = db.Column(db.Integer, default=0)  # Número total de arquivos processados
    actions_count = db.Column(db.Integer, default=0)  # Número total de ações extraídas
    ai_config = db.Column(db.Text)  # Configurações de IA em JSON
    
    def to_dict(self):
        """Converte sessão para dicionário para API"""
        return {
            'id': self.id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'transcription_only_mode': self.transcription_only_mode,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'files_count': self.files_count,
            'actions_count': self.actions_count,
            'has_transcription': bool(self.transcription_file),
            'has_screenshots': bool(self.screenshot_files and self.screenshot_files != '[]'),
            'has_documentation': bool(self.generated_documentation)
        }
    
    def __repr__(self):
        return f'<Session {self.id}>'

class ProcessedDocument(db.Model):
    """Modelo for documentos processados"""
    __tablename__ = 'processed_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    format = db.Column(db.String(10), nullable=False)  # markdown, docx, pdf
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    session = db.relationship('Session', backref=db.backref('documents', lazy=True))
    
    def __repr__(self):
        return f'<ProcessedDocument {self.id}>'

class ProcessingLog(db.Model):
    """Modelo para logs detalhados de processamento"""
    __tablename__ = 'processing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('sessions.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR
    step = db.Column(db.String(50), nullable=False)  # upload, transcription, ocr, correlation, ai, export
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)  # JSON com detalhes adicionais
    
    session = db.relationship('Session', backref=db.backref('logs', lazy=True, order_by='ProcessingLog.timestamp'))
    
    def to_dict(self):
        """Converte log para dicionário para API"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'step': self.step,
            'message': self.message,
            'details': self.details
        }
    
    def __repr__(self):
        return f'<ProcessingLog {self.id} - {self.step}>'