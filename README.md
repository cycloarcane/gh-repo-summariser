# GitHub Repository Summarizer

A Python application that automatically analyzes all your created GitHub repositories and generates a comprehensive Obsidian-compatible Markdown summary using a locally hosted LLM.

## Features

- **GitHub API Integration**: Fetches all original repositories (excluding forks) from your GitHub account.
- **Detailed Repository Analysis**: Collects language statistics, commit counts, stars, forks, and README contents.
- **AI-Powered Summaries**: Uses a local LLM to generate concise, informative summaries for each repository.
- **Obsidian Compatibility**: Produces a well-formatted Markdown file ready for use in Obsidian or other Markdown editors.
- **Error Resilience**: Handles API rate limits and repository access errors gracefully.

## Benefits

- **Portfolio Overview**: Quickly obtain an overview of all your GitHub projects.
- **Documentation**: Auto-generate documentation that summarizes your development work.
- **Project Insights**: Gain insights into language usage and activity patterns across repositories.
- **Time Saving**: Eliminate manual documentation and portfolio creation.

## Usage

### Prerequisites

- Python 3.6 or higher
- Local LLM with API (similar to the DeepSeek setup)
- GitHub Personal Access Token
- Required Python packages: `requests`, `python-dotenv`

### Quick Start

```bash
# Clone this repository
git clone https://github.com/cycloarcane/gh-repo-summariser.git
cd gh-repo-summariser

# Set up virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install requests python-dotenv

# Create .env file with your configuration
echo "LOCAL_LLM_API=http://127.0.0.1:5000/v1/chat/completions
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username
OUTPUT_DIR=~/Documents/github-summaries" > .env

# Run the script
python summarize.py
```

### Environment Variables

- `LOCAL_LLM_API`: URL of your local LLM API endpoint
- `GITHUB_TOKEN`: Your GitHub Personal Access Token with appropriate permissions
- `GITHUB_USERNAME`: Your GitHub username
- `OUTPUT_DIR`: Directory where the summary file will be saved

## Output Example

The script generates a comprehensive Markdown file with sections for:

- Overall repository statistics
- Primary programming languages used
- Most active repositories
- Detailed information for each repository including:
  - Creation and update dates
  - Stars and forks
  - Language breakdown with percentages
  - Commit count
  - Topics
  - AI-generated summary

## Customization

You can customize the script by:
- Modifying the LLM prompt in the `generate_repo_summary` function
- Adjusting the Markdown template in the `create_markdown_summary` function
- Adding additional repository metrics to collect and display

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## Author

cycloarcane  
Email: cycloarkane@gmail.com  
GitHub: [cycloarcane](https://github.com/cycloarcane)

## License

This project is licensed under the MIT License. See the LICENSE file for more information.