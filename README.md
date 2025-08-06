# MVP RPA Documentation Generator

Sistema automatizado para geração de documentação RPA baseado em transcrições de voz e screenshots de processos.

## 🎯 Funcionalidades Principais

- 📝 **Processamento de Transcrições**: Análise automática de transcrições do Microsoft Teams
- 🖼️ **OCR de Screenshots**: Extração de texto e elementos UI das imagens  
- 🤖 **Geração por IA**: Documentação automática usando múltiplos provedores (OpenAI, Azure, Anthropic, Google)
- 🎨 **Múltiplos Agentes**: 5 tipos diferentes de documentação (Geral, Técnico, Business, Analista, Personalizado)
- 📄 **Exportação**: Documentos em Markdown e Word (.docx)
- 🔄 **Processamento Inteligente**: Correlação entre ações faladas e elementos visuais
- 📊 **Histórico Completo**: Acompanhamento de todas as sessões processadas

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.8+
- Tesseract OCR (opcional, para melhor qualidade de OCR)
- API Key de provedor de IA (OpenAI, Azure, etc.)

### Instalação
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente no arquivo `.env`
4. Execute: `python app.py`
5. Acesse: http://localhost:5000

## 📝 Personalização de Prompts

Os prompts estão externalizados em arquivos editáveis na pasta `prompts/`:
- `rpa_general.txt` - Documentação RPA geral
- `rpa_technical.txt` - Foco técnico avançado
- `rpa_business.txt` - Análise de negócio e ROI
- `process_analyst.txt` - Mapeamento de processos
- `custom.txt` - Totalmente personalizável

### Como personalizar:
1. Edite os arquivos `.txt` na pasta `prompts/`
2. Mantenha os placeholders `{variavel}`
3. Salve e use - mudanças são aplicadas automaticamente

## 🤖 Provedores de IA Suportados
- ✅ OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5 Turbo)
- ⚠️ Azure OpenAI (requer configuração adicional)
- ⚠️ Anthropic Claude (em desenvolvimento)  
- ⚠️ Google Gemini (em desenvolvimento)

## 📖 Como Usar
1. **Upload**: Envie transcrição (.txt/.vtt) e screenshots (opcional)
2. **Configure**: Escolha provedor, modelo e tipo de agente
3. **Processe**: Sistema analisa automaticamente
4. **Resultado**: Documentação em Markdown e Word

---
**Desenvolvido com ❤️ para automatização de documentação RPA**
