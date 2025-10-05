# Release v0.1.0

🎉 **Initial Release of Gemini Search MCP**

Gemini Search MCP is a Model Context Protocol (MCP) server that brings Google Gemini's powerful AI capabilities to your development workflow through Codex and Copilot CLI.

## ✨ Key Features

### 🔍 Web Search Tool
Use Gemini 2.5 Flash with Google Search grounding to get up-to-date information from the web directly in your CLI.

```bash
# Example usage in Copilot/Codex CLI
> Search for the latest Python 3.13 release notes
> What are the new features in React 19?
```

### 📄 Document Question Answering
Analyze and answer questions about local documents (PDF, images, Office files) using Gemini 2.5 Flash Lite.

```bash
# Example usage
> Summarize the main points from this research paper: /path/to/paper.pdf
> What is the conclusion in this document?
```

### ⚙️ Easy Configuration
Automatic configuration for both Codex and Copilot CLI with a single command:

```bash
# Configure both CLIs at once
gemini-search-mcp configure --cli-type both --api-key "YOUR_KEY"

# Or configure individually
gemini-search-mcp configure --cli-type codex --api-key "YOUR_KEY"
gemini-search-mcp configure --cli-type copilot --api-key "YOUR_KEY"
```

## 📦 Installation

### Python (pip)
```bash
pip install gemini-search-mcp==0.1.0
```

### Node.js (npm)
```bash
npm install -g gemini-search-mcp@0.1.0
```

## 🚀 Quick Start

1. **Install the package** (see above)

2. **Get a Google API Key** from [Google AI Studio](https://aistudio.google.com/)

3. **Configure your CLI**:
   ```bash
   gemini-search-mcp configure --cli-type both --api-key "YOUR_API_KEY"
   ```

4. **Start using it** in Codex or Copilot CLI!

For detailed setup instructions, see the [Quick Start Guide](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/QUICKSTART.md).

## 🔧 What's Included

### Core Functionality
- ✅ MCP server with stdio transport
- ✅ `web_search` tool with Google Search grounding
- ✅ `document_question_answering` tool with multi-format support
- ✅ CLI commands: `run`, `configure`, `clear-cache`
- ✅ Automatic config file management (JSON & TOML)

### Platform Support
- ✅ Python 3.9, 3.10, 3.11, 3.12
- ✅ Node.js 18, 20, 22
- ✅ Windows, macOS, Linux

### Documentation
- 📖 [README](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/README.md) - Overview and features
- 📖 [QUICKSTART](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/QUICKSTART.md) - Getting started guide
- 📖 [SETUP_ACCOUNTS](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/SETUP_ACCOUNTS.md) - Account setup guide
- 📖 [CHANGELOG](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/CHANGELOG.md) - Version history

## 🐛 Bug Fixes

This release includes several important fixes:
- Fixed Node.js wrapper to correctly call Python CLI entry point
- Fixed default command handling when no subcommand is provided
- Improved Copilot CLI configuration support

## 🔐 Security Notes

- Never commit your API keys to version control
- Use environment variables or the configure command to manage credentials
- See [SETUP_ACCOUNTS.md](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/SETUP_ACCOUNTS.md) for security best practices

## 📚 Links

- **PyPI**: https://pypi.org/project/gemini-search-mcp/0.1.0/
- **npm**: https://www.npmjs.com/package/gemini-search-mcp/v/0.1.0
- **Documentation**: https://github.com/MIMICLab/GeminiSearchMCP
- **Issues**: https://github.com/MIMICLab/GeminiSearchMCP/issues

## 🙏 Requirements

- Google API key with Gemini access
- Python 3.9+ (for Python installation)
- Node.js 18+ (for npm installation or Node wrapper)
- Codex CLI or Copilot CLI

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues or pull requests.

## 📄 License

MIT License - see [LICENSE](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/LICENSE) for details.

---

**Full Changelog**: https://github.com/MIMICLab/GeminiSearchMCP/commits/v0.1.0
