import re
from typing import List, Dict, Any
from dataclasses import dataclass
import webvtt
import os

@dataclass
class Action:
    """Representa uma ação identificada na transcrição"""
    action_type: str  # click, type, select, navigate
    element: str      # elemento mencionado
    sequence: int     # ordem na sequência
    timestamp: str    # quando foi mencionado
    speaker: str      # quem falou
    confidence: float # confiança na identificação
    raw_text: str     # texto original

@dataclass
class TranscriptionSegment:
    """Segmento de transcrição com timestamp"""
    timestamp: str
    speaker: str
    text: str
    duration: float = 0.0

class BasicTranscriptionParser:
    """Parser básico para transcrições do Teams"""
    
    def __init__(self):
        # Padrões de ação em português (para transcrições de fala)
        self.verbal_action_patterns = {
            'click': [
                r'clico?\s+(?:no|na|em)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'pressiono\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'aperto\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'seleciono\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)'
            ],
            'type': [
                r'digito\s+(.+?)(?:\s|$|,|\.|;)',
                r'escrevo\s+(.+?)(?:\s|$|,|\.|;)',
                r'preencho\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'coloco\s+(.+?)(?:\s|$|,|\.|;)'
            ],
            'select': [
                r'seleciono\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'escolho\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'marco\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)'
            ],
            'navigate': [
                r'vou\s+para\s+(.+?)(?:\s|$|,|\.|;)',
                r'acesso\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'abro\s+(?:o|a)?\s*(.+?)(?:\s|$|,|\.|;)',
                r'navego\s+para\s+(.+?)(?:\s|$|,|\.|;)'
            ]
        }
        
        # Padrões para instruções técnicas (para documentação de implementação)
        self.technical_instruction_patterns = {
            'configure': [
                r'configure?\s+(?:o|a)?\s*(.+?)(?:\.|$)',
                r'defina?\s+(?:o|a)?\s*(.+?)(?:\.|$)',
                r'estabeleça?\s+(?:o|a)?\s*(.+?)(?:\.|$)',
                r'ajuste?\s+(?:o|a)?\s*(.+?)(?:\.|$)'
            ],
            'install': [
                r'instale?\s+(?:o|a)?\s*(.+?)(?:\.|$)',
                r'baixe?\s+(?:o|a)?\s*(.+?)(?:\.|$)',
                r'faça\s+(?:o\s+)?download\s+(?:do|da)?\s*(.+?)(?:\.|$)'
            ],
            'create': [
                r'crie?\s+(?:um|uma)?\s*(.+?)(?:\.|$)',
                r'adicione?\s+(?:um|uma)?\s*(.+?)(?:\.|$)',
                r'implemente?\s+(?:um|uma)?\s*(.+?)(?:\.|$)',
                r'desenvolva?\s+(?:um|uma)?\s*(.+?)(?:\.|$)'
            ],
            'setup': [
                r'configure?\s+(?:a|o)?\s*(.+?)(?:\.|$)',
                r'prepare?\s+(?:a|o)?\s*(.+?)(?:\.|$)',
                r'inicialize?\s+(?:a|o)?\s*(.+?)(?:\.|$)'
            ],
            'execute': [
                r'execute?\s+(.+?)(?:\.|$)',
                r'rode?\s+(.+?)(?:\.|$)',
                r'realize?\s+(.+?)(?:\.|$)',
                r'faça?\s+(.+?)(?:\.|$)'
            ],
            'validate': [
                r'valide?\s+(.+?)(?:\.|$)',
                r'verifique?\s+(.+?)(?:\.|$)',
                r'teste?\s+(.+?)(?:\.|$)',
                r'confirme?\s+(.+?)(?:\.|$)'
            ],
            'monitor': [
                r'monitore?\s+(.+?)(?:\.|$)',
                r'acompanhe?\s+(.+?)(?:\.|$)',
                r'observe?\s+(.+?)(?:\.|$)'
            ]
        }
        
        # Combinação de ambos os padrões
        self.action_patterns = {**self.verbal_action_patterns, **self.technical_instruction_patterns}
        
        # Palavras de ruído para filtrar
        self.noise_words = ['uhm', 'né', 'então', 'assim', 'tipo', 'é', 'ah', 'oh']
        
        # Padrões para sequenciamento
        self.sequence_patterns = [
            r'primeiro(?:,)?\s+(.+)',
            r'segundo(?:,)?\s+(.+)', 
            r'terceiro(?:,)?\s+(.+)',
            r'depois(?:,)?\s+(.+)',
            r'em seguida(?:,)?\s+(.+)',
            r'agora(?:,)?\s+(.+)'
        ]

    def parse_vtt_file(self, file_path: str) -> List[TranscriptionSegment]:
        """Parse arquivo VTT do Teams"""
        segments = []
        
        try:
            vtt = webvtt.read(file_path)
            for caption in vtt:
                # Extrair speaker se presente no formato "Nome: texto"
                text = caption.text.strip()
                speaker = "Unknown"
                
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        potential_speaker = parts[0].strip()
                        # Verificar se é um nome válido (não muito longo, sem números)
                        if len(potential_speaker) < 50 and not any(char.isdigit() for char in potential_speaker):
                            speaker = potential_speaker
                            text = parts[1].strip()
                
                segment = TranscriptionSegment(
                    timestamp=caption.start,
                    speaker=speaker,
                    text=text,
                    duration=self._calculate_duration(caption.start, caption.end)
                )
                segments.append(segment)
                
        except Exception as e:
            print(f"Erro ao processar VTT: {e}")
            # Fallback para processamento como texto
            return self.parse_text_file(file_path)
            
        return segments

    def parse_text_file(self, file_path: str) -> List[TranscriptionSegment]:
        """Parse arquivo de texto simples"""
        segments = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Dividir por linhas e processar
            lines = content.split('\n')
            timestamp_counter = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                speaker = "Unknown"
                text = line
                
                # Tentar extrair speaker
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        potential_speaker = parts[0].strip()
                        if len(potential_speaker) < 50 and not any(char.isdigit() for char in potential_speaker):
                            speaker = potential_speaker
                            text = parts[1].strip()
                
                segment = TranscriptionSegment(
                    timestamp=f"00:{timestamp_counter:02d}:00",
                    speaker=speaker,
                    text=text
                )
                segments.append(segment)
                timestamp_counter += 1
                
        except Exception as e:
            print(f"Erro ao processar arquivo de texto: {e}")
            
        return segments

    def extract_actions(self, segments: List[TranscriptionSegment]) -> List[Action]:
        """Extrai ações dos segmentos de transcrição"""
        actions = []
        sequence_counter = 1
        
        # Detectar se é documentação técnica ou transcrição de fala
        is_technical_doc = self._detect_document_type(segments)
        
        for segment in segments:
            # Limpar texto de ruído
            cleaned_text = self._clean_text(segment.text)
            
            if is_technical_doc:
                # Para documentação técnica, extrair instruções e fases
                actions.extend(self._extract_technical_instructions(segment, cleaned_text, sequence_counter))
                sequence_counter += len(actions)
            else:
                # Para transcrições de fala, usar padrões verbais
                for action_type, patterns in self.verbal_action_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
                        
                        for match in matches:
                            element = match.group(1).strip()
                            if element and len(element) > 2:  # Filtrar elementos muito curtos
                                action = Action(
                                    action_type=action_type,
                                    element=self._clean_element_name(element),
                                    sequence=sequence_counter,
                                    timestamp=segment.timestamp,
                                    speaker=segment.speaker,
                                    confidence=self._calculate_confidence(action_type, element, cleaned_text),
                                    raw_text=segment.text
                                )
                                actions.append(action)
                                sequence_counter += 1
        
        # Ordenar por timestamp e resequenciar
        actions.sort(key=lambda x: x.timestamp)
        for i, action in enumerate(actions, 1):
            action.sequence = i
            
        return actions

    def _clean_text(self, text: str) -> str:
        """Remove ruído do texto"""
        # Converter para minúsculas
        text = text.lower()
        
        # Remover palavras de ruído
        for noise in self.noise_words:
            text = re.sub(rf'\b{noise}\b', '', text, flags=re.IGNORECASE)
        
        # Remover múltiplos espaços
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _clean_element_name(self, element: str) -> str:
        """Limpa nome do elemento"""
        # Remover artigos e preposições
        element = re.sub(r'^(o|a|os|as|do|da|dos|das|no|na|nos|nas|em|de)\s+', '', element, flags=re.IGNORECASE)
        
        # Remover pontuação final
        element = re.sub(r'[.,;!?]+$', '', element)
        
        return element.strip()

    def _calculate_confidence(self, action_type: str, element: str, full_text: str) -> float:
        """Calcula confiança na identificação da ação"""
        confidence = 0.7  # Base
        
        # Aumentar confiança se elemento contém palavras-chave UI
        ui_keywords = ['botão', 'campo', 'menu', 'link', 'checkbox', 'dropdown', 'formulário']
        if any(keyword in element.lower() for keyword in ui_keywords):
            confidence += 0.2
            
        # Diminuir confiança se elemento é muito genérico
        generic_words = ['isso', 'aquilo', 'coisa', 'negócio', 'item']
        if any(word in element.lower() for word in generic_words):
            confidence -= 0.3
            
        # Limitar entre 0.1 e 1.0
        return max(0.1, min(1.0, confidence))

    def _calculate_duration(self, start: str, end: str) -> float:
        """Calcula duração entre timestamps"""
        try:
            # Converter timestamps para segundos e calcular diferença
            start_seconds = self._timestamp_to_seconds(start)
            end_seconds = self._timestamp_to_seconds(end)
            return end_seconds - start_seconds
        except:
            return 0.0

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Converte timestamp para segundos"""
        try:
            # Formato esperado: HH:MM:SS.mmm
            parts = timestamp.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0.0

    def _detect_document_type(self, segments: List[TranscriptionSegment]) -> bool:
        """Detecta se é documentação técnica ou transcrição de fala"""
        technical_indicators = 0
        total_text = ""
        
        for segment in segments[:10]:  # Analisar primeiros 10 segmentos
            total_text += segment.text.lower() + " "
        
        # Indicadores de documentação técnica
        technical_keywords = [
            'implementação', 'configuração', 'desenvolvimento', 'sistema',
            'aplicação', 'processo', 'ferramenta', 'tecnologia', 'framework',
            'deploy', 'monitoramento', 'arquitetura', 'servidor', 'banco de dados',
            'api', 'interface', 'workflow', 'automação', 'rpa', 'uipath',
            'fase', 'etapa', 'passo', 'procedimento', 'instale', 'configure',
            'crie', 'implemente', 'execute', 'valide', 'teste'
        ]
        
        for keyword in technical_keywords:
            if keyword in total_text:
                technical_indicators += 1
        
        # Se tem mais de 5 indicadores técnicos, é provável que seja documentação
        return technical_indicators >= 5

    def _extract_technical_instructions(self, segment: TranscriptionSegment, cleaned_text: str, start_sequence: int) -> List[Action]:
        """Extrai instruções técnicas de documentação"""
        actions = []
        sequence_counter = start_sequence
        
        # Detectar fases e etapas
        phase_pattern = r'(?:fase|etapa|passo)\s+(\d+)[:\-\s]*(.+?)(?:\n|$|\.|;)'
        phase_matches = re.finditer(phase_pattern, cleaned_text, re.IGNORECASE)
        
        for match in phase_matches:
            phase_num = match.group(1)
            phase_desc = match.group(2).strip()
            
            action = Action(
                action_type='setup',
                element=f"Fase {phase_num}: {phase_desc}",
                sequence=sequence_counter,
                timestamp=segment.timestamp,
                speaker=segment.speaker,
                confidence=0.9,
                raw_text=segment.text
            )
            actions.append(action)
            sequence_counter += 1
        
        # Detectar instruções técnicas usando os padrões
        for action_type, patterns in self.technical_instruction_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
                
                for match in matches:
                    element = match.group(1).strip()
                    if element and len(element) > 5:  # Instruções técnicas são mais longas
                        # Limitar tamanho para evitar textos muito grandes
                        if len(element) > 100:
                            element = element[:100] + "..."
                            
                        action = Action(
                            action_type=action_type,
                            element=self._clean_element_name(element),
                            sequence=sequence_counter,
                            timestamp=segment.timestamp,
                            speaker=segment.speaker,
                            confidence=self._calculate_confidence(action_type, element, cleaned_text),
                            raw_text=segment.text
                        )
                        actions.append(action)
                        sequence_counter += 1
        
        # Detectar objetivos e requisitos
        objective_pattern = r'(?:objetivo|meta|finalidade)[:\-\s]*(.+?)(?:\n|$|\.|;)'
        objective_matches = re.finditer(objective_pattern, cleaned_text, re.IGNORECASE)
        
        for match in objective_matches:
            objective = match.group(1).strip()
            if len(objective) > 10:
                action = Action(
                    action_type='validate',
                    element=f"Objetivo: {objective[:80]}..." if len(objective) > 80 else f"Objetivo: {objective}",
                    sequence=sequence_counter,
                    timestamp=segment.timestamp,
                    speaker=segment.speaker,
                    confidence=0.8,
                    raw_text=segment.text
                )
                actions.append(action)
                sequence_counter += 1
        
        return actions

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Processa arquivo completo e retorna resultado estruturado"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.vtt':
            segments = self.parse_vtt_file(file_path)
        else:
            segments = self.parse_text_file(file_path)
        
        actions = self.extract_actions(segments)
        
        return {
            'segments': [
                {
                    'timestamp': seg.timestamp,
                    'speaker': seg.speaker,
                    'text': seg.text,
                    'duration': seg.duration
                } for seg in segments
            ],
            'actions': [
                {
                    'action_type': action.action_type,
                    'element': action.element,
                    'sequence': action.sequence,
                    'timestamp': action.timestamp,
                    'speaker': action.speaker,
                    'confidence': action.confidence,
                    'raw_text': action.raw_text
                } for action in actions
            ],
            'summary': {
                'total_segments': len(segments),
                'total_actions': len(actions),
                'speakers': list(set(seg.speaker for seg in segments)),
                'action_types': list(set(action.action_type for action in actions))
            }
        }