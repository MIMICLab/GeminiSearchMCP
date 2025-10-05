# Publishing Guide

This document describes how to publish `gemini-search-mcp` to PyPI and npm using GitHub Actions.

⚠️ **계정이 필요합니다!** PyPI와 npm에 배포하려면 각 플랫폼의 계정과 인증 정보가 필요합니다.
상세한 설정 방법은 [SETUP_ACCOUNTS.md](SETUP_ACCOUNTS.md)를 참조하세요.

## Prerequisites

### 1. PyPI Setup

**Option A: Trusted Publishing (Recommended)**

1. Go to [PyPI](https://pypi.org/) and create an account if you don't have one
2. Navigate to your account settings → Publishing
3. Add a new pending publisher with these details:
   - **PyPI Project Name**: `gemini-search-mcp`
   - **Owner**: Your GitHub username or organization
   - **Repository name**: `GeminiSearchMCP`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `release`

**Option B: API Token**

1. Go to [PyPI](https://pypi.org/) and create an account
2. Go to Account settings → API tokens
3. Create a new API token with scope for the `gemini-search-mcp` project
4. Add the token to GitHub repository secrets as `PYPI_API_TOKEN`

### 2. npm Setup

1. Create an [npm](https://www.npmjs.com/) account if you don't have one
2. Generate an npm access token:
   - Go to npm → Profile → Access Tokens
   - Generate New Token → Classic Token
   - Select "Automation" type
3. Add the token to GitHub repository secrets:
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Create new secret: `NPM_TOKEN` = your npm token

### 3. GitHub Repository Setup

1. Enable GitHub Actions in your repository
2. Create a new environment called `release`:
   - Go to Settings → Environments → New environment
   - Name: `release`
   - (Optional) Add protection rules like required reviewers

## Publishing Methods

### Method 1: Create a GitHub Release (Automatic)

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Choose a tag (e.g., `v0.1.0`)
4. Write release notes
5. Click "Publish release"

The workflow will automatically:
- Validate the version
- Build and publish to PyPI
- Build and publish to npm

### Method 2: Manual Workflow Dispatch

1. Go to Actions → "Publish to PyPI and npm"
2. Click "Run workflow"
3. Enter the version number (e.g., `0.1.0`)
4. Click "Run workflow"

This method will:
- Publish to both PyPI and npm
- Create a GitHub release automatically

## Version Management

Version numbers should follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR.MINOR.PATCH-suffix** for pre-releases (e.g., `1.0.0-beta.1`)

### Version Update Checklist

Before publishing:
1. ✅ Update version in `pyproject.toml`
2. ✅ Update version in `package.json`
3. ✅ Update `CHANGELOG.md` with changes
4. ✅ Test locally:
   ```bash
   # Test Python package
   pip install -e .
   gemini-search-mcp --help
   
   # Test Node package
   node bin/gemini-search-mcp.js --help
   ```
5. ✅ Commit and push changes
6. ✅ Create release or run workflow

**Note**: The GitHub Actions workflow will automatically update version numbers in both files, so you can also let it handle versioning.

## Troubleshooting

### PyPI Publishing Fails

**Trusted Publishing Error**:
- Verify the pending publisher settings match exactly
- Ensure you're using the correct environment name (`release`)

**Version Already Exists**:
- PyPI doesn't allow overwriting versions
- Increment the version number

### npm Publishing Fails

**Authentication Error**:
- Verify `NPM_TOKEN` is set in GitHub secrets
- Check token hasn't expired
- Ensure token has publish permissions

**Package Name Taken**:
- Change package name in `package.json`
- Use scoped package: `@username/gemini-search-mcp`

### Workflow Permissions Error

- Go to Settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"
- Enable "Allow GitHub Actions to create and approve pull requests"

## Post-Release

After successful publishing:

1. Verify packages are available:
   - PyPI: https://pypi.org/project/gemini-search-mcp/
   - npm: https://www.npmjs.com/package/gemini-search-mcp

2. Test installation:
   ```bash
   # Test PyPI
   pip install gemini-search-mcp
   
   # Test npm
   npm install -g gemini-search-mcp
   ```

3. Update documentation if needed

## CI/CD Pipeline

The repository includes two workflows:

### 1. CI Tests (`ci.yml`)
Runs on every push and pull request:
- Tests Python package on multiple Python versions (3.9-3.12)
- Tests Node wrapper on multiple Node versions (18, 20, 22)
- Tests on Ubuntu, macOS, and Windows
- Runs linting and formatting checks
- Tests MCP protocol compatibility

### 2. Publish (`publish.yml`)
Runs on release or manual trigger:
- Validates version format
- Builds and publishes to PyPI
- Builds and publishes to npm
- Creates GitHub release (if manual)

## Security Notes

- Never commit API tokens or secrets to the repository
- Use GitHub Secrets for sensitive data
- Consider using trusted publishing for PyPI (more secure)
- Review the `.gitignore` file to ensure credentials aren't tracked

## Support

For issues with the publishing process:
1. Check GitHub Actions logs
2. Review this guide
3. Open an issue on GitHub
