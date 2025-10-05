# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Gemini Search MCP
- MCP server implementation with stdio transport
- `web_search` tool for Google-grounded web searches via Gemini
- `document_question_answering` tool for document analysis
- CLI with `run`, `configure`, and `clear-cache` commands
- Support for both Python (pip) and Node.js (npm) installation
- **Automatic configuration for both Codex and Copilot CLI**
- **Support for JSON config files (Copilot) and TOML config files (Codex)**
- **`--cli-type` option to configure specific or both CLIs at once**
- GitHub Actions workflows for CI/CD
- Comprehensive documentation

### Fixed
- Node.js wrapper now correctly calls Python CLI entry point
- Default command handling when no subcommand is provided
- Support for Copilot CLI configuration

## [0.1.0] - 2025-01-XX

### Added
- Initial public release
- Core MCP server functionality
- Web search and document Q&A tools
- Cross-platform support (Windows, macOS, Linux)
- Python 3.9+ support
- Node.js 18+ support

[Unreleased]: https://github.com/YOUR_USERNAME/GeminiSearchMCP/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YOUR_USERNAME/GeminiSearchMCP/releases/tag/v0.1.0
