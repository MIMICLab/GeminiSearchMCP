# Release v0.1.0

🎉 **Initial Release of Gemini Search MCP**

## ✨ What's New

### Added
- 🔍 **Web Search Tool** - Google-grounded web searches via Gemini 2.5 Flash
- 📄 **Document Q&A Tool** - Analyze PDFs, images, and documents with Gemini 2.5 Flash Lite
- ⚙️ **Smart Configuration** - Automatic setup for both Codex and Copilot CLI
- 🎛️ **CLI Commands** - `run`, `configure`, `clear-cache`
- 🌍 **Cross-Platform** - Python 3.9+ and Node.js 18+ support
- 📖 **Complete Documentation** - Quick start, setup guides, and API references

### Fixed
- Node.js wrapper now correctly calls Python CLI entry point
- Default command handling improved
- Copilot CLI configuration support enhanced

## 📦 Installation

```bash
# Python
pip install gemini-search-mcp==0.1.0

# Node.js
npm install -g gemini-search-mcp@0.1.0
```

## 🚀 Quick Start

```bash
# 1. Configure for both Codex and Copilot CLI
gemini-search-mcp configure --cli-type both --api-key "YOUR_GOOGLE_API_KEY"

# 2. Start using in your CLI!
# Now you can ask questions like:
# - "Search for the latest Python releases"
# - "Summarize this PDF: /path/to/document.pdf"
```

## 📚 Documentation

- [Quick Start Guide](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/QUICKSTART.md)
- [Setup Accounts](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/SETUP_ACCOUNTS.md)
- [Full Changelog](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/CHANGELOG.md)

## 🔗 Links

- **PyPI**: https://pypi.org/project/gemini-search-mcp/0.1.0/
- **npm**: https://www.npmjs.com/package/gemini-search-mcp/v/0.1.0
- **Issues**: https://github.com/MIMICLab/GeminiSearchMCP/issues

## 🙏 Requirements

- Google API key with Gemini access ([Get one here](https://aistudio.google.com/))
- Python 3.9+ or Node.js 18+
- Codex CLI or Copilot CLI

---

**Full Changelog**: https://github.com/MIMICLab/GeminiSearchMCP/commits/v0.1.0
