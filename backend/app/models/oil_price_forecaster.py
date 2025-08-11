#!/usr/bin/env python3
"""
유가 예측 모델
시계열 분석 + 머신러닝을 결합한 앙상블 예측 시스템
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 시계열 분석
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# 머신러닝
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

# 딥러닝 (TensorFlow/Keras)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("TensorFlow not available. Using traditional models only.")

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OilPriceForecaster:
    """유가 예측 모델 클래스"""
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        
        # 모델 성능 추적
        self.model_performance = {}
        
        # 지역 목록
        self.regions = [
            "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", 
            "ulsan", "gyeonggi", "gangwon", "chungbuk", "chungnam", 
            "jeonbuk", "jeonnam", "gyeongbuk", "gyeongnam", "jeju", "sejong"
        ]
        
        # COVID-19 기간 (이상치 제거용)
        self.covid_period = {
            "start": "2020-01-01",
            "end": "2021-12-31"
        }
    
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """처리된 JSON 데이터를 로드"""
        logger.info("데이터 로딩 시작...")
        
        data_files = {
            "regional": "regional_gas_prices.json",
            "national": "national_gas_prices.json", 
            "dubai_oil": "dubai_oil_prices.json",
            "exchange_rate": "exchange_rate.json",
            "fuel_tax": "fuel_tax.json"
        }
        
        datasets = {}
        
        for key, filename in data_files.items():
            try:
                filepath = self.data_dir / filename
                with open(filepath, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                df = pd.DataFrame(json_data["data"])
                if not df.empty and "date" in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df = df.dropna(subset=['date'])
                    df = df.sort_values('date')
                    datasets[key] = df
                    logger.info(f"{key} 데이터 로드 완료: {len(df)}행")
                
            except Exception as e:
                logger.error(f"{key} 데이터 로드 실패: {e}")
        
        return datasets
    
    def create_features(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """특징 엔지니어링"""
        logger.info("특징 엔지니어링 시작...")
        
        # 기본 데이터프레임 생성 (전국 가격 기준)
        if "national" not in datasets:
            raise ValueError("전국 가격 데이터가 없습니다")
        
        df = datasets["national"].copy()
        df = df[df['date'] >= '2010-01-01'].copy()
        
        # COVID-19 기간 제외
        covid_mask = (df['date'] >= self.covid_period['start']) & (df['date'] <= self.covid_period['end'])
        df = df[~covid_mask].copy()
        
        # 1. 시계열 특징
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        # 계절성 특징
        df['season'] = df['month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'autumn', 10: 'autumn', 11: 'autumn'
        })
        
        # 원-핫 인코딩
        season_dummies = pd.get_dummies(df['season'], prefix='season')
        df = pd.concat([df, season_dummies], axis=1)
        
        # 2. 이동평균 및 지연 특징
        for fuel in ['gasoline', 'diesel']:
            if fuel in df.columns:
                # 이동평균 (7일, 30일)
                df[f'{fuel}_ma7'] = df[fuel].rolling(window=7, min_periods=1).mean()
                df[f'{fuel}_ma30'] = df[fuel].rolling(window=30, min_periods=1).mean()
                
                # 지연 특징 (1일, 7일, 30일 전)
                for lag in [1, 7, 30]:
                    df[f'{fuel}_lag{lag}'] = df[fuel].shift(lag)
                
                # 변화율
                df[f'{fuel}_pct_change'] = df[fuel].pct_change()
                df[f'{fuel}_diff'] = df[fuel].diff()
        
        # 3. 외부 요인 추가
        df = self._add_external_factors(df, datasets)
        
        # 4. 결측치 처리
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        logger.info(f"특징 엔지니어링 완료: {len(df)}행, {len(df.columns)}열")
        return df
    
    def _add_external_factors(self, df: pd.DataFrame, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """외부 요인 추가"""
        
        # Dubai 유가
        if "dubai_oil" in datasets:
            dubai_df = datasets["dubai_oil"].copy()
            dubai_df = dubai_df.groupby('date').agg({
                'krw_per_liter': 'mean',
                'usd_per_barrel': 'mean'
            }).reset_index()
            
            df = df.merge(dubai_df, on='date', how='left')
            
            # Dubai 유가 이동평균
            for col in ['krw_per_liter', 'usd_per_barrel']:
                if col in df.columns:
                    df[f'dubai_{col}_ma7'] = df[col].rolling(window=7, min_periods=1).mean()
                    df[f'dubai_{col}_ma30'] = df[col].rolling(window=30, min_periods=1).mean()
        
        # 환율
        if "exchange_rate" in datasets:
            exchange_df = datasets["exchange_rate"].copy()
            exchange_df = exchange_df.groupby('date')['usd_krw'].mean().reset_index()
            
            df = df.merge(exchange_df, on='date', how='left')
            
            # 환율 특징
            if 'usd_krw' in df.columns:
                df['usd_krw_ma7'] = df['usd_krw'].rolling(window=7, min_periods=1).mean()
                df['usd_krw_ma30'] = df['usd_krw'].rolling(window=30, min_periods=1).mean()
                df['usd_krw_volatility'] = df['usd_krw'].rolling(window=30).std()
        
        # 유류세 (최신 세율 적용)
        if "fuel_tax" in datasets:
            tax_df = datasets["fuel_tax"].copy()
            if not tax_df.empty:
                latest_tax = tax_df.iloc[-1]
                df['gasoline_tax_rate'] = latest_tax['gasoline']['total'] if 'gasoline' in latest_tax else 0
                df['diesel_tax_rate'] = latest_tax['diesel']['total'] if 'diesel' in latest_tax else 0
        
        return df
    
    def prepare_ml_data(self, df: pd.DataFrame, target_col: str, 
                       forecast_horizon: int = 28) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """머신러닝용 데이터 준비"""
        
        # 특징 선택 (숫자형 컬럼만)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 타겟 컬럼 제외
        if target_col in numeric_cols:
            numeric_cols.remove(target_col)
        
        # 날짜 관련 컬럼 제외
        exclude_cols = ['year', 'month', 'quarter', 'day_of_year', 'week_of_year']
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        # 특징 매트릭스 생성
        X = df[feature_cols].values
        y = df[target_col].values
        
        # 결측치 처리
        from sklearn.impute import SimpleImputer
        imputer = SimpleImputer(strategy='mean')
        X = imputer.fit_transform(X)
        
        # 미래 예측용 시퀀스 생성
        X_sequences = []
        y_sequences = []
        
        sequence_length = 30  # 30일 시퀀스
        
        for i in range(sequence_length, len(X) - forecast_horizon + 1):
            X_sequences.append(X[i-sequence_length:i])
            y_sequences.append(y[i:i+forecast_horizon])
        
        return np.array(X_sequences), np.array(y_sequences), feature_cols
    
    def build_lstm_model(self, sequence_length: int, n_features: int, 
                        forecast_horizon: int) -> Optional[object]:
        """LSTM 모델 구축"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(sequence_length, n_features)),
            Dropout(0.2),
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            Dense(50, activation='relu'),
            Dense(forecast_horizon)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), 
                     loss='mse', 
                     metrics=['mae'])
        
        return model
    
    def train_models(self, df: pd.DataFrame, target_col: str = 'gasoline') -> Dict:
        """모델 학습"""
        logger.info(f"{target_col} 예측 모델 학습 시작...")
        
        # 데이터 준비
        X, y, feature_cols = self.prepare_ml_data(df, target_col)
        
        if len(X) == 0:
            logger.error("학습 데이터가 부족합니다")
            return {}
        
        # 데이터 분할 (시계열 고려)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # 정규화
        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
        X_test_scaled = scaler_X.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
        
        scaler_y = MinMaxScaler()
        y_train_scaled = scaler_y.fit_transform(y_train)
        y_test_scaled = scaler_y.transform(y_test)
        
        self.scalers[f'{target_col}_X'] = scaler_X
        self.scalers[f'{target_col}_y'] = scaler_y
        
        models = {}
        performance = {}
        
        # 1. Random Forest
        logger.info("Random Forest 학습...")
        rf_X_train = X_train.mean(axis=1)  # 시퀀스를 평균으로 축소
        rf_X_test = X_test.mean(axis=1)
        rf_y_train = y_train.mean(axis=1)  # 다중 출력을 평균으로 축소
        rf_y_test = y_test.mean(axis=1)
        
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        rf_model.fit(rf_X_train, rf_y_train)
        
        rf_pred = rf_model.predict(rf_X_test)
        performance['random_forest'] = {
            'mae': mean_absolute_error(rf_y_test, rf_pred),
            'rmse': np.sqrt(mean_squared_error(rf_y_test, rf_pred)),
            'r2': r2_score(rf_y_test, rf_pred)
        }
        models['random_forest'] = rf_model
        
        # 특징 중요도 저장
        self.feature_importance[f'{target_col}_rf'] = dict(zip(feature_cols, rf_model.feature_importances_))
        
        # 2. Gradient Boosting
        logger.info("Gradient Boosting 학습...")
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        gb_model.fit(rf_X_train, rf_y_train)
        
        gb_pred = gb_model.predict(rf_X_test)
        performance['gradient_boosting'] = {
            'mae': mean_absolute_error(rf_y_test, gb_pred),
            'rmse': np.sqrt(mean_squared_error(rf_y_test, gb_pred)),
            'r2': r2_score(rf_y_test, gb_pred)
        }
        models['gradient_boosting'] = gb_model
        
        # 3. LSTM (TensorFlow 사용 가능한 경우)
        if TENSORFLOW_AVAILABLE:
            logger.info("LSTM 학습...")
            lstm_model = self.build_lstm_model(
                sequence_length=X_train.shape[1], 
                n_features=X_train.shape[2], 
                forecast_horizon=y_train.shape[1]
            )
            
            if lstm_model:
                # 조기 종료 설정
                early_stopping = tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss', patience=10, restore_best_weights=True
                )
                
                history = lstm_model.fit(
                    X_train_scaled, y_train_scaled,
                    validation_data=(X_test_scaled, y_test_scaled),
                    epochs=50, batch_size=32, verbose=0,
                    callbacks=[early_stopping]
                )
                
                lstm_pred = lstm_model.predict(X_test_scaled)
                lstm_pred = scaler_y.inverse_transform(lstm_pred)
                
                performance['lstm'] = {
                    'mae': mean_absolute_error(y_test.flatten(), lstm_pred.flatten()),
                    'rmse': np.sqrt(mean_squared_error(y_test.flatten(), lstm_pred.flatten())),
                    'r2': r2_score(y_test.flatten(), lstm_pred.flatten())
                }
                models['lstm'] = lstm_model
        
        self.models[target_col] = models
        self.model_performance[target_col] = performance
        
        # 성능 출력
        logger.info(f"{target_col} 모델 성능:")
        for model_name, perf in performance.items():
            logger.info(f"  {model_name}: MAE={perf['mae']:.2f}, RMSE={perf['rmse']:.2f}, R²={perf['r2']:.3f}")
        
        return models
    
    def ensemble_predict(self, models: Dict, X_new: np.ndarray, target_col: str) -> np.ndarray:
        """앙상블 예측"""
        predictions = []
        weights = []
        
        for model_name, model in models.items():
            if model_name in ['random_forest', 'gradient_boosting']:
                # 시퀀스를 평균으로 축소
                X_reduced = X_new.mean(axis=1) if len(X_new.shape) == 3 else X_new
                pred = model.predict(X_reduced)
                
                # 다중 출력으로 확장 (28일 예측)
                pred = np.repeat(pred.reshape(-1, 1), 28, axis=1)
                
            elif model_name == 'lstm' and TENSORFLOW_AVAILABLE:
                # 정규화
                scaler_X = self.scalers[f'{target_col}_X']
                scaler_y = self.scalers[f'{target_col}_y']
                
                X_scaled = scaler_X.transform(X_new.reshape(-1, X_new.shape[-1])).reshape(X_new.shape)
                pred_scaled = model.predict(X_scaled)
                pred = scaler_y.inverse_transform(pred_scaled)
            
            else:
                continue
            
            predictions.append(pred)
            
            # 성능 기반 가중치
            if target_col in self.model_performance:
                perf = self.model_performance[target_col].get(model_name, {})
                weight = 1 / (1 + perf.get('mae', 1))  # MAE가 낮을수록 높은 가중치
                weights.append(weight)
            else:
                weights.append(1.0)
        
        if not predictions:
            return np.array([])
        
        # 가중 평균
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        ensemble_pred = np.average(predictions, axis=0, weights=weights)
        return ensemble_pred
    
    def forecast(self, df: pd.DataFrame, forecast_horizon: int = 28) -> Dict:
        """4주 예측 실행"""
        logger.info(f"{forecast_horizon}일 예측 시작...")
        
        forecasts = {}
        
        for fuel_type in ['gasoline', 'diesel']:
            if fuel_type not in df.columns:
                continue
                
            logger.info(f"{fuel_type} 예측 중...")
            
            # 모델 학습
            models = self.train_models(df, fuel_type)
            
            if not models:
                continue
            
            # 최근 데이터로 예측
            X, _, _ = self.prepare_ml_data(df, fuel_type, forecast_horizon)
            
            if len(X) == 0:
                continue
            
            # 가장 최근 시퀀스 사용
            X_latest = X[-1:] 
            
            # 앙상블 예측
            prediction = self.ensemble_predict(models, X_latest, fuel_type)
            
            if len(prediction) > 0:
                # 날짜 생성
                last_date = df['date'].iloc[-1]
                forecast_dates = pd.date_range(
                    start=last_date + timedelta(days=1),
                    periods=forecast_horizon,
                    freq='D'
                ).tolist()
                
                forecasts[fuel_type] = {
                    'dates': [d.isoformat() for d in forecast_dates],
                    'prices': prediction[0].tolist() if len(prediction.shape) > 1 else prediction.tolist(),
                    'confidence_intervals': self._calculate_confidence_intervals(prediction[0] if len(prediction.shape) > 1 else prediction),
                    'model_performance': self.model_performance.get(fuel_type, {}),
                    'feature_importance': self.feature_importance.get(f'{fuel_type}_rf', {})
                }
        
        return forecasts
    
    def _calculate_confidence_intervals(self, predictions: np.ndarray, confidence: float = 0.95) -> Dict:
        """신뢰구간 계산"""
        # 간단한 신뢰구간 (표준편차 기반)
        std = np.std(predictions)
        margin = 1.96 * std  # 95% 신뢰구간
        
        return {
            'lower': (predictions - margin).tolist(),
            'upper': (predictions + margin).tolist(),
            'confidence_level': confidence
        }
    
    def save_model(self, filepath: str):
        """모델 저장"""
        import pickle
        
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'feature_importance': self.feature_importance,
            'model_performance': self.model_performance,
            'regions': self.regions
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"모델 저장 완료: {filepath}")
    
    def load_model(self, filepath: str):
        """모델 로드"""
        import pickle
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.models = model_data['models']
        self.scalers = model_data['scalers']
        self.feature_importance = model_data['feature_importance']
        self.model_performance = model_data['model_performance']
        self.regions = model_data['regions']
        
        logger.info(f"모델 로드 완료: {filepath}")

