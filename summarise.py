import os
import json
import requests
import subprocess
from datetime import datetime
import re
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration using environment variables
API_ENDPOINT = os.getenv("LOCAL_LLM_API", "http://127.0.0.1:5000/v1/chat/completions")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
OUTPUT_DIR = os.path.expanduser(os.getenv("OUTPUT_DIR", "~/Documents/github-summaries"))

# Validate required environment variables
required_vars = ["LOCAL_LLM_API", "GITHUB_TOKEN", "GITHUB_USERNAME"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable {var} is not set.")

def fetch_user_repositories():
    """Fetch all repositories created by the user (excluding forks)"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repos = []
    page = 1
    
    while True:
        url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?page={page}&per_page=100"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        page_repos = response.json()
        if not page_repos:
            break
            
        # Filter out forked repositories
        original_repos = [repo for repo in page_repos if not repo["fork"]]
        repos.extend(original_repos)
        
        page += 1
    
    print(f"Found {len(repos)} original repositories.")
    return repos

def fetch_repo_details(repo_name):
    """Fetch additional details about a repository"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get repository information
    repo_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}"
    repo_response = requests.get(repo_url, headers=headers)
    repo_response.raise_for_status()
    repo_data = repo_response.json()
    
    # Get languages used
    languages_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/languages"
    languages_response = requests.get(languages_url, headers=headers)
    languages_response.raise_for_status()
    languages_data = languages_response.json()
    
    # Get README content if available
    readme_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/readme"
    try:
        readme_response = requests.get(readme_url, headers=headers)
        readme_response.raise_for_status()
        readme_data = readme_response.json()
        readme_content = base64.b64decode(readme_data["content"]).decode("utf-8")
    except:
        readme_content = ""
    
    # Get commit count
    commit_count = 0
    try:
        commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits?per_page=1"
        commits_response = requests.get(commits_url, headers=headers)
        commits_response.raise_for_status()
        
        if 'Link' in commits_response.headers:
            links = commits_response.headers['Link']
            if 'rel="last"' in links:
                last_page_url = [link.split(';')[0].strip('<>') for link in links.split(',') if 'rel="last"' in link][0]
                commit_count = int(re.search(r'page=(\d+)', last_page_url).group(1))
        else:
            # If no Link header, try to count manually but with better error handling
            try:
                commits_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits?per_page=100"
                page = 1
                while True:
                    paged_url = f"{commits_url}&page={page}"
                    page_response = requests.get(paged_url, headers=headers)
                    page_response.raise_for_status()
                    page_commits = page_response.json()
                    if not page_commits:
                        break
                    commit_count += len(page_commits)
                    page += 1
                    if page > 10:  # Reasonable limit to avoid excessive API calls
                        print(f"  Warning: Repository {repo_name} has many commits, limiting count to 1000+")
                        commit_count = "1000+"
                        break
            except requests.exceptions.HTTPError as e:
                print(f"  Warning: Error fetching commit count for {repo_name}: {e}")
                commit_count = "Unknown"
    except requests.exceptions.HTTPError as e:
        print(f"  Warning: Error fetching commit count for {repo_name}: {e}")
        commit_count = "Unknown"
    
    return {
        "name": repo_data["name"],
        "description": repo_data["description"] or "",
        "url": repo_data["html_url"],
        "created_at": repo_data["created_at"],
        "updated_at": repo_data["updated_at"],
        "stars": repo_data["stargazers_count"],
        "forks": repo_data["forks_count"],
        "languages": languages_data,
        "readme": readme_content,
        "commit_count": commit_count,
        "topics": repo_data.get("topics", [])
    }

