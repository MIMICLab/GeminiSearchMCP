# 배포 스크립트

이 디렉토리에는 PyPI와 npm에 수동으로 배포하기 위한 스크립트들이 있습니다.

## 사용 방법

### 1. 버전 업데이트

```bash
./scripts/bump-version.sh
```

새 버전 번호를 입력하면 `pyproject.toml`과 `package.json`의 버전을 자동으로 업데이트합니다.

### 2. 빌드 테스트

```bash
./scripts/test-build.sh
```

배포 전 모든 체크리스트를 확인하고 패키지를 빌드하여 테스트합니다:
- 버전 일치 확인
- 필수 파일 존재 확인
- Git 상태 확인
- 빌드 도구 확인
- Python 패키지 빌드 및 검증
- Node.js 래퍼 테스트
- 로컬 설치 테스트
- CHANGELOG 업데이트 확인
- 계정 로그인 상태 확인

### 3. 릴리스 노트 생성

```bash
./scripts/create-release-notes.sh
```

CHANGELOG.md의 내용을 기반으로 GitHub 릴리스 노트를 자동 생성합니다.
생성된 파일(`.github/RELEASE_vX.Y.Z.md`)을 GitHub 릴리스 페이지에 복사하여 사용합니다.

### 4. 배포

```bash
./scripts/publish.sh
```

PyPI와 npm에 패키지를 배포합니다. 이 스크립트는:
- 버전을 확인하고
- 패키지를 빌드하고
- 검증을 수행한 후
- PyPI와 npm에 배포합니다
- 선택적으로 Git 태그를 생성합니다

## 배포 전 준비사항

### PyPI 계정
1. [PyPI](https://pypi.org/)에서 계정 생성
2. 배포 시 계정 정보 입력 필요

### npm 계정
1. [npm](https://www.npmjs.com/)에서 계정 생성
2. 로그인:
   ```bash
   npm login
   ```

## 전체 배포 프로세스

```bash
# 1. 버전 업데이트
./scripts/bump-version.sh

# 2. CHANGELOG.md 수동 업데이트

# 3. 변경사항 커밋
git add .
git commit -m "Bump version to X.Y.Z"

# 4. 빌드 테스트
./scripts/test-build.sh

# 5. 릴리스 노트 생성
./scripts/create-release-notes.sh

# 6. 배포 (모든 테스트 통과 시)
./scripts/publish.sh

# 7. GitHub에 푸시
git push origin main
git push origin vX.Y.Z  # 태그 푸시

# 8. GitHub 릴리스 생성
# 옵션 1: GitHub 웹에서
#   - Releases → New Release
#   - Tag: vX.Y.Z 선택
#   - .github/RELEASE_vX.Y.Z.md 내용 복사
#
# 옵션 2: GitHub CLI 사용
#   gh release create vX.Y.Z --title "Release vX.Y.Z" --notes-file .github/RELEASE_vX.Y.Z.md
```

## 필수 도구

이 스크립트들을 실행하려면 다음 도구들이 필요합니다:

- Python 3.9+
- Node.js 18+
- npm
- `pip install build twine`

## 트러블슈팅

### PyPI 배포 실패
- 패키지 이름이 이미 사용 중인 경우 `pyproject.toml`의 `name` 변경
- 같은 버전을 다시 배포할 수 없음 (버전 증가 필요)

### npm 배포 실패
- `npm login`으로 로그인 확인
- 패키지 이름 충돌 시 scoped package 사용: `@username/package-name`

### 권한 에러
- 스크립트 실행 권한 확인: `chmod +x scripts/*.sh`

## 참고 문서

- [SETUP_ACCOUNTS.md](../SETUP_ACCOUNTS.md) - 계정 설정 상세 가이드
- [PUBLISHING.md](../PUBLISHING.md) - 배포 가이드
- [CHANGELOG.md](../CHANGELOG.md) - 버전 히스토리
