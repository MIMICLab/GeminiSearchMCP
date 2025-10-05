# 계정 설정 가이드

PyPI와 npm에 패키지를 배포하려면 각 플랫폼에 계정을 만들고 GitHub에 인증 정보를 설정해야 합니다.

## 1. PyPI 계정 설정

### 1.1 계정 생성
1. [PyPI](https://pypi.org/)에 접속
2. "Register" 클릭하여 계정 생성
3. 이메일 인증 완료

### 1.2 인증 설정 (두 가지 방법 중 선택)

#### 옵션 A: Trusted Publishing (권장, 더 안전함)

**장점**:
- API 토큰을 GitHub에 저장하지 않아도 됨
- GitHub Actions와 PyPI 간 자동 인증
- 보안이 더 강력함

**설정 방법**:
1. PyPI에 로그인
2. Account settings → Publishing으로 이동
3. "Add a new pending publisher" 클릭
4. 다음 정보 입력:
   ```
   PyPI Project Name: gemini-search-mcp
   Owner: YOUR_GITHUB_USERNAME
   Repository name: GeminiSearchMCP
   Workflow name: publish.yml
   Environment name: release
   ```
5. "Add" 클릭

**주의**: 첫 배포 전에는 프로젝트가 존재하지 않으므로 "pending publisher"로 등록해야 합니다.

#### 옵션 B: API Token

**장점**:
- 설정이 더 간단함
- 로컬에서도 수동 배포 가능

**설정 방법**:
1. PyPI에 로그인
2. Account settings → API tokens으로 이동
3. "Add API token" 클릭
4. Token name 입력: `gemini-search-mcp-github-actions`
5. Scope: "Entire account" 선택 (첫 배포용) 또는 프로젝트 지정
6. "Add token" 클릭
7. **토큰을 즉시 복사** (다시 볼 수 없습니다!)
8. GitHub 저장소 → Settings → Secrets and variables → Actions
9. "New repository secret" 클릭
10. Name: `PYPI_API_TOKEN`
11. Value: 복사한 토큰 붙여넣기
12. "Add secret" 클릭

**Trusted Publishing vs API Token 비교**:

| 항목 | Trusted Publishing | API Token |
|------|-------------------|-----------|
| 보안 | ⭐⭐⭐⭐⭐ 매우 안전 | ⭐⭐⭐ 안전 |
| 설정 복잡도 | 중간 | 쉬움 |
| GitHub에 시크릿 저장 | ❌ 불필요 | ✅ 필요 |
| 로컬 배포 | ❌ 불가능 | ✅ 가능 |
| 권장 여부 | ✅ 권장 | ⚠️ 대안 |

## 2. npm 계정 설정

### 2.1 계정 생성
1. [npm](https://www.npmjs.com/)에 접속
2. "Sign Up" 클릭하여 계정 생성
3. 이메일 인증 완료

### 2.2 패키지 이름 확인
1. npm에 로그인 후 [https://www.npmjs.com/package/gemini-search-mcp](https://www.npmjs.com/package/gemini-search-mcp) 접속
2. 이름이 사용 가능한지 확인
3. 만약 이미 사용 중이라면:
   - `package.json`의 `name`을 변경: `@MIMICLab/gemini-search-mcp`
   - Scoped package 사용 (예: `@tgisaturday/gemini-search-mcp`)

### 2.3 Access Token 생성
1. npm에 로그인
2. 프로필 아이콘 → "Access Tokens" 클릭
3. "Generate New Token" → "Classic Token" 선택
4. Token 타입: **Automation** 선택 (중요!)
5. Token name 입력: `gemini-search-mcp-github-actions`
6. "Generate Token" 클릭
7. **토큰을 즉시 복사** (다시 볼 수 없습니다!)
8. GitHub 저장소 → Settings → Secrets and variables → Actions
9. "New repository secret" 클릭
10. Name: `NPM_TOKEN`
11. Value: 복사한 토큰 붙여넣기
12. "Add secret" 클릭

**Token 타입 설명**:
- **Automation**: CI/CD용 (GitHub Actions에서 사용)
- **Publish**: 수동 배포용
- **Read-only**: 읽기 전용

## 3. GitHub 저장소 설정

### 3.1 저장소 생성
1. GitHub에서 새 저장소 생성
2. 이름: `GeminiSearchMCP` (또는 원하는 이름)
3. Public 또는 Private 선택
4. README, .gitignore 등은 추가하지 않음 (이미 로컬에 있음)

### 3.2 로컬 코드 푸시
```bash
cd /Users/taehoon.kim/Desktop/Sources/GeminiSearchMCP

# MIMICLab을 실제 GitHub 사용자명으로 변경
git remote add origin https://github.com/MIMICLab/GeminiSearchMCP.git

# 또는 SSH 사용
# git remote add origin git@github.com:MIMICLab/GeminiSearchMCP.git

git add .
git commit -m "Initial commit with CI/CD setup"
git branch -M main
git push -u origin main
```

### 3.3 GitHub Environment 설정
1. 저장소 → Settings → Environments
2. "New environment" 클릭
3. Name: `release`
4. "Configure environment" 클릭
5. (선택사항) Protection rules 추가:
   - Required reviewers: 배포 전 승인 필요
   - Wait timer: 배포 전 대기 시간
   - Deployment branches: main 브랜치만 배포 가능

### 3.4 GitHub Actions 권한 설정
1. 저장소 → Settings → Actions → General
2. "Workflow permissions" 섹션:
   - "Read and write permissions" 선택
   - "Allow GitHub Actions to create and approve pull requests" 체크
3. "Save" 클릭

## 4. 설정 확인 체크리스트

배포 전에 다음 사항을 확인하세요:

### PyPI
- [ ] PyPI 계정 생성 완료
- [ ] Trusted Publishing 설정 완료 또는 API Token 생성 완료
- [ ] GitHub Secrets에 `PYPI_API_TOKEN` 추가 (API Token 사용 시)

### npm
- [ ] npm 계정 생성 완료
- [ ] 패키지 이름 사용 가능 확인
- [ ] Access Token (Automation 타입) 생성 완료
- [ ] GitHub Secrets에 `NPM_TOKEN` 추가

### GitHub
- [ ] 저장소 생성 완료
- [ ] 코드 푸시 완료
- [ ] Environment `release` 생성 완료
- [ ] Workflow permissions 설정 완료

### 파일 업데이트
- [ ] 모든 파일의 `MIMICLab`을 실제 사용자명으로 변경
- [ ] `package.json`의 repository URL 업데이트
- [ ] `pyproject.toml`의 URL 업데이트
- [ ] README.md의 배지 URL 업데이트

## 5. 테스트 배포

### 5.1 로컬 빌드 테스트
```bash
# Python 패키지 빌드
python -m build
twine check dist/*

# npm 패키지 테스트
npm pack
```

### 5.2 첫 번째 배포
1. 버전 확인:
   - `pyproject.toml`: `version = "0.1.0"`
   - `package.json`: `"version": "0.1.0"`

2. GitHub에서 릴리스 생성:
   - Releases → "Create a new release"
   - Tag: `v0.1.0`
   - Title: `Release v0.1.0`
   - Description: 릴리스 노트 작성
   - "Publish release" 클릭

3. GitHub Actions 확인:
   - Actions 탭에서 워크플로우 실행 상태 확인
   - 에러 발생 시 로그 확인

4. 배포 확인:
   - PyPI: https://pypi.org/project/gemini-search-mcp/
   - npm: https://www.npmjs.com/package/gemini-search-mcp

## 6. 트러블슈팅

### PyPI 배포 실패

**문제**: `403 Forbidden` 에러
- **원인**: 패키지 이름이 이미 존재하거나 권한 없음
- **해결**: `pyproject.toml`의 `name`을 변경

**문제**: Trusted Publishing 실패
- **원인**: Pending publisher 설정 오류
- **해결**: PyPI에서 설정 재확인 (Owner, Repository, Workflow 이름)

### npm 배포 실패

**문제**: `404 Not Found` 또는 `403 Forbidden`
- **원인**: 패키지 이름이 이미 사용 중
- **해결**: Scoped package 사용 (`@username/package-name`)

**문제**: `ENEEDAUTH` 에러
- **원인**: Access Token이 잘못되었거나 만료됨
- **해결**: 새 토큰 생성 후 GitHub Secrets 업데이트

### GitHub Actions 실패

**문제**: `GITHUB_TOKEN` 권한 에러
- **원인**: Workflow permissions 설정 필요
- **해결**: Settings → Actions → General에서 권한 부여

**문제**: Environment `release`를 찾을 수 없음
- **원인**: Environment 미생성
- **해결**: Settings → Environments에서 `release` 생성

## 7. 보안 권장사항

### API 토큰 관리
- ✅ GitHub Secrets에만 저장
- ❌ 절대 코드에 하드코딩하지 말 것
- ❌ 로그에 출력하지 말 것
- ✅ 정기적으로 토큰 교체

### 2FA (Two-Factor Authentication)
- PyPI와 npm 계정에 2FA 활성화 권장
- GitHub에도 2FA 활성화 권장

### Scoped Packages
- npm에서는 scoped package 사용 권장 (`@username/package`)
- 이름 충돌 방지 및 소유권 명확화

## 8. 다음 단계

설정이 완료되면:
1. 첫 번째 릴리스 생성 (v0.1.0)
2. 배포 성공 확인
3. 설치 테스트:
   ```bash
   pip install gemini-search-mcp
   npm install -g gemini-search-mcp
   ```
4. 사용자 피드백 수집
5. 버전 업데이트 계획

## 도움이 필요하시면

- PyPI Help: https://pypi.org/help/
- npm Support: https://docs.npmjs.com/
- GitHub Actions: https://docs.github.com/en/actions
