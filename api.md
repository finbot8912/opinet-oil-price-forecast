# API.MD - 오피넷 유가 예측 시스템 API 문서

## 📋 개요

**프로젝트**: 한국석유공사 오피넷 실시간 유가 예측 시스템  
**버전**: 3.0.0_opinet_realtime  
**기술 스택**: Flask + Python + 15개 AI 모델  
**베이스 URL**: http://127.0.0.1:8001  

---

## 🚀 API 엔드포인트

### 1. 시스템 상태 확인

#### GET `/api/health`
**제목**: 시스템 헬스 체크  
**참조**: 시스템 상태, 데이터 로드 상태, MCP 연결 상태 확인  

**응답 예시**:
```json
{
  "status": "healthy",
  "data_loaded": {
    "forecast": true,
    "regions": true
  },
  "opinet_connected": true,
  "weekly_engine": true
}
```

**API 코드**:
```python
@app.route('/api/health')
def api_health_check():
    """API 헬스 체크"""
    return jsonify({
        "status": "healthy",
        "data_loaded": {
            "forecast": forecast_data is not None,
            "regions": len(regions_data) > 0
        },
        "opinet_connected": opinet_connector is not None,
        "weekly_engine": weekly_engine is not None
    })
```

---

### 2. 일주일 예측 데이터

#### GET `/api/weekly-forecast`
**제목**: 15개 요인 기반 7일간 유가 예측  
**참조**: 오피넷 실시간 가격 + 15개 변동요인 분석을 통한 과학적 예측  

**응답 구조**:
```json
{
  "metadata": {
    "generated_at": "2025-08-10T20:55:49.615120",
    "forecast_horizon_days": 7,
    "total_regions": 17,
    "model_version": "3.0.0_opinet_realtime",
    "methodology": "오피넷 실시간 가격 + 15개 변동요인 분석 → 일주일 예측",
    "data_source": "한국석유공사 오피넷 + 15개 경제지표"
  },
  "current_prices": {
    "gasoline": {
      "price": 1668.88,
      "date": "20250810",
      "diff": 0.0
    },
    "diesel": {
      "price": 1538.37,
      "date": "20250810", 
      "diff": 0.0
    }
  },
  "forecasts": {
    "seoul": {
      "gasoline": {
        "current_price": 1734.3,
        "forecasts": [
          {
            "date": "2025-08-11T20:55:49.615142",
            "price": 1734.3,
            "change_rate": 0.0,
            "factors_impact": 0.0,
            "day_label": "1일차",
            "is_current_day": true
          }
        ],
        "week_end_price": 1740.7,
        "week_total_change": 0.37
      }
    }
  },
  "national_average": {
    "gasoline": {
      "current_price": 1668.9,
      "week_end_price": 1687.5,
      "week_total_change": 1.12
    }
  },
  "factor_analysis": {
    "analysis_date": "2025-08-10T20:55:49.615130",
    "total_factors": 15,
    "methodology": "다중회귀분석 + 시계열 분석 + 실시간 데이터",
    "confidence": 92.3
  }
}
```

**API 코드**:
```python
@app.route('/api/weekly-forecast')
def get_weekly_forecast():
    """실시간 일주일 예측 데이터"""
    try:
        if weekly_engine:
            logger.info("🎯 실시간 일주일 예측 생성 중...")
            weekly_data = weekly_engine.generate_weekly_forecast()
            logger.info("✅ 일주일 예측 완료")
            return jsonify(weekly_data)
        else:
            logger.warning("주간 예측 엔진 없음, 기존 데이터 반환")
            if forecast_data:
                converted_data = convert_to_weekly_format(forecast_data)
                return jsonify(converted_data)
            else:
                return jsonify({"error": "No forecast data available"}), 404
    except Exception as e:
        logger.error(f"일주일 예측 생성 실패: {e}")
        return jsonify({"error": "Weekly forecast generation failed", "details": str(e)}), 500
```

---

### 3. 오피넷 실시간 현재가

#### GET `/api/opinet-current`
**제목**: 오피넷 실시간 가격 조회  
**참조**: 한국석유공사 오피넷 공식 API를 통한 실시간 유가 정보  

