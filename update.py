#!/usr/bin/python3

import json
import os
import subprocess

import requests
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

########### CONFIG ################

found_configuration = False

try:
    from config import GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_PRIVKEY, GITHUB_BLACKLIST
    github = True
    found_configuration = True
except Exception:
    github = False
    pass

try:
    from config import GITOLITE_URL, GITOLITE_USER, GITOLITE_PRIVKEY
    gitolite = True
    found_configuration = True
except Exception:
    gitolite = False
    pass


cwd = os.path.abspath(os.path.dirname(__file__))

def set_ssh_privkey(privkey_path):
    ssh = f"ssh -i {os.path.join(cwd, privkey_path)}"
    os.environ["GIT_SSH_COMMAND"] = ssh

def unset_ssh_privkey():
    os.environ["GIT_SSH_COMMAND"] = "ssh"


########### FETCH LIST OF REPOS ##############

def fetch_gitolite_repos():
    """
    returns List[url, target_folder]
    """

    print(f"Fetching repos from {GITOLITE_URL} ...")
    repos = []

    print()
    ssh = os.environ["GIT_SSH_COMMAND"]
    p = subprocess.check_output(ssh.split(" ") + [f"{GITOLITE_USER}@{GITOLITE_URL}"]).decode("utf8")
    print()

    for s in p.split("\n\n")[1].split("\n"):
        if len(s) > 2:
            repo = s.split("\t")[1]
            target_folder = f"{GITOLITE_URL}/{repo}"
            # print(f"{repo}, {target_folder}")
            repos.append((f"{GITOLITE_USER}@{GITOLITE_URL}:{repo}", target_folder))

    return repos


def fetch_github_repos():
    """
    returns List[url, target_folder]

    target_folder is a relative path from this file
    """

    print(f"Fetching repos from github.com/{GITHUB_USERNAME}...")
    repos = []

    p = requests.get(
        "https://api.github.com/user/repos", auth=HTTPBasicAuth(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    response = json.loads(p.content)
#    print(json.dumps(response, indent=4))
    if "Bad credentials" in str(response) or "Requires authentication" in str(response):
        print("Invalid token, exiting...")
        exit(1)

    for r in response:
        url = r["git_url"].replace("git://github.com/", "git@github.com:")
        name = r["full_name"]
        repos.append((url, f"github/{name.lower()}"))

    return repos

########### UPDATE REPOS ##############

def update_repos(repos):
    """
    repos: List[url, target_folder]

    target_folder is a relative path from this file
    """

    print("Updating...")

    for repo_url, target_folder in tqdm(repos):
        if any(map(lambda x: x in repo_url, GITHUB_BLACKLIST)):
            continue

        if not os.path.exists(target_folder):
            print(f"Adding {repo_url}...")
            subprocess.run(["git", "clone", repo_url, target_folder])

            os.chdir(target_folder)
            branches = str(subprocess.check_output(["git", "branch", "--all"]))
            if "master" in branches:
                subprocess.run(["git", "checkout", "master"])

            elif "main" in branches:
                subprocess.run(["git", "checkout", "main"])

        else:
            os.chdir(target_folder)

            try:
                out = subprocess.check_output(["git", "pull", "--ff-only"]).strip().decode()
            except subprocess.CalledProcessError:
                print(f"Failed for {target_folder}")
                exit(1)

            if out != "Already up to date.":
                print(f"[{repo_url}]    {out}")

        os.chdir(cwd)


if __name__ == "__main__":
    if not found_configuration:
        print(f"Nothing configured, expected to find {os.path.join(cwd, 'config.py')}.")
        exit(1)

    if gitolite:
        print()
        set_ssh_privkey(GITOLITE_PRIVKEY)
        repos = fetch_gitolite_repos()
        update_repos(repos)

    if github:
        print()
        set_ssh_privkey(GITHUB_PRIVKEY)
        repos = fetch_github_repos()
        update_repos(repos)
