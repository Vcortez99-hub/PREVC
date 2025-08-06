import openai
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import time
import re
from mvp.processors.correlator import CorrelatedProcess, CorrelatedEvent
from mvp.utils.prompt_loader import PromptLoader

@dataclass
class DocumentationResult:
    """Resultado da geração de documentação"""
    content: str
    format: str
    metadata: Dict[str, Any]
    generation_time: float
    token_usage: Dict[str, int]
    success: bool
    error_message: Optional[str] = None

class AIDocumentGenerator:
    """Cliente para geração de documentação usando diferentes provedores de IA"""
    
    def __init__(self, api_key: str, provider: str = "openai", model: str = "gpt-4", agent_type: str = "rpa_general"):
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self.agent_type = agent_type
        self.max_tokens = 2000
        self.temperature = 0.3  # Baixa para documentação mais consistente
        
        # Inicializar cliente baseado no provedor
        self._initialize_client()
        
        # Inicializar carregador de prompts
        self.prompt_loader = PromptLoader()
        
        # Carregar prompt para o tipo de agente especificado
        self.base_prompt = self._load_agent_prompt()

    def _initialize_client(self):
        """Inicializa o cliente baseado no provedor"""
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == "azure":
            # Para Azure OpenAI, você precisará configurar endpoint e versão da API
            self.client = openai.AzureOpenAI(
                api_key=self.api_key,
                # azure_endpoint="https://your-endpoint.openai.azure.com/",
                # api_version="2024-02-15-preview"
            )
        elif self.provider == "anthropic":
            # Para Anthropic, você precisará instalar a biblioteca anthropic
            # import anthropic
            # self.client = anthropic.Anthropic(api_key=self.api_key)
            raise NotImplementedError("Suporte ao Anthropic será implementado em versão futura")
        elif self.provider == "google":
            # Para Google, você precisará configurar a biblioteca google-generativeai
            # import google.generativeai as genai
            # genai.configure(api_key=self.api_key)
            raise NotImplementedError("Suporte ao Google será implementado em versão futura")
        else:
            raise ValueError(f"Provedor não suportado: {self.provider}")

    def _load_agent_prompt(self) -> str:
        """Carrega o prompt do agente especificado"""
        loaded_prompt = self.prompt_loader.load_prompt(self.agent_type)
        
        if loaded_prompt:
            return loaded_prompt
        else:
            # Fallback para prompt padrão se não conseguir carregar
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Retorna prompt padrão caso não consiga carregar do arquivo"""
        return """
Você é um especialista em documentação de processos RPA (Robotic Process Automation). 

Sua tarefa é gerar uma documentação técnica estruturada e clara baseada nas informações fornecidas sobre um processo automatizável.

**FORMATO DE SAÍDA OBRIGATÓRIO:**
```markdown
# {processo_nome}

## Objetivo
{objetivo_claro_e_conciso}

## Pré-requisitos
- {prerequisito_1}
- {prerequisito_2}
- {prerequisito_n}

## Passos Detalhados
{passos_numerados_com_acoes_e_elementos}

## Validações
{pontos_de_validacao_importantes}

## Tratamento de Exceções
{possiveis_erros_e_tratamentos}

## Observações Técnicas
{informacoes_adicionais_para_desenvolvimento}
```

**REGRAS IMPORTANTES:**
1. Use linguagem técnica mas clara
2. Seja específico sobre elementos de interface (botões, campos, etc.)
3. Inclua validações e tratamentos de erro quando identificados
4. Mantenha a sequência lógica das ações
5. Use verbos no infinitivo (clicar, digitar, selecionar)
6. Cite elementos UI exatamente como aparecem na interface
"""

    def change_agent_type(self, agent_type: str):
        """Muda o tipo de agente e recarrega o prompt"""
        self.agent_type = agent_type
        self.base_prompt = self._load_agent_prompt()

    def get_available_agents(self) -> List[str]:
        """Retorna lista de agentes disponíveis"""
        return self.prompt_loader.get_available_agents()

    def get_agent_info(self, agent_type: str = None) -> Dict:
        """Retorna informações sobre um agente"""
        if agent_type is None:
            agent_type = self.agent_type
        return self.prompt_loader.get_agent_info(agent_type)

    def generate_documentation(self, 
                             correlated_data: CorrelatedProcess, 
                             custom_prompt: Optional[str] = None,
                             template_base: Optional[str] = None) -> DocumentationResult:
        """Gera documentação baseada nos dados correlacionados"""
        start_time = time.time()
        
        try:
            # Usar prompt customizado se fornecido, senão usar o padrão
            system_prompt = custom_prompt if custom_prompt else self.base_prompt
            
            # Construir prompt contextualizado
            user_prompt = self._build_contextualized_prompt(correlated_data, template_base)
            
            # Fazer chamada para OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extrair conteúdo da resposta
            generated_content = response.choices[0].message.content
            
            # Validar e limpar conteúdo
            cleaned_content = self._validate_and_clean_content(generated_content)
            
            # Calcular tempo de geração
            generation_time = time.time() - start_time
            
            # Extrair metadata
            metadata = self._extract_metadata(correlated_data, cleaned_content)
            
            return DocumentationResult(
                content=cleaned_content,
                format="markdown",
                metadata=metadata,
                generation_time=generation_time,
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                success=True
            )
            
        except Exception as e:
            return DocumentationResult(
                content="",
                format="markdown",
                metadata={},
                generation_time=time.time() - start_time,
                token_usage={},
                success=False,
                error_message=str(e)
            )

    def _build_contextualized_prompt(self, 
                                    correlated_data: CorrelatedProcess, 
                                    template_base: Optional[str] = None) -> str:
        """Constrói prompt contextualizado baseado nos dados"""
        
        # Informações básicas do processo
        process_info = f"""
