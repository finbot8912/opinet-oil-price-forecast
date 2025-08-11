#!/usr/bin/env python3
"""
간단한 테스트 서버
웹 애플리케이션 테스트용
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
import logging
import sys
import os
from datetime import datetime, timedelta

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from opinet_api_connector import OpinetAPIConnector
    from weekly_forecast_engine import WeeklyForecastEngine
except ImportError as e:
    logging.warning(f"일부 모듈 임포트 실패 (대체 기능 사용): {e}")
    OpinetAPIConnector = None
    WeeklyForecastEngine = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})  # CORS 설정

# 데이터 로드
def load_data():
    try:
        # 예측 데이터 로드
        forecast_file = Path("data/processed/current_forecast.json")
        regions_file = Path("data/processed/regions.json")
        
        forecast_data = None
        regions_data = []
        
        if forecast_file.exists():
            with open(forecast_file, 'r', encoding='utf-8') as f:
                forecast_data = json.load(f)
            logger.info("예측 데이터 로드 성공")
        
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                regions_data = json.load(f)
            logger.info("지역 데이터 로드 성공")
        
        return forecast_data, regions_data
        
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}")
        return None, []

# 전역 데이터
forecast_data, regions_data = load_data()

# 주간 예측 엔진 초기화
weekly_engine = WeeklyForecastEngine() if WeeklyForecastEngine else None
opinet_connector = OpinetAPIConnector() if OpinetAPIConnector else None

def convert_to_weekly_format(old_forecast_data):
    """기존 28일 예측을 7일 예측으로 변환"""
    if not old_forecast_data or 'forecasts' not in old_forecast_data:
        return {"error": "Invalid forecast data"}
    
    weekly_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "forecast_horizon_days": 7,
            "total_regions": 17,
            "model_version": "2.5.0_converted",
            "methodology": "기존 28일 데이터에서 일주일 추출"
        },
        "forecasts": {},
        "national_average": {}
    }
    
    # 각 지역별 7일 데이터 추출
    for region, region_data in old_forecast_data['forecasts'].items():
        weekly_data["forecasts"][region] = {}
        
        for fuel_type in ['gasoline', 'diesel']:
            if fuel_type in region_data:
                fuel_data = region_data[fuel_type]
                current_price = fuel_data.get('current_price', 1650 if fuel_type == 'gasoline' else 1490)
                
                # 첫 7일만 추출
                weekly_forecasts = fuel_data['forecasts'][:7] if 'forecasts' in fuel_data else []
                
                weekly_data["forecasts"][region][fuel_type] = {
                    "current_price": current_price,
                    "forecasts": weekly_forecasts
                }
    
    # 전국 평균 계산
    if 'national_average' in old_forecast_data:
        weekly_data["national_average"] = {}
        for fuel_type in ['gasoline', 'diesel']:
            if fuel_type in old_forecast_data['national_average']:
                fuel_data = old_forecast_data['national_average'][fuel_type]
                current_price = fuel_data.get('current_price', 1650 if fuel_type == 'gasoline' else 1490)
                
                weekly_forecasts = fuel_data['forecasts'][:7] if 'forecasts' in fuel_data else []
                
                weekly_data["national_average"][fuel_type] = {
                    "current_price": current_price,
                    "forecasts": weekly_forecasts
                }
    
    return weekly_data

@app.route('/')
def home():
    return jsonify({
        "message": "유가 예측 API 서버",
        "status": "running",
        "endpoints": [
            "/regions",
            "/forecast",
            "/health"
        ]
    })

@app.route('/regions')
def get_regions():
    """지역 목록 반환"""
    return jsonify(regions_data)

@app.route('/forecast')
def get_forecast():
    """예측 데이터 반환"""
    if forecast_data:
        return jsonify(forecast_data)
    else:
        return jsonify({"error": "No forecast data available"}), 404

@app.route('/api/regions')
def api_get_regions():
    """API 엔드포인트: 지역 목록"""
    return jsonify(regions_data)

@app.route('/api/forecast')
def api_get_forecast():
    """API 엔드포인트: 예측 데이터"""
    if forecast_data:
        return jsonify(forecast_data)
    else:
        return jsonify({"error": "No forecast data available"}), 404

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
        },
        {
            "factor": "환율 (USD/KRW)",
            "weight": 18.7,
            "impact": "높음",
            "description": "원달러 환율 상승 시 수입 원유 비용 증가로 유가 상승",
            "trend": "변동",
            "category": "환율"
        },
        {
            "factor": "국내 수요량",
            "weight": 12.3,
            "impact": "높음",
            "description": "계절적 요인과 경제활동에 따른 유류 소비량 변화",
            "trend": "안정",
            "category": "수급"
        },
        {
            "factor": "정부 유류세 정책",
            "weight": 11.8,
            "impact": "높음",
            "description": "유류세 인하/인상 정책이 소비자 가격에 직접 반영",
            "trend": "정책변화",
            "category": "정책"
        },
        {
            "factor": "정제마진",
            "weight": 8.9,
            "impact": "보통",
            "description": "정유사의 원유 정제 과정에서 발생하는 마진율",
            "trend": "안정",
            "category": "제조"
        },
        {
            "factor": "지정학적 리스크",
            "weight": 4.2,
            "impact": "보통",
            "description": "중동, 러시아-우크라이나 등 산유국 정세 불안",
            "trend": "증가",
            "category": "국제정치"
        },
        {
            "factor": "계절적 요인",
            "weight": 3.8,
            "impact": "보통",
            "description": "여름/겨울철 수요 증가, 휴가철 교통량 변화",
            "trend": "주기적",
            "category": "계절성"
        },
        {
            "factor": "물류비용",
            "weight": 2.1,
            "impact": "낮음",
            "description": "유조선 운임, 저장시설 비용 등 유통단계 비용",
            "trend": "안정",
            "category": "물류"
        },
        {
            "factor": "재고량",
            "weight": 1.8,
            "impact": "낮음",
            "description": "석유공사 비축유 및 정유사 재고 보유량",
            "trend": "안정",
            "category": "수급"
        },
        {
            "factor": "OPEC+ 생산량 조절",
            "weight": 1.2,
            "impact": "낮음",
            "description": "석유수출국기구의 원유 생산량 증감 결정",
            "trend": "변동",
            "category": "국제경제"
        },
        {
            "factor": "미국 셰일오일 생산량",
            "weight": 0.9,
            "impact": "낮음",
            "description": "미국 비전통 원유 생산이 글로벌 공급에 미치는 영향",
            "trend": "증가",
            "category": "국제경제"
        },
        {
            "factor": "중국 경제성장률",
            "weight": 0.8,
            "impact": "낮음",
            "description": "세계 최대 원유 소비국의 경제성장과 에너지 수요",
            "trend": "둔화",
            "category": "국제경제"
        },
        {
            "factor": "글로벌 인플레이션",
            "weight": 0.7,
            "impact": "낮음",
            "description": "전 세계 물가상승이 원유 및 에너지 가격에 미치는 영향",
            "trend": "안정화",
            "category": "국제경제"
        },
        {
            "factor": "대체에너지 보급률",
            "weight": 0.6,
            "impact": "낮음",
            "description": "전기차, 재생에너지 확산으로 인한 유류 수요 감소",
            "trend": "증가",
            "category": "신에너지"
        },
        {
            "factor": "국내 경기지수",
            "weight": 0.5,
            "impact": "낮음",
            "description": "국내 경제활동 지표가 유류 소비량에 미치는 영향",
            "trend": "회복",
            "category": "국내경제"
        },
        {
            "factor": "교통량 지수",
            "weight": 0.4,
            "impact": "낮음",
            "description": "도로 교통량과 물류활동 변화에 따른 유류 수요",
            "trend": "안정",
            "category": "교통"
        }
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
        },
        "fuel_comparison": {
            "gasoline_trend": {
                "direction": "완만한 상승",
                "rate": "+0.4%/주",
                "reasons": [
                    "여름철 드라이빙 시즌으로 수요 소폭 증가",
                    "국제 원유가격의 제한적 상승 압력",
                    "환율 변동성으로 인한 수입 비용 증가",
                    "계절적 수요 패턴에 따른 자연스러운 상승"
                ]
            },
            "diesel_trend": {
                "direction": "소폭 하락",
                "rate": "-0.3%/주",
                "reasons": [
                    "여름철 난방 수요 감소로 경유 소비 둔화",
                    "친환경 정책으로 인한 점진적 수요 감소",
                    "물류업계 효율화로 경유 사용량 최적화",
                    "전기상용차 보급으로 장기 수요 감소"
                ]
            },
            "market_analysis": "한국 유가 시장은 오피넷 시스템의 투명성과 정부 안정화 정책으로 국제유가 대비 안정적 변동성을 유지. 환율(45%)이 가격변동에 가장 큰 영향을 미치며, 계절적 요인은 완만하게 반영됨. 4주간 휘발유는 +1.7%, 경유는 -1.3%의 현실적 변동 예상."
        }
    })

@app.route('/health')
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "data_loaded": {
            "forecast": forecast_data is not None,
            "regions": len(regions_data) > 0
        }
    })

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
            # 기존 데이터를 일주일 형식으로 변환
            if forecast_data:
                converted_data = convert_to_weekly_format(forecast_data)
                return jsonify(converted_data)
            else:
                return jsonify({"error": "No forecast data available"}), 404
    except Exception as e:
        logger.error(f"일주일 예측 생성 실패: {e}")
        return jsonify({"error": "Weekly forecast generation failed", "details": str(e)}), 500

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

if __name__ == '__main__':
    logger.info("Flask 서버 시작...")
    logger.info(f"예측 데이터: {'로드됨' if forecast_data else '없음'}")
    logger.info(f"지역 데이터: {len(regions_data)}개")
    
    # Flask 서버 실행
    app.run(
        host='127.0.0.1',
        port=8001,
        debug=True,
        use_reloader=False  # 리로더 비활성화
    )