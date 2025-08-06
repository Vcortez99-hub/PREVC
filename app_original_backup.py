from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from threading import Thread
import traceback

# Importações dos módulos MVP
from config import config
from mvp.models import db, Session, ProcessedDocument, ProcessingLog
from mvp.utils.logging_helper import SessionLogger
from mvp.parsers.transcription import BasicTranscriptionParser
from mvp.processors.ocr import BasicOCR
from mvp.processors.correlator import BasicCorrelator
from mvp.generators.ai_client import AIDocumentGenerator
from mvp.generators.formatter import DocumentFormatter

# Importações MVP_02 - Enhanced features
from mvp.processors.enhanced_ocr import EnhancedOCRProcessor
from mvp.processors.temporal_correlator import AdvancedTemporalCorrelator
from mvp.generators.domain_templates import DomainTemplateManager, ProcessDomain
from mvp.validators.document_validator import DocumentValidator

def create_app(config_name=None):
    """Factory function para criar aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Criar tabelas
    with app.app_context():
        db.create_all()
    
    return app

# Criar aplicação
app = create_app()

# Inicializar processadores básicos
transcription_parser = BasicTranscriptionParser()
ocr_processor = BasicOCR()
correlator = BasicCorrelator()
formatter = DocumentFormatter()

# Inicializar processadores MVP_02 - Enhanced
enhanced_ocr_processor = EnhancedOCRProcessor()
advanced_correlator = AdvancedTemporalCorrelator()
domain_manager = DomainTemplateManager()
document_validator = DocumentValidator()

# Inicializar cliente AI (será feito sob demanda para verificar API key)
ai_generator = None

def get_ai_generator(provider="openai", model="gpt-4", agent_type="rpa_general", custom_api_key=None):
    """Obtém gerador AI (lazy initialization)"""
    global ai_generator
    
    # Usar API key customizada se fornecida, senão usar a padrão
    api_key = custom_api_key if custom_api_key else app.config.get('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your-openai-api-key-here':
        raise ValueError("API Key não configurada. Por favor, configure sua chave ou forneça uma chave personalizada.")
    
    # Sempre criar nova instância se parâmetros mudaram
    ai_generator = AIDocumentGenerator(
        api_key=api_key,
        provider=provider,
        model=model,
        agent_type=agent_type
    )
    
    return ai_generator

def allowed_file(filename, allowed_extensions):
    """Verifica se arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/history-page')
def history_page():
    """Página do histórico"""
    return render_template('history.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Endpoint para upload de arquivos"""
    try:
        # Verificar se é modo apenas transcrição
        transcription_only_mode = request.form.get('transcription_only_mode', 'false').lower() == 'true'
        
        # Capturar configurações de IA
        ai_config = {
            'provider': request.form.get('aiProvider', 'openai'),
            'model': request.form.get('aiModel', 'gpt-4'),
            'agent_type': request.form.get('agentType', 'rpa_general'),
            'custom_api_key': request.form.get('aiToken', '').strip() or None
        }
        
        # Criar nova sessão
        session_id = str(uuid.uuid4())
        session = Session(id=session_id, status='uploading', transcription_only_mode=transcription_only_mode)
        
        # Salvar configurações de IA na sessão (como JSON)
        session.ai_config = json.dumps(ai_config)
        
        uploaded_files = {
            'transcription': None,
            'screenshots': []
        }
        
        # Processar arquivo de transcrição
        if 'transcription' in request.files:
            file = request.files['transcription']
            if file and file.filename and allowed_file(file.filename, app.config['ALLOWED_TRANSCRIPTION_EXTENSIONS']):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
                file.save(file_path)
                uploaded_files['transcription'] = file_path
                session.transcription_file = file_path
        
        # Processar screenshots (apenas se não for modo apenas transcrição)
        screenshot_paths = []
        if not transcription_only_mode and 'screenshots' in request.files:
            files = request.files.getlist('screenshots')
            for i, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{i}_{filename}")
                    file.save(file_path)
                    screenshot_paths.append(file_path)
                    uploaded_files['screenshots'].append(file_path)
        
        session.screenshot_files = json.dumps(screenshot_paths)
        
        # Validação baseada no modo
        if transcription_only_mode:
            # No modo apenas transcrição, só precisa da transcrição
            if not uploaded_files['transcription']:
                return jsonify({'error': 'Arquivo de transcrição é obrigatório'}), 400
        else:
            # No modo normal, precisa de pelo menos um arquivo
            if not uploaded_files['transcription'] and not uploaded_files['screenshots']:
                return jsonify({'error': 'Nenhum arquivo válido foi enviado'}), 400
        
        # Salvar sessão no banco
        db.session.add(session)
        db.session.commit()
        
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
        app.logger.error(f"Erro no upload: {str(e)}")
        return jsonify({'error': 'Erro interno no upload'}), 500

@app.route('/process/<session_id>', methods=['POST'])
def process_session(session_id):
    """Inicia processamento básico de uma sessão"""
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
        
        # Iniciar processamento em thread separada
        thread = Thread(target=process_session_async, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'session_id': session_id,
            'status': 'processing',
            'message': 'Processamento iniciado'
        }), 202
        
    except Exception as e:
        app.logger.error(f"Erro ao iniciar processamento: {str(e)}")
        return jsonify({'error': 'Erro interno no processamento'}), 500

