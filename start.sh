#!/usr/bin/env bash
set -e

echo "============================================"
echo "  기업 리서치 크롤러 - 웹 서버 시작"
echo "============================================"
echo ""

# Python 확인 (python3 우선, 없으면 python)
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "[오류] Python이 설치되어 있지 않습니다."
    echo "       sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Python 버전 확인
PY_VERSION=$($PYTHON --version 2>&1)
echo "[정보] $PY_VERSION"
echo ""

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "[설정] 가상환경 생성 중..."
    $PYTHON -m venv venv
    echo "[설정] 가상환경 생성 완료"
    echo ""
fi

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
echo "[설정] 패키지 확인 중..."
pip install -r requirements.txt -q
echo "[설정] 패키지 준비 완료"
echo ""

# 서버 시작
echo "============================================"
echo "  서버가 시작됩니다."
echo "  브라우저에서 http://localhost:5000 접속"
echo "  종료: Ctrl+C"
echo "============================================"
echo ""

python app.py
