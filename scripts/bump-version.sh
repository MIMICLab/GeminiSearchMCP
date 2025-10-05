#!/bin/bash
# 버전 업데이트 스크립트

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# 현재 버전 확인
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                       버전 업데이트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
info "현재 버전: $CURRENT_VERSION"
echo

# 새 버전 입력
read -p "새 버전 입력 (예: 0.2.0): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo "버전이 입력되지 않았습니다."
    exit 1
fi

# 버전 형식 검증
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
    echo "❌ 잘못된 버전 형식입니다. (예: 0.2.0, 1.0.0-beta.1)"
    exit 1
fi

echo
info "다음 파일들의 버전을 업데이트합니다:"
echo "  - pyproject.toml"
echo "  - package.json"
echo

read -p "계속하시겠습니까? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# pyproject.toml 업데이트
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi
success "pyproject.toml 업데이트 완료"

# package.json 업데이트
npm version "$NEW_VERSION" --no-git-tag-version > /dev/null
success "package.json 업데이트 완료"

echo
success "버전이 $CURRENT_VERSION → $NEW_VERSION 로 업데이트되었습니다!"
echo
info "다음 단계:"
echo "  1. CHANGELOG.md 업데이트"
echo "  2. 변경사항 커밋: git commit -am 'Bump version to $NEW_VERSION'"
echo "  3. 빌드 테스트: ./scripts/test-build.sh"
echo "  4. 배포: ./scripts/publish.sh"
echo
