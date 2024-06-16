import os
import requests
import aiohttp
import asyncio
from github import Github

# GitHub API token
token = os.getenv('GITHUB_TOKEN')
repo_name = os.getenv('REPO_NAME')
pr_number = os.getenv('PR_NUMBER')
azure_api_key = os.getenv('AZURE_API_KEY')
azure_endpoint = os.getenv('AZURE_ENDPOINT')

def comment_on_pr_line(repo, pr_number, commit_id, file_path, line_number, comment_body):
    url = f'https://api.github.com/repos/{repo}/pulls/{pr_number}/comments'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'body': comment_body,
        'commit_id': commit_id,
        'path': file_path,
        'side': 'RIGHT',
        'line': line_number
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print(f'Successfully commented on the line {line_number} in file {file_path}.')
    else:
        print(f'Failed to comment on the line: {response.content}')

async def main():
    # Initialize GitHub client
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    # Get the latest commit on the PR
    commit_id = pr.get_commits().reversed[0].sha

    # Iterate over files changed in the PR
    files_changed = pr.get_files()


if __name__ == "__main__":
    asyncio.run(main())
