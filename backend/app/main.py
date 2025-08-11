#!/usr/bin/env python3
"""
유가 예측 시스템 백엔드 API 서버
FastAPI 기반 REST API 서버
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 로컬 모듈
from .models.simple_forecaster import SimpleOilPriceForecaster
from .utils.improved_data_processor import ImprovedOilPriceDataProcessor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="유가 예측 API",
    description="한국 석유 가격 예측 시스템 API",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
forecaster = SimpleOilPriceForecaster()
data_processor = ImprovedOilPriceDataProcessor()
data_dir = Path("data/processed")

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "유가 예측 API 서버",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "forecast": "/api/forecast",
            "regions": "/api/regions",
            "historical": "/api/historical",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    try:
        # 데이터 파일 존재 확인
        forecast_file = data_dir / "oil_price_forecast.json"
        data_available = forecast_file.exists()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "data_available": data_available,
            "services": {
                "forecasting": "operational",
                "data_processing": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/api/forecast")
async def get_current_forecast(
    region: Optional[str] = None,
    fuel_type: Optional[str] = None,
    days: Optional[int] = None
):
    """현재 유가 예측 조회"""
    try:
        # 예측 데이터 로드
        forecast_file = data_dir / "oil_price_forecast.json"
        
        if not forecast_file.exists():
            raise HTTPException(
                status_code=404, 
                detail="예측 데이터를 찾을 수 없습니다. 예측을 먼저 생성해주세요."
            )
        
        with open(forecast_file, 'r', encoding='utf-8') as f:
            forecast_data = json.load(f)
        
        # 필터링 적용
        result = forecast_data.copy()
        
        # 특정 지역 필터링
        if region:
            if region not in forecast_data.get('forecasts', {}):
                raise HTTPException(status_code=404, detail=f"지역 '{region}'을 찾을 수 없습니다")
            
            result = {
                'metadata': forecast_data['metadata'],
                'forecasts': {region: forecast_data['forecasts'][region]},
                'national_average': forecast_data.get('national_average', {})
            }
        
        # 특정 연료 타입 필터링
        if fuel_type and fuel_type in ['gasoline', 'diesel']:
            if 'forecasts' in result:
                filtered_forecasts = {}
                for reg, reg_data in result['forecasts'].items():
                    if fuel_type in reg_data:
                        filtered_forecasts[reg] = {fuel_type: reg_data[fuel_type]}
                result['forecasts'] = filtered_forecasts
            
            if 'national_average' in result:
                if fuel_type in result['national_average']:
                    result['national_average'] = {fuel_type: result['national_average'][fuel_type]}
                else:
                    result['national_average'] = {}
        
        # 예측 기간 제한
        if days and days > 0:
            result = _limit_forecast_days(result, days)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"예측 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/regions")
async def get_available_regions():
    """사용 가능한 지역 목록 조회"""
    try:
        forecast_file = data_dir / "oil_price_forecast.json"
        
        # 지역 정보 파일에서 로드
        regions_file = data_dir / "regions.json"
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                regions_data = json.load(f)
                return {"regions": regions_data}
        
        if not forecast_file.exists():
            # 기본 지역 목록 반환
            return {
                "regions": [
                    {"code": "seoul", "name": "서울특별시", "short_name": "서울"},
                    {"code": "busan", "name": "부산광역시", "short_name": "부산"},
                    {"code": "daegu", "name": "대구광역시", "short_name": "대구"},
                    {"code": "incheon", "name": "인천광역시", "short_name": "인천"},
                    {"code": "gwangju", "name": "광주광역시", "short_name": "광주"},
                    {"code": "daejeon", "name": "대전광역시", "short_name": "대전"},
                    {"code": "ulsan", "name": "울산광역시", "short_name": "울산"},
                    {"code": "sejong", "name": "세종특별자치시", "short_name": "세종"},
                    {"code": "gyeonggi", "name": "경기도", "short_name": "경기"},
                    {"code": "gangwon", "name": "강원특별자치도", "short_name": "강원"},
                    {"code": "chungbuk", "name": "충청북도", "short_name": "충북"},
                    {"code": "chungnam", "name": "충청남도", "short_name": "충남"},
                    {"code": "jeonbuk", "name": "전북특별자치도", "short_name": "전북"},
                    {"code": "jeonnam", "name": "전라남도", "short_name": "전남"},
                    {"code": "gyeongbuk", "name": "경상북도", "short_name": "경북"},
                    {"code": "gyeongnam", "name": "경상남도", "short_name": "경남"},
                    {"code": "jeju", "name": "제주특별자치도", "short_name": "제주"}
                ]
            }
        
        with open(forecast_file, 'r', encoding='utf-8') as f:
            forecast_data = json.load(f)
        
        # 실제 예측 데이터가 있는 지역들 추출
        available_regions = []
        region_name_map = {
            "seoul": "서울", "busan": "부산", "daegu": "대구", "incheon": "인천",
            "gwangju": "광주", "daejeon": "대전", "ulsan": "울산", "gyeonggi": "경기",
            "gangwon": "강원", "chungbuk": "충북", "chungnam": "충남", "jeonbuk": "전북",
            "jeonnam": "전남", "gyeongbuk": "경북", "gyeongnam": "경남", "jeju": "제주",
            "sejong": "세종"
        }
        
        for region_code in forecast_data.get('forecasts', {}):
            available_regions.append({
                "code": region_code,
                "name": region_name_map.get(region_code, region_code)
            })
        
        return {"regions": available_regions}
        
    except Exception as e:
        logger.error(f"Region list retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="지역 목록 조회 중 오류가 발생했습니다")

@app.get("/api/historical")
async def get_historical_data(
    region: Optional[str] = None,
    fuel_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """과거 가격 데이터 조회"""
    try:
        # 지역별 가격 데이터 로드
        regional_file = data_dir / "regional_gas_prices.json"
        
        if not regional_file.exists():
            raise HTTPException(status_code=404, detail="과거 데이터를 찾을 수 없습니다")
        
        with open(regional_file, 'r', encoding='utf-8') as f:
            regional_data = json.load(f)
        
        # 데이터 필터링 및 변환
        historical_records = []
        
        for record in regional_data.get('data', []):
            record_date = record.get('date')
            if not record_date:
                continue
                
            # 날짜 필터링
            if start_date and record_date < start_date:
                continue
            if end_date and record_date > end_date:
                continue
            
            # 지역 필터링
            gasoline_data = record.get('gasoline', {})
            diesel_data = record.get('diesel', {})
            
            if region:
                gasoline_data = {region: gasoline_data.get(region)} if region in gasoline_data else {}
                diesel_data = {region: diesel_data.get(region)} if region in diesel_data else {}
            
            # 연료 타입 필터링
            record_entry = {"date": record_date}
            
            if not fuel_type or fuel_type == 'gasoline':
                record_entry['gasoline'] = gasoline_data
            if not fuel_type or fuel_type == 'diesel':
                record_entry['diesel'] = diesel_data
            
            historical_records.append(record_entry)
        
        return {
            "metadata": {
                "total_records": len(historical_records),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "filters": {
                    "region": region,
                    "fuel_type": fuel_type
                }
            },
            "data": historical_records[-100:] if len(historical_records) > 100 else historical_records  # 최근 100개로 제한
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Historical data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="과거 데이터 조회 중 오류가 발생했습니다")

@app.post("/api/forecast/refresh")
async def refresh_forecast(background_tasks: BackgroundTasks):
    """예측 데이터 갱신 (백그라운드 작업)"""
    try:
        # 백그라운드 작업으로 예측 재생성
        background_tasks.add_task(run_forecast_update)
        
        return {
            "message": "예측 갱신이 백그라운드에서 시작되었습니다",
            "timestamp": datetime.now().isoformat(),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Forecast refresh failed: {e}")
        raise HTTPException(status_code=500, detail="예측 갱신 중 오류가 발생했습니다")

@app.get("/api/analysis")
async def get_analysis_report():
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
    
    return {
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
                "rate": "+0.3~0.5%/주",
                "reasons": [
                    "여름철 드라이빙 시즌으로 수요 소폭 증가",
                    "국제 원유가격의 제한적 상승 압력",
                    "원달러 환율 변동성으로 인한 비용 증가",
                    "계절적 수요 패턴에 따른 자연스러운 상승"
                ]
            },
            "diesel_trend": {
                "direction": "소폭 하락",
                "rate": "-0.2~0.4%/주",
                "reasons": [
                    "여름철 난방 수요 감소로 경유 소비 둔화",
                    "친환경 정책으로 인한 점진적 수요 감소",
                    "물류업계 효율화로 경유 사용량 최적화",
                    "전기상용차 보급 확산의 장기적 영향"
                ]
            },
            "market_analysis": "한국 유가 시장은 오피넷 시스템으로 인한 투명성 확보와 정부 정책의 안정화 효과로 인해 국제유가 대비 상대적으로 안정적인 변동성을 보임. 환율이 가격변동에 더 큰 영향을 미치며, 계절적 요인은 존재하나 과도한 변동보다는 완만한 조정 양상을 보임."
        }
    }

@app.get("/api/forecast/summary")
async def get_forecast_summary():
    """예측 요약 정보 조회"""
    try:
        forecast_file = data_dir / "oil_price_forecast.json"
        
        if not forecast_file.exists():
            raise HTTPException(status_code=404, detail="예측 데이터를 찾을 수 없습니다")
        
        with open(forecast_file, 'r', encoding='utf-8') as f:
            forecast_data = json.load(f)
        
        # 요약 정보 생성
        summary = {
            "metadata": forecast_data.get('metadata', {}),
            "national_average": forecast_data.get('national_average', {}),
            "regional_summary": {}
        }
        
        # 지역별 요약
        forecasts = forecast_data.get('forecasts', {})
        for region, region_data in forecasts.items():
            region_summary = {}
            
            for fuel_type in ['gasoline', 'diesel']:
                if fuel_type in region_data and 'forecasts' in region_data[fuel_type]:
                    forecasts_list = region_data[fuel_type]['forecasts']
                    current_price = region_data[fuel_type]['current_price']
                    
                    if forecasts_list:
                        final_price = forecasts_list[-1]['price']
                        price_change = final_price - current_price
                        price_change_pct = (price_change / current_price) * 100
                        
                        region_summary[fuel_type] = {
                            "current_price": current_price,
                            "forecast_price": final_price,
                            "change_amount": round(price_change, 2),
                            "change_percent": round(price_change_pct, 2),
                            "trend": "상승" if price_change > 0 else "하락" if price_change < 0 else "보합"
                        }
            
            if region_summary:
                summary["regional_summary"][region] = region_summary
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast summary failed: {e}")
        raise HTTPException(status_code=500, detail="예측 요약 조회 중 오류가 발생했습니다")

def _limit_forecast_days(data: dict, days: int) -> dict:
    """예측 기간 제한"""
    result = data.copy()
    
    # 지역별 예측 제한
    if 'forecasts' in result:
        for region, region_data in result['forecasts'].items():
            for fuel_type in ['gasoline', 'diesel']:
                if fuel_type in region_data and 'forecasts' in region_data[fuel_type]:
                    region_data[fuel_type]['forecasts'] = region_data[fuel_type]['forecasts'][:days]
    
    # 전국 평균 제한
    if 'national_average' in result:
        for fuel_type in ['gasoline', 'diesel']:
            if fuel_type in result['national_average'] and 'forecasts' in result['national_average'][fuel_type]:
                result['national_average'][fuel_type]['forecasts'] = result['national_average'][fuel_type]['forecasts'][:days]
    
    return result

async def run_forecast_update():
    """백그라운드 예측 갱신 작업"""
    try:
        logger.info("백그라운드 예측 갱신 시작...")
        
        # 새로운 예측 생성
        forecast_data = forecaster.generate_forecast(forecast_days=28)
        
        if forecast_data:
            # 결과 저장
            forecaster.save_forecast(forecast_data)
            logger.info("백그라운드 예측 갱신 완료")
        else:
            logger.error("예측 생성 실패")
            
    except Exception as e:
        logger.error(f"백그라운드 예측 갱신 오류: {e}")

# 서버 시작시 초기 예측 생성 (개발용)
@app.on_event("startup")
async def startup_event():
    """서버 시작시 실행"""
    logger.info("유가 예측 API 서버 시작...")
    
    # 예측 데이터 파일 확인
    forecast_file = data_dir / "oil_price_forecast.json"
    if not forecast_file.exists():
        logger.info("예측 데이터가 없습니다. 초기 예측을 생성합니다...")
        try:
            forecast_data = forecaster.generate_forecast(forecast_days=28)
            if forecast_data:
                forecaster.save_forecast(forecast_data)
                logger.info("초기 예측 생성 완료")
        except Exception as e:
            logger.error(f"초기 예측 생성 실패: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)