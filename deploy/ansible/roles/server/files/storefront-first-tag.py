"""
Prints the image tag of a storefront's first start on this server, followed by where it comes from:

    storefront-first-tag.py REGISTRY GITHUB_REPOSITORY BRANCH production|latest

production: the image that the last successful Run workflow of Frontend CI on the branch deployed, whose tag the
deploy job makes from the commit's date in Moscow time and its short hash. Without such a run, and for latest, the
latest build, whose version label is its tag. The repository is public, so GitHub needs no token.
"""
import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def github(repository, path):
    request = urllib.request.Request(f'https://api.github.com/repos/{repository}/{path}',
                                     headers={'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def deployed(repository, branch):
    runs = github(repository, f'actions/workflows/frontend.yml/runs?branch={branch}'
                              '&event=workflow_dispatch&status=success&per_page=20')['workflow_runs']
    if not runs:
        return None
    # A re-run of an older deploy, a rollback, keeps its creation time, but starts again
    sha = max(runs, key=lambda run: run['run_started_at'])['head_sha']
    date = datetime.fromisoformat(github(repository, f'commits/{sha}')['commit']['committer']['date'])
    return f'{date.astimezone(ZoneInfo("Europe/Moscow")):%Y.%m.%d}-{sha[:7]}'


def latest(registry, branch):
    ref = f'{registry}/{branch}:latest'
    subprocess.run(['docker', 'pull', '--quiet', ref], check=True, stdout=subprocess.DEVNULL)
    labels = json.loads(subprocess.run(['docker', 'image', 'inspect', '--format', '{{json .Config.Labels}}', ref],
                                       check=True, capture_output=True, text=True).stdout) or {}
    return labels['org.opencontainers.image.version']


def main(registry, repository, branch, mode):
    if mode == 'production' and repository:
        tag = deployed(repository, branch)
        if tag:
            print(tag, 'production')
            return
    print(latest(registry, branch), 'latest')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit(f'usage: {sys.argv[0]} REGISTRY GITHUB_REPOSITORY BRANCH production|latest')
    main(*sys.argv[1:])
