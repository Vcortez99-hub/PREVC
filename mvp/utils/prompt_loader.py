import os
import json
from typing import Dict, Optional, List
from pathlib import Path

class PromptLoader:
    """Classe para carregar prompts externos de arquivos"""
    
    def __init__(self, prompts_dir: str = None):
        """
        Inicializa o carregador de prompts
        
        Args:
            prompts_dir: Diretório onde estão os arquivos de prompt. 
                        Se None, usa o diretório padrão do projeto
        """
        if prompts_dir is None:
            # Diretório padrão relativo ao projeto
            base_dir = Path(__file__).parent.parent.parent
            self.prompts_dir = base_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._cache = {}  # Cache para prompts carregados
        
    def get_available_agents(self) -> List[str]:
        """Retorna lista de agentes disponíveis baseado nos arquivos de prompt"""
        if not self.prompts_dir.exists():
            return []
        
        agents = []
        for file_path in self.prompts_dir.glob("*.txt"):
            agent_name = file_path.stem
            agents.append(agent_name)
        
        return sorted(agents)
    
    def load_prompt(self, agent_type: str) -> Optional[str]:
        """
        Carrega o prompt para um tipo de agente específico
        
        Args:
            agent_type: Tipo do agente (ex: 'rpa_general', 'rpa_technical')
            
        Returns:
            String com o prompt ou None se não encontrado
        """
        # Verificar cache primeiro
        if agent_type in self._cache:
            return self._cache[agent_type]
        
        prompt_file = self.prompts_dir / f"{agent_type}.txt"
        
        if not prompt_file.exists():
            return None
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read().strip()
            
            # Adicionar ao cache
            self._cache[agent_type] = prompt_content
            return prompt_content
            
        except Exception as e:
            print(f"Erro ao carregar prompt {agent_type}: {e}")
            return None
    
    def get_agent_info(self, agent_type: str) -> Dict:
        """
        Retorna informações sobre um agente específico
        
        Args:
            agent_type: Tipo do agente
            
        Returns:
            Dicionário com informações do agente
        """
        agent_info = {
            'rpa_general': {
                'name': 'RPA Geral',
                'description': 'Documentação geral para processos RPA com foco na clareza e completude',
                'focus': 'Documentação técnica balanceada',
                'audience': 'Desenvolvedores e analistas RPA'
            },
            'rpa_technical': {
                'name': 'RPA Técnico',
                'description': 'Documentação técnica detalhada para implementação avançada',
                'focus': 'Especificações técnicas e código',
                'audience': 'Desenvolvedores e arquitetos RPA'
            },
            'rpa_business': {
                'name': 'RPA Business',
                'description': 'Documentação focada no valor de negócio e ROI',
                'focus': 'Benefícios de negócio e análise financeira',
                'audience': 'Executivos e stakeholders de negócio'
            },
            'process_analyst': {
                'name': 'Analista de Processos',
                'description': 'Análise detalhada de processos e mapeamento de fluxos',
                'focus': 'Mapeamento e otimização de processos',
                'audience': 'Analistas de processo e consultores'
            },
            'custom': {
                'name': 'Personalizado',
                'description': 'Prompt customizável para casos específicos',
                'focus': 'Flexível e personalizável',
                'audience': 'Configurável conforme necessidade'
            }
        }
        
        return agent_info.get(agent_type, {
            'name': agent_type.title(),
            'description': 'Agente personalizado',
            'focus': 'Não especificado',
            'audience': 'Não especificado'
        })
    
    def reload_prompts(self):
        """Limpa o cache e recarrega todos os prompts"""
        self._cache.clear()
    
    def create_prompt_template(self, agent_type: str, template_content: str):
        """
        Cria um novo arquivo de prompt
        
        Args:
            agent_type: Nome do tipo de agente
            template_content: Conteúdo do prompt
        """
        # Criar diretório se não existir
        self.prompts_dir.mkdir(exist_ok=True)
        
        prompt_file = self.prompts_dir / f"{agent_type}.txt"
        
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # Limpar cache para forçar reload
            if agent_type in self._cache:
                del self._cache[agent_type]
                
        except Exception as e:
            raise Exception(f"Erro ao criar prompt {agent_type}: {e}")
    
    def get_models_by_provider(self, provider: str) -> List[Dict]:
        """
        Retorna modelos disponíveis por provedor
        
        Args:
            provider: Nome do provedor (openai, azure, anthropic, google)
            
        Returns:
            Lista de dicionários com informações dos modelos
        """
        models = {
            'openai': [
                {'id': 'gpt-4', 'name': 'GPT-4', 'description': 'Modelo mais avançado da OpenAI'},
                {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'description': 'GPT-4 otimizado para velocidade'},
                {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'description': 'Modelo rápido e eficiente'}
            ],
            'azure': [
                {'id': 'gpt-4', 'name': 'Azure GPT-4', 'description': 'GPT-4 via Azure OpenAI'},
                {'id': 'gpt-35-turbo', 'name': 'Azure GPT-3.5 Turbo', 'description': 'GPT-3.5 via Azure'}
            ],
            'anthropic': [
                {'id': 'claude-3-opus', 'name': 'Claude 3 Opus', 'description': 'Modelo mais avançado da Anthropic'},
                {'id': 'claude-3-sonnet', 'name': 'Claude 3 Sonnet', 'description': 'Modelo balanceado'},
                {'id': 'claude-3-haiku', 'name': 'Claude 3 Haiku', 'description': 'Modelo rápido e eficiente'}
            ],
            'google': [
                {'id': 'gemini-pro', 'name': 'Gemini Pro', 'description': 'Modelo principal do Google'},
                {'id': 'gemini-pro-vision', 'name': 'Gemini Pro Vision', 'description': 'Com capacidades de visão'}
            ]
        }
        
        return models.get(provider, [])
    
    def validate_prompt(self, prompt_content: str) -> Dict:
        """
        Valida se um prompt está bem formatado
        
        Args:
            prompt_content: Conteúdo do prompt para validar
            
        Returns:
            Dicionário com resultado da validação
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Verificações básicas
        if not prompt_content or len(prompt_content.strip()) < 50:
            validation_result['valid'] = False
            validation_result['errors'].append('Prompt muito curto ou vazio')
        
        # Verificar se tem formato markdown
        if '```markdown' not in prompt_content and '# ' not in prompt_content:
            validation_result['warnings'].append('Prompt não parece usar formato Markdown')
        
        # Verificar se tem placeholders
        if '{' not in prompt_content or '}' not in prompt_content:
            validation_result['warnings'].append('Prompt não tem placeholders para personalização')
        
        return validation_result