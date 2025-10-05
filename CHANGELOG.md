# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **get_document_content** tool - Converts documents to markdown and returns full content
- **get_document_chunk** tool - Retrieves specific chunks of large documents for easier processing
- **get_next_chunk** tool - Automatically continues reading from the last position (stateful navigation)
- Session state tracking for seamless document navigation
- Support for reading entire documents without asking questions
- Cached file location information in all document tools

## [0.1.0] - 2025-01-05

### Added
- Initial release of Gemini Search MCP
- MCP server implementation with stdio transport
- `web_search` tool for Google-grounded web searches via Gemini 2.5 Flash
- `document_question_answering` tool for document analysis with Gemini 2.5 Flash Lite
- CLI with `run`, `configure`, and `clear-cache` commands
- Support for both Python (pip) and Node.js (npm) installation
- **Automatic configuration for both Codex and Copilot CLI**
- **Support for JSON config files (Copilot) and TOML config files (Codex)**
- **`--cli-type` option to configure specific or both CLIs at once**
- Cross-platform support (Windows, macOS, Linux)
- Python 3.9+ support
- Node.js 18+ support
- Comprehensive documentation (README, QUICKSTART, PUBLISHING guides)
- Manual deployment scripts for PyPI and npm
- Detailed account setup guide

### Fixed
- Node.js wrapper now correctly calls Python CLI entry point
- Default command handling when no subcommand is provided
- Proper support for Copilot CLI configuration alongside Codex

### Technical Details
- Uses FastMCP for MCP protocol implementation
- Google Gemini API integration
- PDF and document processing with opendataloader-pdf
- Image captioning for document analysis
- Markdown conversion and formatting
- Cache management for processed documents

[Unreleased]: https://github.com/MIMICLab/GeminiSearchMCP/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/MIMICLab/GeminiSearchMCP/releases/tag/v0.1.0
