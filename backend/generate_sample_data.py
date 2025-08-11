#!/usr/bin/env python3
"""
샘플 데이터 생성기
웹 애플리케이션 테스트용 데이터 생성
"""

import json
from datetime import datetime, timedelta
import random
from pathlib import Path

def generate_sample_forecast_data():
    """샘플 예측 데이터 생성"""
    
    # 지역 목록
    regions = [
        {"code": "seoul", "name": "서울"},
        {"code": "busan", "name": "부산"},
        {"code": "daegu", "name": "대구"},
        {"code": "incheon", "name": "인천"},
        {"code": "gwangju", "name": "광주"},
        {"code": "daejeon", "name": "대전"},
        {"code": "ulsan", "name": "울산"},
        {"code": "gyeonggi", "name": "경기"},
        {"code": "gangwon", "name": "강원"},
        {"code": "chungbuk", "name": "충북"},
        {"code": "chungnam", "name": "충남"},
        {"code": "jeonbuk", "name": "전북"},
        {"code": "jeonnam", "name": "전남"},
        {"code": "gyeongbuk", "name": "경북"},
        {"code": "gyeongnam", "name": "경남"},
        {"code": "jeju", "name": "제주"},
        {"code": "sejong", "name": "세종"}
    ]
    
    # 기본 가격 (2024년 기준)
    base_gasoline_price = 1650
    base_diesel_price = 1450
    
    # 예측 데이터 구조 생성
    forecast_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "forecast_horizon_days": 28,
            "total_regions": len(regions),
            "model_version": "1.0.0"
        },
        "forecasts": {},
        "national_average": {
            "gasoline": {
                "current_price": base_gasoline_price,
                "forecasts": [],
                "volatility": 0.03
            },
            "diesel": {
                "current_price": base_diesel_price, 
                "forecasts": [],
                "volatility": 0.025
            }
        }
    }
    
    # 28일 국가 평균 예측 생성
    for day in range(1, 29):
        date = (datetime.now() + timedelta(days=day)).isoformat()
        
        # 약간의 계절적 변동과 랜덤 요소 추가
        seasonal_factor = 1.0 + 0.02 * random.random() - 0.01
        trend_factor = 1.0 + (day * 0.0003)  # 약간의 상승 트렌드
        
        gas_price = base_gasoline_price * seasonal_factor * trend_factor
        diesel_price = base_diesel_price * seasonal_factor * trend_factor
        
        forecast_data["national_average"]["gasoline"]["forecasts"].append({
            "date": date,
            "price": round(gas_price, 1)
        })
        
        forecast_data["national_average"]["diesel"]["forecasts"].append({
            "date": date,
            "price": round(diesel_price, 1)
        })
    
    # 각 지역별 예측 데이터 생성
    for region in regions:
        region_code = region["code"]
        
        # 지역별 기본 가격 차이 (서울이 가장 높고, 지방이 조금 낮음)
        if region_code == "seoul":
            gas_multiplier = 1.05
            diesel_multiplier = 1.04
        elif region_code in ["busan", "daegu", "incheon"]:
            gas_multiplier = 1.02
            diesel_multiplier = 1.01
        elif region_code == "jeju":
            gas_multiplier = 1.08  # 제주는 운송비로 인해 높음
            diesel_multiplier = 1.07
        else:
            gas_multiplier = 0.98
            diesel_multiplier = 0.97
        
        region_gas_price = base_gasoline_price * gas_multiplier
        region_diesel_price = base_diesel_price * diesel_multiplier
        
        forecast_data["forecasts"][region_code] = {
            "gasoline": {
                "current_price": round(region_gas_price, 1),
                "forecasts": [],
                "volatility": 0.025 + random.random() * 0.01
            },
            "diesel": {
                "current_price": round(region_diesel_price, 1),
                "forecasts": [],
                "volatility": 0.02 + random.random() * 0.01
            }
        }
        
        # 28일 지역별 예측 생성
        for day in range(1, 29):
            date = (datetime.now() + timedelta(days=day)).isoformat()
            
            # 지역별 고유한 변동성 추가
            regional_factor = 1.0 + (random.random() * 0.04 - 0.02)
            trend_factor = 1.0 + (day * 0.0003)
            
            gas_forecast = region_gas_price * regional_factor * trend_factor
            diesel_forecast = region_diesel_price * regional_factor * trend_factor
            
            forecast_data["forecasts"][region_code]["gasoline"]["forecasts"].append({
                "date": date,
                "price": round(gas_forecast, 1)
            })
            
            forecast_data["forecasts"][region_code]["diesel"]["forecasts"].append({
                "date": date,
                "price": round(diesel_forecast, 1)
            })
    
    return forecast_data

def generate_regions_data():
    """지역 정보 데이터 생성"""
    return [
        {"code": "seoul", "name": "서울"},
        {"code": "busan", "name": "부산"},
        {"code": "daegu", "name": "대구"},
        {"code": "incheon", "name": "인천"},
        {"code": "gwangju", "name": "광주"},
        {"code": "daejeon", "name": "대전"},
        {"code": "ulsan", "name": "울산"},
        {"code": "gyeonggi", "name": "경기"},
        {"code": "gangwon", "name": "강원"},
        {"code": "chungbuk", "name": "충북"},
        {"code": "chungnam", "name": "충남"},
        {"code": "jeonbuk", "name": "전북"},
        {"code": "jeonnam", "name": "전남"},
        {"code": "gyeongbuk", "name": "경북"},
        {"code": "gyeongnam", "name": "경남"},
        {"code": "jeju", "name": "제주"},
        {"code": "sejong", "name": "세종"}
    ]

if __name__ == "__main__":
    # 데이터 디렉토리 생성
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 샘플 예측 데이터 생성
    print("샘플 예측 데이터 생성 중...")
    forecast_data = generate_sample_forecast_data()
    
    with open(data_dir / "current_forecast.json", "w", encoding="utf-8") as f:
        json.dump(forecast_data, f, ensure_ascii=False, indent=2)
    
    # 지역 정보 생성
    print("지역 정보 데이터 생성 중...")
    regions_data = generate_regions_data()
    
    with open(data_dir / "regions.json", "w", encoding="utf-8") as f:
        json.dump(regions_data, f, ensure_ascii=False, indent=2)
    
    print("샘플 데이터 생성 완료!")
    print(f"- 예측 데이터: {data_dir / 'current_forecast.json'}")
    print(f"- 지역 정보: {data_dir / 'regions.json'}")