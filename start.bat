@echo off
chcp 65001 >nul 2>&1
title 기업 리서치 크롤러

echo ============================================
echo   기업 리서치 크롤러 - 웹 서버 시작
echo ============================================
echo.

:: Python 확인
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo        https://www.python.org/downloads/ 에서 설치해주세요.
    echo        설치 시 "Add Python to PATH" 체크를 꼭 해주세요.
    pause
    exit /b 1
)

:: Python 버전 확인
python --version 2>&1 | findstr /R "3\.[89]\. 3\.1[0-9]\." >nul
if %errorlevel% neq 0 (
    echo [경고] Python 3.8 이상이 필요합니다.
    python --version
    echo.
)

:: 가상환경 확인 및 생성
if not exist "venv" (
    echo [설정] 가상환경 생성 중...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo [설정] 가상환경 생성 완료
    echo.
)

:: 가상환경 활성화
call venv\Scripts\activate.bat

:: 패키지 설치
echo [설정] 패키지 확인 중...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [오류] 패키지 설치 실패
    pause
    exit /b 1
)
echo [설정] 패키지 준비 완료
echo.

:: 서버 시작
echo ============================================
echo   서버가 시작됩니다.
echo   브라우저에서 http://localhost:5000 접속
echo   종료: Ctrl+C
echo ============================================
echo.

python app.py

pause
