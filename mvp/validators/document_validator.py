"""
Sistema de validações automáticas de documentação
Versão 2 - Validações inteligentes para garantir qualidade da documentação gerada
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os
from datetime import datetime

from mvp.parsers.transcription import Action
from mvp.processors.ocr import OCRResult
from mvp.processors.correlator import CorrelatedProcess
from mvp.generators.domain_templates import ProcessDomain, DomainTemplateManager

class ValidationSeverity(Enum):
    """Severidade dos problemas encontrados"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Problema identificado na validação"""
    severity: ValidationSeverity
    category: str
    description: str
    location: str  # Seção/linha onde foi encontrado
    suggestion: str
    auto_fixable: bool
    confidence: float

@dataclass
class ValidationReport:
    """Relatório completo de validação"""
    document_id: str
    validation_timestamp: str
    overall_score: float
    issues: List[ValidationIssue]
    domain: ProcessDomain
    completeness_metrics: Dict[str, float]
    quality_metrics: Dict[str, float]
    suggestions_for_improvement: List[str]
    auto_fixes_applied: List[str]

class DocumentValidator:
    """Validador automático de documentação RPA"""
    
    def __init__(self):
        self.domain_manager = DomainTemplateManager()
        
        # Pesos para cálculo de score geral
        self.scoring_weights = {
            'completeness': 0.3,
            'accuracy': 0.25,
            'clarity': 0.2,
            'consistency': 0.15,
            'technical_quality': 0.1
        }
        
        # Padrões para identificar problemas comuns
        self.common_patterns = {
            'incomplete_steps': [
                r'\d+\.\s*$',  # Número seguido de ponto sem texto
                r'^\s*-\s*$',  # Item de lista vazio
                r'(clica|digita|seleciona)\s*$'  # Ação sem objeto
            ],
            'vague_descriptions': [
                r'\b(algo|alguma coisa|isso|aquilo)\b',
                r'\b(etc\.?|\.\.\.)\b',
                r'\bna (tela|página|área)\b$'  # Muito genérico
            ],
            'technical_errors': [
                r'\b(erro|falha|problema)\b(?!\s+(de|caso|se))',  # Mentions de erro não tratadas
                r'\bclica\s+em\s+"[^"]*"\s*$',  # Referência a elemento inexistente
                r'\b(campo|botão)\s+sem\s+nome\b'
            ],
            'formatting_issues': [
                r'^\s*\d+\s*$',  # Numeração solta
                r'[\.]{3,}',     # Múltiplos pontos
                r'[A-Z]{3,}',    # TEXTO EM MAIÚSCULAS
                r'\s{3,}'        # Múltiplos espaços
            ]
        }
        
        # Vocabulário de qualidade para diferentes domínios
        self.quality_vocabularies = {
            ProcessDomain.AUTHENTICATION: {
                'required_terms': ['usuário', 'senha', 'login', 'autenticação'],
                'security_terms': ['segurança', 'credenciais', 'autenticação', 'acesso'],
                'action_terms': ['inserir', 'digitar', 'informar', 'confirmar']
            },
            ProcessDomain.FORM_FILLING: {
                'required_terms': ['campo', 'formulário', 'dados', 'informações'],
                'validation_terms': ['validar', 'verificar', 'confirmar', 'formato'],
                'action_terms': ['preencher', 'selecionar', 'inserir', 'escolher']
            },
            ProcessDomain.FINANCIAL: {
                'required_terms': ['valor', 'conta', 'transação', 'pagamento'],
                'control_terms': ['validar', 'confirmar', 'aprovar', 'autorizar'],
                'audit_terms': ['registro', 'comprovante', 'histórico', 'rastreabilidade']
            }
        }

    def validate_documentation(self, 
                             documentation: str, 
                             correlation_data: CorrelatedProcess,
                             domain: Optional[ProcessDomain] = None) -> ValidationReport:
        """Valida documentação gerada usando múltiplos critérios"""
        
        document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Identificar domínio se não fornecido
        if not domain:
            domain = self._identify_document_domain(documentation, correlation_data)
        
        # Executar validações
        issues = []
        
        # 1. Validações estruturais
        structural_issues = self._validate_structure(documentation)
        issues.extend(structural_issues)
        
        # 2. Validações de conteúdo
        content_issues = self._validate_content(documentation, correlation_data)
        issues.extend(content_issues)
        
        # 3. Validações específicas do domínio
        domain_issues = self._validate_domain_specific(documentation, domain)
        issues.extend(domain_issues)
        
        # 4. Validações de correlação
        correlation_issues = self._validate_correlation_quality(documentation, correlation_data)
        issues.extend(correlation_issues)
        
        # 5. Validações técnicas
        technical_issues = self._validate_technical_quality(documentation)
        issues.extend(technical_issues)
        
        # Calcular métricas
        completeness_metrics = self._calculate_completeness_metrics(documentation, correlation_data)
        quality_metrics = self._calculate_quality_metrics(documentation, issues)
        
        # Score geral
        overall_score = self._calculate_overall_score(completeness_metrics, quality_metrics, issues)
        
        # Sugestões de melhoria
        suggestions = self._generate_improvement_suggestions(issues, completeness_metrics)
        
        # Auto-fixes aplicáveis
        auto_fixes = self._identify_auto_fixes(issues)
        
        return ValidationReport(
            document_id=document_id,
            validation_timestamp=datetime.now().isoformat(),
            overall_score=overall_score,
            issues=issues,
            domain=domain,
            completeness_metrics=completeness_metrics,
            quality_metrics=quality_metrics,
            suggestions_for_improvement=suggestions,
            auto_fixes_applied=auto_fixes
        )

    def _validate_structure(self, documentation: str) -> List[ValidationIssue]:
        """Valida estrutura básica da documentação"""
        issues = []
        
        # Verificar se tem seções básicas
        required_sections = ['objetivo', 'passos', 'pré-requisitos']
        doc_lower = documentation.lower()
        
        for section in required_sections:
            if section not in doc_lower:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="estrutura",
                    description=f"Seção '{section}' não encontrada",
                    location="documento_geral",
                    suggestion=f"Adicionar seção sobre {section}",
                    auto_fixable=True,
                    confidence=0.8
                ))
        
        # Verificar numeração de passos
        step_pattern = r'^\s*\d+\.\s+'
        lines = documentation.split('\n')
        step_lines = [line for line in lines if re.match(step_pattern, line)]
        
        if len(step_lines) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="estrutura",
                description="Documentação tem poucos passos numerados (menos de 3)",
                location="passos_procedimento",
                suggestion="Adicionar mais detalhes aos procedimentos",
                auto_fixable=False,
                confidence=0.9
            ))
        
        # Verificar passos incompletos
        for i, line in enumerate(step_lines):
            for pattern in self.common_patterns['incomplete_steps']:
                if re.search(pattern, line):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="estrutura",
                        description=f"Passo incompleto na linha {i+1}",
                        location=f"passo_{i+1}",
                        suggestion="Completar descrição do passo",
                        auto_fixable=False,
                        confidence=0.85
                    ))
        
        return issues

    def _validate_content(self, documentation: str, correlation_data: CorrelatedProcess) -> List[ValidationIssue]:
        """Valida qualidade do conteúdo"""
        issues = []
        
        # Verificar descrições vagas
        for pattern in self.common_patterns['vague_descriptions']:
            matches = re.finditer(pattern, documentation, re.IGNORECASE)
            for match in matches:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="clareza",
                    description=f"Descrição vaga encontrada: '{match.group()}'",
                    location=f"posicao_{match.start()}",
                    suggestion="Usar descrições mais específicas e detalhadas",
                    auto_fixable=False,
                    confidence=0.7
                ))
        
        # Verificar cobertura de ações
        total_actions = len(correlation_data.correlated_events)
        documented_actions = len(re.findall(r'^\s*\d+\.', documentation, re.MULTILINE))
        
        coverage_ratio = documented_actions / total_actions if total_actions > 0 else 0
        
        if coverage_ratio < 0.8:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="completude",
                description=f"Cobertura baixa: {documented_actions}/{total_actions} ações documentadas",
                location="documento_geral",
                suggestion="Incluir todas as ações identificadas na transcrição",
                auto_fixable=False,
                confidence=0.9
            ))
        
        # Verificar menções de elementos UI
        ui_elements_mentioned = 0
        total_ui_elements = sum(len(event.ocr_result.ui_elements) 
                              for event in correlation_data.correlated_events 
                              if event.ocr_result)
        
        # Buscar referências a elementos UI
        ui_patterns = [r'botão\s+["\'][^"\']+["\']', r'campo\s+["\'][^"\']+["\']', 
                      r'menu\s+["\'][^"\']+["\']', r'link\s+["\'][^"\']+["\']']
        
        for pattern in ui_patterns:
            ui_elements_mentioned += len(re.findall(pattern, documentation, re.IGNORECASE))
        
        if total_ui_elements > 0 and ui_elements_mentioned < total_ui_elements * 0.5:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completude",
                description="Poucos elementos de interface mencionados explicitamente",
                location="documento_geral",
                suggestion="Incluir nomes específicos de botões, campos e menus identificados",
                auto_fixable=False,
                confidence=0.7
            ))
        
        return issues

    def _validate_domain_specific(self, documentation: str, domain: ProcessDomain) -> List[ValidationIssue]:
        """Validações específicas do domínio"""
        issues = []
        doc_lower = documentation.lower()
        
        if domain in self.quality_vocabularies:
            vocab = self.quality_vocabularies[domain]
            
            # Verificar termos obrigatórios
            if 'required_terms' in vocab:
                missing_terms = []
                for term in vocab['required_terms']:
                    if term not in doc_lower:
                        missing_terms.append(term)
                
                if missing_terms:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="dominio_especifico",
                        description=f"Termos importantes ausentes: {', '.join(missing_terms)}",
                        location="vocabulario",
                        suggestion=f"Incluir contexto sobre {', '.join(missing_terms)}",
                        auto_fixable=False,
                        confidence=0.6
                    ))
            
            # Verificações específicas por domínio
            if domain == ProcessDomain.AUTHENTICATION:
                if not any(term in doc_lower for term in ['segurança', 'credential', 'autenticação']):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="seguranca",
                        description="Considerar adicionar seção sobre aspectos de segurança",
                        location="documento_geral",
                        suggestion="Incluir validações de segurança e tratamento de falhas de login",
                        auto_fixable=False,
                        confidence=0.5
                    ))
            
            elif domain == ProcessDomain.FINANCIAL:
                if not any(term in doc_lower for term in ['validar', 'confirmar', 'aprovar']):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="controle_financeiro",
                        description="Faltam controles de validação financeira",
                        location="documento_geral",
                        suggestion="Incluir passos de validação de valores e confirmação de transações",
                        auto_fixable=False,
                        confidence=0.7
                    ))
        
        return issues

    def _validate_correlation_quality(self, documentation: str, correlation_data: CorrelatedProcess) -> List[ValidationIssue]:
        """Valida qualidade da correlação entre transcrição e documentação"""
        issues = []
        
        # Verificar qualidade geral da correlação
        if correlation_data.correlation_quality < 0.7:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="correlacao",
                description=f"Qualidade de correlação baixa: {correlation_data.correlation_quality:.2f}",
                location="processo_correlacao",
                suggestion="Revisar manualmente a correspondência entre ações e elementos de interface",
                auto_fixable=False,
                confidence=0.8
            ))
        
        # Verificar eventos não correlacionados
        uncorrelated_events = [event for event in correlation_data.correlated_events 
                             if event.correlation_score < 0.5]
        
        if len(uncorrelated_events) > len(correlation_data.correlated_events) * 0.3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="correlacao",
                description=f"{len(uncorrelated_events)} ações não foram bem correlacionadas",
                location="eventos_correlacao",
                suggestion="Verificar qualidade das imagens e transcrição",
                auto_fixable=False,
                confidence=0.85
            ))
        
        return issues

    def _validate_technical_quality(self, documentation: str) -> List[ValidationIssue]:
        """Valida aspectos técnicos da documentação"""
        issues = []
        
        # Verificar problemas de formatação
        for pattern in self.common_patterns['formatting_issues']:
            matches = re.finditer(pattern, documentation)
            for match in matches:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="formatacao",
                    description=f"Problema de formatação: '{match.group()}'",
                    location=f"posicao_{match.start()}",
                    suggestion="Corrigir formatação do texto",
                    auto_fixable=True,
                    confidence=0.8
                ))
        
        # Verificar erros técnicos mencionados sem tratamento
        for pattern in self.common_patterns['technical_errors']:
            matches = re.finditer(pattern, documentation, re.IGNORECASE)
            for match in matches:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="tratamento_erros",
                    description=f"Possível erro não tratado: '{match.group()}'",
                    location=f"posicao_{match.start()}",
                    suggestion="Adicionar seção de tratamento de erros e exceções",
                    auto_fixable=False,
                    confidence=0.6
                ))
        
        # Verificar comprimento dos passos
        step_lines = re.findall(r'^\s*\d+\.\s*(.+)$', documentation, re.MULTILINE)
        for i, step in enumerate(step_lines):
            if len(step.strip()) < 10:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="detalhamento",
                    description=f"Passo {i+1} muito curto ou incompleto",
                    location=f"passo_{i+1}",
                    suggestion="Adicionar mais detalhes ao passo",
                    auto_fixable=False,
                    confidence=0.7
                ))
        
        return issues

    def _calculate_completeness_metrics(self, documentation: str, correlation_data: CorrelatedProcess) -> Dict[str, float]:
        """Calcula métricas de completude"""
        metrics = {}
        
        # Cobertura de ações
        total_actions = len(correlation_data.correlated_events)
        documented_steps = len(re.findall(r'^\s*\d+\.', documentation, re.MULTILINE))
        metrics['action_coverage'] = min(1.0, documented_steps / total_actions) if total_actions > 0 else 0.0
        
        # Cobertura de elementos UI
        total_ui_elements = sum(len(event.ocr_result.ui_elements) 
                              for event in correlation_data.correlated_events 
                              if event.ocr_result)
        
        ui_mentions = len(re.findall(r'(botão|campo|menu|link)\s+["\'][^"\']+["\']', 
                                   documentation, re.IGNORECASE))
        metrics['ui_coverage'] = min(1.0, ui_mentions / total_ui_elements) if total_ui_elements > 0 else 0.0
        
        # Presença de seções essenciais
        essential_sections = ['objetivo', 'passos', 'pré-requisitos', 'validação']
        doc_lower = documentation.lower()
        sections_present = sum(1 for section in essential_sections if section in doc_lower)
        metrics['section_completeness'] = sections_present / len(essential_sections)
        
        # Detalhamento médio
        step_lengths = [len(step.strip()) for step in re.findall(r'^\s*\d+\.\s*(.+)$', documentation, re.MULTILINE)]
        avg_step_length = sum(step_lengths) / len(step_lengths) if step_lengths else 0
        metrics['detail_level'] = min(1.0, avg_step_length / 50.0)  # Normalizado para ~50 chars
        
        return metrics

    def _calculate_quality_metrics(self, documentation: str, issues: List[ValidationIssue]) -> Dict[str, float]:
        """Calcula métricas de qualidade"""
        metrics = {}
        
        # Severidade dos problemas
        severity_weights = {
            ValidationSeverity.INFO: 0.1,
            ValidationSeverity.WARNING: 0.3,
            ValidationSeverity.ERROR: 0.7,
            ValidationSeverity.CRITICAL: 1.0
        }
        
        total_severity = sum(severity_weights[issue.severity] for issue in issues)
        doc_length = len(documentation.split())
        
        metrics['error_density'] = total_severity / max(doc_length, 100) * 100  # Erros por 100 palavras
        metrics['clarity_score'] = max(0.0, 1.0 - (total_severity / 10.0))  # Normalizado
        
        # Consistência (poucos problemas de formatação)
        formatting_issues = [issue for issue in issues if issue.category == 'formatacao']
        metrics['consistency_score'] = max(0.0, 1.0 - len(formatting_issues) / 20.0)
        
        # Precisão técnica
        technical_issues = [issue for issue in issues if issue.category in ['tratamento_erros', 'correlacao']]
        metrics['technical_accuracy'] = max(0.0, 1.0 - len(technical_issues) / 10.0)
        
        return metrics

    def _calculate_overall_score(self, completeness: Dict[str, float], 
                               quality: Dict[str, float], 
                               issues: List[ValidationIssue]) -> float:
        """Calcula score geral da documentação"""
        
        # Componentes do score
        completeness_score = sum(completeness.values()) / len(completeness) if completeness else 0.0
        
        # Penalizar por issues críticos
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        critical_penalty = len(critical_issues) * 0.2
        
        error_issues = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR]
        error_penalty = len(error_issues) * 0.1
        
        # Score final
        base_score = (
            completeness_score * self.scoring_weights['completeness'] +
            quality.get('clarity_score', 0.5) * self.scoring_weights['clarity'] +
            quality.get('consistency_score', 0.5) * self.scoring_weights['consistency'] +
            quality.get('technical_accuracy', 0.5) * self.scoring_weights['technical_quality'] +
            0.7 * self.scoring_weights['accuracy']  # Baseline accuracy
        )
        
        final_score = max(0.0, base_score - critical_penalty - error_penalty)
        
        return min(1.0, final_score)

    def _identify_document_domain(self, documentation: str, correlation_data: CorrelatedProcess) -> ProcessDomain:
        """Identifica domínio do documento"""
        # Usar o domain manager para identificação
        actions_text = " ".join([event.action.raw_text for event in correlation_data.correlated_events])
        ui_elements = []
        
        for event in correlation_data.correlated_events:
            if event.ocr_result:
                ui_elements.extend([elem.text for elem in event.ocr_result.ui_elements])
        
        return self.domain_manager.identify_domain(documentation + " " + actions_text, ui_elements, [])

    def _generate_improvement_suggestions(self, issues: List[ValidationIssue], 
                                        completeness: Dict[str, float]) -> List[str]:
        """Gera sugestões de melhoria"""
        suggestions = []
        
        # Sugestões baseadas em métricas baixas
        if completeness.get('action_coverage', 0) < 0.8:
            suggestions.append("Incluir todos os passos identificados na transcrição")
        
        if completeness.get('ui_coverage', 0) < 0.6:
            suggestions.append("Mencionar explicitamente os nomes dos botões, campos e menus")
        
        if completeness.get('section_completeness', 0) < 0.7:
            suggestions.append("Adicionar seções de pré-requisitos e validações")
        
        # Sugestões baseadas em issues frequentes
        issue_categories = {}
        for issue in issues:
            if issue.category not in issue_categories:
                issue_categories[issue.category] = 0
            issue_categories[issue.category] += 1
        
        if issue_categories.get('clareza', 0) > 2:
            suggestions.append("Substituir descrições vagas por termos específicos")
        
        if issue_categories.get('tratamento_erros', 0) > 0:
            suggestions.append("Adicionar seção sobre tratamento de erros e cenários alternativos")
        
        if issue_categories.get('correlacao', 0) > 1:
            suggestions.append("Revisar qualidade das imagens e transcrição para melhor correlação")
        
        return suggestions[:5]  # Limitar a 5 sugestões principais

    def _identify_auto_fixes(self, issues: List[ValidationIssue]) -> List[str]:
        """Identifica correções que podem ser aplicadas automaticamente"""
        auto_fixes = []
        
        fixable_issues = [issue for issue in issues if issue.auto_fixable]
        
        for issue in fixable_issues:
            if issue.category == 'formatacao':
                auto_fixes.append(f"Corrigir formatação: {issue.description}")
            elif issue.category == 'estrutura' and 'seção' in issue.description:
                auto_fixes.append(f"Adicionar seção faltante: {issue.description}")
        
        return auto_fixes

    def apply_auto_fixes(self, documentation: str, validation_report: ValidationReport) -> str:
        """Aplica correções automáticas à documentação"""
        fixed_doc = documentation
        
        # Aplicar correções de formatação
        for issue in validation_report.issues:
            if issue.auto_fixable and issue.category == 'formatacao':
                # Correções básicas de formatação
                fixed_doc = re.sub(r'\s{3,}', ' ', fixed_doc)  # Múltiplos espaços
                fixed_doc = re.sub(r'[\.]{3,}', '...', fixed_doc)  # Múltiplos pontos
        
        # Adicionar seções básicas se faltarem
        doc_lower = fixed_doc.lower()
        
        if 'objetivo' not in doc_lower:
            objective_section = "\n## Objetivo\n\nExecutar processo conforme procedimentos estabelecidos.\n"
            fixed_doc = objective_section + fixed_doc
        
        if 'pré-requisitos' not in doc_lower and 'prerequisitos' not in doc_lower:
            prereq_section = "\n## Pré-requisitos\n\n- Sistema acessível\n- Permissões necessárias\n- Dados requeridos disponíveis\n"
            fixed_doc += prereq_section
        
        return fixed_doc

    def export_validation_report(self, report: ValidationReport, output_path: str) -> bool:
        """Exporta relatório de validação para arquivo"""
        try:
            report_data = {
                'document_id': report.document_id,
                'validation_timestamp': report.validation_timestamp,
                'overall_score': report.overall_score,
                'domain': report.domain.value,
                'issues': [
                    {
                        'severity': issue.severity.value,
                        'category': issue.category,
                        'description': issue.description,
                        'location': issue.location,
                        'suggestion': issue.suggestion,
                        'auto_fixable': issue.auto_fixable,
                        'confidence': issue.confidence
                    }
                    for issue in report.issues
                ],
                'completeness_metrics': report.completeness_metrics,
                'quality_metrics': report.quality_metrics,
                'suggestions_for_improvement': report.suggestions_for_improvement,
                'auto_fixes_applied': report.auto_fixes_applied
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Erro ao exportar relatório: {e}")
            return False