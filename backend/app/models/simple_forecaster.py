#!/usr/bin/env python3
"""
간단한 유가 예측 모델
기존 데이터를 활용한 실용적인 예측 시스템
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleOilPriceForecaster:
    """간단한 유가 예측 클래스"""
    
    def __init__(self):
        self.data_dir = Path("data/processed")
        self.regions = [
            "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", 
            "ulsan", "gyeonggi", "gangwon", "chungbuk", "chungnam", 
            "jeonbuk", "jeonnam", "gyeongbuk", "gyeongnam", "jeju", "sejong"
        ]
    
    def load_regional_data(self):
        """지역별 가격 데이터 로드"""
        try:
            with open(self.data_dir / "regional_gas_prices.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df_list = []
            for record in data["data"]:
                if record["date"] and (record["gasoline"] or record["diesel"]):
                    # 휘발유 가격
                    for region, price in record["gasoline"].items():
                        df_list.append({
                            "date": record["date"],
                            "region": region,
                            "fuel_type": "gasoline",
                            "price": price
                        })
                    
                    # 경유 가격  
                    for region, price in record["diesel"].items():
                        df_list.append({
                            "date": record["date"],
                            "region": region,
                            "fuel_type": "diesel", 
                            "price": price
                        })
            
            df = pd.DataFrame(df_list)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(['date', 'region', 'fuel_type'])
            
            logger.info(f"지역별 데이터 로드 완료: {len(df)}행")
            return df
            
        except Exception as e:
            logger.error(f"지역별 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_external_factors(self):
        """외부 요인 데이터 로드"""
        factors = {}
        
        # 환율 데이터
        try:
            with open(self.data_dir / "exchange_rate.json", 'r', encoding='utf-8') as f:
                exchange_data = json.load(f)
            
            exchange_df = pd.DataFrame(exchange_data["data"])
            if not exchange_df.empty:
                exchange_df['date'] = pd.to_datetime(exchange_df['date'])
                factors['exchange_rate'] = exchange_df
                logger.info(f"환율 데이터: {len(exchange_df)}행")
        except:
            logger.warning("환율 데이터 로드 실패")
        
        # Dubai 유가 (사용 가능한 경우)
        try:
            with open(self.data_dir / "dubai_oil_prices.json", 'r', encoding='utf-8') as f:
                dubai_data = json.load(f)
            
            dubai_df = pd.DataFrame(dubai_data["data"])
            if not dubai_df.empty:
                dubai_df['date'] = pd.to_datetime(dubai_df['date'])
                dubai_df = dubai_df.dropna(subset=['krw_per_liter', 'usd_per_barrel'], how='all')
                factors['dubai_oil'] = dubai_df
                logger.info(f"Dubai 유가 데이터: {len(dubai_df)}행")
        except:
            logger.warning("Dubai 유가 데이터 로드 실패")
        
        return factors
    
    def calculate_trend(self, prices: pd.Series, days: int = 30):
        """가격 추세 계산"""
        if len(prices) < days:
            return 0
        
        recent_prices = prices.tail(days)
        
        # 선형 회귀를 통한 추세 계산
        from sklearn.linear_model import LinearRegression
        
        X = np.arange(len(recent_prices)).reshape(-1, 1)
        y = recent_prices.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        return model.coef_[0]  # 기울기 (일일 변화율)
    
    def seasonal_adjustment(self, date: datetime, base_price: float, fuel_type: str):
        """현실적인 계절성 조정 - 한국 유가 시장 특성 반영"""
        month = date.month
        
        # 한국 유가의 실제 계절적 변동성 반영 (±2% 이내)
        if fuel_type == "gasoline":
            # 휘발유: 여름 드라이빙 시즌과 명절 수요 반영
            seasonal_factors = {
                1: 0.995, 2: 0.993, 3: 0.998,  # 겨울 (미세 하락)
                4: 1.002, 5: 1.005, 6: 1.008,  # 봄->여름 (수요 증가)
                7: 1.012, 8: 1.010, 9: 1.005,  # 여름 (피크 시즌)
                10: 1.000, 11: 0.997, 12: 0.995  # 가을->겨울 (수요 감소)
            }
        else:  # diesel
            # 경유: 겨울 난방 수요와 물류 성수기 반영
            seasonal_factors = {
                1: 1.008, 2: 1.006, 3: 1.003,  # 겨울 (난방 수요)
                4: 0.998, 5: 0.995, 6: 0.993,  # 봄->여름 (수요 감소)
                7: 0.990, 8: 0.993, 9: 0.997,  # 여름 (최저점)
                10: 1.002, 11: 1.005, 12: 1.007  # 가을->겨울 (수요 증가)
            }
        
        return base_price * seasonal_factors.get(month, 1.0)
    
    def forecast_region_fuel(self, df: pd.DataFrame, region: str, fuel_type: str, 
                           factors: dict, forecast_days: int = 28):
        """특정 지역/연료 예측"""
        
        # 해당 지역/연료 데이터 필터링
        region_fuel_data = df[
            (df['region'] == region) & (df['fuel_type'] == fuel_type)
        ].sort_values('date')
        
        if region_fuel_data.empty:
            return None
        
        # 최근 데이터
        recent_data = region_fuel_data.tail(90)  # 최근 90일
        if len(recent_data) < 5:
            return None
        
        # 현재 가격 (최신)
        current_price = recent_data['price'].iloc[-1]
        
        # 추세 계산
        trend = self.calculate_trend(recent_data['price'])
        
        # 변동성 계산
        volatility = recent_data['price'].pct_change().std() * np.sqrt(252)  # 연간화
        
        # 기본 예측 생성
        forecasts = []
        base_date = recent_data['date'].iloc[-1]
        
        # 한국 유가 시장 특성을 반영한 현실적 변동성 적용
        weekly_volatility_limit = 0.005 if fuel_type == "gasoline" else 0.004  # 휘발유 0.5%, 경유 0.4%
        daily_volatility_limit = weekly_volatility_limit / 7
        
        # 누적 변동성 추적
        cumulative_change = 0.0
        max_cumulative_change = 0.15 if fuel_type == "gasoline" else 0.12  # 연간 최대 변동
        
        for day in range(1, forecast_days + 1):
            forecast_date = base_date + timedelta(days=day)
            
            # 추세를 현실적 범위로 제한
            limited_trend = max(min(trend, daily_volatility_limit), -daily_volatility_limit)
            trend_component = limited_trend * day
            
            # 평균 회귀 효과 추가 (가격이 과도하게 벗어나면 평균으로 회귀)
            mean_reversion_factor = 0.02  # 2% 평균 회귀
            if abs(trend_component) > weekly_volatility_limit * (day / 7):
                trend_component *= (1 - mean_reversion_factor * day / 28)
            
            # 계절성 조정 (기본가격 기준)
            seasonal_price = self.seasonal_adjustment(
                forecast_date, current_price, fuel_type
            )
            
            # 추세 반영
            base_forecast = seasonal_price + trend_component
            
            # 외부 요인 반영 (제한적)
            external_adjustment = self.get_external_adjustment(factors, forecast_date)
            external_adjustment = max(min(external_adjustment, 0.02), -0.02)  # ±2% 제한
            
            final_price = base_forecast * (1 + external_adjustment)
            
            # 현실적 범위 제한 - 한국 유가 시장 특성
            max_daily_change = current_price * daily_volatility_limit
            min_price = current_price * (1 - max_cumulative_change)
            max_price = current_price * (1 + max_cumulative_change)
            
            final_price = max(final_price, min_price)
            final_price = min(final_price, max_price)
            
            # 일일 변동 제한
            if day > 1:
                prev_price = forecasts[-1]['price']
                max_daily_price = prev_price * (1 + daily_volatility_limit)
                min_daily_price = prev_price * (1 - daily_volatility_limit)
                final_price = max(min(final_price, max_daily_price), min_daily_price)
            
            # 누적 변동성 업데이트
            cumulative_change = abs(final_price - current_price) / current_price
            
            forecasts.append({
                'date': forecast_date.isoformat(),
                'price': round(final_price, 2),
                'confidence': self.calculate_confidence(day, volatility)
            })
        
        return {
            'region': region,
            'fuel_type': fuel_type,
            'current_price': round(current_price, 2),
            'trend': round(trend, 4),
            'volatility': round(volatility, 4),
            'forecasts': forecasts
        }
    
    def get_external_adjustment(self, factors: dict, target_date: datetime):
        """외부 요인 기반 조정 - 한국 시장 특성 반영"""
        adjustment = 0.0
        
        # 환율 영향 (한국 시장에서 더 중요한 요인)
        if 'exchange_rate' in factors:
            exchange_df = factors['exchange_rate']
            recent_rates = exchange_df.tail(10)['usd_krw']
            if len(recent_rates) > 1:
                rate_change = recent_rates.pct_change().mean()
                # 한국 연구 결과: 환율이 가격변동성에 양(+) 영향
                adjustment += rate_change * 0.45  # 환율 변화의 45% 반영 (증대)
        
        # Dubai 유가 영향 (직접 영향은 제한적)
        if 'dubai_oil' in factors:
            dubai_df = factors['dubai_oil']
            recent_oil = dubai_df.tail(10)['usd_per_barrel'].dropna()
            if len(recent_oil) > 1:
                oil_change = recent_oil.pct_change().mean()
                # 한국 연구 결과: 국제유가는 변동성에 직접적 영향 제한
                adjustment += oil_change * 0.25  # 국제유가 변화의 25% 반영 (감소)
        
        # 정책적 안정화 효과 반영 (한국 특성)
        policy_stabilization = 0.95  # 5% 안정화 효과
        adjustment *= policy_stabilization
        
        return min(max(adjustment, -0.03), 0.03)  # ±3% 제한 (현실적 범위)
    
    def calculate_confidence(self, days_ahead: int, volatility: float):
        """예측 신뢰도 계산"""
        # 예측 기간이 길수록, 변동성이 클수록 신뢰도 감소
        base_confidence = 0.95
        time_decay = 0.02 * days_ahead  # 하루당 2% 감소
        volatility_penalty = volatility * 0.5
        
        confidence = base_confidence - time_decay - volatility_penalty
        return max(confidence, 0.5)  # 최소 50%
    
    def generate_forecast(self, forecast_days: int = 28):
        """전체 예측 생성"""
        logger.info("유가 예측 시작...")
        
        # 데이터 로드
        df = self.load_regional_data()
        factors = self.load_external_factors()
        
        if df.empty:
            logger.error("예측 데이터가 없습니다")
            return {}
        
        # 결과 구조
        results = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'forecast_horizon_days': forecast_days,
                'total_regions': len(self.regions),
                'fuel_types': ['gasoline', 'diesel']
            },
            'forecasts': {}
        }
        
        # 각 지역/연료별 예측
        total_forecasts = 0
        for region in self.regions:
            results['forecasts'][region] = {}
            
            for fuel_type in ['gasoline', 'diesel']:
                forecast = self.forecast_region_fuel(
                    df, region, fuel_type, factors, forecast_days
                )
                
                if forecast:
                    results['forecasts'][region][fuel_type] = forecast
                    total_forecasts += 1
                    logger.info(f"{region} {fuel_type} 예측 완료")
        
        logger.info(f"총 {total_forecasts}개 예측 완료")
        
        # 전국 평균 계산
        results['national_average'] = self.calculate_national_average(results['forecasts'])
        
        return results
    
    def calculate_national_average(self, regional_forecasts: dict):
        """전국 평균 계산"""
        national_avg = {}
        
        for fuel_type in ['gasoline', 'diesel']:
            prices_by_date = {}
            
            # 모든 지역의 예측 가격 수집
            for region, region_data in regional_forecasts.items():
                if fuel_type in region_data and 'forecasts' in region_data[fuel_type]:
                    for forecast in region_data[fuel_type]['forecasts']:
                        date = forecast['date']
                        price = forecast['price']
                        
                        if date not in prices_by_date:
                            prices_by_date[date] = []
                        prices_by_date[date].append(price)
            
            # 날짜별 평균 계산
            avg_forecasts = []
            for date, prices in sorted(prices_by_date.items()):
                if prices:
                    avg_forecasts.append({
                        'date': date,
                        'price': round(np.mean(prices), 2),
                        'min_price': round(min(prices), 2),
                        'max_price': round(max(prices), 2),
                        'std_dev': round(np.std(prices), 2)
                    })
            
            if avg_forecasts:
                # 현재가 계산
                current_prices = []
                for region_data in regional_forecasts.values():
                    if fuel_type in region_data:
                        current_prices.append(region_data[fuel_type]['current_price'])
                
                national_avg[fuel_type] = {
                    'current_price': round(np.mean(current_prices), 2) if current_prices else 0,
                    'forecasts': avg_forecasts
                }
        
        return national_avg
    
    def save_forecast(self, forecast_data: dict, filename: str = "oil_price_forecast.json"):
        """예측 결과 저장"""
        output_path = self.data_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(forecast_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"예측 결과 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"저장 실패: {e}")
            return False

def main():
    """메인 실행"""
    forecaster = SimpleOilPriceForecaster()
    
    # 4주 예측 생성
    forecast_data = forecaster.generate_forecast(forecast_days=28)
    
    if forecast_data:
        # 결과 저장
        forecaster.save_forecast(forecast_data)
        
        # 요약 출력
        print("\n" + "="*60)
        print("유가 예측 결과 요약")
        print("="*60)
        
        metadata = forecast_data.get('metadata', {})
        print(f"예측 생성 시간: {metadata.get('generated_at', 'N/A')}")
        print(f"예측 기간: {metadata.get('forecast_horizon_days', 0)}일")
        
        # 전국 평균 출력
        national = forecast_data.get('national_average', {})
        if national:
            print("\n[전국 평균 가격 전망]")
            for fuel_type, data in national.items():
                if 'forecasts' in data and data['forecasts']:
                    current = data['current_price']
                    first_forecast = data['forecasts'][0]['price']
                    last_forecast = data['forecasts'][-1]['price']
                    
                    print(f"{fuel_type.upper()}:")
                    print(f"  현재가: {current}원")
                    print(f"  1일 후: {first_forecast}원")  
                    print(f"  4주 후: {last_forecast}원")
                    print(f"  변화율: {((last_forecast/current-1)*100):+.1f}%")
        
        print("="*60)
    
    else:
        print("예측 생성 실패")

if __name__ == "__main__":
    main()