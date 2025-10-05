# Quick Start Guide

## 1. Installation

Choose your preferred installation method:

### Python (pip)
```bash
pip install gemini-search-mcp
```

### Node.js (npm)
```bash
npm install -g gemini-search-mcp
```

## 2. Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API key"
4. Create a new API key or use an existing one
5. Copy the API key

## 3. Configure

### Option A: Environment Variable
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### Option B: Automatic Configuration (Codex/Copilot CLI)

The easiest way to configure is using the built-in configure command:

```bash
# Configure both Codex and Copilot CLI (recommended)
gemini-search-mcp configure --cli-type both --api-key "your-api-key-here"

# Configure only Codex CLI
gemini-search-mcp configure --cli-type codex --api-key "your-api-key-here"

# Configure only Copilot CLI
gemini-search-mcp configure --cli-type copilot --api-key "your-api-key-here"

# For npm/npx installation
gemini-search-mcp configure --command npx --command-args -y gemini-search-mcp --api-key "your-api-key-here"
```

This will automatically create/update the appropriate configuration files:
- **Codex**: `~/.codex/config.toml` (TOML format)
- **Copilot**: `~/.copilot/config.json` (JSON format)

## 4. Run

Start the MCP server:
```bash
gemini-search-mcp run
# or simply
gemini-search-mcp
```

## 5. Test

Test if the server is working:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | gemini-search-mcp
```

You should see a JSON response with server information.

## 6. Use with Copilot/Codex CLI

Once configured, the tools are automatically available in your CLI:

### Web Search Example
```bash
# In Copilot CLI
gh copilot
> Search for the latest Python 3.13 release notes

# In Codex CLI
codex
> What are the new features in the latest version of React?
```

### Document Q&A Example
```bash
# In Copilot CLI
gh copilot
> Analyze the PDF file at /path/to/document.pdf and summarize the main points

# In Codex CLI
codex
> What is the conclusion in this research paper: /path/to/paper.pdf
```

## Available Tools

### 1. web_search
- **Purpose**: Search the web using Google Search grounding
- **Model**: Gemini 2.5 Flash
- **Use case**: Get up-to-date information from the web

### 2. document_question_answering
- **Purpose**: Analyze and answer questions about documents
- **Supported formats**: PDF, images, Office documents (with LibreOffice)
- **Model**: Gemini 2.5 Flash Lite
- **Use case**: Extract information from local files

## Advanced Usage

### Custom Cache Directory
```bash
export GEMINI_MCP_CACHE="/path/to/custom/cache"
gemini-search-mcp run
```

Or configure permanently:
```bash
gemini-search-mcp configure --cache-dir "/path/to/custom/cache" --api-key "your-key"
```

### Clear Cache
```bash
gemini-search-mcp clear-cache

# Or with custom cache directory
gemini-search-mcp clear-cache --cache-dir /path/to/cache --remove-root
```

## Troubleshooting

### Command not found
**Problem**: `gemini-search-mcp: command not found`

**Solution**:
- For pip: Ensure Python scripts directory is in PATH
  ```bash
  export PATH="$HOME/.local/bin:$PATH"  # Linux
  export PATH="$HOME/Library/Python/3.x/bin:$PATH"  # macOS
  ```
- For npm: Ensure global npm bin directory is in PATH
  ```bash
  export PATH="$(npm config get prefix)/bin:$PATH"
  ```

### API Key Error
**Problem**: `Error: GOOGLE_API_KEY not set`

**Solution**: Set the environment variable or use the configure command

### MCP Server Not Responding
**Problem**: Server starts but doesn't respond

**Solution**:
1. Check if Python is installed: `python3 --version`
2. Verify installation: `gemini-search-mcp --help`
3. Check logs in `~/.codex/log/` or `~/.copilot/logs/`

### LibreOffice Warning
**Problem**: Warning about LibreOffice when processing Office documents

**Solution**: Install LibreOffice (optional, only needed for .docx, .xlsx, etc.)
```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# macOS
brew install --cask libreoffice

# Windows
# Download from https://www.libreoffice.org/
```

## Next Steps

- Read the full [README.md](README.md) for more details
- Check [PUBLISHING.md](PUBLISHING.md) if you want to contribute
- View [CHANGELOG.md](CHANGELOG.md) for version history

## Support

- Issues: [GitHub Issues](https://github.com/MIMICLab/GeminiSearchMCP/issues)
- Documentation: [GitHub Repository](https://github.com/MIMICLab/GeminiSearchMCP)