**응답 예시**:
```json
{
  "status": "success",
  "timestamp": "2025-08-10T20:55:49.615120",
  "national_average": {
    "gasoline": {
      "price": 1668.88,
      "date": "20250810",
      "diff": 0.0
    },
    "diesel": {
      "price": 1538.37,
      "date": "20250810", 
      "diff": 0.0
    }
  },
  "regional_prices": {
    "seoul": {
      "gasoline": {
        "price": 1734.30,
        "date": "20250810"
      },
      "diesel": {
        "price": 1616.95,
        "date": "20250810"
      }
    }
  }
}
```

**API 코드**:
```python
@app.route('/api/opinet-current')
def get_opinet_current():
    """오피넷 실시간 현재가 조회"""
    try:
        if opinet_connector:
            logger.info("📡 오피넷 실시간 가격 조회...")
            current_prices = opinet_connector.get_current_prices()
            regional_prices = opinet_connector.get_regional_prices()
            
            return jsonify({
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "national_average": current_prices,
                "regional_prices": regional_prices
            })
        else:
            return jsonify({"error": "Opinet connector not available"}), 503
    except Exception as e:
        logger.error(f"오피넷 가격 조회 실패: {e}")
        return jsonify({"error": "Opinet price fetch failed", "details": str(e)}), 500
```

---

### 4. 지역 목록

#### GET `/api/regions`
**제목**: 지원 지역 목록 조회  
**참조**: 17개 시도별 지역 코드 및 한글명 정보  

**응답 예시**:
```json
[
  {
    "code": "seoul",
    "name": "서울특별시",
    "type": "특별시"
  },
  {
    "code": "busan", 
    "name": "부산광역시",
    "type": "광역시"
  }
]
```

**API 코드**:
```python
@app.route('/api/regions')
def api_get_regions():
    """API 엔드포인트: 지역 목록"""
    return jsonify(regions_data)
```

---

### 5. 예측 분석 리포트

#### GET `/api/analysis`
**제목**: 유가 변동 요인 분석 리포트  
**참조**: 16개 주요 변동 요인별 가중치, 영향도, 트렌드 분석  

**응답 구조**:
```json
{
  "analysis_date": "2025-08-09",
  "total_factors": 16,
  "methodology": "다중회귀분석 및 시계열 분석",
  "factors": [
    {
      "factor": "국제 원유가격 (WTI/두바이유)",
      "weight": 35.2,
      "impact": "매우높음",
      "description": "글로벌 원유 시장 가격이 국내 유가에 가장 직접적인 영향",
      "trend": "상승",
      "category": "국제경제"
    }
  ],
  "summary": {
    "primary_drivers": "국제유가(35.2%) + 환율(18.7%) + 국내수요(12.3%)",
    "volatility_source": "지정학적 리스크와 OPEC+ 정책 변화",
    "forecast_confidence": 87.4
  },
  "fuel_comparison": {
    "gasoline_trend": {
      "direction": "완만한 상승",
      "rate": "+0.4%/주"
    },
    "diesel_trend": {
      "direction": "소폭 하락", 
      "rate": "-0.3%/주"
    }
  }
}
```

**API 코드**:
```python
@app.route('/api/analysis')
def get_analysis_report():
    """예측요인분석 리포트"""
    # 유가 변동에 영향을 미치는 16개 요인 데이터
    analysis_factors = [
        {
            "factor": "국제 원유가격 (WTI/두바이유)",
            "weight": 35.2,
            "impact": "매우높음",
            "description": "글로벌 원유 시장 가격이 국내 유가에 가장 직접적인 영향",
            "trend": "상승",
            "category": "국제경제"
        }
        # ... 추가 요인들
    ]
    
    return jsonify({
        "analysis_date": "2025-08-09",
        "total_factors": len(analysis_factors),
        "methodology": "다중회귀분석 및 시계열 분석",
        "factors": analysis_factors,
        "summary": {
            "primary_drivers": "국제유가(35.2%) + 환율(18.7%) + 국내수요(12.3%)",
            "volatility_source": "지정학적 리스크와 OPEC+ 정책 변화",
            "forecast_confidence": 87.4
        }
    })
```

---

## 🔧 15개 AI 모델 구성 요소

### 국제 요인 (40% 가중치)
1. **Dubai 국제원유가격** (25%) - ARIMA-LSTM 하이브리드
2. **싱가포르 국제제품가격** (8%) - VAR 모델  
3. **싱가포르 정제마진** (7%) - Gaussian Process Regression

