#!/bin/bash
# GitHub 릴리스 노트를 생성하는 스크립트

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 현재 버전 확인
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                    GitHub 릴리스 노트 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
info "버전: v$VERSION"
echo

# CHANGELOG에서 해당 버전의 변경사항 추출
if grep -q "\[$VERSION\]" CHANGELOG.md; then
    info "CHANGELOG.md에서 변경사항을 추출합니다..."
    
    # 임시 파일에 릴리스 노트 작성
    RELEASE_FILE=".github/RELEASE_v${VERSION}.md"
    
    cat > "$RELEASE_FILE" << EOF
# Release v$VERSION

🎉 **Gemini Search MCP v$VERSION**

## 📦 Installation

\`\`\`bash
# Python
pip install gemini-search-mcp==$VERSION

# Node.js
npm install -g gemini-search-mcp@$VERSION
\`\`\`

## 📝 What's Changed

EOF
    
    # CHANGELOG에서 변경사항 추출
    awk "/^## \[$VERSION\]/,/^## \[/" CHANGELOG.md | \
        grep -v "^## \[$VERSION\]" | \
        grep -v "^## \[" | \
        head -n -1 >> "$RELEASE_FILE"
    
    # 링크 추가
    cat >> "$RELEASE_FILE" << EOF

## 📚 Documentation

- [Quick Start Guide](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/QUICKSTART.md)
- [Full Changelog](https://github.com/MIMICLab/GeminiSearchMCP/blob/main/CHANGELOG.md)

## 🔗 Links

- **PyPI**: https://pypi.org/project/gemini-search-mcp/$VERSION/
- **npm**: https://www.npmjs.com/package/gemini-search-mcp/v/$VERSION

---

**Full Changelog**: https://github.com/MIMICLab/GeminiSearchMCP/compare/v0.0.0...v$VERSION
EOF
    
    success "릴리스 노트가 생성되었습니다: $RELEASE_FILE"
    echo
    info "다음 단계:"
    echo "  1. $RELEASE_FILE 파일을 검토하고 필요시 수정"
    echo "  2. GitHub에서 릴리스 생성:"
    echo "     - Releases → New Release"
    echo "     - Tag: v$VERSION"
    echo "     - Title: Release v$VERSION"
    echo "     - Description: $RELEASE_FILE 내용 복사"
    echo "  3. 또는 GitHub CLI 사용:"
    echo "     gh release create v$VERSION --title \"Release v$VERSION\" --notes-file $RELEASE_FILE"
    echo
else
    warning "CHANGELOG.md에 v$VERSION 항목이 없습니다."
    echo
    info "다음을 수행하세요:"
    echo "  1. CHANGELOG.md에 v$VERSION 변경사항 추가"
    echo "  2. 이 스크립트 다시 실행"
    echo
    exit 1
fi
