"""
OCR aprimorado com múltiplos engines e Google Vision API
Versão 2 do processamento de imagens com melhor precisão e fallbacks
"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import re
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import os
import time
import base64
import io

from mvp.processors.ocr import OCRResult, UIElement, BasicOCR

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

@dataclass
class EnhancedOCRResult:
    """Resultado aprimorado do processamento OCR"""
    original_image_path: str
    extracted_text: str
    confidence: float
    ui_elements: List[UIElement]
    preprocessing_applied: List[str]
    processing_time: float
    engine_used: str
    alternative_results: List[Dict[str, Any]]  # Resultados de engines alternativos
    text_regions: List[Dict[str, Any]]  # Regiões de texto identificadas
    quality_metrics: Dict[str, float]

@dataclass
class TextRegion:
    """Região de texto identificada na imagem"""
    text: str
    bounding_box: tuple  # (x, y, width, height)
    confidence: float
    font_size: float
    is_clickable: bool
    element_type: str

class EnhancedOCRProcessor:
    """Processador OCR aprimorado com múltiplos engines"""
    
    def __init__(self, google_credentials_path: Optional[str] = None):
        # Configurações básicas
        self.tesseract_config = r'--oem 3 --psm 6 -l por'
        self.min_confidence_threshold = 0.6
        
        # Configurar Google Vision se disponível
        self.google_client = None
        if GOOGLE_VISION_AVAILABLE and google_credentials_path and os.path.exists(google_credentials_path):
            try:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_credentials_path
                self.google_client = vision.ImageAnnotatorClient()
            except Exception as e:
                print(f"Erro ao inicializar Google Vision: {e}")
        
        # Configurações de pré-processamento
        self.preprocessing_configs = {
            'basic': {
                'resize_factor': 2.0,
                'contrast_enhance': 1.2,
                'sharpness_enhance': 1.1
            },
            'aggressive': {
                'resize_factor': 3.0,
                'contrast_enhance': 1.5,
                'sharpness_enhance': 1.3,
                'denoise': True,
                'binarize': True
            }
        }
        
        # Padrões avançados para identificação de elementos UI
        self.advanced_ui_patterns = {
            'button': {
                'text_patterns': [
                    r'^(ok|cancel|salvar|enviar|confirmar|entrar|login|sair|fechar)$',
                    r'.*botão.*',
                    r'^[a-záàâãéêíóôõúç\s]{1,20}$'  # Texto curto típico de botão
                ],
                'context_indicators': ['clique', 'pressione', 'selecione'],
                'size_indicators': {'min_width': 30, 'max_width': 200}
            },
            'field': {
                'text_patterns': [
                    r'.*campo.*',
                    r'.*input.*',
                    r'^[a-záàâãéêíóôõúç\s]*:$',  # Label com dois pontos
                    r'^\s*$'  # Campo vazio
                ],
                'context_indicators': ['digite', 'preencha', 'informe'],
                'size_indicators': {'min_width': 50, 'min_height': 20}
            },
            'menu': {
                'text_patterns': [
                    r'.*menu.*',
                    r'.*dropdown.*',
                    r'.*▼.*',  # Seta para baixo
                    r'.*⌄.*'   # Símbolo dropdown
                ],
                'context_indicators': ['selecione', 'escolha', 'opção'],
                'size_indicators': {'min_width': 80}
            }
        }

    def process_image_enhanced(self, image_path: str, use_fallback: bool = True) -> EnhancedOCRResult:
        """Processa imagem com múltiplos engines e configurações"""
        start_time = time.time()
        
        # Carregar imagem
        try:
            image = Image.open(image_path)
        except Exception as e:
            return self._create_error_result(image_path, f"Erro ao carregar imagem: {e}")
        
        # Resultados de diferentes engines
        engines_results = []
        best_result = None
        best_confidence = 0.0
        
        # 1. Tentar Google Vision API primeiro (se disponível)
        if self.google_client:
            try:
                google_result = self._process_with_google_vision(image_path)
                engines_results.append(google_result)
                if google_result['confidence'] > best_confidence:
                    best_result = google_result
                    best_confidence = google_result['confidence']
            except Exception as e:
                print(f"Erro no Google Vision: {e}")
        
        # 2. Tesseract básico
        try:
            tesseract_basic = self._process_with_tesseract(image, config='basic')
            engines_results.append(tesseract_basic)
            if tesseract_basic['confidence'] > best_confidence:
                best_result = tesseract_basic
                best_confidence = tesseract_basic['confidence']
        except Exception as e:
            print(f"Erro no Tesseract básico: {e}")
        
        # 3. Tesseract com pré-processamento agressivo (se confiança baixa)
        if best_confidence < self.min_confidence_threshold and use_fallback:
            try:
                tesseract_aggressive = self._process_with_tesseract(image, config='aggressive')
                engines_results.append(tesseract_aggressive)
                if tesseract_aggressive['confidence'] > best_confidence:
                    best_result = tesseract_aggressive
                    best_confidence = tesseract_aggressive['confidence']
            except Exception as e:
                print(f"Erro no Tesseract agressivo: {e}")
        
        # Se nenhum resultado satisfatório, usar o melhor disponível
        if not best_result and engines_results:
            best_result = max(engines_results, key=lambda x: x['confidence'])
        
        if not best_result:
            return self._create_error_result(image_path, "Nenhum engine OCR funcionou")
        
        # Processar resultado final
        processing_time = time.time() - start_time
        
        # Identificar elementos UI avançados
        ui_elements = self._identify_advanced_ui_elements(
            best_result['text'], 
            best_result.get('text_regions', []),
            image
        )
        
        # Calcular métricas de qualidade
        quality_metrics = self._calculate_quality_metrics(best_result, ui_elements)
        
        return EnhancedOCRResult(
            original_image_path=image_path,
            extracted_text=best_result['text'],
            confidence=best_result['confidence'],
            ui_elements=ui_elements,
            preprocessing_applied=best_result['preprocessing_applied'],
            processing_time=processing_time,
            engine_used=best_result['engine'],
            alternative_results=engines_results,
            text_regions=best_result.get('text_regions', []),
            quality_metrics=quality_metrics
        )

    def _process_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """Processa imagem com Google Vision API"""
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        
        # Text detection
        response = self.google_client.text_detection(image=image)
        texts = response.text_annotations
        
        if response.error.message:
            raise Exception(f'Google Vision error: {response.error.message}')
        
        if not texts:
            return {
                'engine': 'google_vision',
                'text': '',
                'confidence': 0.0,
                'preprocessing_applied': [],
                'text_regions': []
            }
        
        # Primeiro resultado é o texto completo
        full_text = texts[0].description
        
        # Demais resultados são regiões individuais
        text_regions = []
        for text in texts[1:]:  # Pular o primeiro (texto completo)
            vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
            if len(vertices) == 4:
                # Calcular bounding box
                x_coords = [v[0] for v in vertices]
                y_coords = [v[1] for v in vertices]
                x, y = min(x_coords), min(y_coords)
                width, height = max(x_coords) - x, max(y_coords) - y
                
                text_regions.append({
                    'text': text.description,
                    'bounding_box': (x, y, width, height),
                    'confidence': 0.9,  # Google Vision geralmente tem alta confiança
                    'vertices': vertices
                })
        
        # Calcular confiança geral (Google Vision não fornece score direto)
        confidence = 0.9 if full_text.strip() else 0.1
        
        return {
            'engine': 'google_vision',
            'text': full_text,
            'confidence': confidence,
            'preprocessing_applied': [],
            'text_regions': text_regions
        }

    def _process_with_tesseract(self, image: Image.Image, config: str = 'basic') -> Dict[str, Any]:
        """Processa imagem com Tesseract usando configuração específica"""
        preprocessing_applied = []
        processed_image = image.copy()
        
        # Aplicar pré-processamento baseado na configuração
        config_settings = self.preprocessing_configs[config]
        
        # Redimensionamento
        if 'resize_factor' in config_settings:
            factor = config_settings['resize_factor']
            new_size = (int(image.width * factor), int(image.height * factor))
            processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)
            preprocessing_applied.append(f'resize_{factor}x')
        
        # Melhoramento de contraste
        if 'contrast_enhance' in config_settings:
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(config_settings['contrast_enhance'])
            preprocessing_applied.append('contrast_enhance')
        
        # Melhoramento de nitidez
        if 'sharpness_enhance' in config_settings:
            enhancer = ImageEnhance.Sharpness(processed_image)
            processed_image = enhancer.enhance(config_settings['sharpness_enhance'])
            preprocessing_applied.append('sharpness_enhance')
        
        # Redução de ruído (se configurado)
        if config_settings.get('denoise', False):
            processed_image = processed_image.filter(ImageFilter.MedianFilter(3))
            preprocessing_applied.append('median_filter')
        
        # Binarização (se configurado)
        if config_settings.get('binarize', False):
            processed_image = processed_image.convert('L')  # Grayscale
            # Threshold adaptativo
            np_image = np.array(processed_image)
            threshold = np.mean(np_image)
            binary_image = np_image > threshold
            processed_image = Image.fromarray((binary_image * 255).astype(np.uint8))
            preprocessing_applied.append('binarize')
        
        # Converter para escala de cinza se ainda não foi
        if processed_image.mode != 'L':
            processed_image = processed_image.convert('L')
            preprocessing_applied.append('grayscale')
        
        # Extrair texto
        extracted_text = pytesseract.image_to_string(
            processed_image, 
            config=self.tesseract_config
        )
        
        # Calcular confiança usando dados detalhados
        try:
            data = pytesseract.image_to_data(
                processed_image, 
                config=self.tesseract_config, 
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.1
            
            # Extrair regiões de texto
            text_regions = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 30 and data['text'][i].strip():  # Filtrar baixa confiança
                    text_regions.append({
                        'text': data['text'][i],
                        'bounding_box': (
                            data['left'][i], 
                            data['top'][i], 
                            data['width'][i], 
                            data['height'][i]
                        ),
                        'confidence': int(conf) / 100.0
                    })
        
        except Exception as e:
            confidence = 0.5 if extracted_text.strip() else 0.1
            text_regions = []
        
        return {
            'engine': f'tesseract_{config}',
            'text': extracted_text,
            'confidence': confidence,
            'preprocessing_applied': preprocessing_applied,
            'text_regions': text_regions
        }

    def _identify_advanced_ui_elements(self, 
                                     full_text: str, 
                                     text_regions: List[Dict[str, Any]],
                                     image: Image.Image) -> List[UIElement]:
        """Identifica elementos UI usando análise avançada"""
        elements = []
        
        # Processar regiões de texto individuais
        for region in text_regions:
            text = region['text'].strip()
            if not text:
                continue
            
            bbox = region['bounding_box']
            confidence = region['confidence']
            
            # Determinar tipo de elemento
            element_type = self._classify_ui_element_advanced(text, bbox, full_text)
            
            # Verificar se é elemento clicável
            is_clickable = self._is_likely_clickable(text, element_type, bbox)
            
            # Calcular contexto
            context = self._extract_element_context(text, full_text, text_regions)
            
            element = UIElement(
                type=element_type,
                text=text,
                confidence=confidence,
                position=bbox,
                context=context
            )
            
            elements.append(element)
        
        # Se não há regiões específicas, usar análise básica do texto completo
        if not text_regions and full_text.strip():
            basic_elements = self._fallback_ui_identification(full_text)
            elements.extend(basic_elements)
        
        # Remover duplicatas e ordenar por confiança
        elements = self._deduplicate_elements(elements)
        elements.sort(key=lambda x: x.confidence, reverse=True)
        
        return elements

    def _classify_ui_element_advanced(self, 
                                    text: str, 
                                    bbox: tuple, 
                                    full_context: str) -> str:
        """Classifica elemento UI usando padrões avançados"""
        text_lower = text.lower().strip()
        
        # Análise de dimensões
        width, height = bbox[2], bbox[3]
        aspect_ratio = width / height if height > 0 else 1
        
        for ui_type, patterns in self.advanced_ui_patterns.items():
            score = 0.0
            
            # 1. Verificar padrões de texto
            for pattern in patterns['text_patterns']:
                if re.match(pattern, text_lower):
                    score += 0.4
                    break
            
            # 2. Verificar indicadores contextuais
            context_lower = full_context.lower()
            for indicator in patterns['context_indicators']:
                if indicator in context_lower:
                    score += 0.2
                    break
            
            # 3. Verificar indicadores de tamanho
            size_indicators = patterns.get('size_indicators', {})
            
            if 'min_width' in size_indicators and width >= size_indicators['min_width']:
                score += 0.1
            if 'max_width' in size_indicators and width <= size_indicators['max_width']:
                score += 0.1
            if 'min_height' in size_indicators and height >= size_indicators['min_height']:
                score += 0.1
            
            # 4. Análise específica por tipo
            if ui_type == 'button':
                # Botões tendem a ter aspect ratio mais quadrado
                if 0.3 <= aspect_ratio <= 4.0:
                    score += 0.1
                # Texto tipicamente curto
                if len(text) <= 20:
                    score += 0.1
            
            elif ui_type == 'field':
                # Campos tendem a ser mais largos que altos
                if aspect_ratio > 2.0:
                    score += 0.2
                # Ou podem estar vazios
                if not text_lower or text_lower.endswith(':'):
                    score += 0.2
            
            elif ui_type == 'menu':
                # Menus podem ter símbolos específicos
                if any(symbol in text for symbol in ['▼', '⌄', '⏷', '∨']):
                    score += 0.3
            
            # Se score alto o suficiente, classificar como este tipo
            if score >= 0.5:
                return ui_type
        
        # Classificação padrão baseada em características gerais
        if len(text) <= 20 and not text.endswith(':'):
            return 'button'
        elif text.endswith(':') or not text:
            return 'field' 
        elif width > height * 2:
            return 'field'
        else:
            return 'label'

    def _is_likely_clickable(self, text: str, element_type: str, bbox: tuple) -> bool:
        """Determina se elemento é provavelmente clicável"""
        clickable_types = ['button', 'link', 'menu', 'checkbox']
        
        if element_type in clickable_types:
            return True
        
        # Verificar palavras-chave que indicam ação
        action_keywords = [
            'clique', 'click', 'pressione', 'selecione', 'confirme',
            'ok', 'cancel', 'salvar', 'enviar', 'entrar', 'sair',
            'próximo', 'anterior', 'voltar', 'continuar'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in action_keywords)

    def _extract_element_context(self, 
                                element_text: str, 
                                full_text: str, 
                                all_regions: List[Dict[str, Any]]) -> str:
        """Extrai contexto ao redor do elemento"""
        # Encontrar posição do elemento no texto completo
        element_position = full_text.lower().find(element_text.lower())
        
        if element_position == -1:
            return full_text[:100] + "..." if len(full_text) > 100 else full_text
        
        # Extrair contexto ao redor (50 caracteres antes e depois)
        start = max(0, element_position - 50)
        end = min(len(full_text), element_position + len(element_text) + 50)
        
        context = full_text[start:end]
        
        # Adicionar informação de elementos próximos
        nearby_elements = []
        for region in all_regions[:5]:  # Limitar a 5 elementos próximos
            if region['text'].strip() and region['text'] != element_text:
                nearby_elements.append(region['text'].strip())
        
        if nearby_elements:
            context += " | Próximos: " + ", ".join(nearby_elements)
        
        return context

    def _fallback_ui_identification(self, full_text: str) -> List[UIElement]:
        """Identificação UI de fallback quando não há regiões específicas"""
        elements = []
        
        # Dividir texto em linhas para análise
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        for line in lines:
            # Identificar possíveis botões (texto curto, palavras de ação)
            if len(line) <= 25:
                action_words = ['ok', 'cancel', 'salvar', 'enviar', 'confirmar', 'entrar']
                if any(word in line.lower() for word in action_words):
                    elements.append(UIElement(
                        type='button',
                        text=line,
                        confidence=0.6,
                        position=(0, 0, 0, 0),
                        context=full_text[:100]
                    ))
            
            # Identificar campos (linhas com dois pontos)
            elif line.endswith(':'):
                elements.append(UIElement(
                    type='field',
                    text=line,
                    confidence=0.7,
                    position=(0, 0, 0, 0),
                    context=full_text[:100]
                ))
        
        return elements

    def _deduplicate_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Remove elementos duplicados baseado no texto"""
        seen_texts = set()
        unique_elements = []
        
        for element in elements:
            element_text = element.text.strip().lower()
            if element_text and element_text not in seen_texts:
                seen_texts.add(element_text)
                unique_elements.append(element)
        
        return unique_elements

    def _calculate_quality_metrics(self, 
                                 ocr_result: Dict[str, Any], 
                                 ui_elements: List[UIElement]) -> Dict[str, float]:
        """Calcula métricas de qualidade do processamento"""
        metrics = {
            'text_density': 0.0,
            'ui_element_confidence': 0.0,
            'processing_confidence': ocr_result['confidence'],
            'text_coherence': 0.0
        }
        
        text = ocr_result['text']
        
        # Densidade de texto (caracteres úteis / total)
        if text:
            useful_chars = len(re.sub(r'[^\w\s]', '', text))
            total_chars = len(text)
            metrics['text_density'] = useful_chars / total_chars if total_chars > 0 else 0.0
        
        # Confiança média dos elementos UI
        if ui_elements:
            avg_confidence = sum(elem.confidence for elem in ui_elements) / len(ui_elements)
            metrics['ui_element_confidence'] = avg_confidence
        
        # Coerência do texto (palavras reconhecíveis)
        if text:
            words = text.split()
            recognizable_words = sum(1 for word in words if len(word) > 2 and word.isalpha())
            metrics['text_coherence'] = recognizable_words / len(words) if words else 0.0
        
        return metrics

    def _create_error_result(self, image_path: str, error_message: str) -> EnhancedOCRResult:
        """Cria resultado de erro"""
        return EnhancedOCRResult(
            original_image_path=image_path,
            extracted_text="",
            confidence=0.0,
            ui_elements=[],
            preprocessing_applied=[],
            processing_time=0.0,
            engine_used="error",
            alternative_results=[],
            text_regions=[],
            quality_metrics={'error': 1.0}
        )

    def batch_process_enhanced(self, image_paths: List[str]) -> List[EnhancedOCRResult]:
        """Processa múltiplas imagens com processamento aprimorado"""
        results = []
        
        for image_path in image_paths:
            try:
                result = self.process_image_enhanced(image_path)
                results.append(result)
            except Exception as e:
                error_result = self._create_error_result(image_path, str(e))
                results.append(error_result)
        
        return results

    def get_processing_summary(self, results: List[EnhancedOCRResult]) -> Dict[str, Any]:
        """Gera resumo do processamento de múltiplas imagens"""
        if not results:
            return {}
        
        total_images = len(results)
        successful_results = [r for r in results if r.confidence > 0]
        
        engines_used = {}
        for result in successful_results:
            engine = result.engine_used
            engines_used[engine] = engines_used.get(engine, 0) + 1
        
        avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results) if successful_results else 0.0
        avg_processing_time = sum(r.processing_time for r in results) / total_images
        total_ui_elements = sum(len(r.ui_elements) for r in results)
        
        return {
            'total_images_processed': total_images,
            'successful_extractions': len(successful_results),
            'success_rate': len(successful_results) / total_images,
            'engines_used': engines_used,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time,
            'total_ui_elements_found': total_ui_elements,
            'average_ui_elements_per_image': total_ui_elements / total_images if total_images > 0 else 0
        }