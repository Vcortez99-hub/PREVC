#!/usr/bin/env python3
"""
Versão estável da aplicação Flask
Sem threading problemático, com tratamento robusto de erros
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback
import logging

# Configuração estável
from config_stable import config

# Imports MVP (com tratamento de erro)
try:
    from mvp.models import db, Session, ProcessedDocument, ProcessingLog
    from mvp.utils.logging_helper import SessionLogger
    from mvp.parsers.transcription import BasicTranscriptionParser
    from mvp.processors.ocr import BasicOCR
    from mvp.processors.correlator import BasicCorrelator
    from mvp.generators.ai_client import AIDocumentGenerator
    from mvp.generators.formatter import DocumentFormatter
except ImportError as e:
    logging.error(f"Erro ao importar módulos MVP: {e}")
    raise

def create_stable_app(config_name='stable'):
    """Criar aplicação ultra-estável"""
    app = Flask(__name__)
    
    # Configuração
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Criar tabelas
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database inicializado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao criar database: {e}")
            raise
    
    return app

# Criar aplicação
app = create_stable_app()

# Inicializar processadores (lazy loading para estabilidade)
_transcription_parser = None
_ocr_processor = None
_correlator = None
_formatter = None
_ai_generator = None

def get_transcription_parser():
    global _transcription_parser
    if _transcription_parser is None:
        _transcription_parser = BasicTranscriptionParser()
    return _transcription_parser

def get_ocr_processor():
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = BasicOCR()
    return _ocr_processor

def get_correlator():
    global _correlator
    if _correlator is None:
        _correlator = BasicCorrelator()
    return _correlator

def get_formatter():
    global _formatter
    if _formatter is None:
        _formatter = DocumentFormatter()
    return _formatter

def get_ai_generator(provider="openai", model="gpt-4", agent_type="rpa_general", custom_api_key=None):
    """Obter gerador AI com configuração segura"""
    try:
        api_key = custom_api_key if custom_api_key else app.config.get('OPENAI_API_KEY')
        
        if not api_key or api_key == 'your-openai-api-key-here':
            raise ValueError("API Key não configurada")
        
        return AIDocumentGenerator(
            api_key=api_key,
            provider=provider,
            model=model,
            agent_type=agent_type
        )
    except Exception as e:
        logging.error(f"Erro ao criar AI generator: {e}")
        raise

def allowed_file(filename, allowed_extensions):
    """Verificar arquivo permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Página inicial"""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Erro na página inicial: {e}")
        return "Erro interno", 500

@app.route('/upload', methods=['POST'])
def upload_files():
    """Upload com validação robusta"""
    try:
        # Verificar modo
        transcription_only_mode = request.form.get('transcription_only_mode', 'false').lower() == 'true'
        
        # Configurações AI
        ai_config = {
            'provider': request.form.get('aiProvider', 'openai'),
            'model': request.form.get('aiModel', 'gpt-4'),
            'agent_type': request.form.get('agentType', 'rpa_general'),
            'custom_api_key': request.form.get('aiToken', '').strip() or None
        }
        
        # Criar sessão
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id, 
            status='uploading', 
            transcription_only_mode=transcription_only_mode
        )
        session.ai_config = json.dumps(ai_config)
        
        uploaded_files = {
            'transcription': None,
            'screenshots': []
        }
        
        # Processar transcrição
        if 'transcription' in request.files:
            file = request.files['transcription']
            if file and file.filename and allowed_file(file.filename, app.config['ALLOWED_TRANSCRIPTION_EXTENSIONS']):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
                
                # Salvar com tratamento de erro
                try:
                    file.save(file_path)
                    uploaded_files['transcription'] = file_path
                    session.transcription_file = file_path
                except Exception as e:
                    logging.error(f"Erro ao salvar transcrição: {e}")
                    return jsonify({'error': 'Erro ao salvar arquivo de transcrição'}), 500
        
        # Processar screenshots
        screenshot_paths = []
        if not transcription_only_mode and 'screenshots' in request.files:
            files = request.files.getlist('screenshots')
            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{i}_{filename}")
                    
                    try:
                        file.save(file_path)
                        screenshot_paths.append(file_path)
                        uploaded_files['screenshots'].append(file_path)
                    except Exception as e:
                        logging.error(f"Erro ao salvar screenshot {i}: {e}")
        
        session.screenshot_files = json.dumps(screenshot_paths)
        
        # Validação
        if transcription_only_mode:
            if not uploaded_files['transcription']:
                return jsonify({'error': 'Arquivo de transcrição é obrigatório'}), 400
        else:
            if not uploaded_files['transcription'] and not uploaded_files['screenshots']:
                return jsonify({'error': 'Nenhum arquivo válido foi enviado'}), 400
        
        # Salvar sessão
        try:
            db.session.add(session)
            db.session.commit()
            logging.info(f"Sessão {session_id} criada com sucesso")
        except Exception as e:
            logging.error(f"Erro ao salvar sessão: {e}")
            return jsonify({'error': 'Erro interno ao criar sessão'}), 500
        
        return jsonify({
            'session_id': session_id,
            'status': 'uploaded',
            'transcription_only_mode': transcription_only_mode,
            'files_received': {
                'transcription': bool(uploaded_files['transcription']),
                'screenshots': len(uploaded_files['screenshots'])
            }
        })
        
    except Exception as e:
        logging.error(f"Erro no upload: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': 'Erro interno no upload'}), 500

@app.route('/process/<session_id>', methods=['POST'])
def process_session(session_id):
    """Processamento SÍNCRONO para estabilidade"""
    try:
        # Buscar sessão
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        if session.status != 'uploading':
            return jsonify({'error': f'Sessão em status inválido: {session.status}'}), 400
        
        # Atualizar status
        session.status = 'processing'
        db.session.commit()
        
        # Processar SINCRONAMENTE (sem threads para evitar problemas)
        result = process_session_sync(session_id)
        
        if result['success']:
            return jsonify({
                'session_id': session_id,
                'status': 'completed',
                'message': 'Processamento concluído com sucesso',
                'processing_time': result.get('processing_time', 0)
            })
        else:
            return jsonify({
                'session_id': session_id,
                'status': 'error',
                'error': result.get('error', 'Erro desconhecido')
            }), 500
        
    except Exception as e:
        logging.error(f"Erro ao processar sessão {session_id}: {e}")
        logging.error(traceback.format_exc())
        return jsonify({'error': 'Erro interno no processamento'}), 500

def process_session_sync(session_id):
    """Processamento síncrono robusto"""
    start_time = time.time()
    
    try:
        logging.info(f"Iniciando processamento síncrono da sessão {session_id}")
        
        session = Session.query.get(session_id)
        if not session:
            return {'success': False, 'error': 'Sessão não encontrada'}
        
        # 1. Processar transcrição
        actions = []
        if session.transcription_file and os.path.exists(session.transcription_file):
            try:
                parser = get_transcription_parser()
                transcription_result = parser.process_file(session.transcription_file)
                
                # Importar com tratamento seguro
                from mvp.parsers.transcription import TranscriptionSegment
                
                actions = parser.extract_actions([
                    TranscriptionSegment(
                        timestamp=seg['timestamp'],
                        speaker=seg['speaker'],
                        text=seg['text']
                    ) for seg in transcription_result['segments']
                ])
                
                session.processed_actions = json.dumps([
                    {
                        'action_type': action.action_type,
                        'element': action.element,
                        'sequence': action.sequence,
                        'timestamp': action.timestamp,
                        'speaker': action.speaker,
                        'confidence': action.confidence,
                        'raw_text': action.raw_text
                    } for action in actions
                ])
                
                logging.info(f"Transcrição processada: {len(actions)} ações extraídas")
                
            except Exception as e:
                logging.error(f"Erro no processamento de transcrição: {e}")
                session.status = 'error'
                session.error_message = f"Erro na transcrição: {str(e)}"
                db.session.commit()
                return {'success': False, 'error': str(e)}
        
        # 2. Processar OCR (se não for modo apenas transcrição)
        ocr_results = []
        if not session.transcription_only_mode and session.screenshot_files:
            try:
                screenshot_paths = json.loads(session.screenshot_files)
                ocr_processor = get_ocr_processor()
                
                for path in screenshot_paths:
                    if os.path.exists(path):
                        ocr_result = ocr_processor.extract_text(path)
                        ocr_results.append(ocr_result)
                
                session.ocr_results = json.dumps([
                    {
                        'image_path': result.original_image_path,
                        'extracted_text': result.extracted_text,
                        'confidence': result.confidence,
                        'ui_elements': [
                            {
                                'type': elem.type,
                                'text': elem.text,
                                'confidence': elem.confidence,
                                'context': elem.context
                            } for elem in result.ui_elements
                        ],
                        'processing_time': result.processing_time
                    } for result in ocr_results
                ])
                
                logging.info(f"OCR processado: {len(ocr_results)} imagens")
                
            except Exception as e:
                logging.error(f"Erro no processamento OCR: {e}")
                # OCR não é crítico, continuar sem ele
                session.ocr_results = json.dumps([])
        
        # 3. Correlação
        if actions or ocr_results:
            try:
                correlator = get_correlator()
                correlated_process = correlator.correlate_audio_visual(actions, ocr_results)
                correlated_process.session_id = session_id
                
                logging.info(f"Correlação concluída: {correlated_process.successfully_correlated} ações")
                
                # 4. Gerar documentação
                ai_config = json.loads(session.ai_config) if session.ai_config else {}
                
                ai_gen = get_ai_generator(
                    provider=ai_config.get('provider', 'openai'),
                    model=ai_config.get('model', 'gpt-4'),
                    agent_type=ai_config.get('agent_type', 'rpa_general'),
                    custom_api_key=ai_config.get('custom_api_key')
                )
                
                doc_result = ai_gen.generate_documentation(correlated_process)
                
                if doc_result.success:
                    session.generated_documentation = doc_result.content
                    
                    # Salvar documento
                    processed_doc = ProcessedDocument(
                        session_id=session_id,
                        content=doc_result.content,
                        format='markdown'
                    )
                    db.session.add(processed_doc)
                    
                    # Gerar Word
                    formatter = get_formatter()
                    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_documentation.docx")
                    
                    if formatter.format_as_docx(doc_result.content, output_path, doc_result.metadata):
                        processed_doc_word = ProcessedDocument(
                            session_id=session_id,
                            content=doc_result.content,
                            format='docx',
                            file_path=output_path
                        )
                        db.session.add(processed_doc_word)
                    
                    session.status = 'completed'
                    logging.info(f"Documentação gerada com sucesso para sessão {session_id}")
                    
                else:
                    session.status = 'error'
                    session.error_message = doc_result.error_message
                    logging.error(f"Erro na geração IA: {doc_result.error_message}")
                    return {'success': False, 'error': doc_result.error_message}
                
            except Exception as e:
                logging.error(f"Erro na correlação/IA: {e}")
                session.status = 'error'
                session.error_message = str(e)
                db.session.commit()
                return {'success': False, 'error': str(e)}
        else:
            session.status = 'error'
            session.error_message = "Nenhum dado válido para processar"
            logging.error("Nenhum dado válido encontrado")
            db.session.commit()
            return {'success': False, 'error': 'Nenhum dado válido'}
        
        # Finalizar
        end_time = time.time()
        processing_time = end_time - start_time
        session.processing_time = processing_time
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"Processamento da sessão {session_id} concluído em {processing_time:.2f}s")
        
        return {
            'success': True, 
            'processing_time': processing_time,
            'actions_count': len(actions),
            'ocr_count': len(ocr_results)
        }
        
    except Exception as e:
        logging.error(f"Erro crítico no processamento: {e}")
        logging.error(traceback.format_exc())
        
        # Atualizar status de erro
        try:
            session = Session.query.get(session_id)
            if session:
                session.status = 'error'
                session.error_message = str(e)
                session.processing_time = time.time() - start_time
                session.updated_at = datetime.utcnow()
                db.session.commit()
        except:
            pass
        
        return {'success': False, 'error': str(e)}

@app.route('/status/<session_id>')
def get_session_status(session_id):
    """Status da sessão"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        return jsonify({
            'session_id': session_id,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'error_message': session.error_message,
            'processing_time': session.processing_time
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter status: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/result/<session_id>')
def get_session_result(session_id):
    """Resultado da sessão"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        if session.status != 'completed':
            return jsonify({'error': f'Sessão não completada (status: {session.status})'}), 400
        
        return jsonify({
            'session_id': session_id,
            'status': session.status,
            'documentation': session.generated_documentation,
            'processing_time': session.processing_time
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter resultado: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/export/<session_id>/<format>')
def export_document(session_id, format):
    """Export de documento"""
    try:
        session = Session.query.get(session_id)
        if not session or session.status != 'completed':
            return jsonify({'error': 'Sessão não encontrada ou não completada'}), 404
        
        doc = ProcessedDocument.query.filter_by(
            session_id=session_id, 
            format=format
        ).first()
        
        if not doc:
            return jsonify({'error': f'Documento no formato {format} não encontrado'}), 404
        
        if format == 'docx' and doc.file_path and os.path.exists(doc.file_path):
            return send_file(
                doc.file_path,
                as_attachment=True,
                download_name=f"documentacao_rpa_{session_id}.docx"
            )
        elif format == 'markdown':
            return jsonify({'content': doc.content, 'format': 'markdown'})
        else:
            return jsonify({'error': 'Formato não disponível'}), 400
            
    except Exception as e:
        logging.error(f"Erro no export: {e}")
        return jsonify({'error': 'Erro interno no export'}), 500

@app.route('/health')
def health_check():
    """Health check"""
    try:
        # Teste básico do database
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0-stable'
        })
        
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logging.info("Iniciando aplicação estável...")
    app.run(
        host='localhost',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )