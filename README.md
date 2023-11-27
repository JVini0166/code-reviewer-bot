# Bot de Integração Azure DevOps - OpenAI

Este bot foi desenvolvido para integrar o Azure DevOps ao OpenAI. Ele busca automaticamente Pull Requests (PRs) abertos no Azure DevOps, obtém as diferenças desses PRs e as envia para o modelo de linguagem da OpenAI para revisão. Posteriormente, comenta no PR com as sugestões e melhorias propostas pelo modelo.

## Requisitos

- Python 3.x
- Principais Bibliotecas Python: `requests`, `gitpython`, `openai`
- Tokens de autenticação para Azure DevOps e OpenAI

## Configuração Inicial

Antes de executar o bot, configure os tokens de autenticação e os URLs da API no arquivo `config.ini`.

Campos para configuração:

- `GPT_KEY`: Chave de autenticação para o modelo GPT da OpenAI.
- `ORGANIZATION`: Nome da organização no Azure DevOps.
- `PROJECT_ID`: ID do projeto no Azure DevOps.
- `AZURE_TOKEN`: Token de autenticação para Azure DevOps.
- `REPO_PATH`: Caminho da pasta onde os repositórios serão clonados.

## Como Funciona

1. Obtém a lista de PRs abertos do Azure DevOps.
2. Para cada PR, verifica se existe um repositório local. Se não, clona o repositório; se sim, atualiza o repositório local com as mudanças mais recentes.
3. Obtém as diferenças (changes) do PR.
4. Envia essas diferenças para a OpenAI para revisão.
5. Com base na revisão, comenta no PR com sugestões e melhorias.

