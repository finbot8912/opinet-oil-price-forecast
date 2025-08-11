#!/bin/bash

# 오피넷 유가 예측 시스템 - GitHub Pages 배포 스크립트

echo "🚗 오피넷 유가 예측 시스템 배포 시작..."

# Git 상태 확인
if ! command -v git &> /dev/null; then
    echo "❌ Git이 설치되지 않았습니다."
    exit 1
fi

# 현재 디렉토리가 Git 리포지토리인지 확인
if [ ! -d ".git" ]; then
    echo "📦 Git 리포지토리 초기화 중..."
    git init
fi

# 스테이징 및 커밋
echo "📝 변경사항을 스테이징 중..."
git add .

# 커밋 메시지 생성
COMMIT_MESSAGE="Deploy Opinet Oil Price Forecasting System v3.0 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "💾 커밋 생성: $COMMIT_MESSAGE"
git commit -m "$COMMIT_MESSAGE"

# 원격 리포지토리가 설정되어 있는지 확인
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "⚠️  원격 리포지토리가 설정되지 않았습니다."
    echo "다음 명령어를 실행하여 원격 리포지토리를 설정하세요:"
    echo "git remote add origin https://github.com/finbot8912/opinet-oil-price-forecast.git"
    exit 1
fi

# 메인 브랜치로 푸시
echo "🚀 GitHub에 푸시 중..."
git branch -M main
git push -u origin main

echo ""
echo "✅ 배포 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. GitHub 리포지토리 Settings → Pages 이동"
echo "2. Source: 'Deploy from a branch' 선택"
echo "3. Branch: 'main' 선택, '/ (root)' 선택"
echo "4. Save 클릭"
echo ""
echo "🌐 배포 URL (1-10분 후 접속 가능):"
echo "https://finbot8912.github.io/opinet-oil-price-forecast"
echo ""
echo "🎯 GPS 기능을 위해 HTTPS 접속이 필요합니다."
echo "GitHub Pages는 자동으로 HTTPS를 제공합니다."