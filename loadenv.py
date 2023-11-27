import configparser
import boto3
import os


def load_config():
    # Tenta pegar das variáveis de ambiente ou, se não existir, do arquivo config.ini
    def get_config_value(key):
        return os.environ.get(key) or config.get("Credentials", key)

    config = configparser.ConfigParser()
    config.read("config.ini")

    # Lê as variáveis e armazena em um dicionário
    config_values = {
        "ORGANIZATION": get_config_value("ORGANIZATION"),
        "PROJECT_ID": get_config_value("PROJECT_ID"),
        "AZURE_TOKEN": get_config_value("AZURE_TOKEN"),
        "REPO_PATH": get_config_value("REPO_PATH"),
        "REVIEWER_EMAIL": get_config_value("REVIEWER_EMAIL"),
        "AWS_ACCESS_KEY_ID": get_config_value("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": get_config_value("AWS_SECRET_ACCESS_KEY"),
        "GPT_KEY": get_config_value("GPT_KEY")
    }

    return config_values


def download_ssh_keys_from_s3():

    config_values = load_config()

    # Crie uma sessão usando sua access_key e secret_key
    session = boto3.Session(
        aws_access_key_id=config_values["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=config_values["AWS_SECRET_ACCESS_KEY"]
    )

    # Inicie o cliente S3 com a sessão criada
    s3 = session.client('s3')

    # Nome do bucket
    bucket_name = "young-sheldon-keys"

    # Lista de arquivos para baixar
    file_keys = ["id_rsa", "id_rsa.pub"]

    for file_key in file_keys:
        # Caminho local onde o arquivo será salvo
        local_path = os.path.join("./", file_key)

        # Faz o download do arquivo
        s3.download_file(bucket_name, file_key, local_path)

        # Altera as permissões do arquivo baixado para 400
        os.chmod(local_path, 0o400)

        print(f"Arquivo {file_key} feito download de {bucket_name}!")
    print("Chaves SSH sincronizadas!")


