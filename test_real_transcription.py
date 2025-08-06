#!/usr/bin/env python3
"""
Teste com a transcrição real usando modo apenas transcrição
"""

import requests
import time
import json
import os
import shutil

BASE_URL = "http://127.0.0.1:5000"

def test_with_real_transcription():
    """Testa com a transcrição real"""
    
    print("TESTE COM TRANSCRICAO REAL")
    print("=" * 50)
    
    # 1. Copiar transcrição real para pasta de uploads
    source_path = "../Planejamento-MD/Transcrição Forjada.txt"
    temp_path = "data/uploads/transcricao_real_teste.txt"
    
    if not os.path.exists(source_path):
        print(f"Erro: Arquivo nao encontrado: {source_path}")
        return False
    
    try:
        print("1. Preparando arquivo de teste...")
        shutil.copy2(source_path, temp_path)
        print(f"   Arquivo copiado para: {temp_path}")
    except Exception as e:
        print(f"   Erro ao copiar arquivo: {e}")
        return False
    
    # 2. Upload da transcrição real
    print("\n2. Upload da transcricao real...")
    
    try:
        files = {
            'transcription': open(temp_path, 'rb')
        }
        
        data = {
            'transcription_only_mode': 'true'
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data, timeout=10)
        files['transcription'].close()
        
        if response.status_code == 200:
            upload_data = response.json()
            session_id = upload_data['session_id']
            print(f"   Upload realizado com sucesso!")
            print(f"   Session ID: {session_id}")
        else:
            print(f"   Erro no upload: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   Erro no upload: {e}")
        return False
    
    # 3. Processar
    print("\n3. Iniciando processamento...")
    
    try:
        response = requests.post(f"{BASE_URL}/process/{session_id}", timeout=10)
        
        if response.status_code == 202:
            print("   Processamento iniciado!")
        else:
            print(f"   Erro: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   Erro: {e}")
        return False
    
    # 4. Monitorar progresso
    print("\n4. Monitorando progresso...")
    
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/status/{session_id}", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                
                print(f"   Tentativa {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print("   PROCESSAMENTO CONCLUIDO!")
                    
                    # Obter resultado
                    result_response = requests.get(f"{BASE_URL}/result/{session_id}", timeout=10)
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        
                        doc_length = len(result_data.get('documentation', ''))
                        actions_count = len(result_data.get('actions', []))
                        
                        print(f"   Documentacao gerada: {doc_length} caracteres")
                        print(f"   Acoes processadas: {actions_count}")
                        
                        # Mostrar preview da documentação
                        doc = result_data.get('documentation', '')
                        if doc:
                            lines = doc.split('\n')[:15]  # Primeiras 15 linhas
                            print("\n   PREVIEW DA DOCUMENTACAO:")
                            for i, line in enumerate(lines, 1):
                                if line.strip():
                                    print(f"   {i:2d}: {line}")
                            
                            if len(doc.split('\n')) > 15:
                                print("   ...")
                        
                        # Salvar documentação em arquivo
                        output_file = f"data/outputs/transcricao_real_{session_id}.md"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(doc)
                        print(f"\n   Documentacao salva em: {output_file}")
                        
                        return True
                    
                elif status == 'error':
                    print("   PROCESSAMENTO FALHOU!")
                    return False
                    
                elif status in ['processing', 'uploading']:
                    time.sleep(3)
                    attempt += 1
                    continue
                else:
                    time.sleep(3)
                    attempt += 1
                    continue
                    
            else:
                print(f"   Erro ao verificar status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Erro ao monitorar: {e}")
            attempt += 1
            time.sleep(3)
            continue
    
    print("   TIMEOUT!")
    return False

if __name__ == "__main__":
    success = test_with_real_transcription()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCESSO! TRANSCRICAO REAL PROCESSADA!")
        print("A documentacao foi gerada com base na transcricao real.")
        print("O sistema agora entende documentacao tecnica detalhada!")
    else:
        print("FALHA! Verificar logs para mais detalhes.")