#!/usr/bin/env python3
"""
Teste do parser melhorado com a transcrição real
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mvp.parsers.transcription import BasicTranscriptionParser

def test_improved_parser():
    """Testa o parser melhorado com a transcrição real"""
    
    print("TESTE DO PARSER MELHORADO")
    print("=" * 50)
    
    # Caminho para a transcrição real
    real_transcription = "../Planejamento-MD/Transcrição Forjada.txt"
    
    if not os.path.exists(real_transcription):
        print(f"Erro: Arquivo nao encontrado: {real_transcription}")
        return False
    
    try:
        # 1. Testar o parser
        print("1. Inicializando parser...")
        parser = BasicTranscriptionParser()
        
        # 2. Processar arquivo
        print("2. Processando transcricao real...")
        result = parser.process_file(real_transcription)
        
        print(f"   -> {result['summary']['total_segments']} segmentos processados")
        print(f"   -> {result['summary']['total_actions']} acoes extraidas")
        print(f"   -> Speakers: {result['summary']['speakers']}")
        print(f"   -> Tipos de acao: {result['summary']['action_types']}")
        
        # 3. Mostrar algumas ações extraídas
        print("\n3. Amostras das acoes extraidas:")
        actions = result['actions']
        
        if len(actions) == 0:
            print("   ❌ NENHUMA ACAO EXTRAIDA!")
            return False
        
        # Mostrar primeiras 10 ações
        for i, action in enumerate(actions[:10], 1):
            print(f"   {i:2d}. [{action['action_type']}] {action['element']}")
            print(f"       Confianca: {action['confidence']:.2f} | Speaker: {action['speaker']}")
            print()
        
        if len(actions) > 10:
            print(f"   ... e mais {len(actions) - 10} acoes")
        
        # 4. Analisar tipos de ação
        print("\n4. Distribuicao de tipos de acao:")
        action_counts = {}
        for action in actions:
            action_type = action['action_type']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        for action_type, count in sorted(action_counts.items()):
            print(f"   {action_type}: {count} acoes")
        
        # 5. Verificar qualidade das extrações
        print("\n5. Analise de qualidade:")
        
        high_confidence = sum(1 for a in actions if a['confidence'] >= 0.8)
        medium_confidence = sum(1 for a in actions if 0.5 <= a['confidence'] < 0.8)
        low_confidence = sum(1 for a in actions if a['confidence'] < 0.5)
        
        print(f"   Alta confianca (>=0.8): {high_confidence} acoes")
        print(f"   Media confianca (0.5-0.8): {medium_confidence} acoes")
        print(f"   Baixa confianca (<0.5): {low_confidence} acoes")
        
        success = len(actions) > 5 and high_confidence > 0
        
        return success
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_improved_parser()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TESTE CONCLUIDO COM SUCESSO!")
        print("O parser melhorado esta extraindo acoes da transcricao real.")
    else:
        print("❌ TESTE FALHOU!")
        print("O parser ainda nao esta funcionando adequadamente.")