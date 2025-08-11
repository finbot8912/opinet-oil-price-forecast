@echo off
chcp 65001 >nul
echo 🚗 오피넷 유가 예측 시스템 배포 시작...
echo.

REM Git 상태 확인
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Git이 설치되지 않았습니다.
    echo Git을 설치한 후 다시 시도해주세요: https://git-scm.com/
    pause
    exit /b 1
)

REM 현재 디렉토리가 Git 리포지토리인지 확인
if not exist ".git" (
    echo 📦 Git 리포지토리 초기화 중...
    git init
)

REM 스테이징 및 커밋
echo 📝 변경사항을 스테이징 중...
git add .

REM 커밋 메시지 생성
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set mydate=%%c-%%a-%%b
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a:%%b
set COMMIT_MESSAGE=Deploy Opinet Oil Price Forecasting System v3.0 - %mydate% %mytime%

echo 💾 커밋 생성: %COMMIT_MESSAGE%
git commit -m "%COMMIT_MESSAGE%"

REM 원격 리포지토리가 설정되어 있는지 확인
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  원격 리포지토리가 설정되지 않았습니다.
    echo 다음 명령어를 실행하여 원격 리포지토리를 설정하세요:
    echo git remote add origin https://github.com/finbot8912/opinet-oil-price-forecast.git
    echo.
    pause
    exit /b 1
)

REM 메인 브랜치로 푸시
echo 🚀 GitHub에 푸시 중...
git branch -M main
git push -u origin main

echo.
echo ✅ 배포 완료!
echo.
echo 📋 다음 단계:
echo 1. GitHub 리포지토리 Settings → Pages 이동
echo 2. Source: 'Deploy from a branch' 선택
echo 3. Branch: 'main' 선택, '/ (root)' 선택
echo 4. Save 클릭
echo.
echo 🌐 배포 URL (1-10분 후 접속 가능):
echo https://finbot8912.github.io/opinet-oil-price-forecast
echo.
echo 🎯 GPS 기능을 위해 HTTPS 접속이 필요합니다.
echo GitHub Pages는 자동으로 HTTPS를 제공합니다.
echo.
pause