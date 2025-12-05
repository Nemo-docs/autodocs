from openai import OpenAI
from github_client import GitHubClient

def create_summary(client: GitHubClient, api_key: str, default_branch: str, base_url: str = None) -> str:
    readme_path = "README.md"
    try:
        readme_content = client.get_file_content(default_branch, readme_path)
        print(f"[Agents] Fetched README with {len(readme_content)} characters")
    except Exception as e:
        print(f"[Agents] Failed to fetch README: {e}")
        return None

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    openai_client = OpenAI(**client_kwargs)

    prompt = """Please provide a concise summary of the following README file. 
Focus on the project's purpose, key features, installation, and usage. 
Keep it under 500 words.

README:

{}""".format(readme_content)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.choices[0].message.content.strip()
        summary_content = f"""# Automated Repository Summary

{summary}

*This summary was automatically generated using OpenAI.*
"""
        return summary_content
    except Exception as e:
        print(f"[Agents] OpenAI summarization failed: {e}")
        return None
