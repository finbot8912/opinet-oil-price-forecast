"""
Model Configuration for Oil Price Forecasting System
Optimized parameters based on 30 years of petroleum industry analysis
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DataConfig:
    """데이터 설정"""
    data_path: str = "data/processed"
    regional_file: str = "regional_gas_prices.json"
    dubai_file: str = "dubai_oil_prices.json"
    exchange_rate_file: str = "exchange_rate.json"
    fuel_tax_file: str = "fuel_tax.json"
    national_file: str = "national_gas_prices.json"
    
    # 지역별 코드
    regions: List[str] = None
    fuel_types: List[str] = None
    
    def __post_init__(self):
        if self.regions is None:
            self.regions = [
                "seoul", "busan", "daegu", "incheon", "gwangju", 
                "daejeon", "ulsan", "gyeonggi", "gangwon", "chungbuk",
                "chungnam", "jeonbuk", "jeonnam", "gyeongbuk", 
                "gyeongnam", "jeju", "sejong"
            ]
        if self.fuel_types is None:
            self.fuel_types = ["gasoline", "diesel"]

@dataclass
class TimeSeriesConfig:
    """시계열 분석 설정"""
    # 예측 기간
    forecast_horizon: int = 30  # 4-5주 (30일)
    
    # 시계열 분해
    decomposition_model: str = "multiplicative"  # additive, multiplicative
    seasonal_period: int = 365  # 연간 계절성
    weekly_period: int = 7      # 주간 계절성
    
    # 이상치 탐지
    outlier_method: str = "isolation_forest"  # z_score, iqr, isolation_forest
    outlier_threshold: float = 0.1
    
    # COVID-19 기간 처리
    covid_start: str = "2020-01-01"
    covid_end: str = "2022-06-30"
    covid_handling: str = "interpolate"  # remove, interpolate, weight

@dataclass
class ARIMAConfig:
    """ARIMA 모델 설정"""
    max_p: int = 5
    max_d: int = 2
    max_q: int = 5
    seasonal: bool = True
    seasonal_period: int = 365
    information_criterion: str = "aic"  # aic, bic
    method: str = "lbfgs"
    maxiter: int = 500
    
    # 자동 ARIMA 설정
    auto_arima: bool = True
    seasonal_test: str = "ch"  # ch, ocsb
    stepwise: bool = True
    suppress_warnings: bool = True

@dataclass
class LSTMConfig:
    """LSTM 모델 설정"""
    # 네트워크 구조
    hidden_size: int = 128
    num_layers: int = 3
    dropout: float = 0.2
    bidirectional: bool = True
    
    # 시퀀스 설정
    sequence_length: int = 60  # 60일 이력 데이터
    prediction_length: int = 30  # 30일 예측
    
    # 학습 설정
    batch_size: int = 32
    epochs: int = 200
    learning_rate: float = 0.001
    weight_decay: float = 1e-5
    patience: int = 20
    
    # 데이터 정규화
    scaler_type: str = "minmax"  # minmax, standard, robust
    
    # GPU 설정
    device: str = "auto"  # auto, cpu, cuda

@dataclass
class RandomForestConfig:
    """Random Forest 모델 설정"""
    n_estimators: int = 500
    max_depth: int = 20
    min_samples_split: int = 5
    min_samples_leaf: int = 2
    max_features: str = "sqrt"  # sqrt, log2, auto
    bootstrap: bool = True
    random_state: int = 42
    n_jobs: int = -1
    
    # 특징 중요도 임계값
    feature_importance_threshold: float = 0.01

@dataclass
class EnsembleConfig:
    """앙상블 모델 설정"""
    # 모델 가중치 (동적 조정)
    arima_weight: float = 0.3
    lstm_weight: float = 0.4
    rf_weight: float = 0.3
    
    # 가중치 조정 방법
    weight_method: str = "performance_based"  # equal, performance_based, adaptive
    
    # 성능 기반 가중치 조정
    performance_window: int = 90  # 90일 성능 윈도우
    min_weight: float = 0.1
    max_weight: float = 0.6

@dataclass
class ValidationConfig:
    """검증 설정"""
    # 교차 검증
    cv_folds: int = 5
    cv_method: str = "time_series"  # time_series, blocked
    test_size: float = 0.2
    validation_size: float = 0.1
    
    # 백테스팅
    backtest_periods: List[int] = None
    rolling_window: bool = True
    
    # 성능 지표
    metrics: List[str] = None
    target_accuracy: float = 0.95  # 95% 목표 정확도
    
    def __post_init__(self):
        if self.backtest_periods is None:
            self.backtest_periods = [30, 60, 90, 180]  # 다양한 백테스팅 기간
        if self.metrics is None:
            self.metrics = ["mape", "rmse", "mae", "r2", "directional_accuracy"]

@dataclass
class FeatureConfig:
    """특징 엔지니어링 설정"""
    # 시계열 특징
    lag_features: List[int] = None
    rolling_features: List[int] = None
    diff_features: List[int] = None
    
    # 계절성 특징
    seasonal_features: bool = True
    holiday_features: bool = True
    
    # 외부 요인 특징
    oil_price_lags: List[int] = None
    exchange_rate_lags: List[int] = None
    
    # 지역별 특징
    regional_clustering: bool = True
    price_spread_features: bool = True
    
    def __post_init__(self):
        if self.lag_features is None:
            self.lag_features = [1, 2, 3, 7, 14, 21, 30]
        if self.rolling_features is None:
            self.rolling_features = [7, 14, 30, 60]
        if self.diff_features is None:
            self.diff_features = [1, 7]
        if self.oil_price_lags is None:
            self.oil_price_lags = [0, 1, 2, 3, 7]
        if self.exchange_rate_lags is None:
            self.exchange_rate_lags = [0, 1, 2, 3]

class ModelConfigManager:
    """모델 설정 관리자"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.data = DataConfig()
        self.timeseries = TimeSeriesConfig()
        self.arima = ARIMAConfig()
        self.lstm = LSTMConfig()
        self.rf = RandomForestConfig()
        self.ensemble = EnsembleConfig()
        self.validation = ValidationConfig()
        self.features = FeatureConfig()
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """외부 설정 파일 로드"""
        # JSON 또는 YAML 설정 파일 로드 로직
        pass
    
    def save_config(self, config_path: str):
        """설정을 파일로 저장"""
        # JSON 또는 YAML로 설정 저장 로직
        pass
    
    def get_model_params(self, model_type: str) -> Dict[str, Any]:
        """모델별 파라미터 반환"""
        if model_type == "arima":
            return {
                "max_p": self.arima.max_p,
                "max_d": self.arima.max_d,
                "max_q": self.arima.max_q,
                "seasonal": self.arima.seasonal,
                "m": self.arima.seasonal_period,
                "information_criterion": self.arima.information_criterion,
                "method": self.arima.method,
                "maxiter": self.arima.maxiter
            }
        elif model_type == "lstm":
            return {
                "hidden_size": self.lstm.hidden_size,
                "num_layers": self.lstm.num_layers,
                "dropout": self.lstm.dropout,
                "bidirectional": self.lstm.bidirectional,
                "sequence_length": self.lstm.sequence_length,
                "batch_size": self.lstm.batch_size,
                "epochs": self.lstm.epochs,
                "learning_rate": self.lstm.learning_rate,
                "weight_decay": self.lstm.weight_decay,
                "patience": self.lstm.patience
            }
        elif model_type == "rf":
            return {
                "n_estimators": self.rf.n_estimators,
                "max_depth": self.rf.max_depth,
                "min_samples_split": self.rf.min_samples_split,
                "min_samples_leaf": self.rf.min_samples_leaf,
                "max_features": self.rf.max_features,
                "bootstrap": self.rf.bootstrap,
                "random_state": self.rf.random_state,
                "n_jobs": self.rf.n_jobs
            }
        else:
            raise ValueError(f"Unknown model type: {model_type}")

# 글로벌 설정 인스턴스
config = ModelConfigManager()