import time

import requests
import configparser
import loadenv

def get_gpt_key_from_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        return config['Credentials']['GPT_KEY']
    except KeyError:
        print("GPT_KEY não encontrado no arquivo config.ini.")
        return ''


api_key = loadenv.load_config()['GPT_KEY']


CODEREVIEW_PROMPT = """Atue como um revisor de um Pull Request, extremamente experiente, fornecendo feedback sobre possíveis bugs e questões de código limpo.
        As alterações do Pull Request são fornecidas em formato de patch.
        Cada entrada de patch tem a mensagem do commit na linha de assunto, seguida pelas alterações de código (diffs) em um formato unidiff.

        Como revisor de código, sua tarefa é:
            - Revisar apenas linhas adicionadas, editadas ou excluídas.
            - Melhorar o código para tornar mais performático, legível e seguro.
            - Se não houver bugs e as alterações estiverem corretas, escreva apenas 'Sem feedback.'
            - Se houver um bug ou alterações de código incorretas, não escreva 'Sem feedback.'
            
        Utilize esse template para escrever seu feedback e em hipótese alguma utilize outra forma como resposta:
            - Arquivo: (nome do arquivo)
            - Tipo de Melhoria: (cite aqui a categoria de melhoria que você fez)
            - Linha: (número da linha)
            - Feedback: (cite aqui o feedback se houver)
            - Código Atual: (cite aqui o código atual (diff) em Markdown)
            - Sugestão de Código: (cite aqui a melhoria de código em Markdown (somente se houver, caso contrário escreva 'Sem melhoria'))

    """


# Mantendo a função em sua forma original
def get_gpt_response_by_prompt(conversation, prompt, retries=0):
    if retries > 3:
        return "Vish! Não consegui revisar esse arquivo por esse motivo: Mais de 3 Retries"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": conversation
            }
        ],
        "temperature": 0.4,
        "max_tokens": 800,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Lança uma exceção para respostas não-2xx
        json_response = response.json()
        return json_response['choices'][0]['message']['content'].strip(" \n")
    except requests.RequestException as e:
        time.sleep(30)
        retries += 1
        get_gpt_response_by_prompt(conversation, prompt)


# Mantendo a função em sua forma original
def review_code_with_gpt(code):
    response = get_gpt_response_by_prompt(code, CODEREVIEW_PROMPT)
    return response


if __name__ == '__main__':
    get_gpt_response_by_prompt("teste", CODEREVIEW_PROMPT)
