"""
Sistema de templates personalizáveis por domínio
Versão 2 - Templates específicos para diferentes tipos de processos RPA
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import os
from enum import Enum

class ProcessDomain(Enum):
    """Domínios de processo suportados"""
    AUTHENTICATION = "authentication"
    FORM_FILLING = "form_filling"
    DATA_ENTRY = "data_entry"
    FINANCIAL = "financial"
    REPORTING = "reporting"
    NAVIGATION = "navigation"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    GENERIC = "generic"

@dataclass
class TemplateSection:
    """Seção de template"""
    title: str
    content_template: str
    is_required: bool
    order: int
    conditions: List[str]  # Condições para incluir a seção

@dataclass
class DomainTemplate:
    """Template para um domínio específico"""
    domain: ProcessDomain
    name: str
    description: str
    sections: List[TemplateSection]
    prompt_modifications: Dict[str, str]
    validation_rules: List[str]
    expected_elements: List[str]
    complexity_indicators: List[str]

class DomainTemplateManager:
    """Gerenciador de templates por domínio"""
    
    def __init__(self):
        self.templates = {}
        self._initialize_default_templates()
        
        # Indicadores para classificação automática de domínio
        self.domain_indicators = {
            ProcessDomain.AUTHENTICATION: [
                'login', 'senha', 'usuário', 'entrar', 'autenticar', 'acesso',
                'credenciais', 'autenticação', 'logar', 'password', 'user'
            ],
            ProcessDomain.FORM_FILLING: [
                'formulário', 'preencher', 'dados', 'informações', 'campo',
                'cadastro', 'registro', 'form', 'input', 'preenchimento'
            ],
            ProcessDomain.DATA_ENTRY: [
                'inserir', 'dados', 'tabela', 'planilha', 'entrada', 'digitar',
                'input', 'registro', 'informar', 'incluir', 'adicionar'
            ],
            ProcessDomain.FINANCIAL: [
                'pagamento', 'financeiro', 'valor', 'moeda', 'dinheiro', 'conta',
                'fatura', 'cobrança', 'transação', 'saldo', 'extrato'
            ],
            ProcessDomain.REPORTING: [
                'relatório', 'report', 'exportar', 'gerar', 'imprimir',
                'dados', 'consulta', 'listagem', 'download', 'pdf'
            ],
            ProcessDomain.NAVIGATION: [
                'navegar', 'menu', 'página', 'tela', 'aba', 'seção',
                'ir para', 'acessar', 'abrir', 'voltar', 'próximo'
            ],
            ProcessDomain.VALIDATION: [
                'validar', 'verificar', 'conferir', 'checar', 'confirmar',
                'validação', 'erro', 'correto', 'aprovado', 'rejeitado'
            ],
            ProcessDomain.INTEGRATION: [
                'integração', 'api', 'sistema', 'conectar', 'sincronizar',
                'importar', 'exportar', 'transferir', 'enviar', 'receber'
            ]
        }

    def _initialize_default_templates(self):
        """Inicializa templates padrão para cada domínio"""
        
        # Template de Autenticação
        auth_template = DomainTemplate(
            domain=ProcessDomain.AUTHENTICATION,
            name="Processo de Autenticação",
            description="Template para processos de login e autenticação",
            sections=[
                TemplateSection(
                    title="Objetivo",
                    content_template="Realizar autenticação no sistema {system_name} utilizando credenciais válidas.",
                    is_required=True,
                    order=1,
                    conditions=[]
                ),
                TemplateSection(
                    title="Pré-requisitos",
                    content_template="""- Sistema {system_name} acessível
- Credenciais válidas (usuário e senha)
- Conexão com internet estável
- Navegador web atualizado""",
                    is_required=True,
                    order=2,
                    conditions=[]
                ),
                TemplateSection(
                    title="Passos de Autenticação",
                    content_template="{detailed_steps}",
                    is_required=True,
                    order=3,
                    conditions=[]
                ),
                TemplateSection(
                    title="Validações de Segurança",
                    content_template="""- Verificar se a URL está correta (https)
- Confirmar que não há mensagens de erro de certificado
- Validar se o login foi bem-sucedido
- Verificar se não há tentativas de login suspeitas""",
                    is_required=True,
                    order=4,
                    conditions=["has_security_elements"]
                ),
                TemplateSection(
                    title="Tratamento de Erros de Autenticação",
                    content_template="""- **Credenciais inválidas**: Verificar usuário e senha, tentar novamente
