from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from difflib import SequenceMatcher
from mvp.parsers.transcription import Action
from mvp.processors.ocr import OCRResult, UIElement

@dataclass
class CorrelatedEvent:
    """Evento correlacionado entre áudio e visual"""
    action: Action
    ocr_result: Optional[OCRResult]
    matched_ui_element: Optional[UIElement]
    correlation_score: float
    correlation_method: str
    timestamp_diff: float
    notes: str

@dataclass
class CorrelatedProcess:
    """Processo completo correlacionado"""
    session_id: str
    correlated_events: List[CorrelatedEvent]
    transcription_summary: Dict[str, Any]
    ocr_summary: List[Dict[str, Any]]
    correlation_quality: float
    total_actions: int
    successfully_correlated: int

class BasicCorrelator:
    """Correlacionador básico entre transcrições e screenshots"""
    
    def __init__(self):
        # Thresholds para correlação
        self.min_correlation_score = 0.5
        self.max_timestamp_diff = 60.0  # segundos
        
        # Sinônimos para melhorar matching
        self.synonyms = {
            'botão': ['button', 'btn', 'botao'],
            'campo': ['field', 'input', 'caixa', 'texto'],
            'menu': ['dropdown', 'lista', 'seleção', 'selecao'],
            'link': ['hiperlink', 'conexão', 'ligação'],
            'checkbox': ['caixa de seleção', 'marcar', 'selecionar'],
            'formulário': ['form', 'formulario', 'tela'],
            'tela': ['screen', 'página', 'pagina', 'janela'],
            'sistema': ['aplicação', 'aplicacao', 'programa', 'software']
        }

    def correlate_audio_visual(self, 
                              actions: List[Action], 
                              ocr_results: List[OCRResult]) -> CorrelatedProcess:
        """Correlaciona ações de áudio com resultados visuais"""
        
        correlated_events = []
        
        for action in actions:
            # Encontrar melhor correspondência visual
            best_match = self._find_best_visual_match(action, ocr_results)
            
            if best_match:
                ocr_result, ui_element, score, method = best_match
                
                # Calcular diferença temporal (aproximada)
                timestamp_diff = self._calculate_timestamp_diff(action.timestamp, ocr_result)
                
                correlated_event = CorrelatedEvent(
                    action=action,
                    ocr_result=ocr_result,
                    matched_ui_element=ui_element,
                    correlation_score=score,
                    correlation_method=method,
                    timestamp_diff=timestamp_diff,
                    notes=self._generate_correlation_notes(action, ui_element, score)
                )
            else:
                # Ação sem correspondência visual
                correlated_event = CorrelatedEvent(
                    action=action,
                    ocr_result=None,
                    matched_ui_element=None,
                    correlation_score=0.0,
                    correlation_method="no_match",
                    timestamp_diff=0.0,
                    notes="Nenhuma correspondência visual encontrada"
                )
            
            correlated_events.append(correlated_event)
        
        # Calcular qualidade geral da correlação
        correlation_quality = self._calculate_correlation_quality(correlated_events)
        successfully_correlated = len([e for e in correlated_events if e.correlation_score >= self.min_correlation_score])
        
        return CorrelatedProcess(
            session_id="",  # Será definido externamente
            correlated_events=correlated_events,
            transcription_summary=self._create_transcription_summary(actions),
            ocr_summary=[self._create_ocr_summary(ocr) for ocr in ocr_results],
            correlation_quality=correlation_quality,
            total_actions=len(actions),
            successfully_correlated=successfully_correlated
        )

    def _find_best_visual_match(self, action: Action, ocr_results: List[OCRResult]) -> Optional[Tuple[OCRResult, UIElement, float, str]]:
        """Encontra a melhor correspondência visual para uma ação"""
        best_match = None
        best_score = 0.0
        
        for ocr_result in ocr_results:
            # Tentar matching direto com elementos UI
            for ui_element in ocr_result.ui_elements:
                score, method = self._calculate_element_match_score(action, ui_element)
                
                if score > best_score and score >= self.min_correlation_score:
                    best_score = score
                    best_match = (ocr_result, ui_element, score, method)
            
            # Se não encontrou match com elementos UI, tentar matching com texto geral
            if not best_match or best_score < 0.7:
                text_score, text_method = self._calculate_text_match_score(action, ocr_result.extracted_text)
                
                if text_score > best_score and text_score >= self.min_correlation_score:
                    best_score = text_score
                    # Criar UIElement genérico baseado no texto
                    generic_element = UIElement(
                        type="generic",
                        text=self._extract_relevant_text(action.element, ocr_result.extracted_text),
                        confidence=0.6,
                        position=(0, 0, 0, 0),
                        context=ocr_result.extracted_text[:100] + "..." if len(ocr_result.extracted_text) > 100 else ocr_result.extracted_text
                    )
                    best_match = (ocr_result, generic_element, text_score, text_method)
        
        return best_match

    def _calculate_element_match_score(self, action: Action, ui_element: UIElement) -> Tuple[float, str]:
        """Calcula score de correspondência entre ação e elemento UI"""
        score = 0.0
        method = "element_match"
        
        # Normalizar textos para comparação
        action_element = self._normalize_text(action.element)
        ui_text = self._normalize_text(ui_element.text)
        
        # 1. Correspondência exata
        if action_element == ui_text:
            return 1.0, "exact_match"
        
        # 2. Correspondência parcial usando SequenceMatcher
        similarity = SequenceMatcher(None, action_element, ui_text).ratio()
        score += similarity * 0.6
        
        # 3. Verificar se tipo de ação combina com tipo de elemento
        action_type_score = self._match_action_to_ui_type(action.action_type, ui_element.type)
        score += action_type_score * 0.2
        
        # 4. Verificar palavras-chave comuns
        keyword_score = self._match_keywords(action_element, ui_text)
        score += keyword_score * 0.2
        
        # 5. Bonus por confiança do elemento UI
        score += ui_element.confidence * 0.1
        
        return min(1.0, score), method

    def _calculate_text_match_score(self, action: Action, extracted_text: str) -> Tuple[float, str]:
        """Calcula score de correspondência entre ação e texto extraído geral"""
        score = 0.0
        method = "text_match"
        
        action_element = self._normalize_text(action.element)
        text_normalized = self._normalize_text(extracted_text)
        
        # Verificar se elemento mencionado aparece no texto
        if action_element in text_normalized:
            score += 0.7
            method = "text_contains"
        else:
            # Buscar por palavras individuais
            action_words = action_element.split()
            text_words = text_normalized.split()
            
            matches = sum(1 for word in action_words if word in text_words and len(word) > 2)
            if len(action_words) > 0:
                word_match_ratio = matches / len(action_words)
                score += word_match_ratio * 0.5
                method = "word_match"
        
        return score, method

    def _match_action_to_ui_type(self, action_type: str, ui_type: str) -> float:
        """Verifica se tipo de ação combina com tipo de elemento UI"""
        compatibility_matrix = {
            'click': ['button', 'link', 'checkbox', 'menu'],
            'type': ['field', 'input'],
            'select': ['menu', 'dropdown', 'checkbox'],
            'navigate': ['link', 'button', 'menu']
        }
        
        compatible_types = compatibility_matrix.get(action_type, [])
        return 1.0 if ui_type in compatible_types else 0.3

    def _match_keywords(self, text1: str, text2: str) -> float:
        """Verifica correspondência usando sinônimos"""
        score = 0.0
        
        for word1 in text1.split():
            for word2 in text2.split():
                if word1 == word2:
                    score += 0.5
                else:
                    # Verificar sinônimos
                    for canonical, synonyms in self.synonyms.items():
                        if (word1 == canonical and word2 in synonyms) or \
                           (word2 == canonical and word1 in synonyms) or \
                           (word1 in synonyms and word2 in synonyms):
                            score += 0.3
                            break
        
        return min(1.0, score)

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

    def _extract_relevant_text(self, element_name: str, full_text: str) -> str:
        """Extrai texto relevante baseado no nome do elemento"""
        element_normalized = self._normalize_text(element_name)
        text_normalized = self._normalize_text(full_text)
        
        # Tentar encontrar linha que contém o elemento
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        for line in lines:
            line_normalized = self._normalize_text(line)
            if element_normalized in line_normalized:
                return line
        
        # Se não encontrou, retornar palavras relevantes
        words = element_normalized.split()
        relevant_lines = []
        
        for line in lines:
            line_normalized = self._normalize_text(line)
            if any(word in line_normalized for word in words if len(word) > 2):
                relevant_lines.append(line)
        
        return ' | '.join(relevant_lines[:3]) if relevant_lines else element_name

    def _calculate_timestamp_diff(self, action_timestamp: str, ocr_result: OCRResult) -> float:
        """Calcula diferença temporal aproximada"""
        # Para MVP, vamos assumir diferença baseada na ordem dos arquivos
        # Em versão futura, usaríamos timestamps reais das imagens
        return 0.0  # Placeholder

    def _generate_correlation_notes(self, action: Action, ui_element: Optional[UIElement], score: float) -> str:
        """Gera notas sobre a correlação"""
        if not ui_element:
            return "Elemento visual não encontrado"
        
        if score >= 0.9:
            return "Correlação excelente - correspondência quase exata"
        elif score >= 0.7:
            return "Correlação boa - alta probabilidade de correspondência"
        elif score >= 0.5:
            return "Correlação moderada - verificar manualmente"
        else:
            return "Correlação baixa - possível falso positivo"

    def _calculate_correlation_quality(self, events: List[CorrelatedEvent]) -> float:
        """Calcula qualidade geral da correlação"""
        if not events:
            return 0.0
        
        total_score = sum(event.correlation_score for event in events)
        average_score = total_score / len(events)
        
        # Penalizar se muitos eventos não foram correlacionados
        correlated_ratio = len([e for e in events if e.correlation_score >= self.min_correlation_score]) / len(events)
        
        return (average_score * 0.7) + (correlated_ratio * 0.3)

    def _create_transcription_summary(self, actions: List[Action]) -> Dict[str, Any]:
        """Cria resumo da transcrição"""
        return {
            'total_actions': len(actions),
            'action_types': list(set(action.action_type for action in actions)),
            'speakers': list(set(action.speaker for action in actions)),
            'average_confidence': sum(action.confidence for action in actions) / len(actions) if actions else 0.0,
            'elements_mentioned': [action.element for action in actions]
        }

    def _create_ocr_summary(self, ocr_result: OCRResult) -> Dict[str, Any]:
        """Cria resumo do resultado OCR"""
        return {
            'image_path': ocr_result.original_image_path,
            'text_length': len(ocr_result.extracted_text),
            'confidence': ocr_result.confidence,
            'ui_elements_count': len(ocr_result.ui_elements),
            'ui_elements_types': list(set(el.type for el in ocr_result.ui_elements)),
            'processing_time': ocr_result.processing_time
        }