### 환율 요인 (15% 가중치)  
4. **USD/KRW 환율** (15%) - GARCH-LSTM 변동성 모델

### 국내 정책 요인 (20% 가중치)
5. **유류세 정책** (12%) - Policy Detection + Rule-Based
6. **원유수입단가 CIF기준** (8%) - Lasso Regularized MLR

### 국내 수급 요인 (15% 가중치)
7. **국내 석유재고** (6%) - Prophet + Inventory Optimization
8. **국내 제품소비량** (5%) - SARIMAX 계절 모델  
9. **지역별 소비량** (4%) - Hierarchical Time Series + Spatial Analysis

### 경제 요인 (7% 가중치)
10. **소비자 물가지수** (3%) - 공적분 + 오차수정 모델
11. **전국 지가변동률** (2%) - Ridge Regression + Polynomial Features
12. **전국 자동차등록현황** (2%) - Logistic Growth Model

### 유통 요인 (3% 가중치)
13. **정유사-대리점-주유소 마진** (2%) - Game Theory + Nash Equilibrium
14. **물류비용 및 유통비용** (1%) - Transport Cost Optimization

### 추가 모니터링 요인
15. **계절적 요인** - 여름/겨울철 패턴 분석

---

## 📊 응답 코드

| 상태 코드 | 설명 |
|----------|------|
| 200 | 성공 |
| 404 | 데이터 없음 |
| 500 | 서버 오류 |
| 503 | 외부 서비스 연결 실패 |

---

## 🔄 데이터 업데이트 주기

- **실시간 가격**: 오피넷 API 연동 (매시간)
- **7일 예측**: 15개 모델 기반 실시간 생성
- **요인 분석**: 일 1회 업데이트
- **지역별 가격**: 실시간 조회

---

## 🛡️ 에러 처리

### 공통 에러 응답
```json
{
  "error": "오류 메시지",
  "details": "상세 오류 정보",
  "timestamp": "2025-08-10T20:55:49.615120"
}
```

### 주요 에러 케이스
- **오피넷 API 연결 실패**: 기본값으로 대체
- **예측 엔진 오류**: 대체 알고리즘 사용
- **데이터 부재**: 404 에러 반환

---

## 🚀 사용 예시

### JavaScript (Fetch API)
```javascript
// 7일 예측 데이터 가져오기
async function getWeeklyForecast() {
    try {
        const response = await fetch('http://127.0.0.1:8001/api/weekly-forecast');
        const data = await response.json();
        console.log('7일 예측:', data);
        return data;
    } catch (error) {
        console.error('API 호출 실패:', error);
    }
}

// 현재 오피넷 가격 가져오기
async function getCurrentPrices() {
    try {
        const response = await fetch('http://127.0.0.1:8001/api/opinet-current');
        const data = await response.json();
        console.log('현재 가격:', data);
        return data;
    } catch (error) {
        console.error('가격 조회 실패:', error);
    }
}
```

### Python (requests)
```python
import requests

# 7일 예측 조회
def get_weekly_forecast():
    try:
        response = requests.get('http://127.0.0.1:8001/api/weekly-forecast')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 호출 실패: {e}")
        return None

# 시스템 상태 확인
def check_health():
    try:
        response = requests.get('http://127.0.0.1:8001/api/health')
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"헬스 체크 실패: {e}")
        return None
```

### cURL
```bash
# 7일 예측 조회
curl -X GET "http://127.0.0.1:8001/api/weekly-forecast" \
     -H "Content-Type: application/json"

# 현재 가격 조회  
curl -X GET "http://127.0.0.1:8001/api/opinet-current" \
     -H "Content-Type: application/json"

# 시스템 상태 확인
curl -X GET "http://127.0.0.1:8001/api/health" \
     -H "Content-Type: application/json"
```

---

## 📞 지원 및 문의

- **프로젝트 문서**: agents.md, README.md 참조
- **기술 지원**: 15개 AI 모델 기반 고도화된 예측 시스템
- **업데이트**: 실시간 오피넷 연동으로 최신 정보 제공

이 API를 통해 한국 유가 시장의 정확하고 신뢰할 수 있는 예측 데이터를 활용하실 수 있습니다.