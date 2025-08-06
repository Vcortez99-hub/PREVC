# Configuração de Prompts para Agentes IA

Este diretório contém os prompts personalizáveis para diferentes tipos de agentes de documentação RPA.

## Agentes Disponíveis

### 1. RPA Geral (`rpa_general.txt`)
- **Foco**: Documentação técnica balanceada
- **Público**: Desenvolvedores e analistas RPA
- **Uso**: Casos gerais de documentação RPA

### 2. RPA Técnico (`rpa_technical.txt`)
- **Foco**: Especificações técnicas detalhadas
- **Público**: Desenvolvedores e arquitetos RPA
- **Uso**: Implementações complexas e documentação técnica avançada

### 3. RPA Business (`rpa_business.txt`)
- **Foco**: Valor de negócio e análise financeira
- **Público**: Executivos e stakeholders de negócio
- **Uso**: Apresentações executivas e cases de negócio

### 4. Analista de Processos (`process_analyst.txt`)
- **Foco**: Mapeamento e otimização de processos
- **Público**: Analistas de processo e consultores
- **Uso**: Análise de processos antes da automação

### 5. Personalizado (`custom.txt`)
- **Foco**: Configurável conforme necessidade
- **Público**: Qualquer
- **Uso**: Casos específicos que requerem customização

## Como Editar Prompts

1. **Abra o arquivo** correspondente ao agente desejado (ex: `rpa_general.txt`)
2. **Modifique o conteúdo** conforme suas necessidades
3. **Mantenha a estrutura** básica com placeholders `{variavel}`
4. **Salve o arquivo** e reinicie a aplicação se necessário

## Estrutura Recomendada

Cada prompt deve seguir esta estrutura básica:

```
Você é um especialista em [ÁREA DE ESPECIALIZAÇÃO].

Sua tarefa é [OBJETIVO PRINCIPAL].

**FORMATO DE SAÍDA OBRIGATÓRIO:**
```markdown
# {processo_nome}

## Seções...
```

**REGRAS IMPORTANTES:**
1. Regra 1
2. Regra 2
...
```

## Variáveis Disponíveis

Os seguintes placeholders são automaticamente substituídos:

- `{processo_nome}`: Nome do processo identificado
- `{objetivo_claro_e_conciso}`: Objetivo do processo
- `{prerequisito_X}`: Pré-requisitos identificados
- `{passos_numerados_com_acoes_e_elementos}`: Passos detalhados
- E outros conforme o contexto...

## Criando Novos Agentes

Para criar um novo tipo de agente:

1. Crie um arquivo `.txt` neste diretório
2. Use como nome um identificador único (ex: `meu_agente_especial.txt`)
3. Siga a estrutura recomendada acima
4. O agente aparecerá automaticamente na interface

## Dicas de Personalização

### Para Documentação Mais Técnica:
- Inclua seções como "Seletores XPath"
- Detalhe timeouts e configurações
- Especifique tratamento de exceções

### Para Documentação de Negócio:
- Foque em benefícios e ROI
- Use linguagem menos técnica
- Inclua métricas de sucesso

### Para Análise de Processos:
- Inclua mapeamento AS-IS/TO-BE
- Detalhe pontos de decisão
- Analise gargalos e oportunidades

## Validação de Prompts

Para verificar se um prompt está bem formatado, você pode usar a funcionalidade de validação do sistema que verifica:

- Tamanho mínimo do prompt
- Presença de formatação Markdown
- Uso de placeholders para personalização
- Estrutura básica de seções

## Backup e Versionamento

Recomendamos:

1. Fazer backup dos prompts antes de modificar
2. Versionar alterações importantes
3. Documentar mudanças significativas
4. Testar prompts após modificações

## Troubleshooting

### Prompt não aparece na interface:
- Verifique se o arquivo está no diretório correto
- Confirme se a extensão é `.txt`
- Reinicie a aplicação

### Erro ao processar:
- Verifique sintaxe do prompt
- Confirme se placeholders estão corretos
- Consulte logs da aplicação

### Resultado não satisfatório:
- Ajuste instruções específicas
- Modifique exemplos no prompt
- Teste com diferentes configurações