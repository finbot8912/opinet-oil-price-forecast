#!/usr/bin/env python3
"""
한국 유가 시장 특성을 반영한 개선된 예측 모델
한국석유공사 오피넷 데이터 및 연구 결과 기반
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KoreanMarketForecaster:
    """한국 유가 시장 특성을 반영한 예측 클래스"""
    
    def __init__(self):
        self.data_dir = Path("data/processed")
        
        # 한국 유가 시장 특성 상수
        self.MARKET_CHARACTERISTICS = {
            'gasoline': {
                'weekly_volatility': 0.005,  # 주간 변동률 0.5%
                'monthly_max_change': 0.03,  # 월간 최대 변동 3%
                'annual_max_change': 0.15,   # 연간 최대 변동 15%
                'seasonal_amplitude': 0.012, # 계절적 진폭 1.2%
                'mean_reversion_speed': 0.02, # 평균 회귀 속도
                'policy_stability_factor': 0.95 # 정책적 안정화 효과
            },
            'diesel': {
                'weekly_volatility': 0.004,  # 주간 변동률 0.4%
                'monthly_max_change': 0.025, # 월간 최대 변동 2.5%
                'annual_max_change': 0.12,   # 연간 최대 변동 12%
                'seasonal_amplitude': 0.010, # 계절적 진폭 1.0%
                'mean_reversion_speed': 0.025, # 평균 회귀 속도 (경유가 더 안정적)
                'policy_stability_factor': 0.93 # 정책적 안정화 효과
            }
        }
        
        # 외부 요인 영향도 (한국 연구 결과 기반)
        self.EXTERNAL_FACTORS = {
            'exchange_rate_weight': 0.45,    # 환율 영향도 (증대)
            'international_oil_weight': 0.25, # 국제유가 영향도 (감소)
            'domestic_demand_weight': 0.20,   # 국내 수요 영향도
            'policy_effect_weight': 0.10      # 정책 효과 영향도
        }
    
    def calculate_realistic_seasonal_factors(self, fuel_type: str) -> Dict[int, float]:
        """한국 유가의 실제 계절성 패턴 반영"""
        
        if fuel_type == "gasoline":
            # 휘발유: 여름 드라이빙 시즌, 명절 수요 반영
            base_factors = {
                1: -0.5,   # 1월: 신정 이후 수요 감소
                2: -0.7,   # 2월: 겨울철 최저 수요
                3: -0.2,   # 3월: 봄철 회복 시작
                4: 0.2,    # 4월: 봄철 나들이 증가
                5: 0.5,    # 5월: 봄철 성수기
                6: 0.8,    # 6월: 여름철 진입
                7: 1.2,    # 7월: 여름 휴가철 피크
                8: 1.0,    # 8월: 휴가철 지속
                9: 0.5,    # 9월: 추석 등 명절 수요
                10: 0.0,   # 10월: 평균 수준
                11: -0.3,  # 11월: 겨울 진입
                12: -0.5   # 12월: 겨울철 수요 감소
            }
        else:  # diesel
            # 경유: 겨울 난방 수요, 물류 성수기 반영
            base_factors = {
                1: 0.8,    # 1월: 겨울 난방 수요 증가
                2: 0.6,    # 2월: 난방 수요 지속
                3: 0.3,    # 3월: 난방 수요 감소 시작
                4: -0.2,   # 4월: 봄철 수요 감소
                5: -0.5,   # 5월: 봄철 최저점
                6: -0.7,   # 6월: 여름철 최저 수요
                7: -1.0,   # 7월: 여름철 최저점
                8: -0.7,   # 8월: 여름철 지속
                9: -0.3,   # 9월: 가을철 회복 시작
                10: 0.2,   # 10월: 물류 성수기 시작
                11: 0.5,   # 11월: 겨울 준비 수요 증가
                12: 0.7    # 12월: 겨울철 수요 증가
            }
        
        # 기본 요인을 실제 계절성 진폭으로 변환
        amplitude = self.MARKET_CHARACTERISTICS[fuel_type]['seasonal_amplitude']
        return {month: 1.0 + (factor / 100) * amplitude for month, factor in base_factors.items()}
    
    def calculate_volatility_adjusted_trend(self, historical_prices: pd.Series, fuel_type: str) -> float:
        """변동성을 고려한 현실적 추세 계산"""
        
        if len(historical_prices) < 30:
            return 0.0
        
        # 최근 30일 데이터로 추세 계산
        recent_prices = historical_prices.tail(30)
        
        # 선형 회귀로 기본 추세 계산
        from sklearn.linear_model import LinearRegression
        X = np.arange(len(recent_prices)).reshape(-1, 1)
        y = recent_prices.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        base_trend = model.coef_[0]  # 일일 변화율
        
        # 한국 시장 특성에 맞는 추세 제한
        characteristics = self.MARKET_CHARACTERISTICS[fuel_type]
        max_daily_trend = characteristics['weekly_volatility'] / 7
        
        # 추세를 현실적 범위로 제한
        realistic_trend = np.clip(base_trend, -max_daily_trend, max_daily_trend)
        
        # 평균 회귀 효과 적용
        mean_price = recent_prices.mean()
        current_price = recent_prices.iloc[-1]
        
        # 현재가가 평균에서 많이 벗어나면 평균 회귀 압력 증가
        deviation_ratio = (current_price - mean_price) / mean_price
        mean_reversion_adjustment = -deviation_ratio * characteristics['mean_reversion_speed']
        
        final_trend = realistic_trend + mean_reversion_adjustment
        
        return final_trend
    
    def apply_korean_market_constraints(self, forecast_prices: List[float], 
                                      current_price: float, fuel_type: str) -> List[float]:
        """한국 시장 특성을 반영한 가격 제약 조건 적용"""
        
        characteristics = self.MARKET_CHARACTERISTICS[fuel_type]
        constrained_prices = []
        
        daily_volatility_limit = characteristics['weekly_volatility'] / 7
        cumulative_change_limit = characteristics['annual_max_change'] / 365 * len(forecast_prices)
        
        for i, price in enumerate(forecast_prices):
            constrained_price = price
            
            # 1. 일일 변동성 제한
            if i > 0:
                prev_price = constrained_prices[i-1]
                max_daily_change = prev_price * daily_volatility_limit
                
                if abs(constrained_price - prev_price) > max_daily_change:
                    if constrained_price > prev_price:
                        constrained_price = prev_price + max_daily_change
                    else:
                        constrained_price = prev_price - max_daily_change
            
            # 2. 누적 변동성 제한
            cumulative_change = abs(constrained_price - current_price) / current_price
            if cumulative_change > cumulative_change_limit:
                if constrained_price > current_price:
                    constrained_price = current_price * (1 + cumulative_change_limit)
                else:
                    constrained_price = current_price * (1 - cumulative_change_limit)
            
            # 3. 절대적 안정성 보장 (±50% 제한)
            constrained_price = np.clip(constrained_price, 
                                      current_price * 0.5, 
                                      current_price * 1.5)
            
            constrained_prices.append(constrained_price)
        
        return constrained_prices
    
    def calculate_korean_external_factors(self, factors_data: Dict, days_ahead: int) -> float:
        """한국 시장 연구 결과를 반영한 외부 요인 조정"""
        
        total_adjustment = 0.0
        
        # 1. 환율 영향 (한국에서 가장 중요한 요인)
        if 'exchange_rate' in factors_data:
            exchange_df = factors_data['exchange_rate']
            if not exchange_df.empty:
                recent_rates = exchange_df.tail(14)['usd_krw']  # 최근 2주
                if len(recent_rates) > 1:
                    rate_change = recent_rates.pct_change().mean()
                    # 시간 지연 효과 고려 (환율 변동이 유가에 반영되는 시차)
                    time_decay = max(0.8, 1.0 - days_ahead * 0.01)
                    exchange_effect = rate_change * self.EXTERNAL_FACTORS['exchange_rate_weight'] * time_decay
                    total_adjustment += exchange_effect
        
        # 2. 국제 유가 영향 (제한적 직접 영향)
        if 'dubai_oil' in factors_data:
            dubai_df = factors_data['dubai_oil']
            if not dubai_df.empty:
                recent_oil = dubai_df.tail(10)['usd_per_barrel'].dropna()
                if len(recent_oil) > 1:
                    oil_change = recent_oil.pct_change().mean()
                    # 국제유가 영향은 상대적으로 제한적
                    oil_effect = oil_change * self.EXTERNAL_FACTORS['international_oil_weight']
                    total_adjustment += oil_effect
        
        # 3. 정책 안정화 효과
        policy_stabilization = 0.95  # 한국 정부의 유가 안정화 정책 효과
        total_adjustment *= policy_stabilization
        
        # 4. 조정값 현실적 범위 제한
        max_adjustment = 0.02  # ±2%
        return np.clip(total_adjustment, -max_adjustment, max_adjustment)
    
    def forecast_korean_market(self, historical_data: pd.DataFrame, 
                             external_factors: Dict, region: str, fuel_type: str, 
                             forecast_days: int = 28) -> Optional[Dict]:
        """한국 시장 특성을 완전히 반영한 예측"""
        
        region_fuel_data = historical_data[
            (historical_data['region'] == region) & 
            (historical_data['fuel_type'] == fuel_type)
        ].sort_values('date')
        
        if region_fuel_data.empty or len(region_fuel_data) < 30:
            logger.warning(f"충분한 데이터가 없음: {region} {fuel_type}")
            return None
        
        # 현재 가격 및 기본 정보
        current_price = region_fuel_data['price'].iloc[-1]
        base_date = region_fuel_data['date'].iloc[-1]
        
        # 한국 시장 특성 반영 추세 계산
        trend = self.calculate_volatility_adjusted_trend(region_fuel_data['price'], fuel_type)
        
        # 계절성 팩터 계산
        seasonal_factors = self.calculate_realistic_seasonal_factors(fuel_type)
        
        # 예측 생성
        forecasts = []
        forecast_prices = []
        
        for day in range(1, forecast_days + 1):
            forecast_date = base_date + timedelta(days=day)
            
            # 1. 기본 추세 적용
            trend_component = trend * day
            
            # 2. 계절성 조정
            seasonal_factor = seasonal_factors.get(forecast_date.month, 1.0)
            seasonal_adjustment = (seasonal_factor - 1.0) * current_price
            
            # 3. 외부 요인 반영
            external_adjustment = self.calculate_korean_external_factors(external_factors, day)
            external_component = current_price * external_adjustment
            
            # 4. 최종 가격 계산
            forecast_price = current_price + trend_component + seasonal_adjustment + external_component
            forecast_prices.append(forecast_price)
        
        # 한국 시장 제약 조건 적용
        constrained_prices = self.apply_korean_market_constraints(
            forecast_prices, current_price, fuel_type
        )
        
        # 결과 생성
        for i, price in enumerate(constrained_prices):
            forecast_date = base_date + timedelta(days=i+1)
            
            # 신뢰도 계산 (한국 시장 안정성 반영)
            base_confidence = 0.92  # 한국 시장의 높은 안정성
            time_decay = 0.015 * (i + 1)  # 시간에 따른 신뢰도 감소
            volatility = region_fuel_data['price'].pct_change().std()
            volatility_penalty = volatility * 0.3
            
            confidence = max(base_confidence - time_decay - volatility_penalty, 0.6)
            
            forecasts.append({
                'date': forecast_date.isoformat(),
                'price': round(price, 2),
                'confidence': round(confidence, 3),
                'factors': {
                    'trend': round(trend * (i+1), 2),
                    'seasonal': round((seasonal_factors.get(forecast_date.month, 1.0) - 1.0) * current_price, 2),
                    'external': round(current_price * self.calculate_korean_external_factors(external_factors, i+1), 2)
                }
            })
        
        return {
            'region': region,
            'fuel_type': fuel_type,
            'current_price': round(current_price, 2),
            'forecasts': forecasts,
            'model_characteristics': {
                'daily_trend': round(trend, 6),
                'volatility': round(region_fuel_data['price'].pct_change().std(), 4),
                'mean_reversion_speed': self.MARKET_CHARACTERISTICS[fuel_type]['mean_reversion_speed'],
                'seasonal_amplitude': self.MARKET_CHARACTERISTICS[fuel_type]['seasonal_amplitude']
            }
        }

def main():
    """테스트 실행"""
    forecaster = KoreanMarketForecaster()
    
    print("한국 유가 시장 특성 분석")
    print("=" * 50)
    
    for fuel_type in ['gasoline', 'diesel']:
        characteristics = forecaster.MARKET_CHARACTERISTICS[fuel_type]
        seasonal_factors = forecaster.calculate_realistic_seasonal_factors(fuel_type)
        
        print(f"\n{fuel_type.upper()} 특성:")
        print(f"  주간 변동률: ±{characteristics['weekly_volatility']*100:.1f}%")
        print(f"  월간 최대 변동: ±{characteristics['monthly_max_change']*100:.1f}%") 
        print(f"  연간 최대 변동: ±{characteristics['annual_max_change']*100:.1f}%")
        print(f"  계절적 진폭: ±{characteristics['seasonal_amplitude']*100:.1f}%")
        
        print(f"  계절성 팩터 (최고/최저):")
        max_month = max(seasonal_factors.items(), key=lambda x: x[1])
        min_month = min(seasonal_factors.items(), key=lambda x: x[1])
        print(f"    최고: {max_month[0]}월 ({max_month[1]:.3f})")
        print(f"    최저: {min_month[0]}월 ({min_month[1]:.3f})")

if __name__ == "__main__":
    main()