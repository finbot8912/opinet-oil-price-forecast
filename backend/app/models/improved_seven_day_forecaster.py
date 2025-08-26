#!/usr/bin/env python3
"""
서울 지역 7일차 예측 정확도 개선을 위한 특화 모델
2025-08-21 개발 - 7일차 예측 오차 원인 분석 및 해결
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

class ImprovedSevenDayForecaster:
    """7일차 예측 특화 개선 모델"""
    
    def __init__(self):
        self.data_dir = Path("data/processed")
        
        # 7일차 특화 가중치 (기존 agents.md 분석 기반 재조정)
        self.SEVEN_DAY_WEIGHTS = {
            'dubai_oil': 0.15,      # 25% → 15% (시간지연 고려)
            'exchange_rate': 0.20,   # 15% → 20% (한국시장 핵심요인)
            'singapore_product': 0.06, # 8% → 6% (7일차에 영향 감소)
            'refinery_margin': 0.05,   # 7% → 5% (7일차에 영향 감소)
            'fuel_tax': 0.08,         # 12% → 8% (정책예측 한계)
            'import_price': 0.06,     # 8% → 6% (CIF기준 시간지연)
            'inventory': 0.08,        # 6% → 8% (국내요인 강화)
            'consumption': 0.07,      # 5% → 7% (국내요인 강화)
            'regional_consumption': 0.06, # 4% → 6% (지역특성 고려)
            'cpi': 0.04,             # 3% → 4% (경제요인 유지)
            'land_price': 0.02,      # 2% → 2% (장기요인)
            'vehicle_registration': 0.03, # 2% → 3% (수요예측 개선)
            'retail_margin': 0.06,   # 2% → 6% (유통요인 강화)
            'distribution_cost': 0.04 # 1% → 4% (물류비 고려)
        }
        
        # 7일차 특화 신뢰도 계산 파라미터
        self.CONFIDENCE_PARAMS = {
            'base_confidence': 0.75,    # 기존 0.92에서 현실적으로 하향
            'time_decay_rate': 0.025,   # 기존 0.015에서 상향 (더 빠른 감소)
            'volatility_penalty': 0.4,  # 기존 0.3에서 상향 (변동성 영향 증대)
            'min_confidence': 0.45      # 기존 0.6에서 하향 (현실적 하한선)
        }
        
        # 7일차 예측 개선을 위한 시장 특성 반영
        self.MARKET_DYNAMICS = {
            'seoul_premium': 1.08,      # 서울 지역 프리미엄 8%
            'weekday_effect': {         # 요일별 효과
                0: 1.02, 1: 1.00, 2: 0.98, 3: 0.99, 4: 1.01, 5: 1.03, 6: 1.02
            },
            'momentum_decay': 0.85,     # 추세 지속성 (7일 후 85%로 감소)
            'shock_absorption': 0.7     # 충격 흡수율 (한국 시장 안정성)
        }
    
    def load_historical_data(self) -> Optional[pd.DataFrame]:
        """개선된 데이터 로딩 (7일차 예측 특화)"""
        try:
            # 지역별 가격 데이터 로드
            regional_file = self.data_dir / "regional_gas_prices.json"
            with open(regional_file, 'r', encoding='utf-8') as f:
                regional_data = json.load(f)
            
            # 서울 지역 데이터만 추출
            seoul_data = []
            for record in regional_data['data']:
                date = record['date']
                seoul_gasoline = record['gasoline'].get('seoul', 0)
                seoul_diesel = record['diesel'].get('seoul', 0)
                
                if seoul_gasoline > 0:  # 유효한 데이터만
                    seoul_data.append({
                        'date': date,
                        'gasoline': seoul_gasoline,
                        'diesel': seoul_diesel
                    })
            
            df = pd.DataFrame(seoul_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 최근 2년 데이터로 제한 (COVID 이후 패턴 학습)
            cutoff_date = datetime.now() - timedelta(days=730)
            df = df[df['date'] >= cutoff_date]
            
            logger.info(f"서울 지역 데이터 로드 완료: {len(df)}행")
            return df
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            return None
    
    def load_external_factors(self) -> Dict:
        """외부 요인 데이터 로드"""
        factors = {}
        
        try:
            # Dubai 유가
            dubai_file = self.data_dir / "dubai_oil_prices.json"
            if dubai_file.exists():
                with open(dubai_file, 'r', encoding='utf-8') as f:
                    dubai_data = json.load(f)
                df = pd.DataFrame(dubai_data['data'])
                df['date'] = pd.to_datetime(df['date'])
                factors['dubai_oil'] = df
            
            # 환율
            exchange_file = self.data_dir / "exchange_rate.json"
            if exchange_file.exists():
                with open(exchange_file, 'r', encoding='utf-8') as f:
                    exchange_data = json.load(f)
                df = pd.DataFrame(exchange_data['data'])
                df['date'] = pd.to_datetime(df['date'])
                factors['exchange_rate'] = df
                
            logger.info(f"외부 요인 데이터 로드: {list(factors.keys())}")
            
        except Exception as e:
            logger.error(f"외부 요인 로드 실패: {e}")
        
        return factors
    
    def calculate_improved_trend(self, prices: pd.Series, window: int = 14) -> float:
        """개선된 추세 계산 (7일차 특화)"""
        if len(prices) < window:
            return 0.0
        
        recent_prices = prices.tail(window)
        
        # 1. 기본 선형 추세
        from sklearn.linear_model import LinearRegression
        X = np.arange(len(recent_prices)).reshape(-1, 1)
        y = recent_prices.values
        
        lr = LinearRegression()
        lr.fit(X, y)
        linear_trend = lr.coef_[0]
        
        # 2. 변동성 기반 조정
        volatility = recent_prices.pct_change().std()
        volatility_adjustment = min(volatility * 0.5, 0.02)  # 최대 2% 조정
        
        # 3. 평균 회귀 효과 (서울 지역 특화)
        mean_price = recent_prices.mean()
        current_price = recent_prices.iloc[-1]
        mean_reversion = -0.03 * (current_price - mean_price) / mean_price
        
        # 4. 모멘텀 감쇠 (7일차 특화)
        momentum_factor = self.MARKET_DYNAMICS['momentum_decay'] ** 7
        
        # 최종 추세 계산
        adjusted_trend = (linear_trend + mean_reversion) * momentum_factor
        
        # 현실적 범위 제한 (일일 ±0.5%)
        return np.clip(adjusted_trend, -0.005, 0.005)
    
    def calculate_seven_day_seasonality(self, date: datetime, fuel_type: str) -> float:
        """7일차 특화 계절성 계산"""
        month = date.month
        weekday = date.weekday()
        
        # 월별 계절성 (더 보수적으로 조정)
        monthly_factors = {
            1: -0.3, 2: -0.5, 3: -0.1, 4: 0.1, 5: 0.3, 6: 0.5,
            7: 0.8, 8: 0.6, 9: 0.3, 10: 0.0, 11: -0.2, 12: -0.3
        } if fuel_type == 'gasoline' else {
            1: 0.5, 2: 0.3, 3: 0.1, 4: -0.1, 5: -0.3, 6: -0.5,
            7: -0.7, 8: -0.5, 9: -0.2, 10: 0.1, 11: 0.3, 12: 0.5
        }
        
        # 요일별 효과
        weekday_factor = self.MARKET_DYNAMICS['weekday_effect'][weekday]
        
        # 7일차에는 계절성 영향 50% 감소
        seasonal_impact = monthly_factors.get(month, 0) * 0.003  # 0.3% 최대
        weekday_impact = (weekday_factor - 1.0) * 0.002  # 0.2% 최대
        
        return (seasonal_impact + weekday_impact) * 0.5  # 7일차 감쇠
    
    def calculate_external_impact(self, factors: Dict, days_ahead: int) -> float:
        """7일차 특화 외부 요인 영향 계산"""
        total_impact = 0.0
        
        # Dubai 유가 영향 (시간지연 고려)
        if 'dubai_oil' in factors:
            dubai_df = factors['dubai_oil']
            if not dubai_df.empty and len(dubai_df) >= 7:
                recent_oil = dubai_df.tail(7)['usd_per_barrel']
                oil_change = recent_oil.pct_change().mean()
                
                # 7일차에는 유가 영향 감소 및 시간지연 반영
                time_lag_factor = max(0.3, 1.0 - days_ahead * 0.1)  # 7일차: 30%
                oil_impact = oil_change * self.SEVEN_DAY_WEIGHTS['dubai_oil'] * time_lag_factor
                total_impact += oil_impact
        
        # 환율 영향 (한국 시장에서 가장 중요)
        if 'exchange_rate' in factors:
            exchange_df = factors['exchange_rate']
            if not exchange_df.empty and len(exchange_df) >= 7:
                recent_rate = exchange_df.tail(7)['usd_krw']
                rate_change = recent_rate.pct_change().mean()
                
                # 환율 영향은 7일차까지 지속
                rate_impact = rate_change * self.SEVEN_DAY_WEIGHTS['exchange_rate'] * 0.8
                total_impact += rate_impact
        
        # 충격 흡수 효과 적용 (한국 시장 안정성)
        total_impact *= self.MARKET_DYNAMICS['shock_absorption']
        
        # 최대 영향도 제한 (±1.5%)
        return np.clip(total_impact, -0.015, 0.015)
    
    def calculate_realistic_confidence(self, day_ahead: int, price_volatility: float, 
                                     prediction_error: float = 0.03) -> float:
        """현실적인 신뢰도 계산"""
        params = self.CONFIDENCE_PARAMS
        
        base = params['base_confidence']
        time_decay = params['time_decay_rate'] * day_ahead
        volatility_penalty = price_volatility * params['volatility_penalty']
        error_penalty = prediction_error * 0.5
        
        confidence = base - time_decay - volatility_penalty - error_penalty
        return max(confidence, params['min_confidence'])
    
    def forecast_seven_days_seoul(self, fuel_type: str = 'gasoline') -> Optional[Dict]:
        """서울 지역 7일 예측 (개선 모델)"""
        # 데이터 로드
        historical_df = self.load_historical_data()
        external_factors = self.load_external_factors()
        
        if historical_df is None or historical_df.empty:
            logger.error("히스토리 데이터가 없습니다")
            return None
        
        if fuel_type not in historical_df.columns:
            logger.error(f"{fuel_type} 데이터가 없습니다")
            return None
        
        # 기준 정보
        current_price = historical_df[fuel_type].iloc[-1]
        base_date = historical_df['date'].iloc[-1]
        price_series = historical_df[fuel_type]
        
        # 개선된 추세 계산
        trend = self.calculate_improved_trend(price_series)
        
        # 예측 생성
        forecasts = []
        
        for day in range(1, 8):  # 1-7일
            forecast_date = base_date + timedelta(days=day)
            
            # 1. 추세 컴포넌트
            trend_component = trend * current_price * day
            
            # 2. 계절성 컴포넌트
            seasonal_factor = self.calculate_seven_day_seasonality(forecast_date, fuel_type)
            seasonal_component = current_price * seasonal_factor
            
            # 3. 외부 요인 컴포넌트
            external_impact = self.calculate_external_impact(external_factors, day)
            external_component = current_price * external_impact
            
            # 4. 서울 지역 프리미엄 적용
            seoul_premium = (self.MARKET_DYNAMICS['seoul_premium'] - 1.0) * current_price * 0.1
            
            # 최종 예측 가격
            forecast_price = current_price + trend_component + seasonal_component + external_component + seoul_premium
            
            # 현실적 범위 제한 (일일 최대 ±2%)
            daily_limit = current_price * 0.02 * day
            forecast_price = np.clip(forecast_price, 
                                   current_price - daily_limit, 
                                   current_price + daily_limit)
            
            # 신뢰도 계산
            volatility = price_series.pct_change().std()
            confidence = self.calculate_realistic_confidence(day, volatility)
            
            forecasts.append({
                'date': forecast_date.isoformat(),
                'price': round(forecast_price, 2),
                'confidence': round(confidence, 3),
                'day_ahead': day,
                'components': {
                    'trend': round(trend_component, 2),
                    'seasonal': round(seasonal_component, 2),
                    'external': round(external_component, 2),
                    'seoul_premium': round(seoul_premium, 2)
                }
            })
        
        return {
            'region': 'seoul',
            'fuel_type': fuel_type,
            'current_price': round(current_price, 2),
            'base_date': base_date.isoformat(),
            'forecasts': forecasts,
            'model_info': {
                'version': '2.0_seven_day_optimized',
                'daily_trend': round(trend, 6),
                'volatility': round(volatility, 4),
                'confidence_method': 'improved_realistic',
                'weights_optimized_for': '7_day_accuracy'
            },
            'improvements': {
                'weight_adjustment': 'Reduced Dubai oil (25%→15%), Increased FX (15%→20%)',
                'confidence_calibration': 'Base 75%, more realistic decay',
                'trend_calculation': 'Momentum decay, mean reversion enhanced',
                'seoul_specific': 'Regional premium, weekday effects considered'
            }
        }
    
    def validate_seven_day_accuracy(self, historical_days: int = 90) -> Dict:
        """7일차 예측 정확도 검증"""
        historical_df = self.load_historical_data()
        if historical_df is None or len(historical_df) < historical_days + 7:
            return {}
        
        actual_7day = []
        predicted_7day = []
        confidence_7day = []
        
        # 과거 90일간 7일차 예측 시뮬레이션
        for i in range(historical_days):
            # 과거 i일 전까지의 데이터로 예측
            end_idx = len(historical_df) - historical_days + i
            past_data = historical_df.iloc[:end_idx]
            
            # 7일 후 실제 가격
            actual_idx = end_idx + 7
            if actual_idx < len(historical_df):
                actual_price = historical_df.iloc[actual_idx]['gasoline']
                
                # 예측 실행 (간단화)
                current_price = past_data['gasoline'].iloc[-1]
                trend = self.calculate_improved_trend(past_data['gasoline'])
                
                # 간단 예측 (실제 모델 축소 버전)
                predicted_price = current_price + (trend * current_price * 7)
                volatility = past_data['gasoline'].pct_change().std()
                confidence = self.calculate_realistic_confidence(7, volatility)
                
                actual_7day.append(actual_price)
                predicted_7day.append(predicted_price)
                confidence_7day.append(confidence)
        
        if not actual_7day:
            return {}
        
        # 정확도 지표 계산
        actual = np.array(actual_7day)
        predicted = np.array(predicted_7day)
        
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mae = np.mean(np.abs(actual - predicted))
        
        direction_accuracy = np.mean(np.sign(actual[1:] - actual[:-1]) == np.sign(predicted[1:] - predicted[:-1])) * 100
        
        return {
            'validation_period': f'{historical_days} days',
            'sample_size': len(actual_7day),
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'direction_accuracy': round(direction_accuracy, 2),
            'average_confidence': round(np.mean(confidence_7day), 3),
            'confidence_vs_accuracy': {
                'high_confidence_samples': sum(1 for c in confidence_7day if c > 0.6),
                'high_confidence_mape': round(np.mean([
                    abs((a - p) / a) * 100 for a, p, c in zip(actual, predicted, confidence_7day) if c > 0.6
                ]), 2) if any(c > 0.6 for c in confidence_7day) else 0
            }
        }

def main():
    """테스트 실행"""
    forecaster = ImprovedSevenDayForecaster()
    
    print("개선된 7일차 예측 모델 테스트")
    print("=" * 50)
    
    # 서울 지역 7일 예측
    result = forecaster.forecast_seven_days_seoul('gasoline')
    
    if result:
        print(f"\n서울 지역 휘발유 예측:")
        print(f"현재 가격: {result['current_price']}원")
        print(f"모델 버전: {result['model_info']['version']}")
        
        print(f"\n7일차 예측:")
        day7_forecast = result['forecasts'][6]  # 7일차 (인덱스 6)
        print(f"예측 가격: {day7_forecast['price']}원")
        print(f"신뢰도: {day7_forecast['confidence']*100:.1f}%")
        print(f"가격 변동: {day7_forecast['price'] - result['current_price']:+.2f}원")
        
        print(f"\n개선사항:")
        for key, value in result['improvements'].items():
            print(f"  {key}: {value}")
    
    # 정확도 검증
    print(f"\n과거 정확도 검증:")
    validation = forecaster.validate_seven_day_accuracy()
    if validation:
        print(f"MAPE: {validation['mape']:.1f}%")
        print(f"방향성 정확도: {validation['direction_accuracy']:.1f}%")
        print(f"평균 신뢰도: {validation['average_confidence']:.3f}")

if __name__ == "__main__":
    main()