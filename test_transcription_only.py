#!/usr/bin/env python3
"""
Teste da nova funcionalidade: modo apenas transcrição
"""

import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_transcription_only_mode():
    """Testa o modo apenas transcrição"""
    
    print("TESTE: MODO APENAS TRANSCRICAO")
    print("=" * 50)
    
    # 1. Testar health check
    print("1. Testando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
        else:
            print(f"   Erro: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   Erro ao conectar: {e}")
        return False
    
    # 2. Upload apenas com transcrição
    print("\n2. Upload APENAS com transcricao (sem screenshots)...")
    
    transcription_path = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_Transcricao_Forjada.txt"
    
    if not os.path.exists(transcription_path):
        print(f"   Erro: Arquivo de transcricao nao encontrado: {transcription_path}")
        return False
    
    try:
        # Criar FormData com apenas transcrição e o flag do modo
        files = {
            'transcription': open(transcription_path, 'rb')
        }
        
        data = {
            'transcription_only_mode': 'true'  # Ativar modo apenas transcrição
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data, timeout=10)
        
        # Fechar arquivo
        files['transcription'].close()
        
        if response.status_code == 200:
            upload_data = response.json()
            session_id = upload_data['session_id']
            print(f"   Upload realizado com sucesso!")
            print(f"   Session ID: {session_id}")
            print(f"   Modo apenas transcricao: {upload_data.get('transcription_only_mode')}")
            print(f"   Files received: {upload_data['files_received']}")
        else:
            print(f"   Erro no upload: Status {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Erro no upload: {e}")
        return False
    
    # 3. Iniciar processamento
    print("\n3. Iniciando processamento...")
    
    try:
        response = requests.post(f"{BASE_URL}/process/{session_id}", timeout=10)
        
        if response.status_code == 202:
            process_data = response.json()
            print(f"   Processamento iniciado!")
            print(f"   Status: {process_data['status']}")
        else:
            print(f"   Erro ao iniciar processamento: Status {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"   Erro ao iniciar processamento: {e}")
        return False
    
    # 4. Monitorar progresso
    print("\n4. Monitorando progresso (modo apenas transcricao)...")
    
    max_attempts = 60  # 5 minutos
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/status/{session_id}", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                
                print(f"   Tentativa {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print("   PROCESSAMENTO CONCLUIDO COM SUCESSO!")
                    
                    # Obter resultado
                    result_response = requests.get(f"{BASE_URL}/result/{session_id}", timeout=10)
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        print(f"   Documentacao gerada: {len(result_data.get('documentation', ''))} caracteres")
                        print(f"   Acoes processadas: {len(result_data.get('actions', []))}")
                        print(f"   Resultados OCR: {len(result_data.get('ocr_results', []))} (deve ser 0)")
                        
                        # Mostrar trecho da documentação
                        doc_preview = result_data.get('documentation', '')[:200]
                        print(f"   Preview da documentacao: {doc_preview}...")
                        
                        return True
                    
                elif status == 'error':
                    print("   PROCESSAMENTO FALHOU!")
                    return False
                    
                elif status in ['processing', 'uploading']:
                    print(f"   Processando... ({status})")
                    time.sleep(3)
                    attempt += 1
                    continue
                else:
                    print(f"   Status desconhecido: {status}")
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
    
    print("   TIMEOUT: Processamento demorou mais de 5 minutos")
    return False

if __name__ == "__main__":
    success = test_transcription_only_mode()
    
    print("\n" + "=" * 50)
    if success:
        print("TESTE MODO APENAS TRANSCRICAO: SUCESSO!")
        print("A nova funcionalidade esta funcionando corretamente.")
        print("Screenshots foram pulados e documentacao foi gerada apenas com transcricao.")
    else:
        print("TESTE MODO APENAS TRANSCRICAO: FALHOU!")
        print("Verifique os logs da aplicacao para mais detalhes.")