- **Conta bloqueada**: Aguardar ou contatar administrador
- **Sistema indisponível**: Verificar conectividade e tentar mais tarde
- **Timeout**: Reiniciar processo de login""",
                    is_required=True,
                    order=5,
                    conditions=[]
                )
            ],
            prompt_modifications={
                "focus": "autenticação e segurança",
                "emphasis": "Enfatize aspectos de segurança, validação de credenciais e tratamento de erros de login",
                "security_note": "Inclua considerações específicas sobre segurança da informação"
            },
            validation_rules=[
                "deve_conter_validacao_credenciais",
                "deve_incluir_tratamento_erro_login",
                "deve_verificar_sucesso_autenticacao"
            ],
            expected_elements=[
                "campo_usuario", "campo_senha", "botao_entrar", "botao_login",
                "link_esqueci_senha", "mensagem_erro", "indicador_sucesso"
            ],
            complexity_indicators=[
                "autenticacao_dois_fatores", "captcha", "multiplas_tentativas"
            ]
        )
        
        # Template de Preenchimento de Formulário
        form_template = DomainTemplate(
            domain=ProcessDomain.FORM_FILLING,
            name="Preenchimento de Formulário",
            description="Template para processos de preenchimento de formulários",
            sections=[
                TemplateSection(
                    title="Objetivo",
                    content_template="Preencher formulário {form_name} com as informações necessárias e realizar envio.",
                    is_required=True,
                    order=1,
                    conditions=[]
                ),
                TemplateSection(
                    title="Dados Necessários",
                    content_template="""- {required_fields}
- Documentos de apoio (se aplicável)
- Informações de validação""",
                    is_required=True,
                    order=2,
                    conditions=[]
                ),
                TemplateSection(
                    title="Passos de Preenchimento",
                    content_template="{detailed_steps}",
                    is_required=True,
                    order=3,
                    conditions=[]
                ),
                TemplateSection(
                    title="Validações de Campos",
                    content_template="""- Verificar se campos obrigatórios estão preenchidos
- Validar formato de dados (e-mail, CPF, telefone, etc.)
- Confirmar consistência entre campos relacionados
- Verificar limites de caracteres""",
                    is_required=True,
                    order=4,
                    conditions=["has_validation_fields"]
                ),
                TemplateSection(
                    title="Envio e Confirmação",
                    content_template="""- Revisar dados antes do envio
- Clicar em botão de envio/submissão
- Aguardar confirmação de recebimento
- Salvar comprovante (se disponível)""",
                    is_required=True,
                    order=5,
                    conditions=[]
                )
            ],
            prompt_modifications={
                "focus": "preenchimento preciso e validação de dados",
                "emphasis": "Enfatize a importância da precisão dos dados e validações de campo",
                "data_note": "Inclua considerações sobre tipos de dados e formatos esperados"
            },
            validation_rules=[
                "deve_listar_campos_obrigatorios",
                "deve_incluir_validacoes_formato",
                "deve_confirmar_envio_sucesso"
            ],
            expected_elements=[
                "campos_input", "botao_enviar", "botao_limpar", "checkbox_termos",
                "dropdown_opcoes", "mensagem_validacao", "confirmacao_envio"
            ],
            complexity_indicators=[
                "campos_condicionais", "upload_arquivos", "multiplas_etapas"
            ]
        )
        
        # Template Financeiro
        financial_template = DomainTemplate(
            domain=ProcessDomain.FINANCIAL,
            name="Processo Financeiro",
            description="Template para processos financeiros e transações",
            sections=[
                TemplateSection(
                    title="Objetivo",
                    content_template="Realizar {financial_operation} no valor de {amount} conforme procedimentos financeiros estabelecidos.",
                    is_required=True,
                    order=1,
                    conditions=[]
                ),
                TemplateSection(
                    title="Informações Financeiras",
                    content_template="""- Valor da transação: {amount}
- Conta de origem: {origin_account}
- Conta de destino: {destination_account}
- Finalidade: {purpose}
- Data de processamento: {processing_date}""",
                    is_required=True,
                    order=2,
                    conditions=[]
                ),
                TemplateSection(
                    title="Passos da Transação",
                    content_template="{detailed_steps}",
                    is_required=True,
                    order=3,
                    conditions=[]
                ),
                TemplateSection(
                    title="Validações Financeiras",
                    content_template="""- Verificar saldo disponível
