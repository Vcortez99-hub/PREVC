"""
Helper para logging detalhado de sessões
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..models import db, ProcessingLog

class SessionLogger:
    """Logger para sessões de processamento"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
    
    def log(self, level: str, step: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Adiciona um log para a sessão
        
        Args:
            level: INFO, WARNING, ERROR
            step: upload, transcription, ocr, correlation, ai, export
            message: Mensagem do log
            details: Detalhes adicionais em formato dict
        """
        try:
            log_entry = ProcessingLog(
                session_id=self.session_id,
                level=level.upper(),
                step=step,
                message=message,
                details=json.dumps(details) if details else None
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            # Não queremos que erros de logging quebrem o processamento
            print(f"Erro ao salvar log: {e}")
    
    def info(self, step: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de nível INFO"""
        self.log('INFO', step, message, details)
    
    def warning(self, step: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de nível WARNING"""
        self.log('WARNING', step, message, details)
    
    def error(self, step: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de nível ERROR"""
        self.log('ERROR', step, message, details)
    
    def step_start(self, step: str, message: str):
        """Marca o início de uma etapa"""
        self.info(step, f"🚀 Iniciando: {message}")
    
    def step_progress(self, step: str, message: str, progress: Optional[int] = None):
        """Atualiza o progresso de uma etapa"""
        details = {'progress': progress} if progress is not None else None
        self.info(step, f"📊 {message}", details)
    
    def step_complete(self, step: str, message: str, stats: Optional[Dict[str, Any]] = None):
        """Marca a conclusão de uma etapa"""
        self.info(step, f"✅ Concluído: {message}", stats)
    
    def step_error(self, step: str, message: str, error: Exception):
        """Marca erro em uma etapa"""
        details = {
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        self.error(step, f"❌ Erro: {message}", details)