import os
import time
import shutil
import argparse
import requests
import subprocess
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import urljoin
from structured_config import Structure, PathField


class Config(Structure):
    server = "https://app.getoutline.com"
    api_token = "A1B2C3"
    git_url = "git@github.com:username/wiki_backup.git"
    git_rsa = PathField("~/.ssh/id_rsa")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="read config file (or write new one if missing)")
    args = parser.parse_args()

    configfile = Path(args.config).resolve()
    config = Config(configfile)

    print(f"Backup from {config.server}")

    export_url = urljoin(config.server, "/api/collections.export_all")
    headers = {
        'authorization': f'Bearer {config.api_token}',
        'content-type': 'application/json',
        'accept': 'application/json',
    }
    response = requests.post(export_url, headers=headers)

    response.raise_for_status()

    data = response.json()

    file_operation = data.get('data', {}).get('fileOperation')
    if not file_operation:
        raise SystemExit("Did not get the fileOperation details:", data)

    start = int(time.time())
    file_id = file_operation['id']
    details = {}
    file_url = urljoin(config.server, "/api/fileOperations.info")
    for _retry in range(600):
        details = requests.post(file_url, headers=headers, json={'id': file_id}).json()
        if details.get('data', {})['state'] == "complete":
            break
        time.sleep(1)
        print(".", end='')

    if not details.get('data', {})['state'] == "complete":
        raise SystemExit("Did not get file download detail")
    end = int(time.time())
    print(f"\nexport on server finished after {end-start}s")

    retreive_url = urljoin(config.server, "/api/fileOperations.redirect")

    backup_name = f'{time.strftime("%Y%m%d-%H%M%S")}_backup'
    filename = Path('.') / f'{backup_name}.zip'

    with requests.post(retreive_url, headers=headers, json={'id': file_id}, stream=True) as r:
        # if r.headers
        with open(filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    print(f"Exported to: {filename.resolve()}")

    gitdir = Path('.') / 'backup_repo'

    git_rsa = str(config.git_rsa.expanduser()).replace("\\", "\\\\")
    ssh_env = os.environ.copy()
    ssh_env["GIT_SSH_COMMAND"] = f'ssh -i {git_rsa} -o IdentitiesOnly=yes'

    if not gitdir.exists():
        subprocess.run(['git', 'clone', config.git_url, str(gitdir)], env=ssh_env)
        subprocess.run(['git', 'lfs', 'install'], cwd=str(gitdir), env=ssh_env)
        subprocess.run(['git', 'lfs', 'track', '*.png'], cwd=str(gitdir), env=ssh_env)
        subprocess.run(['git', 'lfs', 'track', '*.pdf'], cwd=str(gitdir), env=ssh_env)
        subprocess.run(['git', 'lfs', 'track', '*.jpg'], cwd=str(gitdir), env=ssh_env)
        subprocess.run(['git', 'lfs', 'track', '*.zip'], cwd=str(gitdir), env=ssh_env)

    with ZipFile(filename) as zf:
        zf.extractall(path=gitdir)

    subprocess.run(['git', 'add', '.'], cwd=str(gitdir), env=ssh_env)
    subprocess.run(['git', 'commit', '-m', backup_name], cwd=str(gitdir), env=ssh_env)
    subprocess.run(['git', 'push'], cwd=str(gitdir), env=ssh_env)
    print("Finished")


