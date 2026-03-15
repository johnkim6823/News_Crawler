# 기업 리서치 크롤러

취업 준비용 기업/직무 정보를 자동으로 수집하는 웹 애플리케이션입니다.
회사명과 직무명만 입력하면 Google, 네이버 뉴스, 네이버 블로그에서 관련 정보를 크롤링하여 체계적인 리포트를 생성합니다.

> **웹 UI** + **CLI** 두 가지 방식 모두 지원합니다.

---

## 목차

- [주요 기능](#주요-기능)
- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
  - [Windows](#windows)
  - [Ubuntu / Linux](#ubuntu--linux)
- [실행 방법](#실행-방법)
  - [웹 UI (권장)](#웹-ui-권장)
  - [CLI (터미널)](#cli-터미널)
- [웹 UI 사용 가이드](#웹-ui-사용-가이드)
- [수집 항목 상세](#수집-항목-상세)
- [출력 파일](#출력-파일)
- [문제 해결](#문제-해결)
- [라이선스](#라이선스)

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **회사 전반 정보** | 회사 개요, 사업영역, 비전, 핵심가치 |
| **최신 뉴스** | 최근 1주일 뉴스를 최신순으로 수집 (날짜 필터링) |
| **기업문화/복지** | 근무환경, 복지, 워라밸 블로그 후기 |
| **재무 실적** | 매출, 영업이익 등 최신 재무 정보 |
| **산업 동향** | 경쟁사, 시장 점유율, 산업 전망 |
| **최근 이슈** | 신사업, 투자, MOU, 프로젝트 (최근 1개월) |
| **직무 상세 정보** | 업무내용, 기술스택, 필요 역량 |
| **채용 공고** | 자격요건, 우대사항, 최신 공고 |
| **면접 후기** | 면접 질문, 면접 경험담 |
| **연봉/복지** | 연봉 수준, 처우, 워라밸 현직자 후기 |
| **채용공고 바로가기** | 사람인, 잡코리아, 원티드, 링크드인 직접 링크 |

### 웹 UI 추가 기능

- 실시간 크롤링 진행률 표시 (단계 수, 예상 시간)
- 크롤링 중 취소 기능
- 결과 내 키워드 검색/필터링 (하이라이트)
- 리포트 클립보드 복사 / 인쇄
- Markdown, JSON 파일 다운로드
- 인기 기업/직무 빠른 선택 칩
- 리서치 기록 관리 (조회/삭제)
- 카테고리별 수집 현황 대시보드

---

## 시스템 요구사항

| 항목 | 요구사항 |
|------|---------|
| **Python** | 3.8 이상 |
| **OS** | Windows 10/11, Ubuntu 20.04+, macOS |
| **브라우저** | Chrome, Edge, Firefox, Safari (최신 버전) |
| **인터넷** | 필수 (Google, 네이버 크롤링) |

---

## 설치 방법

### Windows

#### 1단계: Python 설치

Python이 설치되어 있지 않다면 아래 링크에서 다운로드합니다.

https://www.python.org/downloads/

> **중요:** 설치 시 **"Add Python to PATH"** 체크박스를 반드시 체크하세요.

설치 확인:

```cmd
python --version
```

`Python 3.x.x`가 출력되면 성공입니다.

#### 2단계: 프로젝트 다운로드

```cmd
git clone https://github.com/johnkim6823/News_Crawler.git
cd News_Crawler
```

또는 GitHub에서 ZIP 파일을 다운로드하여 압축을 풀어주세요.

#### 3단계: 실행

**방법 A — 원클릭 실행 (권장)**

`start.bat` 파일을 더블클릭합니다.

- 자동으로 가상환경 생성
- 자동으로 패키지 설치
- 웹 서버 시작

**방법 B — 수동 실행**

```cmd
:: 가상환경 생성 (최초 1회)
python -m venv venv

:: 가상환경 활성화
venv\Scripts\activate

:: 패키지 설치 (최초 1회)
pip install -r requirements.txt

:: 웹 서버 실행
python app.py
```

---

### Ubuntu / Linux

#### 1단계: Python 및 필수 패키지 설치

Ubuntu 20.04에는 Python 3이 기본 설치되어 있습니다. `venv`와 `pip`만 추가합니다.

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

설치 확인:

```bash
python3 --version
```

`Python 3.x.x`가 출력되면 성공입니다.

#### 2단계: 프로젝트 다운로드

```bash
git clone https://github.com/johnkim6823/News_Crawler.git
cd News_Crawler
```

#### 3단계: 실행

**방법 A — 원클릭 실행 (권장)**

```bash
chmod +x start.sh
./start.sh
```

- 자동으로 가상환경 생성
- 자동으로 패키지 설치
- 웹 서버 시작

**방법 B — 수동 실행**

```bash
# 가상환경 생성 (최초 1회)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (최초 1회)
pip install -r requirements.txt

# 웹 서버 실행
python app.py
```

---

## 실행 방법

### 웹 UI (권장)

서버 실행 후 브라우저에서 접속합니다.

```
http://localhost:5000
```

| OS | 실행 명령 |
|----|----------|
| **Windows** | `start.bat` 더블클릭 또는 `python app.py` |
| **Linux** | `./start.sh` 또는 `python app.py` |

서버가 정상 실행되면 아래와 같이 표시됩니다:

```
 * Running on http://127.0.0.1:5000
```

종료: 터미널에서 `Ctrl + C`를 누릅니다.

### CLI (터미널)

웹 UI 없이 터미널에서 직접 사용할 수도 있습니다.

```bash
python crawler.py --company "회사명" --job "직무명"
```

#### CLI 옵션

| 옵션 | 필수 | 설명 | 예시 |
|------|------|------|------|
| `--company` | O | 회사명 | `삼성전자`, `카카오` |
| `--job` | O | 직무명 | `백엔드개발`, `AI엔지니어` |
| `--output` | X | 출력 디렉토리 (기본: `research_output/`) | `./results` |

#### CLI 예시

```bash
# 삼성전자 백엔드개발 리서치
python crawler.py --company "삼성전자" --job "백엔드개발"

# 카카오 AI엔지니어 리서치 (출력 디렉토리 지정)
python crawler.py --company "카카오" --job "AI엔지니어" --output ./results

# LG에너지솔루션 데이터분석 리서치
python crawler.py --company "LG에너지솔루션" --job "데이터분석"
```

---

## 웹 UI 사용 가이드

### 1. 리서치 시작

1. 브라우저에서 `http://localhost:5000` 접속
2. **회사명** 입력 (예: 삼성전자)
3. **직무명** 입력 (예: 백엔드개발)
4. **리서치 시작** 버튼 클릭

> **빠른 선택:** 상단의 추천 칩(삼성전자/백엔드, 카카오/AI 등)을 클릭하면 자동 입력됩니다.

### 2. 진행 상황 확인

- 실시간 로그가 표시됩니다
- 진행률 바와 단계 수(예: `23 / ~65 단계 (35%)`)를 확인할 수 있습니다
- 예상 남은 시간이 표시됩니다
- 취소가 필요하면 **취소** 버튼을 클릭합니다

> 전체 크롤링에는 약 3~5분이 소요됩니다.

### 3. 결과 확인

크롤링이 완료되면 결과가 자동으로 표시됩니다.

- **리포트 탭:** Markdown 리포트를 보기 좋게 렌더링
- **상세 데이터 탭:** 카테고리별로 접어서 볼 수 있는 원본 데이터
- **결과 내 검색:** 우측 상단 검색창에 키워드를 입력하면 실시간 필터링

### 4. 결과 내보내기

| 버튼 | 기능 |
|------|------|
| **복사** | 리포트 Markdown 텍스트를 클립보드에 복사 |
| **인쇄** | 리포트를 브라우저 인쇄 기능으로 출력 (PDF 저장 가능) |
| **MD** | Markdown 파일 다운로드 |
| **JSON** | JSON 원본 데이터 다운로드 |

### 5. 기록 관리

- 상단 **기록** 탭을 클릭하면 이전 리서치 결과를 볼 수 있습니다
- 기록을 클릭하면 결과를 다시 열어볼 수 있습니다
- 휴지통 아이콘으로 불필요한 기록을 삭제할 수 있습니다

---

## 수집 항목 상세

### Part 1 — 회사 전반 (6개 항목)

| 항목 | 검색 소스 | 설명 |
|------|----------|------|
| 회사 개요 | Google | 사업영역, 비전, 핵심가치, 주요사업 |
| 최근 뉴스 | 네이버 뉴스 | 최근 1주일, 최신순 정렬 |
| 기업문화 | 네이버 블로그 | 근무환경, 복지, 워라밸 후기 |
| 재무 실적 | Google | 매출, 영업이익, 재무 현황 |
| 산업 동향 | Google | 경쟁사, 시장 점유율, 산업 전망 |
| 최근 이슈 | Google + 네이버 뉴스 | 신사업, 투자, MOU (최근 1개월) |

### Part 2 — 직무 정보 (7개 항목)

| 항목 | 검색 소스 | 설명 |
|------|----------|------|
| 직무 소개 | Google | 업무내용, 하는 일, 역할 |
| 관련 뉴스 | 네이버 뉴스 | 직무 관련 최신 뉴스 (최근 1개월) |
| 채용 공고 | Google | 자격요건, 우대사항 |
| 기술스택 | Google | 필요 역량, 사용 툴 |
| 면접 후기 | 네이버 블로그 | 면접 질문, 면접 경험 |
| 연봉/복지 | 네이버 블로그 | 연봉, 처우, 워라밸 현직자 후기 |
| 공식 채용 페이지 | Google | 회사 채용 홈페이지 |

### Part 3 — 채용공고 바로가기

| 사이트 | 설명 |
|--------|------|
| 사람인 | saramin.co.kr 검색 결과 직접 링크 |
| 잡코리아 | jobkorea.co.kr 검색 결과 직접 링크 |
| 원티드 | wanted.co.kr 검색 결과 직접 링크 |
| 링크드인 | linkedin.com 채용 검색 직접 링크 |

---

## 출력 파일

크롤링이 완료되면 `research_output/` 디렉토리에 파일이 생성됩니다.

```
research_output/
├── 삼성전자_백엔드개발.json    ← 원본 데이터 (구조화된 JSON)
└── 삼성전자_백엔드개발.md      ← 리서치 리포트 (Markdown)
```

---

## 프로젝트 구조

```
News_Crawler/
├── app.py              ← 웹 서버 (Flask)
├── crawler.py           ← 크롤링 엔진 (CLI + 라이브러리)
├── requirements.txt     ← Python 패키지 목록
├── start.bat            ← Windows 원클릭 실행
├── start.sh             ← Linux/macOS 원클릭 실행
├── templates/
│   └── index.html       ← 웹 UI
├── research_output/     ← 크롤링 결과 저장 (자동 생성)
└── README.md
```

---

## 문제 해결

### Python이 인식되지 않음 (Windows)

```
'python'은(는) 내부 또는 외부 명령... 이 아닙니다.
```

**해결:** Python 설치 시 "Add Python to PATH" 옵션을 체크하지 않은 경우입니다.
- Python을 재설치하고 "Add Python to PATH"를 체크하세요.
- 또는 시스템 환경 변수 > Path에 Python 설치 경로를 수동 추가하세요.

### python3 명령을 찾을 수 없음 (Ubuntu)

```bash
sudo apt install python3 python3-pip python3-venv
```

### pip install 실패

```
error: externally-managed-environment
```

**해결:** 가상환경을 사용하세요 (start.sh / start.bat이 자동으로 처리합니다).

```bash
python3 -m venv venv
source venv/bin/activate   # Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 포트 5000이 이미 사용 중

```
OSError: [Errno 98] Address already in use
```

**해결:** 이미 실행 중인 서버를 종료하거나, 다른 포트를 지정합니다.

```bash
# Linux - 기존 프로세스 확인 및 종료
lsof -i :5000
kill -9 <PID>

# Windows - 기존 프로세스 확인 및 종료
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### 크롤링 결과가 적거나 비어있음

- Google/네이버가 크롤링을 차단했을 수 있습니다. 잠시 후 다시 시도하세요.
- 회사명이 정확한지 확인하세요 (예: "삼성" 대신 "삼성전자").
- 인터넷 연결을 확인하세요.

### Windows에서 한글이 깨짐

`start.bat`은 자동으로 UTF-8 인코딩을 설정합니다. 수동 실행 시:

```cmd
chcp 65001
python app.py
```

---

## 주의사항

- 크롤링 요청 간 **1.5초 딜레이**가 적용되어 전체 실행에 약 3~5분 소요됩니다.
- Google/네이버 검색 결과에 의존하므로 검색 결과가 변경되면 수집 내용도 달라집니다.
- 일부 사이트는 크롤링이 차단될 수 있으며, 이 경우 해당 항목은 건너뜁니다.
- 수집된 내용은 참고용이며, 정확한 정보는 공식 채용 사이트에서 직접 확인하세요.

---

## 라이선스

MIT License
