from openai import AsyncAzureOpenAI
import os
import requests
from github import Github

token = os.getenv('TOKEN')
repo_name = os.getenv('REPO_NAME')
pr_number = os.getenv('PR_NUMBER')
azure_api_key = os.getenv('AZURE_API_KEY')
azure_endpoint = os.getenv('AZURE_ENDPOINT')

MINIMUM_SUPPORTED_AZURE_OPENAI_PREVIEW_API_VERSION = "2024-05-01-preview"
USER_AGENT = "GitHubSampleWebApp/AsyncAzureOpenAI/1.0.0"
GPT_MODEL = "gpt-4o"

# Function to send a prompt and get a response
async def generate_text(azure_openai_client, prompt):
    response = await azure_openai_client.chat.completions.with_raw_response.create(
        model=GPT_MODEL,  # Replace with the appropriate engine name
        messages= prompt,
        max_tokens=50  # Adjust the max tokens as per your need
    )
    return response

async def get_ai_suggestions(code_snippet):
    # Default Headers
    default_headers = {"x-ms-useragent": USER_AGENT}

    azure_openai_client = AsyncAzureOpenAI(
        api_version=MINIMUM_SUPPORTED_AZURE_OPENAI_PREVIEW_API_VERSION,
        api_key=azure_api_key,
        azure_ad_token_provider=None,
        default_headers=default_headers,
        azure_endpoint=azure_endpoint,
    )

    prompt = [
        {"role": "user", "content": "Add comment as to what is there in the code/file \n\n" + code_snippet}
    ]

    raw_response = await generate_text(azure_openai_client, prompt)
    response = raw_response.parse()

    ai_code_suggestions = response.choices[0].message.content
    print(ai_code_suggestions)
    return ai_code_suggestions

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


async def runApp():
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number))

    # Find the specific commit that modified the file
    commit_id = None
    commits = pr.get_commits()
    for commit in commits:
        commit_files = commit.files
        for commit_file in commit_files:
            if commit_file.filename == file_path:
                commit_id = commit.sha
                break
        if commit_id:
            break

    if not commit_id:
        print(f"Could not find commit that modified file {file_path}")
        continue

    # Iterate over files changed in the PR
    files_changed = pr.get_files()
    for file in files_changed:
        file_path = file.filename

        # Get the file content from the head branch of the PR
        file_content = repo.get_contents(file_path, ref=pr.head.ref)
        file_content_decoded = file_content.decoded_content.decode('utf-8')

        # Use the entire content of the file for AI suggestions
        suggestions = await get_ai_suggestions(file_content_decoded)
        comment_body = f"AI Suggestions for the file `{file_path}`:\n\n```\n{suggestions}\n```"

        # Comment on the first modified line in the file
        patch = file.patch.split('\n')
        
        try:
            first_modified_line_number = next(
                i for i, line in enumerate(patch, start=1) if line.startswith('+') and not line.startswith('+++'))
            comment_on_pr_line(repo_name, pr_number, commit_id, file_path, first_modified_line_number, comment_body)
        except StopIteration:
            print(f"No modified lines found in file {file_path}.")

import asyncio
if __name__ == '__main__':
    asyncio.run(runApp())