@app.route('/process-enhanced/<session_id>', methods=['POST'])
def process_session_enhanced(session_id):
    """Inicia processamento aprimorado (MVP_02) de uma sessão"""
    try:
        # Buscar sessão
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        if session.status != 'uploading':
            return jsonify({'error': f'Sessão em status inválido: {session.status}'}), 400
        
        # Atualizar status
        session.status = 'processing_enhanced'
        db.session.commit()
        
        # Iniciar processamento aprimorado em thread separada
        thread = Thread(target=process_session_enhanced_async, args=(session_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'session_id': session_id,
            'status': 'processing_enhanced',
            'message': 'Processamento aprimorado iniciado (MVP_02)'
        }), 202
        
    except Exception as e:
        app.logger.error(f"Erro ao iniciar processamento aprimorado: {str(e)}")
        return jsonify({'error': 'Erro interno no processamento'}), 500

def process_session_async(session_id):
    """Processa sessão de forma assíncrona"""
    with app.app_context():
        start_time = time.time()
        session_logger = SessionLogger(session_id)
        
        try:
            session_logger.step_start('processing', f'Processamento da sessão {session_id}')
            app.logger.info(f"🚀 Iniciando processamento da sessão {session_id}")
            
            session = Session.query.get(session_id)
            if not session:
                session_logger.error('processing', 'Sessão não encontrada', {'session_id': session_id})
                app.logger.error(f"❌ Sessão {session_id} não encontrada")
                return
            
            # 1. Processar transcrição
            session_logger.step_start('transcription', 'Processamento de transcrição')
            app.logger.info(f"📝 Processando transcrição para sessão {session_id}")
            actions = []
            
            if session.transcription_file and os.path.exists(session.transcription_file):
                session_logger.step_progress('transcription', f'Arquivo encontrado: {os.path.basename(session.transcription_file)}')
                app.logger.info(f"📄 Arquivo de transcrição encontrado: {session.transcription_file}")
                
                try:
                    transcription_result = transcription_parser.process_file(session.transcription_file)
                    segments_count = len(transcription_result.get('segments', []))
                    session_logger.step_progress('transcription', f'Arquivo processado: {segments_count} segmentos')
                    app.logger.info(f"✅ Transcrição processada: {segments_count} segmentos")
                    
                    # Importar TranscriptionSegment corretamente
                    from mvp.parsers.transcription import TranscriptionSegment
                    
                    actions = transcription_parser.extract_actions([
                        TranscriptionSegment(
                            timestamp=seg['timestamp'],
                            speaker=seg['speaker'],
                            text=seg['text']
                        ) for seg in transcription_result['segments']
                    ])
                    
                    session_logger.step_complete('transcription', 'Transcrição processada com sucesso', {
                        'segments_count': segments_count,
                        'actions_count': len(actions),
                        'speakers': transcription_result.get('summary', {}).get('speakers', [])
                    })
                    
                except Exception as transcription_error:
                    session_logger.step_error('transcription', 'Falha no processamento da transcrição', transcription_error)
                    raise transcription_error
                
                # Salvar resultado da transcrição
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
            
            # 2. Processar screenshots (apenas se não for modo apenas transcrição)
            session_logger.step_start('ocr', 'Processamento de OCR')
            ocr_results = []
            
            if session.transcription_only_mode:
                session_logger.step_progress('ocr', 'Modo apenas transcrição - OCR pulado')
                app.logger.info(f"📝 Modo apenas transcrição ativado - pulando processamento de screenshots")
                session_logger.step_complete('ocr', 'OCR pulado (modo apenas transcrição)', {'mode': 'transcription_only'})
            else:
                session_logger.step_progress('ocr', 'Iniciando processamento de screenshots')
                app.logger.info(f"🖼️ Processando screenshots para sessão {session_id}")
                
                if session.screenshot_files:
                    screenshot_paths = json.loads(session.screenshot_files)
                    session_logger.step_progress('ocr', f'{len(screenshot_paths)} screenshots encontrados')
                    app.logger.info(f"📸 {len(screenshot_paths)} screenshots encontrados")
                    
                    successful_ocr = 0
                    failed_ocr = 0
                    
                    for i, path in enumerate(screenshot_paths):
                        if os.path.exists(path):
                            session_logger.step_progress('ocr', f'Processando screenshot {i+1}/{len(screenshot_paths)}')
                            app.logger.info(f"🔍 Processando screenshot {i+1}/{len(screenshot_paths)}: {os.path.basename(path)}")
                            
                            try:
                                ocr_result = ocr_processor.extract_text(path)
                                ocr_results.append(ocr_result)
                                successful_ocr += 1
                                session_logger.step_progress('ocr', f'OCR concluído para {os.path.basename(path)}: {len(ocr_result.extracted_text)} caracteres')
                                app.logger.info(f"✅ OCR concluído para {os.path.basename(path)}: {len(ocr_result.extracted_text)} caracteres extraídos")
                            except Exception as ocr_error:
                                failed_ocr += 1
                                session_logger.warning('ocr', f'Erro no OCR para {os.path.basename(path)}', {'error': str(ocr_error)})
                                app.logger.error(f"❌ Erro no OCR para {path}: {ocr_error}")
                        else:
                            failed_ocr += 1
                            session_logger.warning('ocr', f'Arquivo não encontrado: {os.path.basename(path)}')
                            app.logger.warning(f"⚠️ Arquivo não encontrado: {path}")
                    
                    session_logger.step_complete('ocr', 'Processamento de screenshots concluído', {
                        'total_screenshots': len(screenshot_paths),
                        'successful_ocr': successful_ocr,
                        'failed_ocr': failed_ocr,
                        'total_results': len(ocr_results)
                    })
                    app.logger.info(f"✅ Processamento de screenshots concluído: {len(ocr_results)} resultados")
                else:
                    session_logger.step_complete('ocr', 'Nenhum screenshot encontrado', {'screenshot_count': 0})
                    app.logger.info(f"📸 Nenhum screenshot encontrado")
            
            # Salvar resultados OCR (mesmo que vazio no modo apenas transcrição)
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
            
            # 3. Correlacionar dados
            session_logger.step_start('correlation', 'Correlação áudio-visual')
            app.logger.info(f"🔗 Correlacionando dados para sessão {session_id}")
            
            if actions or ocr_results:
                session_logger.step_progress('correlation', f'Correlacionando {len(actions)} ações com {len(ocr_results)} resultados OCR')
                app.logger.info(f"📊 Correlacionando {len(actions)} ações com {len(ocr_results)} resultados OCR")
                
                try:
                    correlated_process = correlator.correlate_audio_visual(actions, ocr_results)
                    correlated_process.session_id = session_id
                    
                    session_logger.step_complete('correlation', 'Correlação concluída', {
                        'total_actions': correlated_process.total_actions,
                        'successfully_correlated': correlated_process.successfully_correlated,
                        'correlation_quality': correlated_process.correlation_quality
                    })
                    app.logger.info(f"✅ Correlação concluída: {correlated_process.successfully_correlated} ações correlacionadas")
                    
                except Exception as correlation_error:
                    session_logger.step_error('correlation', 'Falha na correlação', correlation_error)
                    raise correlation_error
                
                # 4. Gerar documentação com IA
                session_logger.step_start('ai', 'Geração de documentação com IA')
                app.logger.info(f"🤖 Iniciando geração de documentação com IA para sessão {session_id}")
                
                try:
                    # Carregar configurações de IA da sessão
                    ai_config = json.loads(session.ai_config) if session.ai_config else {}
                    
                    ai_gen = get_ai_generator(
                        provider=ai_config.get('provider', 'openai'),
                        model=ai_config.get('model', 'gpt-4'),
                        agent_type=ai_config.get('agent_type', 'rpa_general'),
                        custom_api_key=ai_config.get('custom_api_key')
                    )
                    session_logger.step_progress('ai', f'Cliente IA inicializado - Provedor: {ai_config.get("provider", "openai")}, Agente: {ai_config.get("agent_type", "rpa_general")}')
                    app.logger.info(f"✅ Cliente IA inicializado com {ai_config.get('provider', 'openai')} usando agente {ai_config.get('agent_type', 'rpa_general')}")
                    
                    session_logger.step_progress('ai', 'Gerando documentação...')
                    doc_result = ai_gen.generate_documentation(correlated_process)
                    
                    if doc_result.success:
                        session_logger.step_complete('ai', 'Documentação gerada com sucesso', {
                            'content_length': len(doc_result.content),
                            'token_usage': doc_result.token_usage
                        })
                        app.logger.info(f"✅ Documentação gerada: {len(doc_result.content)} caracteres")
                    else:
                        session_logger.step_error('ai', f'Falha na geração: {doc_result.error_message}', Exception(doc_result.error_message))
                        
                except Exception as ai_error:
                    session_logger.step_error('ai', 'Erro na geração de documentação', ai_error)
                    app.logger.error(f"❌ Erro na geração de documentação: {ai_error}")
                    raise ai_error
                
                if doc_result.success:
                    # Salvar documentação gerada
                    session.generated_documentation = doc_result.content
                    
                    # Criar documento processado
                    processed_doc = ProcessedDocument(
                        session_id=session_id,
                        content=doc_result.content,
                        format='markdown'
                    )
                    db.session.add(processed_doc)
                    
                    # 5. Exportar documentos
                    session_logger.step_start('export', 'Exportação de documentos')
                    
                    # Gerar arquivo Word
                    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{session_id}_documentation.docx")
                    if formatter.format_as_docx(doc_result.content, output_path, doc_result.metadata):
                        processed_doc_word = ProcessedDocument(
                            session_id=session_id,
                            content=doc_result.content,
                            format='docx',
                            file_path=output_path
                        )
                        db.session.add(processed_doc_word)
                        session_logger.step_complete('export', 'Documento Word gerado', {'file_path': output_path})
                        app.logger.info(f"📄 Documento Word gerado: {output_path}")
                    else:
                        session_logger.warning('export', 'Falha na geração do documento Word')
                    
                    session.status = 'completed'
                    
                    # Calcular estatísticas finais
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    # Atualizar sessão com estatísticas
                    session.processing_time = processing_time
                    session.actions_count = len(actions)
                    session.files_count = (1 if session.transcription_file else 0) + len(ocr_results)
                    
                    session_logger.step_complete('processing', 'Processamento concluído com sucesso', {
                        'processing_time': f"{processing_time:.2f}s",
                        'total_actions': len(actions),
                        'total_files': session.files_count,
                        'status': 'completed'
                    })
                    app.logger.info(f"🎉 Processamento da sessão {session_id} concluído em {processing_time:.2f}s")
                    
                else:
                    session.status = 'error'
                    session.error_message = doc_result.error_message
                    session_logger.step_error('processing', f"Erro na geração IA: {doc_result.error_message}", Exception(doc_result.error_message))
                    app.logger.error(f"Erro na geração IA: {doc_result.error_message}")
            
            else:
                session.status = 'error'
                session.error_message = "Nenhum dado válido para processar"
                session_logger.step_error('processing', "Nenhum dado válido para processar", Exception("No valid data"))
                app.logger.error("Nenhum dado válido para processar")
            
            session.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            # Marcar sessão como erro
            session = Session.query.get(session_id)
            if session:
                end_time = time.time()
                processing_time = end_time - start_time
                
                session.status = 'error'
                session.error_message = str(e)
                session.processing_time = processing_time
                session.updated_at = datetime.utcnow()
                db.session.commit()
                
                session_logger.step_error('processing', f'Erro crítico no processamento', e)
                app.logger.error(f"❌ Erro crítico no processamento da sessão {session_id}: {str(e)}")
                app.logger.error(traceback.format_exc())