**INFORMAÇÕES DO PROCESSO:**
- Total de ações identificadas: {correlated_data.total_actions}
- Ações correlacionadas com sucesso: {correlated_data.successfully_correlated}
- Qualidade da correlação: {correlated_data.correlation_quality:.2f}
- Participantes identificados: {', '.join(correlated_data.transcription_summary.get('speakers', []))}
"""
        
        # Sequência de ações
        actions_sequence = "\n**SEQUÊNCIA DE AÇÕES IDENTIFICADAS:**\n"
        for i, event in enumerate(correlated_data.correlated_events, 1):
            action = event.action
            ui_element = event.matched_ui_element
            
            actions_sequence += f"{i}. **{action.action_type.upper()}** "
            actions_sequence += f"'{action.element}' "
            
            if ui_element:
                actions_sequence += f"(Elemento visual: '{ui_element.text}', "
                actions_sequence += f"Tipo: {ui_element.type}, "
                actions_sequence += f"Confiança: {event.correlation_score:.2f}) "
            else:
                actions_sequence += "(Sem correlação visual) "
                
            actions_sequence += f"- Falado por: {action.speaker}\n"
        
        # Informações visuais
        visual_info = "\n**ELEMENTOS VISUAIS IDENTIFICADOS:**\n"
        for i, ocr_summary in enumerate(correlated_data.ocr_summary, 1):
            visual_info += f"Tela {i}: {ocr_summary['ui_elements_count']} elementos UI identificados "
            visual_info += f"(Tipos: {', '.join(ocr_summary.get('ui_elements_types', []))})\n"
        
        # Contexto adicional
        context = "\n**CONTEXTO ADICIONAL:**\n"
        context += f"- Tipos de ação mais comuns: {', '.join(correlated_data.transcription_summary.get('action_types', []))}\n"
        context += f"- Confiança média das ações: {correlated_data.transcription_summary.get('average_confidence', 0):.2f}\n"
        
        # Instruções específicas
        instructions = f"""
**INSTRUÇÕES ESPECÍFICAS PARA ESTE PROCESSO:**
Com base nas informações acima, gere uma documentação completa para automação RPA.

IMPORTANTE:
- Nome do processo: Identifique e sugira um nome baseado nas ações
- Foque nos elementos que têm correlação visual confirmada (score > 0.5)
- Para ações sem correlação visual, use o texto mencionado na transcrição
- Inclua validações para elementos críticos (botões de confirmação, campos obrigatórios)
- Sugira tratamento para possíveis erros (elemento não encontrado, timeout, etc.)
- Use terminologia técnica apropriada para RPA
"""
        
        # Adicionar template base se fornecido
        template_section = ""
        if template_base:
            template_section = f"""
**TEMPLATE BASE PARA SEGUIR:**
{template_base}

