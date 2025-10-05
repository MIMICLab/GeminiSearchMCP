#!/bin/bash
# PyPI와 npm에 패키지를 배포하는 스크립트

set -e  # 에러 발생 시 즉시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 에러 메시지 출력
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
}

# 함수: 성공 메시지 출력
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 경고 메시지 출력
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 함수: 정보 메시지 출력
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 함수: 사용자 확인
confirm() {
    read -p "$(echo -e ${YELLOW}$1${NC}) [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║          Gemini Search MCP - 배포 스크립트                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo

# 1. 버전 확인
info "현재 버전 확인 중..."
PYTHON_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
NPM_VERSION=$(grep '"version":' package.json | head -1 | sed 's/.*"version": "\(.*\)".*/\1/')

echo "  Python (pyproject.toml): $PYTHON_VERSION"
echo "  npm (package.json): $NPM_VERSION"
echo

if [ "$PYTHON_VERSION" != "$NPM_VERSION" ]; then
    error "버전이 일치하지 않습니다!"
    echo "  pyproject.toml과 package.json의 버전을 동일하게 맞춰주세요."
    exit 1
fi

VERSION=$PYTHON_VERSION
success "버전 확인 완료: v$VERSION"
echo

# 2. Git 상태 확인
info "Git 상태 확인 중..."
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    warning "커밋되지 않은 변경사항이 있습니다."
    if ! confirm "계속하시겠습니까?"; then
        exit 1
    fi
fi
success "Git 상태 확인 완료"
echo

# 3. 의존성 확인
info "필수 도구 확인 중..."
MISSING_TOOLS=()

if ! command -v python3 &> /dev/null; then
    MISSING_TOOLS+=("python3")
fi

if ! command -v node &> /dev/null; then
    MISSING_TOOLS+=("node")
fi

if ! command -v npm &> /dev/null; then
    MISSING_TOOLS+=("npm")
fi

if ! python3 -m pip show build &> /dev/null; then
    MISSING_TOOLS+=("python-build (pip install build)")
fi

if ! python3 -m pip show twine &> /dev/null; then
    MISSING_TOOLS+=("twine (pip install twine)")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    error "다음 도구가 필요합니다:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "  - $tool"
    done
    exit 1
fi
success "필수 도구 확인 완료"
echo

# 4. 이전 빌드 정리
info "이전 빌드 파일 정리 중..."
rm -rf dist/ build/ *.egg-info/
success "정리 완료"
echo

# 5. Python 패키지 빌드
info "Python 패키지 빌드 중..."
if python3 -m build; then
    success "Python 패키지 빌드 완료"
else
    error "Python 패키지 빌드 실패"
    exit 1
fi
echo

# 6. Python 패키지 검증
info "Python 패키지 검증 중..."
if python3 -m twine check dist/*; then
    success "Python 패키지 검증 완료"
else
    error "Python 패키지 검증 실패"
    exit 1
fi
echo

# 7. npm 패키지 테스트
info "npm 패키지 테스트 중..."
if node bin/gemini-search-mcp.js --help > /dev/null 2>&1; then
    success "npm 패키지 테스트 완료"
else
    error "npm 패키지 테스트 실패"
    exit 1
fi
echo

# 8. 빌드 결과 표시
info "빌드된 파일:"
ls -lh dist/
echo

# 9. 배포 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
warning "다음 버전을 배포합니다: v$VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

if ! confirm "PyPI와 npm에 배포하시겠습니까?"; then
    warning "배포가 취소되었습니다."
    exit 0
fi
echo

# 10. PyPI 배포
info "PyPI에 배포 중..."
echo "  (PyPI 계정 정보를 입력해주세요)"
if python3 -m twine upload dist/*; then
    success "PyPI 배포 완료!"
    echo "  https://pypi.org/project/gemini-search-mcp/$VERSION/"
else
    error "PyPI 배포 실패"
    echo
    warning "npm 배포를 계속하시겠습니까?"
    if ! confirm "계속하시겠습니까?"; then
        exit 1
    fi
fi
echo

# 11. npm 배포
info "npm에 배포 중..."
echo "  (npm 로그인이 필요합니다)"

# npm 로그인 확인
if ! npm whoami &> /dev/null; then
    warning "npm에 로그인되어 있지 않습니다."
    info "npm login을 실행합니다..."
    npm login
fi

if npm publish --access public; then
    success "npm 배포 완료!"
    echo "  https://www.npmjs.com/package/gemini-search-mcp/v/$VERSION"
else
    error "npm 배포 실패"
    exit 1
fi
echo

# 12. Git 태그 생성
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if confirm "Git 태그 v$VERSION을 생성하고 푸시하시겠습니까?"; then
    if git tag -a "v$VERSION" -m "Release v$VERSION"; then
        success "태그 생성 완료: v$VERSION"
        
        if confirm "태그를 원격 저장소에 푸시하시겠습니까?"; then
            git push origin "v$VERSION"
            success "태그 푸시 완료"
        fi
    else
        warning "태그가 이미 존재하거나 생성에 실패했습니다."
    fi
fi
echo

# 13. 완료 메시지
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    🎉 배포 완료!                                    ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo
success "gemini-search-mcp v$VERSION 배포 성공!"
echo
info "설치 명령어:"
echo "  pip install gemini-search-mcp==$VERSION"
echo "  npm install -g gemini-search-mcp@$VERSION"
echo
info "다음 단계:"
echo "  1. GitHub에서 릴리스 노트 작성"
echo "  2. CHANGELOG.md 업데이트"
echo "  3. 다음 버전 계획"
echo
