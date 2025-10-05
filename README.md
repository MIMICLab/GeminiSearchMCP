# Gemini Search MCP

[![PyPI version](https://badge.fury.io/py/gemini-search-mcp.svg)](https://badge.fury.io/py/gemini-search-mcp)
[![npm version](https://badge.fury.io/js/gemini-search-mcp.svg)](https://badge.fury.io/js/gemini-search-mcp)
[![CI Tests](https://github.com/YOUR_USERNAME/GeminiSearchMCP/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/GeminiSearchMCP/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Gemini Search MCP packages a [Model Context Protocol](https://www.modelcontextprotocol.io/) server that exposes two tools:

- **web_search** – Uses Gemini with Google Search grounding to answer general questions.
- **document_question_answering** – Converts local documents to captioned markdown and asks Gemini to answer questions about their contents.

## Installation

### Python (pip)

```bash
pip install gemini-search-mcp
```

### Node.js (npm)

```bash
npm install -g gemini-search-mcp
```

## Usage

Set your Google API key (must have Gemini access):

```bash
export GOOGLE_API_KEY="your-key"
```

Run the MCP server (defaults to stdio transport):

```bash
gemini-search-mcp run
# or simply
# gemini-search-mcp
```

Configure Codex automatically (writes to `~/.codex/config.toml` by default):

```bash
gemini-search-mcp configure --api-key "YOUR_KEY"
```

Configure Copilot CLI (writes to `~/.copilot/config.json`):

```bash
gemini-search-mcp configure --cli-type copilot --api-key "YOUR_KEY"
```

Configure both Codex and Copilot CLI at once:

```bash
gemini-search-mcp configure --cli-type both --api-key "YOUR_KEY"
```

For npm/npx installation with custom command:

```bash
gemini-search-mcp configure --command npx --command-args -y gemini-search-mcp --api-key "YOUR_KEY"
```

Clear cached conversion artifacts:

```bash
gemini-search-mcp clear-cache
# 선택 옵션: --cache-dir /custom/path --remove-root
```

## Development

Install in editable mode with testing dependencies:

```bash
pip install -e .
```

Ensure LibreOffice is installed and on `PATH` if you plan to convert non-PDF documents.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Publishing

For maintainers: See [PUBLISHING.md](PUBLISHING.md) for instructions on how to publish new versions to PyPI and npm.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes in each version.

## License

MIT – all rights reserved.