**IMPORTANTE:** Use o template acima como base estrutural, mas personalize o conteúdo com os dados específicos do processo analisado.
"""
        
        # Montar prompt final
        full_prompt = process_info + actions_sequence + visual_info + context + template_section + instructions
        
        return full_prompt

    def _validate_and_clean_content(self, content: str) -> str:
        """Valida e limpa o conteúdo gerado"""
        # Remover marcadores de código markdown se presentes incorretamente
        content = re.sub(r'^```markdown\s*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```\s*$', '', content, flags=re.MULTILINE)
        
        # Garantir que há seções obrigatórias
        required_sections = ['# ', '## Objetivo', '## Pré-requisitos', '## Passos Detalhados']
        
        for section in required_sections:
            if section not in content:
                # Se seção crítica estiver faltando, adicionar placeholder
                if section == '# ':
                    content = "# Processo RPA\n\n" + content
                elif section == '## Objetivo':
                    content = content.replace('## Pré-requisitos', '## Objetivo\nAutomatizar processo identificado na transcrição.\n\n## Pré-requisitos')
                elif section == '## Pré-requisitos':
                    content = content.replace('## Passos Detalhados', '## Pré-requisitos\n- Sistema acessível\n- Credenciais válidas\n\n## Passos Detalhados')
                elif section == '## Passos Detalhados':
                    content += "\n\n## Passos Detalhados\n1. Seguir sequência identificada na análise"
        
        # Limpar espaços excessivos
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        return content

    def _extract_metadata(self, correlated_data: CorrelatedProcess, generated_content: str) -> Dict[str, Any]:
        """Extrai metadata do processo de geração"""
        
        # Contar seções geradas
        sections = re.findall(r'^## (.+)$', generated_content, re.MULTILINE)
        
        # Contar passos
        steps = re.findall(r'^\d+\. ', generated_content, re.MULTILINE)
        
        return {
            'process_quality': {
                'correlation_quality': correlated_data.correlation_quality,
                'total_actions': correlated_data.total_actions,
                'correlated_actions': correlated_data.successfully_correlated,
                'correlation_ratio': correlated_data.successfully_correlated / correlated_data.total_actions if correlated_data.total_actions > 0 else 0
            },
            'document_structure': {
                'sections_generated': len(sections),
                'sections_list': sections,
                'steps_count': len(steps),
                'word_count': len(generated_content.split()),
                'character_count': len(generated_content)
            },
            'generation_context': {
                'speakers_involved': correlated_data.transcription_summary.get('speakers', []),
                'action_types_identified': correlated_data.transcription_summary.get('action_types', []),
                'visual_screens_processed': len(correlated_data.ocr_summary)
            }
        }

    def generate_multiple_formats(self, correlated_data: CorrelatedProcess) -> Dict[str, DocumentationResult]:
        """Gera documentação em múltiplos formatos"""
        results = {}
        
        # Formato padrão (markdown técnico)
        results['technical'] = self.generate_documentation(correlated_data)
        
        # Formato executivo (mais resumido)
        results['executive'] = self._generate_executive_summary(correlated_data)
        
        # Formato checklist (para validação)
        results['checklist'] = self._generate_validation_checklist(correlated_data)
        
        return results

    def _generate_executive_summary(self, correlated_data: CorrelatedProcess) -> DocumentationResult:
        """Gera resumo executivo do processo"""
        start_time = time.time()
        
        try:
            prompt = f"""
Baseado no processo RPA analisado, gere um RESUMO EXECUTIVO conciso:

**Dados do processo:**
- {correlated_data.total_actions} ações identificadas
- {correlated_data.successfully_correlated} ações com correlação visual
- Qualidade da correlação: {correlated_data.correlation_quality:.0%}

**Formato de saída:**
```markdown
# Resumo Executivo - Automação RPA

## Processo Identificado
[Nome/descrição em 1 linha]

## Benefícios da Automação
- [Benefício 1]
- [Benefício 2]
- [Benefício 3]

## Complexidade
- **Nível:** [Baixa/Média/Alta]
- **Tempo estimado desenvolvimento:** [X semanas]
- **ROI esperado:** [Alto/Médio/Baixo]

## Próximos Passos
1. [Passo 1]
2. [Passo 2]
3. [Passo 3]
```
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            return DocumentationResult(
                content=self._validate_and_clean_content(content),
                format="markdown",
                metadata={'type': 'executive_summary'},
                generation_time=time.time() - start_time,
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                success=True
            )
            
        except Exception as e:
            return DocumentationResult(
                content="",
                format="markdown",
                metadata={'type': 'executive_summary'},
                generation_time=time.time() - start_time,
                token_usage={},
                success=False,
                error_message=str(e)
            )

    def _generate_validation_checklist(self, correlated_data: CorrelatedProcess) -> DocumentationResult:
        """Gera checklist para validação do processo"""
        start_time = time.time()
        
        # Gerar checklist baseado nas ações identificadas
        checklist_items = []
        
        for event in correlated_data.correlated_events:
            action = event.action
            correlation_note = ""
            
            if event.correlation_score >= 0.8:
                correlation_note = "✅ Alta confiança"
            elif event.correlation_score >= 0.5:
                correlation_note = "⚠️ Verificar manualmente"
            else:
                correlation_note = "❌ Baixa confiança - revisar"
            
            checklist_items.append(f"- [ ] {action.action_type.title()} em '{action.element}' {correlation_note}")
        
        content = f"""# Checklist de Validação - Processo RPA

## Informações Gerais
- **Total de ações:** {correlated_data.total_actions}
- **Ações correlacionadas:** {correlated_data.successfully_correlated}
- **Qualidade geral:** {correlated_data.correlation_quality:.0%}

## Lista de Verificação
{chr(10).join(checklist_items)}

## Validações Adicionais
- [ ] Todos os elementos de interface foram identificados corretamente
- [ ] Sequência de ações está logicamente correta
- [ ] Tratamentos de erro foram considerados
- [ ] Validações de dados estão incluídas
- [ ] Processo pode ser executado de forma independente

## Próximas Ações
- [ ] Revisar itens com baixa confiança
- [ ] Testar processo manualmente
- [ ] Implementar automação
- [ ] Realizar testes da automação
"""
        
        return DocumentationResult(
            content=content,
            format="markdown",
            metadata={'type': 'validation_checklist'},
            generation_time=time.time() - start_time,
            token_usage={},
            success=True
        )

    def estimate_tokens(self, text: str) -> int:
        """Estima número de tokens para um texto"""
        # Estimativa aproximada: ~4 caracteres por token em português
        return len(text) // 4

    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo sendo usado"""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'estimated_cost_per_1k_tokens': 0.03  # Valor aproximado GPT-4
        }