def process_session_enhanced_async(session_id):
    """Processa sessão com funcionalidades aprimoradas (MVP_02)"""
    with app.app_context():
        try:
            session = Session.query.get(session_id)
            if not session:
                return
            
            # 1. Processar transcrição (igual ao básico)
            actions = []
            if session.transcription_file and os.path.exists(session.transcription_file):
                transcription_result = transcription_parser.process_file(session.transcription_file)
                # Importar TranscriptionSegment corretamente
                from mvp.parsers.transcription import TranscriptionSegment
                
                actions = transcription_parser.extract_actions([
                    TranscriptionSegment(
                        timestamp=seg['timestamp'],
                        speaker=seg['speaker'],
                        text=seg['text']
                    ) for seg in transcription_result['segments']
                ])
                
                # Salvar resultado da transcrição
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
            
            # 2. Processar screenshots com OCR aprimorado
            ocr_results = []
            enhanced_ocr_results = []
            if session.screenshot_files:
                screenshot_paths = json.loads(session.screenshot_files)
                for path in screenshot_paths:
                    if os.path.exists(path):
                        # Usar OCR aprimorado para melhor precisão
                        enhanced_result = enhanced_ocr_processor.process_image_enhanced(path)
                        enhanced_ocr_results.append(enhanced_result)
                        
                        # Converter para formato compatível com correlator básico
                        basic_result = ocr_processor.OCRResult(
                            original_image_path=enhanced_result.original_image_path,
                            extracted_text=enhanced_result.extracted_text,
                            confidence=enhanced_result.confidence,
                            ui_elements=enhanced_result.ui_elements,
                            processing_time=enhanced_result.processing_time,
                            preprocessing_applied=enhanced_result.preprocessing_applied
                        )
                        ocr_results.append(basic_result)
                
                # Salvar resultados OCR aprimorados
                session.ocr_results = json.dumps([
                    {
                        'image_path': result.original_image_path,
                        'extracted_text': result.extracted_text,
                        'confidence': result.confidence,
                        'engine_used': result.engine_used,
                        'ui_elements': [
                            {
                                'type': elem.type,
                                'text': elem.text,
                                'confidence': elem.confidence,
                                'context': elem.context
                            } for elem in result.ui_elements
                        ],
                        'processing_time': result.processing_time,
                        'quality_metrics': result.quality_metrics
                    } for result in enhanced_ocr_results
                ])
            
            # 3. Correlação avançada com análise temporal
            if actions or ocr_results:
                # Usar correlador avançado
                correlated_process = advanced_correlator.correlate_with_temporal_analysis(
                    actions, ocr_results
                )
                correlated_process.session_id = session_id
                
                # 4. Identificar domínio do processo
                transcription_text = " ".join([action.raw_text for action in actions])
                ui_elements = []
                for result in enhanced_ocr_results:
                    ui_elements.extend([elem.text for elem in result.ui_elements])
                
                domain = domain_manager.identify_domain(
                    transcription_text, ui_elements, [action.action_type for action in actions]
                )
                
                # 5. Gerar documentação com template específico do domínio
                # Carregar configurações de IA da sessão
                ai_config = json.loads(session.ai_config) if session.ai_config else {}
                
                ai_gen = get_ai_generator(
                    provider=ai_config.get('provider', 'openai'),
                    model=ai_config.get('model', 'gpt-4'),
                    agent_type=ai_config.get('agent_type', 'rpa_general'),
                    custom_api_key=ai_config.get('custom_api_key')
                )
                
                # Obter template específico do domínio
                context_data = {
                    'system_name': 'Sistema identificado',
                    'process_name': f'Processo {domain.value}',
                    'detailed_steps': [
                        {
                            'action': event.action.action_type,
                            'element': event.action.element,
                            'description': event.action.raw_text
                        } for event in correlated_process.correlated_events
                    ]
                }
                
                # Gerar documentação usando template do domínio
                template_documentation = domain_manager.generate_documentation_with_template(
                    domain, context_data
                )
                
                # Usar prompt aprimorado para IA
                enhanced_prompt = domain_manager.get_enhanced_prompt_for_domain(
                    domain, ai_gen.base_prompt
                )
                
                # Gerar com IA usando contexto aprimorado
                doc_result = ai_gen.generate_documentation(
                    correlated_process, 
                    custom_prompt=enhanced_prompt,
                    template_base=template_documentation
                )
                
                if doc_result.success:
                    # 6. Validar documentação gerada
                    validation_report = document_validator.validate_documentation(
                        doc_result.content, correlated_process, domain
                    )
                    
                    # Aplicar correções automáticas se possível
                    final_documentation = document_validator.apply_auto_fixes(
                        doc_result.content, validation_report
                    )
                    
                    # Salvar documentação com validações
                    session.generated_documentation = final_documentation
                    
                    # Salvar relatório de validação
                    validation_path = os.path.join(
                        app.config['OUTPUT_FOLDER'], 
                        f"{session_id}_validation_report.json"
                    )
                    document_validator.export_validation_report(validation_report, validation_path)
                    
                    # Criar documento processado
                    processed_doc = ProcessedDocument(
                        session_id=session_id,
                        content=final_documentation,
                        format='markdown'
                    )
                    db.session.add(processed_doc)
                    
                    # Gerar arquivo Word
                    output_path = os.path.join(
                        app.config['OUTPUT_FOLDER'], 
                        f"{session_id}_documentation_enhanced.docx"
                    )
                    enhanced_metadata = {
                        **doc_result.metadata,
                        'domain': domain.value,
                        'validation_score': validation_report.overall_score,
                        'processing_method': 'enhanced_mvp_02'
                    }
                    
                    if formatter.format_as_docx(final_documentation, output_path, enhanced_metadata):
                        processed_doc_word = ProcessedDocument(
                            session_id=session_id,
                            content=final_documentation,
                            format='docx',
                            file_path=output_path
                        )
                        db.session.add(processed_doc_word)
                    
                    session.status = 'completed_enhanced'
                else:
                    session.status = 'error'
                    app.logger.error(f"Erro na geração IA aprimorada: {doc_result.error_message}")
            
            else:
                session.status = 'error'
                app.logger.error("Nenhum dado válido para processar (enhanced)")
            
            session.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            # Marcar sessão como erro
            session.status = 'error'
            session.updated_at = datetime.utcnow()
            db.session.commit()
            app.logger.error(f"Erro no processamento assíncrono aprimorado: {str(e)}")
            app.logger.error(traceback.format_exc())

