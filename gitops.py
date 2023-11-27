from git import Repo, Git
import shutil
import os

git_ssh_identity_file = os.path.expanduser('/id_rsa')
git_ssh_cmd = 'ssh -o StrictHostKeyChecking=no -i %s' % git_ssh_identity_file


def get_pr_diff(repo, source_branch, target_branch):
    try:
        with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
            # Garanta que temos as referências mais recentes
            repo.remotes.origin.fetch()

            base = repo.commit(f"refs/remotes/origin/{target_branch}")
            diffs = base.diff(f"refs/remotes/origin/{source_branch}", create_patch=True)

            changes = []

            for diff_obj in diffs:
                # Convertendo o diff para string
                diff_str = diff_obj.diff.decode('utf-8', 'ignore')

                # Encontrando a linha que começa com "@@ -" que indica os números das linhas que mudaram
                lines = diff_str.split('\n')
                for line in lines:
                    if line.startswith("@@ -"):
                        # Parsing das linhas
                        parts = line.split(' ')
                        old_line_data = parts[1][1:].split(',')
                        new_line_data = parts[2][1:].split(',')

                        file_name = diff_obj.b_path if diff_obj.b_path else diff_obj.a_path

                        file_change = {
                            "file": "/" + file_name,
                            "start_line": int(new_line_data[0]),
                            "end_line": int(new_line_data[0]) + (
                                int(new_line_data[1]) if len(new_line_data) > 1 else 1) - 1,
                            "change": diff_str
                        }
                        changes.append(file_change)
                        break
            return changes
    except Exception as e:
        print(f"Erro ao obter diff entre {source_branch} e {target_branch}: {e}")
        return ""


def get_repo(repo_url, repo_name, pr_id, repository_path):
    repo_path = os.path.join(repository_path, repo_name)

    # Se o repositório já existe, apenas atualize
    if os.path.exists(repo_path):
        try:
            with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                repo = Repo(repo_path)
                repo.remotes.origin.fetch(env={"GIT_SSH_COMMAND": git_ssh_cmd})   # Busca as últimas mudanças do remoto
        except Exception as e:
            # Se houver qualquer erro ao atualizar, remova e clone novamente
            with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                shutil.rmtree(repo_path)
                repo = Repo.clone_from(repo_url, repo_path, env={"GIT_SSH_COMMAND": git_ssh_cmd})
    else:
        with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
            repo = Repo.clone_from(repo_url, repo_path, env={"GIT_SSH_COMMAND": git_ssh_cmd})

    return repo
