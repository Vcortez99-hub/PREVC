#!/usr/bin/env python3
"""
Teste da aplicação web para verificar se o processamento funciona via HTTP
"""

import requests
import time
import json
import os

BASE_URL = "http://127.0.0.1:5000"

def test_upload_and_process():
    """Testa upload e processamento via API"""
    
    print("TESTE DA APLICACAO WEB")
    print("=" * 50)
    
    # 1. Testar health check
    print("1. Testando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   OpenAI configurada: {health_data.get('openai_configured')}")
        else:
            print(f"   Erro: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   Erro ao conectar: {e}")
        print("   DICA: Certifique-se que a aplicacao esta rodando em http://127.0.0.1:5000")
        return False
    
    # 2. Upload de arquivos
    print("\n2. Fazendo upload de arquivos...")
    
    transcription_path = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_Transcricao_Forjada.txt"
    image_path = "data/uploads/3445a457-233c-413e-a8c0-604ee6e4273f_0_imagem.png"
    
    if not os.path.exists(transcription_path):
        print(f"   Erro: Arquivo de transcricao nao encontrado: {transcription_path}")
        return False
        
    if not os.path.exists(image_path):
        print(f"   Erro: Arquivo de imagem nao encontrado: {image_path}")
        return False
    
    try:
        files = {
            'transcription': open(transcription_path, 'rb'),
            'screenshots': open(image_path, 'rb')
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=10)
        
        # Fechar arquivos
        files['transcription'].close()
        files['screenshots'].close()
        
        if response.status_code == 200:
            upload_data = response.json()
            session_id = upload_data['session_id']
            print(f"   Upload realizado com sucesso!")
            print(f"   Session ID: {session_id}")
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
    print("\n4. Monitorando progresso...")
    
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
                        print(f"   Resultados OCR: {len(result_data.get('ocr_results', []))}")
                        return True
                    
                elif status == 'error':
                    print("   PROCESSAMENTO FALHOU!")
                    return False
                    
                elif status in ['processing', 'uploading']:
                    print(f"   Processando... ({status})")
                    time.sleep(5)
                    attempt += 1
                    continue
                else:
                    print(f"   Status desconhecido: {status}")
                    time.sleep(5)
                    attempt += 1
                    continue
                    
            else:
                print(f"   Erro ao verificar status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   Erro ao monitorar: {e}")
            attempt += 1
            time.sleep(5)
            continue
    
    print("   TIMEOUT: Processamento demorou mais de 5 minutos")
    return False

if __name__ == "__main__":
    success = test_upload_and_process()
    
    print("\n" + "=" * 50)
    if success:
        print("TESTE WEB CONCLUIDO COM SUCESSO!")
        print("A aplicacao esta funcionando corretamente.")
    else:
        print("TESTE WEB FALHOU!")
        print("Verifique os logs da aplicacao para mais detalhes.")