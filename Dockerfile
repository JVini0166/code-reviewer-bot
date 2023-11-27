FROM python:3.11-bullseye

ENV TZ UTC+3

COPY requirements.txt ./

# Instalação dos pacotes e dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-client git dos2unix && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install Flask && \
    pip install flask[async] && \
    pip install -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*  # Limpar a lista de pacotes para reduzir o tamanho da imagem

COPY . .

# Configurações SSH
RUN mkdir -p /ssh && \
    touch /ssh/config && \
    touch /ssh/known_hosts && \
    chmod -R 400 /ssh/

EXPOSE 8080

EXPOSE 5000

CMD ["/bin/bash", "-c", "source /vault/secrets/config && uwsgi --http 0.0.0.0:8080 --master -p 4 -t 5 -w app:app --enable-threads"]

