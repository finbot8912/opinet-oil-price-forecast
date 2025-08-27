# 오피넷 유가예측 시스템

Github 주소 : https://github.com/finbot8912/opinet-oil-price-forecast

## 프로젝트 설정 가이드

### Git 관리
- .git 이 존재하지 않으면 Git 저장소 초기화할것 ( git init )
- 파일 생성 또는 수정 시, 파일 생성 또는 수정한 후, git add와 commit 수행할 것
- 파일 삭제시 git rm 및 commit 사용 할것

### 원격 저장소 푸시 시 주의사항
- HTTP 버퍼 크기를 늘리고 조금씩 나누어 푸시할 것
- 에러 시 작은 변경사항만 포함하는 새 커밋을 만들어 푸시할 것

## 프로젝트 구조

### 주요 파일
- `index.html` - 메인 웹 인터페이스
- `opinet_historical_data.json` - 오피넷 유가 데이터
- `frontend/` - React 기반 프론트엔드

### Python 스크립트
- `calculate_forecast_accuracy.py` - 예측 정확도 계산
- `generate_7day_regional_forecast.py` - 7일 예측 생성
- `opinet_data_analysis.py` - 데이터 분석

### 데이터 파일
- `7day_regional_forecast.json` - 7일 예측 결과
- `forecast_accuracy_report.json` - 정확도 보고서
- `regional_accuracy_data.json` - 지역별 정확도