def generate_repo_summary(repo_details):
    """Generate a summary of the repository using the LLM"""
    
    # Create a prompt for the LLM
    prompt = f"""
    As a technical writer, create a concise and informative summary of this GitHub repository:
    
    Repository Name: {repo_details['name']}
    Description: {repo_details['description']}
    Languages: {', '.join(repo_details['languages'].keys())}
    Stars: {repo_details['stars']}
    Forks: {repo_details['forks']}
    Created: {repo_details['created_at']}
    Last Updated: {repo_details['updated_at']}
    Commit Count: {repo_details['commit_count']}
    Topics: {', '.join(repo_details['topics'])}
    
    README Content:
    {repo_details['readme'][:1000] if len(repo_details['readme']) > 1000 else repo_details['readme']}
    
    Write a 2-3 paragraph summary that explains what this project does, its key features, and its technological significance.
    Focus on the purpose, technologies used, and any notable aspects.
    """
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "mode": "instruct"
    }
    
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            print(f"No content found in API response for {repo_details['name']}.")
            return None
            
        content = response_json["choices"][0]["message"]["content"]
        return content.strip()
        
    except Exception as e:
        print(f"Error generating summary for {repo_details['name']}: {e}")
        return None

def create_markdown_summary(repos_data):
    """Create a comprehensive markdown summary of all repositories"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    markdown = f"""# GitHub Repository Summary

*Generated on {timestamp}*

This document provides an overview of all original repositories created by [{GITHUB_USERNAME}](https://github.com/{GITHUB_USERNAME}).

## Overview

- Total Repositories: {len(repos_data)}
- Primary Languages: {get_primary_languages(repos_data)}
- Most Active Repositories: {get_most_active_repos(repos_data)}

## Repositories

"""
    
    # Sort repositories by update date (most recent first)
    sorted_repos = sorted(repos_data, key=lambda x: x["updated_at"], reverse=True)
    
    for repo in sorted_repos:
        # Format creation and update dates
        created_date = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        updated_date = datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        
        # Format languages with percentages
        total_bytes = sum(repo["languages"].values())
        languages_formatted = []
        for lang, bytes_count in repo["languages"].items():
            percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
            languages_formatted.append(f"{lang} ({percentage:.1f}%)")
        
        # Add repository section
        markdown += f"""### [{repo["name"]}]({repo["url"]})

- **Created:** {created_date}
- **Last Updated:** {updated_date}
- **Stars:** {repo["stars"]}
- **Forks:** {repo["forks"]}
- **Languages:** {', '.join(languages_formatted)}
- **Commits:** {repo["commit_count"]}
- **Topics:** {', '.join(repo["topics"]) if repo["topics"] else "None"}

{repo["summary"] if repo["summary"] else "No summary available."}

---

"""
    
    return markdown

def get_primary_languages(repos_data):
    """Calculate and return the most used languages across all repositories"""
    language_counts = {}
    
    for repo in repos_data:
        for language in repo["languages"].keys():
            if language in language_counts:
                language_counts[language] += 1
            else:
                language_counts[language] = 1
    
    # Sort by frequency and get top 5
    top_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return ', '.join([lang for lang, count in top_languages])

def get_most_active_repos(repos_data):
    """Return the names of the most active repositories (by commit count)"""
    valid_repos = [repo for repo in repos_data if isinstance(repo["commit_count"], int)]
    if not valid_repos:
        return "Unable to determine"
    sorted_by_commits = sorted(valid_repos, key=lambda x: x["commit_count"], reverse=True)[:3]
    return ', '.join([repo["name"] for repo in sorted_by_commits])

def main():
    # Create output directory if it doesn't exist
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output will be saved to: {output_dir}")
    
    # Fetch all original repositories
    repos = fetch_user_repositories()
    
    # Process each repository
    all_repo_data = []
    for i, repo in enumerate(repos, 1):
        print(f"Processing repository {i}/{len(repos)}: {repo['name']}")
        
        try:
            # Fetch detailed information
            repo_details = fetch_repo_details(repo["name"])
            
            # Generate summary using LLM
            print(f"Generating summary for {repo['name']}...")
            summary = generate_repo_summary(repo_details)
            repo_details["summary"] = summary
            
            all_repo_data.append(repo_details)
        except Exception as e:
            print(f"Error processing repository {repo['name']}: {e}")
            print(f"Skipping {repo['name']} and continuing with next repository.")
    
    # Create the markdown summary
    markdown_content = create_markdown_summary(all_repo_data)
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"github_summary_{timestamp}.md"
    file_path = output_dir / filename
    
    with open(file_path, "w") as f:
        f.write(markdown_content)
    
    print(f"Summary saved to: {file_path}")

if __name__ == "__main__":
    main()