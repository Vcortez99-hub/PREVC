#!/usr/bin/env python3
"""
Teste do fluxo completo simulando o que acontece na aplicação
"""

import os
import sys
import json
import uuid
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("TESTE DO FLUXO COMPLETO - SIMULACAO DA APLICACAO")
print("=" * 60)

def simulate_session_processing():
    """Simula o processamento completo de uma sessão"""
    
    # Simular dados de uma sessão real
    session_id = "test-session-" + str(uuid.uuid4())[:8]
    transcription_file = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_Transcricao_Forjada.txt"
    screenshot_files = ["data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_0_imagem.png"]
    
    print(f"Simulando sessao: {session_id}")
    print(f"Arquivo de transcricao: {transcription_file}")
    print(f"Screenshots: {len(screenshot_files)} arquivo(s)")
    
    try:
        # Imports
        from mvp.parsers.transcription import BasicTranscriptionParser, TranscriptionSegment
        from mvp.processors.ocr import BasicOCR
        from mvp.processors.correlator import BasicCorrelator
        from mvp.generators.ai_client import AIDocumentGenerator
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Inicializar processadores
        transcription_parser = BasicTranscriptionParser()
        ocr_processor = BasicOCR()
        correlator = BasicCorrelator()
        
        print("\n1. PROCESSAMENTO DE TRANSCRICAO (10-30%)")
        print("   Processando arquivo de transcricao...")
        
        actions = []
        if os.path.exists(transcription_file):
            transcription_result = transcription_parser.process_file(transcription_file)
            print(f"   -> {len(transcription_result['segments'])} segmentos encontrados")
            
            actions = transcription_parser.extract_actions([
                TranscriptionSegment(
                    timestamp=seg['timestamp'],
                    speaker=seg['speaker'],
                    text=seg['text']
                ) for seg in transcription_result['segments']
            ])
            
            print(f"   -> {len(actions)} acoes extraidas")
            for i, action in enumerate(actions[:3], 1):
                print(f"      Acao {i}: {action.action_type} -> '{action.element}'")
        
        print("\n2. PROCESSAMENTO DE OCR (30-60%)")
        print("   Processando screenshots...")
        
        ocr_results = []
        for i, path in enumerate(screenshot_files):
            if os.path.exists(path):
                print(f"   -> Processando screenshot {i+1}: {os.path.basename(path)}")
                try:
                    ocr_result = ocr_processor.extract_text(path)
                    ocr_results.append(ocr_result)
                    print(f"      Texto extraido: {len(ocr_result.extracted_text)} caracteres")
                    print(f"      Confianca: {ocr_result.confidence:.2f}")
                    print(f"      Elementos UI: {len(ocr_result.ui_elements)}")
                except Exception as e:
                    print(f"      ERRO: {e}")
        
        print("\n3. CORRELACAO DE DADOS (60-80%)")
        print("   Correlacionando acoes com elementos visuais...")
        
        if actions or ocr_results:
            correlated_process = correlator.correlate_audio_visual(actions, ocr_results)
            correlated_process.session_id = session_id
            
            print(f"   -> Total de acoes: {correlated_process.total_actions}")
            print(f"   -> Acoes correlacionadas: {correlated_process.successfully_correlated}")
            print(f"   -> Qualidade da correlacao: {correlated_process.correlation_quality:.2f}")
        else:
            print("   -> Nenhum dado para correlacionar")
            return False
        
        print("\n4. GERACAO DE DOCUMENTACAO IA (80-100%)")
        print("   Gerando documentacao com IA...")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your-openai-api-key-here':
            print("   ERRO: OpenAI API Key nao configurada")
            return False
        
        ai_gen = AIDocumentGenerator(api_key)
        print("   -> Cliente IA inicializado")
        
        doc_result = ai_gen.generate_documentation(correlated_process)
        
        if doc_result.success:
            print(f"   -> Documentacao gerada: {len(doc_result.content)} caracteres")
            print(f"   -> Tokens usados: {doc_result.token_usage.get('total_tokens', 'N/A')}")
            
            # Salvar resultado em arquivo temporário
            output_file = f"data/outputs/test_output_{session_id}.md"
            os.makedirs("data/outputs", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(doc_result.content)
            
            print(f"   -> Documentacao salva em: {output_file}")
            return True
        else:
            print(f"   ERRO na geracao: {doc_result.error_message}")
            return False
            
    except Exception as e:
        print(f"ERRO no processamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = simulate_session_processing()
    
    print("\n" + "=" * 60)
    if success:
        print("TESTE CONCLUIDO COM SUCESSO! 100% completado")
    else:
        print("TESTE FALHOU - Identificar ponto de falha acima")
    
    print(f"Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")