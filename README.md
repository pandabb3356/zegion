# Zegion

<p align="center">
  <img src="logo.svg" alt="Zegion">
</p>

<p align="center">
    <em>Automate Your Code Documentation Journey</em>
</p>

<p align="center">
<a target="_blank">
    <img src="https://img.shields.io/badge/python-3.13-blue.svg" alt="Supported Python versions">
</a>
</p>

---

`Zegion` is an automated documentation generation tool designed to streamline the process of reading your code, generating insightful summaries, formatting them into Markdown, and seamlessly uploading the result to Notion. Leveraging advanced AI agents, Zegion transforms raw code into well-structured, professional documentation.

## Features

- **Automated Code Parsing:** Extracts the structure of your codebase.
- **Intelligent Summary Generation:** Uses AI to create comprehensive code summaries.
- **Markdown Formatting:** Converts summaries into clean, readable Markdown.
- **Notion Integration:** Uploads documentation as Notion blocks for easy sharing and collaboration.
- **Customizable Workflow:** Supports various configurations for different documentation writers and models.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your_username/zegion.git
   cd zegion
   ```
2. **Install Dependencies:**

    Use your preferred package manager (e.g., pip) to install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage
Below is an example of how to run `Zegion`:

```bash
zegion --title=DocWriter --src=docwriter --writer=notion --notion-api-key=<your_notion_api_key> --openai-model=gpt-4o-mini --notion-parent-page-id=<your_page_id>
```

### Options

| Option                    | Alias  | Type                                      | Description                                                                               | Default      | Required |
|---------------------------|--------|-------------------------------------------|-------------------------------------------------------------------------------------------|--------------|----------|
| `--src`                   | `-s`   | path                                      | The path to the source code directory.                                                  | None         | Yes      |
| `--title`                 | `-t`   | text                                      | The title of the documentation.                                                         | None         | Yes      |
| `--writer`                | `-w`   | notion / none                             | The type of documentation writer to use.                                                | None         | Yes      |
| `--notion-api-key`        |        | text                                      | The Notion API key.                                                                       | None         | No       |
| `--notion-parent-page-id` |        | text                                      | The Notion parent page ID.                                                                | None         | No       |
| `--openai-model`          |        | text                                      | The default OpenAI model.                                                                 | gpt-4o-mini  | No       |
| `--log-level`             |        | DEBUG / INFO / WARNING / ERROR / CRITICAL | The log level to use.                                                                     | WARNING      | No       |
| `--help`                  |        | N/A                                       | Show this message and exit.                                                               | N/A          | No       |
