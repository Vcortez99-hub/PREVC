"""
Correlacionador temporal avançado para MVP v2
Melhora a correlação entre transcrições e screenshots usando timestamps e análise contextual
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from difflib import SequenceMatcher

from mvp.parsers.transcription import Action, TranscriptionSegment
from mvp.processors.ocr import OCRResult, UIElement
from mvp.processors.correlator import CorrelatedEvent, CorrelatedProcess

@dataclass
class TemporalMarker:
    """Marcador temporal para correlação"""
    timestamp: str
    source: str  # 'audio', 'image', 'system'
    content: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass  
class ContextualMatch:
    """Match contextual avançado"""
    action: Action
    ui_element: UIElement
    temporal_score: float
    semantic_score: float
    context_score: float
    combined_score: float
    match_type: str
    confidence_factors: List[str]

class AdvancedTemporalCorrelator:
    """Correlacionador temporal avançado com análise contextual"""
    
    def __init__(self):
        # Configurações de correlação
        self.min_correlation_threshold = 0.6
        self.temporal_window_seconds = 30  # Janela temporal para busca
        self.context_window_actions = 3   # Ações antes/depois para contexto
        
        # Padrões de elementos UI por tipo de ação
        self.action_ui_patterns = {
            'click': {
                'preferred_types': ['button', 'link', 'checkbox', 'menu'],
                'required_keywords': ['clica', 'pressiona', 'seleciona'],
                'ui_indicators': ['btn', 'button', 'link', 'menu', 'item']
            },
            'type': {
                'preferred_types': ['field', 'input', 'textbox'],
                'required_keywords': ['digita', 'escreve', 'preenche', 'informa'],
                'ui_indicators': ['input', 'field', 'texto', 'campo', 'caixa']
            },
            'select': {
                'preferred_types': ['dropdown', 'combobox', 'select', 'menu'],
                'required_keywords': ['seleciona', 'escolhe', 'opta'],
                'ui_indicators': ['dropdown', 'combo', 'lista', 'opção']
            },
            'navigate': {
                'preferred_types': ['link', 'button', 'menu'],
                'required_keywords': ['navega', 'vai', 'acessa', 'abre'],
                'ui_indicators': ['página', 'tela', 'aba', 'seção']
            }
        }
        
        # Vocabulário contextual para melhor matching
        self.contextual_vocabulary = {
            'authentication': ['login', 'senha', 'usuário', 'entrar', 'acesso', 'autenticação'],
            'form_filling': ['formulário', 'dados', 'informações', 'preencher', 'campo'],
            'navigation': ['menu', 'página', 'tela', 'navegar', 'ir para'],
            'confirmation': ['confirmar', 'ok', 'salvar', 'enviar', 'finalizar'],
            'search': ['buscar', 'pesquisar', 'filtrar', 'procurar', 'localizar']
        }

    def correlate_with_temporal_analysis(self, 
                                       actions: List[Action], 
                                       ocr_results: List[OCRResult],
                                       image_timestamps: Optional[List[str]] = None) -> CorrelatedProcess:
        """
        Correlaciona ações com resultados visuais usando análise temporal avançada
        """
        
        # Extrair marcadores temporais
        temporal_markers = self._extract_temporal_markers(actions, ocr_results, image_timestamps)
        
        # Criar contexto para cada ação
        action_contexts = self._build_action_contexts(actions)
        
        # Correlação avançada
        advanced_correlations = []
        
        for action in actions:
            # Buscar matches na janela temporal
            candidate_matches = self._find_temporal_candidates(
                action, ocr_results, temporal_markers
            )
            
            # Avaliar matches com análise contextual
            contextual_matches = []
            for candidate in candidate_matches:
                match = self._evaluate_contextual_match(
                    action, candidate, action_contexts.get(action.sequence, {})
                )
                if match and match.combined_score >= self.min_correlation_threshold:
                    contextual_matches.append(match)
            
            # Selecionar melhor match
            best_match = self._select_best_match(contextual_matches)
            
            if best_match:
                # Encontrar OCR result correspondente
                corresponding_ocr = next(
                    (ocr for ocr in ocr_results 
                     if any(elem.text == best_match.ui_element.text 
                           for elem in ocr.ui_elements)), None
                )
                
                correlation_event = CorrelatedEvent(
                    action=action,
                    ocr_result=corresponding_ocr,
                    matched_ui_element=best_match.ui_element,
                    correlation_score=best_match.combined_score,
                    correlation_method=f"temporal_advanced_{best_match.match_type}",
                    timestamp_diff=best_match.temporal_score,
                    notes=self._generate_advanced_notes(best_match)
                )
            else:
                # Sem correlação encontrada
                correlation_event = CorrelatedEvent(
                    action=action,
                    ocr_result=None,
                    matched_ui_element=None,
                    correlation_score=0.0,
                    correlation_method="temporal_no_match",
                    timestamp_diff=0.0,
                    notes="Nenhuma correlação temporal/contextual encontrada"
                )
            
            advanced_correlations.append(correlation_event)
        
        # Calcular qualidade geral da correlação
        correlation_quality = self._calculate_advanced_correlation_quality(advanced_correlations)
        successfully_correlated = len([e for e in advanced_correlations 
                                     if e.correlation_score >= self.min_correlation_threshold])
        
        return CorrelatedProcess(
            session_id="",  # Será definido externamente
            correlated_events=advanced_correlations,
            transcription_summary=self._create_advanced_transcription_summary(actions),
            ocr_summary=[self._create_ocr_summary(ocr) for ocr in ocr_results],
            correlation_quality=correlation_quality,
            total_actions=len(actions),
            successfully_correlated=successfully_correlated
        )

    def _extract_temporal_markers(self, 
                                actions: List[Action], 
                                ocr_results: List[OCRResult],
                                image_timestamps: Optional[List[str]]) -> List[TemporalMarker]:
        """Extrai marcadores temporais de todas as fontes"""
        markers = []
        
        # Marcadores de ações (áudio)
        for action in actions:
            marker = TemporalMarker(
                timestamp=action.timestamp,
                source='audio',
                content=f"{action.action_type}:{action.element}",
                confidence=action.confidence,
                metadata={
                    'speaker': action.speaker,
                    'sequence': action.sequence,
                    'raw_text': action.raw_text
                }
            )
            markers.append(marker)
        
        # Marcadores de imagens
        for i, ocr_result in enumerate(ocr_results):
            # Usar timestamp fornecido ou inferir baseado na ordem
            if image_timestamps and i < len(image_timestamps):
                timestamp = image_timestamps[i]
            else:
                # Inferir timestamp baseado na sequência (placeholder)
                timestamp = f"00:{i*2:02d}:00"
            
            marker = TemporalMarker(
                timestamp=timestamp,
                source='image',
                content=f"screen:{ocr_result.original_image_path}",
                confidence=ocr_result.confidence,
                metadata={
                    'ui_elements_count': len(ocr_result.ui_elements),
                    'processing_time': ocr_result.processing_time
                }
            )
            markers.append(marker)
        
        # Ordenar por timestamp
        markers.sort(key=lambda x: self._timestamp_to_seconds(x.timestamp))
        
        return markers

    def _build_action_contexts(self, actions: List[Action]) -> Dict[int, Dict[str, Any]]:
        """Constrói contexto para cada ação baseado em ações vizinhas"""
        contexts = {}
        
        for i, action in enumerate(actions):
            context = {
                'preceding_actions': [],
                'following_actions': [],
                'semantic_context': [],
                'process_phase': self._identify_process_phase(action, actions)
            }
            
            # Ações precedentes
            start_idx = max(0, i - self.context_window_actions)
            context['preceding_actions'] = actions[start_idx:i]
            
            # Ações seguintes
            end_idx = min(len(actions), i + self.context_window_actions + 1)
            context['following_actions'] = actions[i+1:end_idx]
            
            # Contexto semântico
            all_nearby_actions = context['preceding_actions'] + context['following_actions']
            context['semantic_context'] = self._identify_semantic_context(
                action, all_nearby_actions
            )
            
            contexts[action.sequence] = context
        
        return contexts

    def _find_temporal_candidates(self, 
                                action: Action, 
                                ocr_results: List[OCRResult],
                                temporal_markers: List[TemporalMarker]) -> List[Tuple[OCRResult, UIElement]]:
        """Encontra candidatos dentro da janela temporal"""
        candidates = []
        action_time = self._timestamp_to_seconds(action.timestamp)
        
        for ocr_result in ocr_results:
            # Encontrar timestamp da imagem
            image_markers = [m for m in temporal_markers 
                           if m.source == 'image' and ocr_result.original_image_path in m.content]
            
            if not image_markers:
                continue
                
            image_time = self._timestamp_to_seconds(image_markers[0].timestamp)
            time_diff = abs(action_time - image_time)
            
            # Verificar se está dentro da janela temporal
            if time_diff <= self.temporal_window_seconds:
                for ui_element in ocr_result.ui_elements:
                    candidates.append((ocr_result, ui_element))
        
        return candidates

    def _evaluate_contextual_match(self, 
                                 action: Action, 
                                 candidate: Tuple[OCRResult, UIElement],
                                 context: Dict[str, Any]) -> Optional[ContextualMatch]:
        """Avalia match usando análise contextual avançada"""
        ocr_result, ui_element = candidate
        
        # Calcular scores individuais
        temporal_score = self._calculate_temporal_score(action, ocr_result)
        semantic_score = self._calculate_semantic_score(action, ui_element)
        context_score = self._calculate_context_score(action, ui_element, context)
        
        # Score combinado com pesos
        weights = {'temporal': 0.3, 'semantic': 0.4, 'context': 0.3}
        combined_score = (
            temporal_score * weights['temporal'] +
            semantic_score * weights['semantic'] +
            context_score * weights['context']
        )
        
        # Determinar tipo de match
        match_type = self._determine_match_type(semantic_score, context_score, temporal_score)
        
        # Fatores de confiança
        confidence_factors = self._identify_confidence_factors(
            action, ui_element, temporal_score, semantic_score, context_score
        )
        
        return ContextualMatch(
            action=action,
            ui_element=ui_element,
            temporal_score=temporal_score,
            semantic_score=semantic_score,
            context_score=context_score,
            combined_score=combined_score,
            match_type=match_type,
            confidence_factors=confidence_factors
        )

    def _calculate_temporal_score(self, action: Action, ocr_result: OCRResult) -> float:
        """Calcula score temporal baseado na proximidade dos timestamps"""
        # Para MVP, usar ordem sequencial como proxy temporal
        # Em implementação completa, usar timestamps reais
        return 0.8  # Placeholder - assumindo proximidade temporal razoável

    def _calculate_semantic_score(self, action: Action, ui_element: UIElement) -> float:
        """Calcula score semântico baseado na correspondência de conteúdo"""
        score = 0.0
        
        # Normalizar textos
        action_element = self._normalize_text(action.element)
        ui_text = self._normalize_text(ui_element.text)
        
        # 1. Correspondência exata
        if action_element == ui_text:
            score += 0.4
        
        # 2. Correspondência parcial
        similarity = SequenceMatcher(None, action_element, ui_text).ratio()
        score += similarity * 0.3
        
        # 3. Compatibilidade de tipo de ação com tipo de elemento
        if action.action_type in self.action_ui_patterns:
            patterns = self.action_ui_patterns[action.action_type]
            if ui_element.type in patterns['preferred_types']:
                score += 0.2
        
        # 4. Palavras-chave contextuais
        if self._has_contextual_keywords(action_element, ui_text, action.action_type):
            score += 0.1
        
        return min(1.0, score)

    def _calculate_context_score(self, 
                               action: Action, 
                               ui_element: UIElement, 
                               context: Dict[str, Any]) -> float:
        """Calcula score contextual baseado no contexto do processo"""
        score = 0.0
        
        # 1. Contexto semântico do processo
        semantic_context = context.get('semantic_context', [])
        for context_type in semantic_context:
            if context_type in self.contextual_vocabulary:
                vocab = self.contextual_vocabulary[context_type]
                if any(word in ui_element.text.lower() for word in vocab):
                    score += 0.2
        
        # 2. Fase do processo
        process_phase = context.get('process_phase', 'unknown')
        if self._element_matches_process_phase(ui_element, process_phase):
            score += 0.3
        
        # 3. Consistência com ações precedentes/seguintes
        consistency_score = self._calculate_action_consistency(
            action, context.get('preceding_actions', []), 
            context.get('following_actions', [])
        )
        score += consistency_score * 0.2
        
        # 4. Confiança do elemento UI
        score += ui_element.confidence * 0.3
        
        return min(1.0, score)

    def _select_best_match(self, matches: List[ContextualMatch]) -> Optional[ContextualMatch]:
        """Seleciona o melhor match baseado no score combinado"""
        if not matches:
            return None
        
        # Ordenar por score combinado
        matches.sort(key=lambda x: x.combined_score, reverse=True)
        
        best_match = matches[0]
        
        # Verificar se o melhor match atende aos critérios mínimos
        if best_match.combined_score >= self.min_correlation_threshold:
            return best_match
        
        return None

    def _identify_process_phase(self, action: Action, all_actions: List[Action]) -> str:
        """Identifica a fase do processo baseada na posição e contexto"""
        total_actions = len(all_actions)
        position_ratio = action.sequence / total_actions
        
        # Identificar baseado em palavras-chave
        text = action.raw_text.lower()
        
        if any(word in text for word in ['login', 'entrar', 'acesso', 'autenticar']):
            return 'authentication'
        elif any(word in text for word in ['preencher', 'dados', 'informações', 'formulário']):
            return 'form_filling'
        elif any(word in text for word in ['navegar', 'menu', 'página', 'ir para']):
            return 'navigation'
        elif any(word in text for word in ['confirmar', 'salvar', 'finalizar', 'enviar']):
            return 'confirmation'
        elif any(word in text for word in ['buscar', 'pesquisar', 'filtrar']):
            return 'search'
        elif position_ratio < 0.3:
            return 'initialization'
        elif position_ratio > 0.7:
            return 'finalization'
        else:
            return 'main_process'

    def _identify_semantic_context(self, 
                                 action: Action, 
                                 nearby_actions: List[Action]) -> List[str]:
        """Identifica contexto semântico baseado em ações próximas"""
        contexts = []
        
        all_text = action.raw_text + ' ' + ' '.join(a.raw_text for a in nearby_actions)
        all_text = all_text.lower()
        
        for context_type, keywords in self.contextual_vocabulary.items():
            if any(keyword in all_text for keyword in keywords):
                contexts.append(context_type)
        
        return contexts

    def _has_contextual_keywords(self, action_text: str, ui_text: str, action_type: str) -> bool:
        """Verifica se há palavras-chave contextuais relevantes"""
        if action_type not in self.action_ui_patterns:
            return False
        
        patterns = self.action_ui_patterns[action_type]
        combined_text = (action_text + ' ' + ui_text).lower()
        
        return any(keyword in combined_text for keyword in patterns['ui_indicators'])

    def _element_matches_process_phase(self, ui_element: UIElement, phase: str) -> bool:
        """Verifica se elemento UI é consistente com a fase do processo"""
        element_text = ui_element.text.lower()
        
        phase_indicators = {
            'authentication': ['login', 'senha', 'entrar', 'acesso'],
            'form_filling': ['nome', 'dados', 'campo', 'informações'],
            'navigation': ['menu', 'página', 'voltar', 'próximo'],
            'confirmation': ['ok', 'confirmar', 'salvar', 'enviar'],
            'search': ['buscar', 'filtro', 'pesquisar']
        }
        
        if phase in phase_indicators:
            return any(indicator in element_text for indicator in phase_indicators[phase])
        
        return True  # Neutro para fases desconhecidas

    def _calculate_action_consistency(self, 
                                    current_action: Action,
                                    preceding: List[Action], 
                                    following: List[Action]) -> float:
        """Calcula consistência com ações precedentes e seguintes"""
        consistency_score = 0.5  # Base neutral
        
        # Verificar padrões lógicos
        if preceding:
            last_action = preceding[-1]
            if self._actions_are_logically_related(last_action, current_action):
                consistency_score += 0.3
        
        if following:
            next_action = following[0]
            if self._actions_are_logically_related(current_action, next_action):
                consistency_score += 0.2
        
        return min(1.0, consistency_score)

    def _actions_are_logically_related(self, action1: Action, action2: Action) -> bool:
        """Verifica se duas ações são logicamente relacionadas"""
        logical_sequences = [
            (['navigate', 'click'], ['type']),  # Navegar/clicar antes de digitar
            (['type'], ['click']),              # Digitar antes de clicar (ex: submit)
            (['select'], ['click']),            # Selecionar antes de confirmar
            (['click'], ['navigate'])           # Clicar pode levar à navegação
        ]
        
        for seq in logical_sequences:
            if action1.action_type in seq[0] and action2.action_type in seq[1]:
                return True
        
        return False

    def _determine_match_type(self, semantic: float, context: float, temporal: float) -> str:
        """Determina o tipo de match baseado nos scores"""
        if semantic >= 0.8:
            return "high_semantic"
        elif context >= 0.8:
            return "high_context"
        elif temporal >= 0.8:
            return "high_temporal"
        elif semantic >= 0.6 and context >= 0.6:
            return "semantic_context_balanced"
        elif semantic >= 0.6:
            return "semantic_dominant"
        elif context >= 0.6:
            return "context_dominant"
        else:
            return "low_confidence"

    def _identify_confidence_factors(self, 
                                   action: Action, 
                                   ui_element: UIElement,
                                   temporal: float, 
                                   semantic: float, 
                                   context: float) -> List[str]:
        """Identifica fatores que contribuem para a confiança"""
        factors = []
        
        if semantic >= 0.8:
            factors.append("Alta correspondência semântica")
        if context >= 0.8:
            factors.append("Alto contexto processual")
        if temporal >= 0.8:
            factors.append("Excelente proximidade temporal")
        if ui_element.confidence >= 0.9:
            factors.append("Alta confiança OCR")
        if action.confidence >= 0.9:
            factors.append("Alta confiança na identificação da ação")
        
        if not factors:
            factors.append("Correlação baseada em múltiplos fatores")
        
        return factors

    def _generate_advanced_notes(self, match: ContextualMatch) -> str:
        """Gera notas detalhadas sobre a correlação"""
        notes = f"Match tipo: {match.match_type} | "
        notes += f"Scores - Semântico: {match.semantic_score:.2f}, "
        notes += f"Contextual: {match.context_score:.2f}, "
        notes += f"Temporal: {match.temporal_score:.2f} | "
        notes += "Fatores: " + ", ".join(match.confidence_factors)
        
        return notes

    def _calculate_advanced_correlation_quality(self, events: List[CorrelatedEvent]) -> float:
        """Calcula qualidade geral da correlação avançada"""
        if not events:
            return 0.0
        
        # Score médio ponderado
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for event in events:
            # Peso baseado na confiança da ação original
            weight = event.action.confidence
            total_weighted_score += event.correlation_score * weight
            total_weight += weight
        
        average_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Fator de completude
        successfully_correlated = len([e for e in events if e.correlation_score >= self.min_correlation_threshold])
        completeness_factor = successfully_correlated / len(events)
        
        # Score final combinado
        final_score = (average_score * 0.7) + (completeness_factor * 0.3)
        
        return final_score

    def _create_advanced_transcription_summary(self, actions: List[Action]) -> Dict[str, Any]:
        """Cria resumo avançado da transcrição"""
        summary = {
            'total_actions': len(actions),
            'action_types': list(set(action.action_type for action in actions)),
            'speakers': list(set(action.speaker for action in actions)),
            'average_confidence': sum(action.confidence for action in actions) / len(actions) if actions else 0.0,
            'elements_mentioned': [action.element for action in actions],
            'process_phases': []
        }
        
        # Identificar fases do processo
        for action in actions:
            phase = self._identify_process_phase(action, actions)
            if phase not in summary['process_phases']:
                summary['process_phases'].append(phase)
        
        return summary

    def _create_ocr_summary(self, ocr_result: OCRResult) -> Dict[str, Any]:
        """Cria resumo do resultado OCR"""
        return {
            'image_path': ocr_result.original_image_path,
            'text_length': len(ocr_result.extracted_text),
            'confidence': ocr_result.confidence,
            'ui_elements_count': len(ocr_result.ui_elements),
            'ui_elements_types': list(set(el.type for el in ocr_result.ui_elements)),
            'processing_time': ocr_result.processing_time,
            'preprocessing_applied': ocr_result.preprocessing_applied
        }

    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação"""
        # Converter para minúsculas
        text = text.lower()
        
        # Remover acentos básicos
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e',
            'í': 'i', 'î': 'i',
            'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'û': 'u',
            'ç': 'c'
        }
        for accented, plain in replacements.items():
            text = text.replace(accented, plain)
        
        # Remover pontuação e caracteres especiais
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Converte timestamp para segundos"""
        try:
            # Formato esperado: HH:MM:SS.mmm ou HH:MM:SS
            parts = timestamp.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0.0