def main():
    """메인 실행 함수"""
    # 예측 모델 초기화
    forecaster = OilPriceForecaster()
    
    # 데이터 로드
    datasets = forecaster.load_data()
    
    if not datasets:
        logger.error("데이터를 로드할 수 없습니다")
        return
    
    # 특징 생성
    df = forecaster.create_features(datasets)
    
    # 4주 예측 실행
    forecasts = forecaster.forecast(df, forecast_horizon=28)
    
    # 결과 저장
    output_file = "data/processed/oil_price_forecasts.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(forecasts, f, ensure_ascii=False, indent=2)
    
    logger.info(f"예측 결과 저장: {output_file}")
    
    # 결과 출력
    print("\n" + "="*60)
    print("유가 예측 결과 요약")
    print("="*60)
    
    for fuel_type, forecast in forecasts.items():
        print(f"\n{fuel_type.upper()} 예측:")
        print(f"  예측 기간: {len(forecast['dates'])}일")
        
        if forecast['prices']:
            current_price = forecast['prices'][0]
            avg_price = np.mean(forecast['prices'])
            print(f"  1일 후 예상가: {current_price:.0f}원")
            print(f"  4주 평균가: {avg_price:.0f}원")
            
        if forecast['model_performance']:
            best_model = min(forecast['model_performance'].items(), 
                           key=lambda x: x[1].get('mae', float('inf')))
            print(f"  최고 성능 모델: {best_model[0]} (MAE: {best_model[1]['mae']:.2f})")

if __name__ == "__main__":
    main()