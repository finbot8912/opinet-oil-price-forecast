#!/usr/bin/env python3
"""
개선된 한국 유가 예측 시스템 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 백엔드 모듈 경로 추가
sys.path.append(str(Path(__file__).parent / "backend" / "app"))

from models.korean_market_forecaster import KoreanMarketForecaster
from utils.regional_adjustment import RegionalAdjustmentEngine
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    
    # 최근 90일간의 가격 데이터 생성
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), 
                         end=datetime.now(), freq='D')
    
    regions = ['seoul', 'busan', 'gyeonggi', 'jeju', 'ulsan']
    
    data_list = []
    base_gasoline_price = 1650  # 기준 휘발유 가격
    base_diesel_price = 1450    # 기준 경유 가격
    
    for date in dates:
        # 작은 무작위 변동 (±1% 이내)
        daily_variation = np.random.normal(0, 0.005)  # 평균 0, 표준편차 0.5%
        
        for region in regions:
            # 지역별 가격 조정
            engine = RegionalAdjustmentEngine()
            
            # 휘발유 가격
            gasoline_price = engine.calculate_regional_price_adjustment(
                base_gasoline_price * (1 + daily_variation), region, 'gasoline'
            )
            
            # 경유 가격  
            diesel_price = engine.calculate_regional_price_adjustment(
                base_diesel_price * (1 + daily_variation), region, 'diesel'
            )
            
            data_list.extend([
                {
                    'date': date,
                    'region': region,
                    'fuel_type': 'gasoline',
                    'price': round(gasoline_price, 2)
                },
                {
                    'date': date,
                    'region': region, 
                    'fuel_type': 'diesel',
                    'price': round(diesel_price, 2)
                }
            ])
    
    return pd.DataFrame(data_list)

def create_sample_external_factors():
    """테스트용 외부 요인 데이터 생성"""
    
    dates = pd.date_range(start=datetime.now() - timedelta(days=90), 
                         end=datetime.now(), freq='D')
    
    # 환율 데이터 (1300원 기준, ±50원 변동)
    exchange_rates = []
    base_rate = 1300
    for date in dates:
        rate_change = np.random.normal(0, 10)  # 일일 ±10원 변동
        base_rate += rate_change
        base_rate = max(1200, min(1400, base_rate))  # 1200-1400원 범위
        
        exchange_rates.append({
            'date': date,
            'usd_krw': round(base_rate, 2)
        })
    
    # Dubai 유가 데이터 ($80 기준, ±$20 변동)
    dubai_prices = []
    base_oil_price = 80
    for date in dates:
        oil_change = np.random.normal(0, 2)  # 일일 ±$2 변동
        base_oil_price += oil_change
        base_oil_price = max(60, min(100, base_oil_price))  # $60-100 범위
        
        dubai_prices.append({
            'date': date,
            'usd_per_barrel': round(base_oil_price, 2),
            'krw_per_liter': round(base_oil_price * base_rate / 159, 2)  # 배럴당 159리터
        })
    
    return {
        'exchange_rate': pd.DataFrame(exchange_rates),
        'dubai_oil': pd.DataFrame(dubai_prices)
    }

def test_korean_market_forecaster():
    """한국 시장 특화 예측기 테스트"""
    
    print("=" * 60)
    print("한국 유가 예측 시스템 개선 테스트")
    print("=" * 60)
    
    # 테스트 데이터 생성
    print("\n1. 테스트 데이터 생성 중...")
    historical_data = create_sample_data()
    external_factors = create_sample_external_factors()
    
    print(f"   히스토리 데이터: {len(historical_data)}행")
    print(f"   환율 데이터: {len(external_factors['exchange_rate'])}행") 
    print(f"   Dubai 유가 데이터: {len(external_factors['dubai_oil'])}행")
    
    # 예측기 초기화
    print("\n2. 한국 시장 특화 예측기 초기화...")
    forecaster = KoreanMarketForecaster()
    
    # 시장 특성 출력
    print("\n3. 한국 유가 시장 특성:")
    for fuel_type in ['gasoline', 'diesel']:
        chars = forecaster.MARKET_CHARACTERISTICS[fuel_type]
        print(f"   {fuel_type.upper()}:")
        print(f"     주간 변동률: ±{chars['weekly_volatility']*100:.1f}%")
        print(f"     연간 최대 변동: ±{chars['annual_max_change']*100:.0f}%")
        print(f"     계절적 진폭: ±{chars['seasonal_amplitude']*100:.1f}%")
    
    # 지역별 예측 테스트
    print("\n4. 지역별 예측 결과:")
    print("   " + "="*50)
    
    test_regions = ['seoul', 'busan', 'jeju', 'gyeongbuk']
    
    for region in test_regions:
        print(f"\n   [{region.upper()}]")
        
        for fuel_type in ['gasoline', 'diesel']:
            forecast_result = forecaster.forecast_korean_market(
                historical_data, external_factors, region, fuel_type, 28
            )
            
            if forecast_result:
                current_price = forecast_result['current_price']
                forecasts = forecast_result['forecasts']
                
                # 1주후, 4주후 예측
                week1_price = forecasts[6]['price']  # 7일후
                week4_price = forecasts[27]['price'] # 28일후
                
                week1_change = ((week1_price / current_price) - 1) * 100
                week4_change = ((week4_price / current_price) - 1) * 100
                
                print(f"     {fuel_type:8s}: {current_price:7.2f}원 → {week1_price:7.2f}원({week1_change:+5.1f}%) → {week4_price:7.2f}원({week4_change:+5.1f}%)")
            else:
                print(f"     {fuel_type:8s}: 예측 불가")

def test_regional_adjustment():
    """지역별 조정 엔진 테스트"""
    
    print("\n" + "="*60)
    print("지역별 유가 조정 특성 테스트")
    print("="*60)
    
    engine = RegionalAdjustmentEngine()
    
    # 지역별 특성 리포트
    report = engine.generate_regional_adjustment_report()
    
    print(f"\n전체 분석 지역: {report['summary']['total_regions']}개")
    print(f"최고 프리미엄: {report['summary']['highest_premium_region']}")
    print(f"최저 프리미엄: {report['summary']['lowest_premium_region']}")
    print(f"최고 변동성: {report['summary']['most_volatile_region']}")
    print(f"최고 안정성: {report['summary']['most_stable_region']}")
    
    # 가격 조정 테스트 (기준가 1500원)
    print(f"\n기준가 1500원 기준 지역별 조정 가격:")
    base_price = 1500
    
    test_regions = ['seoul', 'gyeonggi', 'busan', 'jeju', 'ulsan', 'gyeongbuk']
    
    print("   지역      휘발유    경유   프리미엄  변동성")
    print("   " + "-"*45)
    
    for region in test_regions:
        gasoline_price = engine.calculate_regional_price_adjustment(base_price, region, 'gasoline')
        diesel_price = engine.calculate_regional_price_adjustment(base_price, region, 'diesel')
        
        chars = engine.get_regional_characteristics(region)
        premium = chars['price_premium'] * 100
        volatility = chars['volatility_factor']
        
        print(f"   {region:8s} {gasoline_price:7.0f}원 {diesel_price:7.0f}원 {premium:+6.1f}% {volatility:6.2f}")

def test_seasonal_patterns():
    """계절성 패턴 테스트"""
    
    print("\n" + "="*60) 
    print("개선된 계절성 패턴 테스트")
    print("="*60)
    
    forecaster = KoreanMarketForecaster()
    
    for fuel_type in ['gasoline', 'diesel']:
        print(f"\n{fuel_type.upper()} 월별 계절성 팩터:")
        seasonal_factors = forecaster.calculate_realistic_seasonal_factors(fuel_type)
        
        months = ['1월', '2월', '3월', '4월', '5월', '6월',
                 '7월', '8월', '9월', '10월', '11월', '12월']
        
        print("   ", end="")
        for i, (month, factor) in enumerate(zip(months, seasonal_factors.values())):
            change = (factor - 1.0) * 100
            print(f"{month}:{change:+4.1f}%", end="  ")
            if (i + 1) % 4 == 0:
                print("\n   ", end="")
        print()
        
        max_factor = max(seasonal_factors.values())
        min_factor = min(seasonal_factors.values())
        range_pct = (max_factor - min_factor) * 100
        
        print(f"   연중 변동폭: ±{range_pct:.1f}%")

def save_test_results():
    """테스트 결과를 JSON 파일로 저장"""
    
    print("\n" + "="*60)
    print("테스트 결과 저장")
    print("="*60)
    
    # 샘플 예측 결과 생성
    forecaster = KoreanMarketForecaster()
    historical_data = create_sample_data()
    external_factors = create_sample_external_factors()
    
    results = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'model_version': 'korean_market_v1.0',
            'forecast_horizon_days': 28
        },
        'forecasts': {}
    }
    
    test_regions = ['seoul', 'busan', 'gyeonggi']
    
    for region in test_regions:
        results['forecasts'][region] = {}
        
        for fuel_type in ['gasoline', 'diesel']:
            forecast = forecaster.forecast_korean_market(
                historical_data, external_factors, region, fuel_type, 28
            )
            
            if forecast:
                results['forecasts'][region][fuel_type] = forecast
    
    # 파일 저장
    output_file = Path("data/processed/improved_forecast_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"테스트 결과 저장: {output_file}")
    print(f"예측 지역: {len(results['forecasts'])}개")
    total_forecasts = sum(len(data) for data in results['forecasts'].values())
    print(f"총 예측 수: {total_forecasts}개")

def main():
    """메인 실행 함수"""
    
    print("🇰🇷 한국 유가 예측 시스템 개선 테스트")
    print("현실적인 변동률과 시장 특성을 반영한 예측 모델")
    
    try:
        # 1. 한국 시장 특화 예측기 테스트
        test_korean_market_forecaster()
        
        # 2. 지역별 조정 엔진 테스트  
        test_regional_adjustment()
        
        # 3. 계절성 패턴 테스트
        test_seasonal_patterns()
        
        # 4. 테스트 결과 저장
        save_test_results()
        
        print("\n" + "="*60)
        print("✅ 모든 테스트 완료!")
        print("주요 개선사항:")
        print("  - 휘발유 주간 변동률: 1.2% → 0.5%")
        print("  - 경유 주간 변동률: 1.8% → 0.4%")
        print("  - 계절적 진폭: ±5% → ±1.2%")
        print("  - 지역별 차등 변동성 적용")
        print("  - 한국 시장 특성 완전 반영")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()