- Confirmar dados bancários
- Validar limites de transação
- Verificar taxa de câmbio (se aplicável)
- Confirmar finalidade da operação""",
                    is_required=True,
                    order=4,
                    conditions=[]
                ),
                TemplateSection(
                    title="Controles de Auditoria",
                    content_template="""- Registrar log da transação
- Salvar comprovantes e recibos
- Documentar aprovações necessárias
- Manter rastreabilidade da operação""",
                    is_required=True,
                    order=5,
                    conditions=["has_audit_requirements"]
                )
            ],
            prompt_modifications={
                "focus": "precisão financeira e conformidade",
                "emphasis": "Enfatize controles financeiros, validações monetárias e rastreabilidade",
                "compliance_note": "Inclua considerações de compliance e auditoria financeira"
            },
            validation_rules=[
                "deve_validar_valores_monetarios",
                "deve_incluir_controles_auditoria",
                "deve_confirmar_transacao_sucesso"
            ],
            expected_elements=[
                "campo_valor", "campo_conta", "botao_transferir", "botao_confirmar",
                "comprovante_transacao", "saldo_disponivel", "historico_transacoes"
            ],
            complexity_indicators=[
                "multiplas_moedas", "aprovacao_hierarquica", "integracao_bancaria"
            ]
        )
        
        # Template Genérico
        generic_template = DomainTemplate(
            domain=ProcessDomain.GENERIC,
            name="Processo Genérico",
            description="Template padrão para processos não classificados",
            sections=[
                TemplateSection(
                    title="Objetivo",
                    content_template="Executar processo {process_name} conforme procedimentos estabelecidos.",
                    is_required=True,
                    order=1,
                    conditions=[]
                ),
                TemplateSection(
                    title="Pré-requisitos",
                    content_template="""- Sistema acessível
- Permissões necessárias
- Dados/informações requeridas
- Conexão estável""",
                    is_required=True,
                    order=2,
                    conditions=[]
                ),
                TemplateSection(
                    title="Passos Detalhados",
                    content_template="{detailed_steps}",
                    is_required=True,
                    order=3,
                    conditions=[]
                ),
                TemplateSection(
                    title="Validações",
                    content_template="""- Verificar se processo foi executado corretamente
- Confirmar resultados esperados
- Validar dados de saída""",
                    is_required=True,
                    order=4,
                    conditions=[]
                ),
                TemplateSection(
                    title="Tratamento de Exceções",
                    content_template="""- **Erro de sistema**: Verificar logs e tentar novamente
