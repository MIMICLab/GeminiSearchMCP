#!/bin/bash
# 배포 전 체크리스트 및 빌드 테스트 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}" >&2; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║              배포 전 체크리스트 & 빌드 테스트                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo

ERRORS=0
WARNINGS=0

# 1. 버전 확인
info "1. 버전 일치 확인"
PYTHON_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
NPM_VERSION=$(grep '"version":' package.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')

echo "   Python: $PYTHON_VERSION"
echo "   npm:    $NPM_VERSION"

if [ "$PYTHON_VERSION" = "$NPM_VERSION" ]; then
    success "버전이 일치합니다: v$PYTHON_VERSION"
else
    error "버전이 일치하지 않습니다!"
    ((ERRORS++))
fi
echo

# 2. 필수 파일 확인
info "2. 필수 파일 존재 확인"
REQUIRED_FILES=(
    "README.md"
    "LICENSE"
    "pyproject.toml"
    "package.json"
    "bin/gemini-search-mcp.js"
    "gemini_search_mcp/__init__.py"
    "gemini_search_mcp/cli.py"
    "gemini_search_mcp/server.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        error "$file 파일이 없습니다!"
        ((ERRORS++))
    fi
done
success "필수 파일 확인 완료"
echo

# 3. Git 상태 확인
info "3. Git 상태 확인"
if git diff-index --quiet HEAD -- 2>/dev/null; then
    success "모든 변경사항이 커밋되었습니다"
else
    warning "커밋되지 않은 변경사항이 있습니다"
    git status --short
    ((WARNINGS++))
fi
echo

# 4. 의존성 확인
info "4. 빌드 도구 확인"
TOOLS_OK=true

if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version)
    echo "   ✓ $PYTHON_VER"
else
    error "python3가 설치되지 않았습니다"
    TOOLS_OK=false
fi

if command -v node &> /dev/null; then
    NODE_VER=$(node --version)
    echo "   ✓ Node.js $NODE_VER"
else
    error "Node.js가 설치되지 않았습니다"
    TOOLS_OK=false
fi

if command -v npm &> /dev/null; then
    NPM_VER=$(npm --version)
    echo "   ✓ npm $NPM_VER"
else
    error "npm이 설치되지 않았습니다"
    TOOLS_OK=false
fi

if python3 -m pip show build &> /dev/null; then
    echo "   ✓ python build"
else
    error "python build 모듈이 없습니다 (pip install build)"
    TOOLS_OK=false
fi

if python3 -m pip show twine &> /dev/null; then
    echo "   ✓ twine"
else
    error "twine이 설치되지 않았습니다 (pip install twine)"
    TOOLS_OK=false
fi

if $TOOLS_OK; then
    success "모든 도구가 설치되어 있습니다"
else
    ((ERRORS++))
fi
echo

# 5. Python 패키지 빌드 테스트
info "5. Python 패키지 빌드 테스트"
rm -rf dist/ build/ *.egg-info/

if python3 -m build > /tmp/build.log 2>&1; then
    success "빌드 성공"
    ls -lh dist/
else
    error "빌드 실패"
    cat /tmp/build.log
    ((ERRORS++))
fi
echo

# 6. Python 패키지 검증
if [ -d "dist" ]; then
    info "6. Python 패키지 검증"
    if python3 -m twine check dist/* > /tmp/twine.log 2>&1; then
        success "패키지 검증 통과"
    else
        error "패키지 검증 실패"
        cat /tmp/twine.log
        ((ERRORS++))
    fi
    echo
fi

# 7. Node 래퍼 테스트
info "7. Node.js 래퍼 테스트"
if node bin/gemini-search-mcp.js --help > /dev/null 2>&1; then
    success "Node.js 래퍼 작동 확인"
else
    error "Node.js 래퍼 테스트 실패"
    ((ERRORS++))
fi
echo

# 8. 설치 테스트
info "8. 로컬 설치 테스트"
if pip install -e . > /tmp/install.log 2>&1; then
    success "로컬 설치 성공"
    
    if gemini-search-mcp --help > /dev/null 2>&1; then
        success "CLI 실행 확인"
    else
        error "CLI 실행 실패"
        ((ERRORS++))
    fi
else
    error "로컬 설치 실패"
    cat /tmp/install.log
    ((ERRORS++))
fi
echo

# 9. CHANGELOG 확인
info "9. CHANGELOG.md 업데이트 확인"
if grep -q "\[$PYTHON_VERSION\]" CHANGELOG.md 2>/dev/null; then
    success "CHANGELOG에 v$PYTHON_VERSION 항목이 있습니다"
else
    warning "CHANGELOG.md에 v$PYTHON_VERSION를 추가하는 것을 권장합니다"
    ((WARNINGS++))
fi
echo

# 10. PyPI/npm 계정 확인
info "10. 배포 계정 확인"

# npm 로그인 확인
if npm whoami &> /dev/null; then
    NPM_USER=$(npm whoami)
    success "npm에 로그인되어 있습니다 (사용자: $NPM_USER)"
else
    warning "npm에 로그인되어 있지 않습니다 (npm login 필요)"
    ((WARNINGS++))
fi

# PyPI는 배포 시 인증이 필요하므로 여기서는 확인하지 않음
info "PyPI 계정은 배포 시 확인됩니다"
echo

# 결과 요약
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                           결과 요약"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    success "모든 검사를 통과했습니다! 배포 준비 완료 🎉"
    echo
    info "배포 명령어:"
    echo "  ./scripts/publish.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    warning "$WARNINGS개의 경고가 있습니다"
    echo
    info "배포는 가능하지만 경고 사항을 확인하세요"
    echo "  ./scripts/publish.sh"
    exit 0
else
    error "$ERRORS개의 에러와 $WARNINGS개의 경고가 있습니다"
    echo
    error "에러를 수정한 후 다시 시도하세요"
    exit 1
fi
