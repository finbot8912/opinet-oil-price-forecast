#!/usr/bin/env python3
"""
간단하고 현실적인 유가 예측 데이터 생성기
"""

import json
import random
from datetime import datetime, timedelta

def generate_realistic_forecast():
    """현실적인 예측 생성 - 안정적이고 단순한 버전"""
    
    # 기준 가격 (2025년 8월 현실적 가격)
    base_prices = {
        'gasoline': 1650,  # 휘발유
        'diesel': 1490     # 경유
    }
    
    # 지역별 조정 계수 (현실적 범위)
    regional_multipliers = {
        'seoul': {'gasoline': 1.015, 'diesel': 1.010},     
        'busan': {'gasoline': 0.998, 'diesel': 0.995},      
        'daegu': {'gasoline': 1.000, 'diesel': 0.998},      
        'incheon': {'gasoline': 1.008, 'diesel': 1.005},    
        'gwangju': {'gasoline': 0.995, 'diesel': 0.992},    
        'daejeon': {'gasoline': 0.997, 'diesel': 0.994},    
        'ulsan': {'gasoline': 0.985, 'diesel': 0.980},      
        'sejong': {'gasoline': 1.005, 'diesel': 1.002},     
        'gyeonggi': {'gasoline': 1.012, 'diesel': 1.008},   
        'gangwon': {'gasoline': 1.025, 'diesel': 1.020},    
        'chungbuk': {'gasoline': 1.000, 'diesel': 0.995},   
        'chungnam': {'gasoline': 0.990, 'diesel': 0.985},   
        'jeonbuk': {'gasoline': 0.988, 'diesel': 0.983},    
        'jeonnam': {'gasoline': 0.985, 'diesel': 0.980},    
        'gyeongbuk': {'gasoline': 0.992, 'diesel': 0.987},  
        'gyeongnam': {'gasoline': 0.995, 'diesel': 0.990},  
        'jeju': {'gasoline': 1.040, 'diesel': 1.035}        
    }
    
    forecast_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "forecast_horizon_days": 28,
            "total_regions": 17,
            "model_version": "2.1.0_stable",
            "methodology": "한국 시장 현실화 모델 (주간 변동률 제한)"
        },
        "forecasts": {},
        "national_average": {}
    }
    
    # 각 지역별 예측 생성
    for region, multipliers in regional_multipliers.items():
        forecast_data["forecasts"][region] = {
            "gasoline": generate_fuel_forecast('gasoline', base_prices['gasoline'], multipliers['gasoline']),
            "diesel": generate_fuel_forecast('diesel', base_prices['diesel'], multipliers['diesel'])
        }
    
    # 전국 평균 계산
    forecast_data["national_average"] = calculate_national_average(forecast_data["forecasts"])
    
    return forecast_data

def generate_fuel_forecast(fuel_type, base_price, regional_multiplier):
    """연료별 예측 생성 - 안정적 버전"""
    current_price = base_price * regional_multiplier
    
    # 현실적인 주간 변동률 설정
    if fuel_type == 'gasoline':
        weekly_change = 0.004  # +0.4%/주
        daily_volatility = 0.001  # ±0.1%/일
    else:  # diesel
        weekly_change = -0.003  # -0.3%/주  
        daily_volatility = 0.0015  # ±0.15%/일
    
    daily_trend = weekly_change / 7  # 일간 트렌드
    
    forecasts = []
    price = current_price
    
    for day in range(28):
        # 작은 랜덤 변동 + 기본 트렌드
        random_change = random.uniform(-daily_volatility, daily_volatility)
        
        # 가격 계산 (안전한 방식)
        price_change_rate = daily_trend + random_change
        
        # 극단적 변화 방지
        if price_change_rate > 0.005:  # 최대 +0.5%/일
            price_change_rate = 0.005
        elif price_change_rate < -0.005:  # 최대 -0.5%/일
            price_change_rate = -0.005
        
        price = price * (1 + price_change_rate)
        
        # 가격 하한선 보장 (기준가의 80%)
        min_price = base_price * regional_multiplier * 0.8
        if price < min_price:
            price = min_price
        
        # 가격 상한선 보장 (기준가의 120%)    
        max_price = base_price * regional_multiplier * 1.2
        if price > max_price:
            price = max_price
        
        forecasts.append({
            "date": (datetime.now() + timedelta(days=day+1)).isoformat(),
            "price": round(price, 1)
        })
    
    return {
        "current_price": round(current_price, 1),
        "forecasts": forecasts
    }

def calculate_national_average(regional_forecasts):
    """전국 평균 계산"""
    national_avg = {}
    
    for fuel_type in ['gasoline', 'diesel']:
        # 현재 가격 평균
        current_prices = [data[fuel_type]['current_price'] for data in regional_forecasts.values()]
        avg_current = sum(current_prices) / len(current_prices)
        
        # 예측 가격 평균
        forecasts = []
        for day in range(28):
            day_prices = [data[fuel_type]['forecasts'][day]['price'] for data in regional_forecasts.values()]
            avg_price = sum(day_prices) / len(day_prices)
            
            forecasts.append({
                "date": (datetime.now() + timedelta(days=day+1)).isoformat(),
                "price": round(avg_price, 1)
            })
        
        national_avg[fuel_type] = {
            "current_price": round(avg_current, 1),
            "forecasts": forecasts
        }
    
    return national_avg

def main():
    print("현실적인 유가 예측 데이터 생성...")
    
    forecast_data = generate_realistic_forecast()
    
    # 결과 요약
    gasoline_current = forecast_data['national_average']['gasoline']['current_price']
    gasoline_week1 = forecast_data['national_average']['gasoline']['forecasts'][6]['price']  # 7일째
    gasoline_week4 = forecast_data['national_average']['gasoline']['forecasts'][27]['price']  # 28일째
    
    diesel_current = forecast_data['national_average']['diesel']['current_price']  
    diesel_week1 = forecast_data['national_average']['diesel']['forecasts'][6]['price']
    diesel_week4 = forecast_data['national_average']['diesel']['forecasts'][27]['price']
    
    gasoline_change_1w = ((gasoline_week1 - gasoline_current) / gasoline_current) * 100
    gasoline_change_4w = ((gasoline_week4 - gasoline_current) / gasoline_current) * 100
    diesel_change_1w = ((diesel_week1 - diesel_current) / diesel_current) * 100
    diesel_change_4w = ((diesel_week4 - diesel_current) / diesel_current) * 100
    
    print(f"\n예측 결과:")
    print(f"휘발유 현재: {gasoline_current}원")
    print(f"휘발유 1주후: {gasoline_week1}원 ({gasoline_change_1w:+.1f}%)")
    print(f"휘발유 4주후: {gasoline_week4}원 ({gasoline_change_4w:+.1f}%)")
    print(f"")
    print(f"경유 현재: {diesel_current}원")
    print(f"경유 1주후: {diesel_week1}원 ({diesel_change_1w:+.1f}%)")
    print(f"경유 4주후: {diesel_week4}원 ({diesel_change_4w:+.1f}%)")
    
    # 저장
    with open("backend/data/processed/current_forecast.json", 'w', encoding='utf-8') as f:
        json.dump(forecast_data, f, ensure_ascii=False, indent=2)
    
    print("\n데이터 저장 완료!")
    print("주요 개선사항:")
    print("- 현실적인 변동률: 휘발유 +0.4%/주, 경유 -0.3%/주")
    print("- 안정적인 예측 범위 (±20% 제한)")
    print("- 17개 지역별 차등화 적용")

if __name__ == "__main__":
    main()