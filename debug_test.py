#!/usr/bin/env python3
"""
Script para testar os componentes da aplicação individualmente
e identificar onde está o problema nos 30%
"""

import os
import sys
import traceback
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("TESTE DEBUG - IDENTIFICANDO PROBLEMA DOS 30%")
print("=" * 60)

# Testar imports
print("\n1. TESTANDO IMPORTS...")
try:
    from config import config
    print("OK Config importado")
    
    from mvp.parsers.transcription import BasicTranscriptionParser
    print("OK TranscriptionParser importado")
    
    from mvp.processors.ocr import BasicOCR
    print("OK BasicOCR importado")
    
    from mvp.processors.correlator import BasicCorrelator
    print("OK BasicCorrelator importado")
    
    from mvp.generators.ai_client import AIDocumentGenerator
    print("OK AIDocumentGenerator importado")
    
except Exception as e:
    print(f"ERRO no import: {e}")
    traceback.print_exc()
    sys.exit(1)

# Testar arquivos de teste
print("\n2. VERIFICANDO ARQUIVOS DE TESTE...")
test_transcription = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_Transcricao_Forjada.txt"
test_image = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_0_imagem.png"

if os.path.exists(test_transcription):
    print(f"OK Transcricao encontrada: {test_transcription}")
else:
    print(f"ERRO Transcricao nao encontrada: {test_transcription}")
    
if os.path.exists(test_image):
    print(f"OK Imagem encontrada: {test_image}")
else:
    print(f"ERRO Imagem nao encontrada: {test_image}")

# Testar processamento de transcrição
print("\n3. TESTANDO PROCESSAMENTO DE TRANSCRICAO...")
try:
    parser = BasicTranscriptionParser()
    result = parser.process_file(test_transcription)
    print(f"OK Transcricao processada: {result['summary']['total_segments']} segmentos, {result['summary']['total_actions']} acoes")
    
    # Mostrar algumas ações encontradas
    actions = result['actions'][:3]  # Primeiras 3 ações
    for i, action in enumerate(actions, 1):
        print(f"   Acao {i}: {action['action_type']} -> {action['element']}")
        
except Exception as e:
    print(f"ERRO no processamento de transcricao: {e}")
    traceback.print_exc()

# Testar OCR
print("\n4. TESTANDO OCR...")
try:
    ocr = BasicOCR()
    ocr_result = ocr.extract_text(test_image)
    print(f"OK OCR concluido: {len(ocr_result.extracted_text)} caracteres extraidos")
    print(f"   Confianca: {ocr_result.confidence:.2f}")
    print(f"   Elementos UI: {len(ocr_result.ui_elements)}")
    print(f"   Texto extraido (primeiros 200 chars): {ocr_result.extracted_text[:200]}...")
    
except Exception as e:
    print(f"ERRO no OCR: {e}")
    traceback.print_exc()

# Testar correlação
print("\n5. TESTANDO CORRELACAO...")
try:
    # Recriar objetos para correlação
    parser = BasicTranscriptionParser()
    transcription_result = parser.process_file(test_transcription)
    
    # Importar TranscriptionSegment corretamente
    from mvp.parsers.transcription import TranscriptionSegment
    
    actions = parser.extract_actions([
        TranscriptionSegment(
            timestamp=seg['timestamp'],
            speaker=seg['speaker'],
            text=seg['text']
        ) for seg in transcription_result['segments']
    ])
    
    ocr = BasicOCR()
    ocr_results = [ocr.extract_text(test_image)]
    
    correlator = BasicCorrelator()
    correlated_process = correlator.correlate_audio_visual(actions, ocr_results)
    
    print(f"OK Correlacao concluida:")
    print(f"   Total de acoes: {correlated_process.total_actions}")
    print(f"   Acoes correlacionadas: {correlated_process.successfully_correlated}")
    print(f"   Qualidade da correlacao: {correlated_process.correlation_quality:.2f}")
    
except Exception as e:
    print(f"ERRO na correlacao: {e}")
    traceback.print_exc()

# Testar IA
print("\n6. TESTANDO GERACAO DE DOCUMENTACAO IA...")
try:
    # Verificar configuração da API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your-openai-api-key-here':
        print("ERRO OpenAI API Key nao configurada corretamente")
    else:
        print(f"OK OpenAI API Key configurada (ultimos 4 chars: ...{api_key[-4:]})")
        
        # Tentar criar cliente IA
        ai_generator = AIDocumentGenerator(api_key)
        print("OK Cliente IA criado")
        
        # Tentar gerar documentação
        print("   Gerando documentacao... (isso pode demorar)")
        doc_result = ai_generator.generate_documentation(correlated_process)
        
        if doc_result.success:
            print(f"OK Documentacao gerada: {len(doc_result.content)} caracteres")
            print(f"   Tokens usados: {doc_result.token_usage.get('total_tokens', 'N/A')}")
        else:
            print(f"ERRO Falha na geracao: {doc_result.error_message}")
    
except Exception as e:
    print(f"ERRO na geracao IA: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("TESTE CONCLUIDO!")
print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")