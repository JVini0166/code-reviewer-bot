import requests
import loadenv
import base64
import time
import gitops
import gpt
from concurrent.futures import ThreadPoolExecutor

MAX_THREADS = 5

config_values = loadenv.load_config()

AZURE_DEVOPS_PROJECT_IDS = config_values["PROJECT_ID"].split(',')
AZURE_DEVOPS_ORGANIZATION = config_values["ORGANIZATION"]
AZURE_DEVOPS_VALUE_TOKEN = config_values["AZURE_TOKEN"]
AZURE_DEVOPS_TOKEN = base64.b64encode(f":{AZURE_DEVOPS_VALUE_TOKEN}".encode('ascii')).decode('ascii')
AZURE_DEVOPS_REVIEWER_EMAIL = config_values["REVIEWER_EMAIL"]
REPO_PATH = config_values["REPO_PATH"]

# Constantes para os status do revisor
WAITING_AUTHOR_REVIEW = -5
NOT_REVIEWED = 0
AZURE_API_VERSION = "7.0"
APPROVED = 10
APPROVED_WITH_SUGGESTIONS = 5

headers_azure = {
    "authorization": f"Basic {AZURE_DEVOPS_TOKEN}",
}


def process_diff(pr_diff, pull_request_comment_url):
    comment_text = gpt.review_code_with_gpt(pr_diff["change"])
    if comment_text:
        print(f"Comentando no arquivo {pr_diff['file']} nas linhas {pr_diff['start_line']} a {pr_diff['end_line']}...")
        comment_on_pr(pull_request_comment_url, comment_text, pr_diff["file"], pr_diff["start_line"],
                      pr_diff["end_line"])


def send_to_gpt_and_comment(pr_diffs, pull_request_comment_url):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_diff, pr_diff, pull_request_comment_url) for pr_diff in pr_diffs]
        for future in futures:
            future.result()


def review_pr(pr, repo_url, pr_id):
    source_branch = pr["sourceRefName"].replace("refs/heads/", "")
    target_branch = pr["targetRefName"].replace("refs/heads/", "")
    repo_name = pr["repository"]["name"]
    pull_request_comment_url = f"{repo_url}/pullRequests/{pr_id}/threads?api-version={AZURE_API_VERSION}"

    print(f"Revisando PR do branch {source_branch} para {target_branch} no repositório {repo_name}...")
    repo_ssh_url = get_ssh_url(repo_url)
    repo = gitops.get_repo(repo_ssh_url, repo_name, pr_id, REPO_PATH)
    pr_diffs = gitops.get_pr_diff(repo, source_branch, target_branch)

    send_to_gpt_and_comment(pr_diffs, pull_request_comment_url)


def check_comments(project_id, repository_id, pull_request_id, change_status_pull_request_url):
    check_comments_response = requests.get('https://dev.azure.com/kdop/'+ str(project_id) +'/_apis/git/repositories/' + str(repository_id) +  '/pullrequests/' + str(pull_request_id) + '/threads', headers=headers_azure)

    # Verifica se a requisição foi bem-sucedida
    if check_comments_response.status_code == 200:
        threads = check_comments_response.json()['value']

        # Checa se todos os comentários estão marcados como 'fixed' e não deletados
        all_fixed_and_not_deleted = all(
            (thread.get('status') == 'fixed' and not thread.get('isDeleted')) if thread.get('active', False) else True
            for thread in threads
        )

        if all_fixed_and_not_deleted:
            print("Todos os comentários estão marcados como 'fixed' e não estão deletados.")
            change_pull_request_status(change_status_pull_request_url, APPROVED)
        else:
            print("Existem comentários que não estão marcados como 'fixed' ou estão deletados.")
    else:
        print("Falha na requisição à API do Azure DevOps.")


def review_process():
    for project_id in AZURE_DEVOPS_PROJECT_IDS:
        AZURE_DEVOPS_API_URL = "https://dev.azure.com/" + str(AZURE_DEVOPS_ORGANIZATION) + "/" + str(
            project_id) + "/_apis/git/pullrequests"
        open_prs = get_open_prs(AZURE_DEVOPS_API_URL)  # Note que agora estamos passando a URL como argumento
        print(f"Verificando {len(open_prs)} PRs abertos para o projeto {project_id}...")

        for pr in open_prs:
            has_reviewers = len(pr["reviewers"]) > 0
            if not has_reviewers:
                print(f"O PR {pr['pullRequestId']} não tem nenhum reviewer")
                continue

            for reviewer in pr["reviewers"]:
                is_bot_reviewer = reviewer["uniqueName"] == AZURE_DEVOPS_REVIEWER_EMAIL
                if not is_bot_reviewer:
                    continue

                repo_url = pr["repository"]["url"]
                pr_id = pr["pullRequestId"]
                reviewer_id = reviewer["id"]

                change_status_pull_request_url = f"{repo_url}/pullRequests/{pr_id}/reviewers/{reviewer_id}?api-version={AZURE_API_VERSION}"

                if reviewer["vote"] == WAITING_AUTHOR_REVIEW:
                    check_comments(project_id, pr["repository"]["id"], pr_id, change_status_pull_request_url)
                    print(f"O bot está esperando o autor do PR revisar as mudanças no PR {pr['pullRequestId']}")
                elif reviewer["vote"] == APPROVED:
                    print(f"O bot já aprovou as mudanças no PR {pr['pullRequestId']}")
                elif reviewer["vote"] == NOT_REVIEWED:
                    review_pr(pr, repo_url, pr_id)
                    change_pull_request_status(change_status_pull_request_url, WAITING_AUTHOR_REVIEW)
                else:
                    print(
                        f"O usuário do bot não foi atrelado ao pull request ou tem um status diferente no PR {pr['pullRequestId']}")

            time.sleep(5)


def get_ssh_url(repo_url):
    response = requests.get(repo_url, headers=headers_azure)

    if response.status_code == 200:
        return response.json()["sshUrl"]
    return []


def get_open_prs(azure_devops_api_url):
    response = requests.get(azure_devops_api_url, headers=headers_azure)
    if response.status_code == 200:
        values = response.json()["value"]
        active_items = [item for item in values if item["status"] == 'active']
        return active_items
    return []


def comment_on_pr(pull_request_comment_url, comment, file_path, start_line, end_line):
    data = {
        "comments": [
            {
                "parentCommentId": 0,
                "content": comment,
                "commentType": 1
            }
        ],
        "status": 1,
        "threadContext": {
            "filePath": file_path,

        },
        "pullRequestThreadContext": {
            "changeTrackingId": 1,
            "iterationContext": {
                "firstComparingIteration": 1,
                "secondComparingIteration": 2
            }
        }
    }
    response = requests.post(pull_request_comment_url, headers=headers_azure, json=data)

    return response.status_code == 200


def change_pull_request_status(pull_request_url, status):
    data = {
        "vote": status
    }

    response = requests.put(pull_request_url, headers=headers_azure, json=data)
    if response.status_code == 200:
        status_message = "aprovado" if status == APPROVED else "Alterado Status, ainda não aprovado"
        print(f"O status do PR foi alterado para {status_message}")
    return response.status_code == 200