- **Dados inválidos**: Corrigir informações e reprocessar
- **Timeout**: Reiniciar processo
- **Falha de conectividade**: Verificar conexão e tentar mais tarde""",
                    is_required=True,
                    order=5,
                    conditions=[]
                )
            ],
            prompt_modifications={
                "focus": "clareza e completude",
                "emphasis": "Enfatize clareza dos passos e tratamento abrangente de exceções"
            },
            validation_rules=[
                "deve_ter_objetivo_claro",
                "deve_incluir_validacoes_basicas",
                "deve_tratar_excecoes_comuns"
            ],
            expected_elements=[],
            complexity_indicators=[]
        )
        
        # Registrar templates
        self.templates[ProcessDomain.AUTHENTICATION] = auth_template
        self.templates[ProcessDomain.FORM_FILLING] = form_template
        self.templates[ProcessDomain.FINANCIAL] = financial_template
        self.templates[ProcessDomain.GENERIC] = generic_template

    def identify_domain(self, 
                       transcription_text: str, 
                       ui_elements: List[str],
                       actions: List[str]) -> ProcessDomain:
        """Identifica automaticamente o domínio do processo"""
        
        # Combinar todo o texto para análise
        all_text = (transcription_text + " " + " ".join(ui_elements) + " " + " ".join(actions)).lower()
        
        # Pontuar cada domínio baseado na presença de indicadores
        domain_scores = {}
        
        for domain, indicators in self.domain_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in all_text:
                    score += 1
            
            # Normalizar score pelo número de indicadores do domínio
            normalized_score = score / len(indicators) if indicators else 0
            domain_scores[domain] = normalized_score
        
        # Adicionar bonificações baseadas em padrões específicos
        
        # Bonificação para autenticação
        if any(word in all_text for word in ['login', 'senha', 'entrar', 'usuário']):
            domain_scores[ProcessDomain.AUTHENTICATION] += 0.3
        
        # Bonificação para formulários
        if any(word in all_text for word in ['formulário', 'preencher', 'campo', 'dados']):
            domain_scores[ProcessDomain.FORM_FILLING] += 0.3
        
        # Bonificação para processos financeiros
        if any(word in all_text for word in ['valor', 'pagamento', 'transferir', 'conta']):
            domain_scores[ProcessDomain.FINANCIAL] += 0.3
        
        # Selecionar domínio com maior pontuação
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            if best_domain[1] > 0.1:  # Threshold mínimo
                return best_domain[0]
        
        return ProcessDomain.GENERIC

    def get_template(self, domain: ProcessDomain) -> Optional[DomainTemplate]:
        """Obtém template para um domínio específico"""
        return self.templates.get(domain)

    def generate_documentation_with_template(self, 
                                           domain: ProcessDomain,
                                           context_data: Dict[str, Any]) -> str:
        """Gera documentação usando template específico do domínio"""
        
        template = self.get_template(domain)
        if not template:
            template = self.templates[ProcessDomain.GENERIC]
        
        documentation_parts = []
        
        # Processar cada seção do template
        for section in sorted(template.sections, key=lambda x: x.order):
            # Verificar condições da seção
            if section.conditions and not self._check_conditions(section.conditions, context_data):
                continue
            
            # Gerar conteúdo da seção
            section_content = self._render_section(section, context_data)
            documentation_parts.append(f"## {section.title}\n\n{section_content}\n")
        
        return "\n".join(documentation_parts)

    def _check_conditions(self, conditions: List[str], context_data: Dict[str, Any]) -> bool:
        """Verifica se condições da seção são atendidas"""
        for condition in conditions:
            if condition == "has_security_elements":
                security_elements = context_data.get('security_elements', [])
                if not security_elements:
                    return False
            elif condition == "has_validation_fields":
                validation_fields = context_data.get('validation_fields', [])
                if not validation_fields:
                    return False
            elif condition == "has_audit_requirements":
                audit_required = context_data.get('audit_required', False)
                if not audit_required:
                    return False
        
        return True

    def _render_section(self, section: TemplateSection, context_data: Dict[str, Any]) -> str:
        """Renderiza conteúdo de uma seção com dados do contexto"""
        content = section.content_template
        
        # Substituir placeholders básicos
        replacements = {
            '{system_name}': context_data.get('system_name', 'Sistema'),
            '{form_name}': context_data.get('form_name', 'formulário'),
            '{process_name}': context_data.get('process_name', 'processo'),
            '{amount}': context_data.get('amount', 'valor especificado'),
            '{financial_operation}': context_data.get('financial_operation', 'operação financeira'),
            '{origin_account}': context_data.get('origin_account', 'conta de origem'),
            '{destination_account}': context_data.get('destination_account', 'conta de destino'),
            '{purpose}': context_data.get('purpose', 'finalidade especificada'),
            '{processing_date}': context_data.get('processing_date', 'data atual'),
            '{required_fields}': self._format_required_fields(context_data.get('required_fields', [])),
            '{detailed_steps}': self._format_detailed_steps(context_data.get('detailed_steps', []))
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        return content

    def _format_required_fields(self, fields: List[str]) -> str:
        """Formata lista de campos obrigatórios"""
        if not fields:
            return "Campos conforme processo"
        
        return "\n".join(f"- {field}" for field in fields)

    def _format_detailed_steps(self, steps: List[Dict[str, Any]]) -> str:
        """Formata passos detalhados do processo"""
        if not steps:
            return "1. Seguir sequência identificada na análise"
        
        formatted_steps = []
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'ação')
            element = step.get('element', 'elemento')
            description = step.get('description', '')
            
            step_text = f"{i}. {action.title()} em '{element}'"
            if description:
                step_text += f" - {description}"
            
            formatted_steps.append(step_text)
        
        return "\n".join(formatted_steps)

    def get_enhanced_prompt_for_domain(self, 
                                     domain: ProcessDomain, 
                                     base_prompt: str) -> str:
        """Obtém prompt aprimorado para domínio específico"""
        template = self.get_template(domain)
        if not template or not template.prompt_modifications:
            return base_prompt
        
        modifications = template.prompt_modifications
        
        enhanced_prompt = base_prompt + "\n\n"
        enhanced_prompt += f"**FOCO ESPECÍFICO**: {modifications.get('focus', '')}\n"
        enhanced_prompt += f"**ÊNFASE**: {modifications.get('emphasis', '')}\n"
        
        if 'security_note' in modifications:
            enhanced_prompt += f"**SEGURANÇA**: {modifications['security_note']}\n"
        
        if 'data_note' in modifications:
            enhanced_prompt += f"**DADOS**: {modifications['data_note']}\n"
        
        if 'compliance_note' in modifications:
            enhanced_prompt += f"**COMPLIANCE**: {modifications['compliance_note']}\n"
        
        return enhanced_prompt

    def validate_documentation_for_domain(self, 
                                        domain: ProcessDomain, 
                                        documentation: str) -> Dict[str, Any]:
        """Valida documentação usando regras específicas do domínio"""
        template = self.get_template(domain)
        if not template:
            return {'valid': True, 'warnings': [], 'missing_elements': []}
        
        warnings = []
        missing_elements = []
        
        doc_lower = documentation.lower()
        
        # Verificar regras de validação
        for rule in template.validation_rules:
            if rule == "deve_conter_validacao_credenciais":
                if not any(word in doc_lower for word in ['credenciais', 'usuário', 'senha', 'login']):
                    warnings.append("Documentação pode não incluir validação adequada de credenciais")
            
            elif rule == "deve_incluir_tratamento_erro_login":
                if not any(word in doc_lower for word in ['erro', 'falha', 'inválido', 'bloqueado']):
                    warnings.append("Falta tratamento de erros de login")
            
            elif rule == "deve_listar_campos_obrigatorios":
                if not any(word in doc_lower for word in ['obrigatório', 'required', 'necessário']):
                    warnings.append("Pode não listar campos obrigatórios adequadamente")
            
            elif rule == "deve_validar_valores_monetarios":
                if not any(word in doc_lower for word in ['valor', 'saldo', 'limite', 'validar']):
                    warnings.append("Falta validação de valores monetários")
        
        # Verificar elementos esperados
        for element in template.expected_elements:
            element_variations = element.replace('_', ' ').split()
            if not any(var in doc_lower for var in element_variations):
                missing_elements.append(element)
        
        is_valid = len(warnings) == 0 and len(missing_elements) < len(template.expected_elements) * 0.5
        
        return {
            'valid': is_valid,
            'warnings': warnings,
            'missing_elements': missing_elements,
            'domain': domain.value,
            'template_used': template.name
        }

    def get_available_domains(self) -> List[Dict[str, str]]:
        """Retorna lista de domínios disponíveis"""
        return [
            {
                'domain': domain.value,
                'name': template.name,
                'description': template.description
            }
            for domain, template in self.templates.items()
        ]

    def export_template(self, domain: ProcessDomain, file_path: str):
        """Exporta template para arquivo JSON"""
        template = self.get_template(domain)
        if not template:
            return False
        
        template_data = {
            'domain': template.domain.value,
            'name': template.name,
            'description': template.description,
            'sections': [
                {
                    'title': section.title,
                    'content_template': section.content_template,
                    'is_required': section.is_required,
                    'order': section.order,
                    'conditions': section.conditions
                }
                for section in template.sections
            ],
            'prompt_modifications': template.prompt_modifications,
            'validation_rules': template.validation_rules,
            'expected_elements': template.expected_elements,
            'complexity_indicators': template.complexity_indicators
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar template: {e}")
            return False

    def import_template(self, file_path: str) -> bool:
        """Importa template de arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            domain = ProcessDomain(template_data['domain'])
            
            sections = [
                TemplateSection(
                    title=section['title'],
                    content_template=section['content_template'],
                    is_required=section['is_required'],
                    order=section['order'],
                    conditions=section['conditions']
                )
                for section in template_data['sections']
            ]
            
            template = DomainTemplate(
                domain=domain,
                name=template_data['name'],
                description=template_data['description'],
                sections=sections,
                prompt_modifications=template_data.get('prompt_modifications', {}),
                validation_rules=template_data.get('validation_rules', []),
                expected_elements=template_data.get('expected_elements', []),
                complexity_indicators=template_data.get('complexity_indicators', [])
            )
            
            self.templates[domain] = template
            return True
            
        except Exception as e:
            print(f"Erro ao importar template: {e}")
            return False