@app.route('/status/<session_id>')
def get_session_status(session_id):
    """Obtém status de uma sessão"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        response = {
            'session_id': session_id,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        }
        
        # Adicionar informações extras baseadas no status
        if session.status in ['completed', 'completed_enhanced']:
            response['documents_available'] = len(session.documents)
            response['has_documentation'] = bool(session.generated_documentation)
            response['is_enhanced'] = session.status == 'completed_enhanced'
            
            # Se é processamento aprimorado, adicionar info do domínio
            if session.status == 'completed_enhanced':
                validation_path = os.path.join(
                    app.config['OUTPUT_FOLDER'], 
                    f"{session_id}_validation_report.json"
                )
                if os.path.exists(validation_path):
                    response['has_validation_report'] = True
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Erro ao obter status: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/result/<session_id>')
def get_session_result(session_id):
    """Obtém resultado de uma sessão processada"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        if session.status not in ['completed', 'completed_enhanced']:
            return jsonify({'error': f'Sessão não completada (status: {session.status})'}), 400
        
        # Carregar dados processados
        processed_actions = json.loads(session.processed_actions) if session.processed_actions else []
        ocr_results = json.loads(session.ocr_results) if session.ocr_results else []
        
        return jsonify({
            'session_id': session_id,
            'status': session.status,
            'documentation': session.generated_documentation,
            'actions': processed_actions,
            'ocr_results': ocr_results,
            'documents': [
                {
                    'format': doc.format,
                    'created_at': doc.created_at.isoformat(),
                    'has_file': bool(doc.file_path)
                } for doc in session.documents
            ]
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter resultado: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/export/<session_id>/<format>')
def export_document(session_id, format):
    """Exporta documento em formato específico"""
    try:
        session = Session.query.get(session_id)
        if not session or session.status not in ['completed', 'completed_enhanced']:
            return jsonify({'error': 'Sessão não encontrada ou não completada'}), 404
        
        # Buscar documento no formato solicitado
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
                download_name=f"documentacao_rpa_{session_id}.docx",
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        
        elif format == 'markdown':
            return jsonify({'content': doc.content, 'format': 'markdown'})
        
        else:
            return jsonify({'error': 'Formato não disponível para download'}), 400
            
    except Exception as e:
        app.logger.error(f"Erro no export: {str(e)}")
        return jsonify({'error': 'Erro interno no export'}), 500

@app.route('/review/<session_id>')
def review_session(session_id):
    """Página de revisão de uma sessão"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return "Sessão não encontrada", 404
        
        return render_template('review.html', session=session)
        
    except Exception as e:
        app.logger.error(f"Erro na página de revisão: {str(e)}")
        return "Erro interno", 500

@app.route('/validation/<session_id>')
def get_validation_report(session_id):
    """Obtém relatório de validação para sessão processada com MVP_02"""
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        # Verificar se existe relatório de validação
        validation_path = os.path.join(
            app.config['OUTPUT_FOLDER'], 
            f"{session_id}_validation_report.json"
        )
        
        if not os.path.exists(validation_path):
            return jsonify({'error': 'Relatório de validação não encontrado'}), 404
        
        # Carregar e retornar relatório
        with open(validation_path, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        return jsonify(validation_data)
        
    except Exception as e:
        app.logger.error(f"Erro ao obter relatório de validação: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/domains')
def get_available_domains():
    """Lista domínios de processo disponíveis"""
    try:
        domains = domain_manager.get_available_domains()
        return jsonify({
            'domains': domains,
            'total': len(domains)
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter domínios: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/agents')
def get_available_agents():
    """Lista agentes de IA disponíveis"""
    try:
        from mvp.utils.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()
        
        agents = prompt_loader.get_available_agents()
        agents_info = []
        
        for agent in agents:
            info = prompt_loader.get_agent_info(agent)
            agents_info.append({
                'id': agent,
                'name': info.get('name', agent.title()),
                'description': info.get('description', 'Sem descrição'),
                'focus': info.get('focus', 'Não especificado'),
                'audience': info.get('audience', 'Não especificado')
            })
        
        return jsonify({
            'agents': agents_info,
            'total': len(agents_info)
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter agentes: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    try:
        # Verificar conexão com banco
        try:
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception as db_error:
            db_status = f'error: {str(db_error)}'
        
        # Verificar configuração OpenAI
        api_key = app.config.get('OPENAI_API_KEY')
        has_openai_key = bool(api_key) and api_key != 'your-openai-api-key-here'
        
        # Verificar Tesseract
        try:
            from mvp.processors.ocr import TESSERACT_AVAILABLE
            tesseract_status = 'available' if TESSERACT_AVAILABLE else 'fallback_mode'
        except Exception:
            tesseract_status = 'fallback_mode'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'openai_configured': has_openai_key,
            'tesseract_ocr': tesseract_status,
            'version': '0.1.0'
        })
        
    except Exception as e:
        app.logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handler para arquivos muito grandes"""
    return jsonify({'error': 'Arquivo muito grande. Limite: 50MB'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handler para recursos não encontrados"""
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handler para erros internos"""
    return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== ENDPOINTS DE HISTÓRICO ====================

@app.route('/history')
def session_history():
    """Endpoint para listar histórico de sessões"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Máximo 50 por página
        
        # Query com ordenação por data mais recente
        sessions_query = Session.query.order_by(Session.created_at.desc())
        
        # Paginação
        sessions_paginated = sessions_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Converter para dicionário
        sessions_data = []
        for session in sessions_paginated.items:
            session_dict = session.to_dict()
            
            # Adicionar informações extras
            if session.screenshot_files:
                screenshot_paths = json.loads(session.screenshot_files)
                session_dict['screenshot_count'] = len(screenshot_paths)
            else:
                session_dict['screenshot_count'] = 0
            
            # Calcular duração de processamento
            if session.processing_time:
                if session.processing_time < 60:
                    session_dict['processing_duration'] = f"{session.processing_time:.1f}s"
                else:
                    minutes = int(session.processing_time // 60)
                    seconds = int(session.processing_time % 60)
                    session_dict['processing_duration'] = f"{minutes}m {seconds}s"
            else:
                session_dict['processing_duration'] = "N/A"
            
            sessions_data.append(session_dict)
        
        return jsonify({
            'sessions': sessions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': sessions_paginated.total,
                'pages': sessions_paginated.pages,
                'has_next': sessions_paginated.has_next,
                'has_prev': sessions_paginated.has_prev
            }
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao buscar histórico: {str(e)}")
        return jsonify({'error': 'Erro interno ao buscar histórico'}), 500

@app.route('/history/<session_id>')
def session_details(session_id):
    """Endpoint para detalhes de uma sessão específica"""
    try:
        session = Session.query.get_or_404(session_id)
        
        # Dados básicos da sessão
        session_data = session.to_dict()
        
        # Adicionar arquivos
        files_info = []
        if session.transcription_file:
            files_info.append({
                'type': 'transcription',
                'filename': os.path.basename(session.transcription_file),
                'path': session.transcription_file,
                'exists': os.path.exists(session.transcription_file)
            })
        
        if session.screenshot_files:
            screenshot_paths = json.loads(session.screenshot_files)
            for i, path in enumerate(screenshot_paths):
                files_info.append({
                    'type': 'screenshot',
                    'filename': os.path.basename(path),
                    'path': path,
                    'index': i,
                    'exists': os.path.exists(path)
                })
        
        session_data['files'] = files_info
        
        # Adicionar logs de processamento
        logs = ProcessingLog.query.filter_by(session_id=session_id)\
                                 .order_by(ProcessingLog.timestamp.asc())\
                                 .all()
        
        session_data['logs'] = [log.to_dict() for log in logs]
        
        # Adicionar documentos gerados
        documents = ProcessedDocument.query.filter_by(session_id=session_id).all()
        session_data['documents'] = []
        
        for doc in documents:
            doc_info = {
                'id': doc.id,
                'format': doc.format,
                'file_path': doc.file_path,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'exists': bool(doc.file_path and os.path.exists(doc.file_path)),
                'size': os.path.getsize(doc.file_path) if doc.file_path and os.path.exists(doc.file_path) else 0
            }
            session_data['documents'].append(doc_info)
        
        return jsonify(session_data)
        
    except Exception as e:
        app.logger.error(f"Erro ao buscar detalhes da sessão {session_id}: {str(e)}")
        return jsonify({'error': 'Erro interno ao buscar detalhes'}), 500

@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """Endpoint para download de arquivos de uma sessão"""
    try:
        session = Session.query.get_or_404(session_id)
        file_path = None
        filename = None
        
        if file_type == 'transcription':
            if session.transcription_file and os.path.exists(session.transcription_file):
                file_path = session.transcription_file
                filename = f"transcricao_{session_id}.txt"
            else:
                return jsonify({'error': 'Arquivo de transcrição não encontrado'}), 404
                
        elif file_type == 'documentation':
            if session.generated_documentation:
                # Criar arquivo temporário com a documentação
                temp_path = os.path.join(app.config['OUTPUT_FOLDER'], f"doc_{session_id}.md")
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(session.generated_documentation)
                
                file_path = temp_path
                filename = f"documentacao_{session_id}.md"
            else:
                return jsonify({'error': 'Documentação não encontrada'}), 404
                
        elif file_type.startswith('screenshot_'):
            # Extrair índice do screenshot
            try:
                screenshot_index = int(file_type.split('_')[1])
                if session.screenshot_files:
                    screenshot_paths = json.loads(session.screenshot_files)
                    if 0 <= screenshot_index < len(screenshot_paths):
                        screenshot_path = screenshot_paths[screenshot_index]
                        if os.path.exists(screenshot_path):
                            file_path = screenshot_path
                            filename = f"screenshot_{session_id}_{screenshot_index}.png"
                        else:
                            return jsonify({'error': 'Screenshot não encontrado'}), 404
                    else:
                        return jsonify({'error': 'Índice de screenshot inválido'}), 400
                else:
                    return jsonify({'error': 'Nenhum screenshot disponível'}), 404
            except (ValueError, IndexError):
                return jsonify({'error': 'Formato de arquivo inválido'}), 400
        else:
            return jsonify({'error': 'Tipo de arquivo inválido'}), 400
        
        if file_path and os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        else:
            return jsonify({'error': 'Arquivo não encontrado'}), 404
            
    except Exception as e:
        app.logger.error(f"Erro no download {file_type} da sessão {session_id}: {str(e)}")
        return jsonify({'error': 'Erro interno no download'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )