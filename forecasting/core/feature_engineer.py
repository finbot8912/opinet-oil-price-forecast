"""
Feature Engineering for Oil Price Forecasting
Advanced feature extraction with petroleum industry expertise
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from scipy import stats
import holidays
import logging
from dataclasses import dataclass

from ..config.model_config import FeatureConfig

logger = logging.getLogger(__name__)

@dataclass
class FeatureEngineeringResult:
    """특징 엔지니어링 결과"""
    feature_data: pd.DataFrame
    feature_importance: Dict[str, float]
    feature_categories: Dict[str, List[str]]
    engineering_summary: Dict[str, Any]

class FeatureEngineer:
    """
    석유업계 전문 특징 엔지니어링
    - 시계열 기반 lag, rolling, diff 특징
    - 계절성 및 휴일 특징
    - 외부 요인 (국제유가, 환율, 유류세) 특징
    - 지역별 특성 및 가격 스프레드 특징
    - 기술적 지표 특징
    """
    
    def __init__(self, config: FeatureConfig):
        self.config = config
        self.feature_categories = {
            'time_series': [],
            'seasonal': [],
            'external': [],
            'regional': [],
            'technical': [],
            'interaction': []
        }
        
        # 한국 휴일 정보
        self.korean_holidays = holidays.SouthKorea(years=range(2010, 2030))
        
        logger.info("FeatureEngineer 초기화 완료")
    
    def create_features(self, df: pd.DataFrame, 
                       target_column: str,
                       external_columns: Optional[List[str]] = None) -> FeatureEngineeringResult:
        """
        전체 특징 엔지니어링 파이프라인
        
        Args:
            df: 입력 데이터프레임
            target_column: 예측 대상 컬럼
            external_columns: 외부 요인 컬럼들
        
        Returns:
            FeatureEngineeringResult
        """
        logger.info(f"특징 엔지니어링 시작: {target_column}")
        
        feature_df = df.copy()
        
        # 1. 시계열 기반 특징
        feature_df = self._create_time_series_features(feature_df, target_column)
        
        # 2. 계절성 및 달력 특징
        feature_df = self._create_seasonal_features(feature_df)
        
        # 3. 외부 요인 특징
        if external_columns:
            feature_df = self._create_external_features(feature_df, external_columns)
        
        # 4. 기술적 지표 특징
        feature_df = self._create_technical_indicators(feature_df, target_column)
        
        # 5. 지역별 특성 특징 (해당하는 경우)
        if self.config.regional_clustering:
            feature_df = self._create_regional_features(feature_df, target_column)
        
        # 6. 상호작용 특징
        feature_df = self._create_interaction_features(feature_df, target_column)
        
        # 7. 특징 중요도 계산
        feature_importance = self._calculate_feature_importance(feature_df, target_column)
        
        # 8. 특징 선택
        selected_features = self._select_features(feature_df, target_column, feature_importance)
        feature_df = feature_df[selected_features + [target_column]]
        
        logger.info(f"특징 엔지니어링 완료: {len(feature_df.columns)-1}개 특징 생성")
        
        engineering_summary = {
            'total_features': len(feature_df.columns) - 1,
            'feature_categories': {k: len(v) for k, v in self.feature_categories.items()},
            'date_range': {
                'start': feature_df.index.min().isoformat(),
                'end': feature_df.index.max().isoformat()
            }
        }
        
        return FeatureEngineeringResult(
            feature_data=feature_df,
            feature_importance=feature_importance,
            feature_categories=self.feature_categories,
            engineering_summary=engineering_summary
        )
    
    def _create_time_series_features(self, df: pd.DataFrame, 
                                   target_column: str) -> pd.DataFrame:
        """시계열 기반 특징 생성"""
        logger.info("시계열 특징 생성...")
        
        feature_df = df.copy()
        
        # Lag 특징
        for lag in self.config.lag_features:
            col_name = f'{target_column}_lag_{lag}'
            feature_df[col_name] = feature_df[target_column].shift(lag)
            self.feature_categories['time_series'].append(col_name)
        
        # Rolling 통계 특징
        for window in self.config.rolling_features:
            # Rolling mean
            col_name = f'{target_column}_ma_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).mean()
            self.feature_categories['time_series'].append(col_name)
            
            # Rolling std
            col_name = f'{target_column}_std_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).std()
            self.feature_categories['time_series'].append(col_name)
            
            # Rolling min/max
            col_name = f'{target_column}_min_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).min()
            self.feature_categories['time_series'].append(col_name)
            
            col_name = f'{target_column}_max_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).max()
            self.feature_categories['time_series'].append(col_name)
            
            # Rolling median
            col_name = f'{target_column}_median_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).median()
            self.feature_categories['time_series'].append(col_name)
        
        # Difference 특징
        for diff_lag in self.config.diff_features:
            col_name = f'{target_column}_diff_{diff_lag}'
            feature_df[col_name] = feature_df[target_column].diff(diff_lag)
            self.feature_categories['time_series'].append(col_name)
            
            # Percentage change
            col_name = f'{target_column}_pct_change_{diff_lag}'
            feature_df[col_name] = feature_df[target_column].pct_change(diff_lag)
            self.feature_categories['time_series'].append(col_name)
        
        # 변동성 특징
        for window in [7, 14, 30]:
            col_name = f'{target_column}_volatility_{window}'
            feature_df[col_name] = feature_df[target_column].rolling(window=window).std() / \
                                 feature_df[target_column].rolling(window=window).mean()
            self.feature_categories['time_series'].append(col_name)
        
        return feature_df
    
    def _create_seasonal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """계절성 및 달력 특징 생성"""
        logger.info("계절성 특징 생성...")
        
        feature_df = df.copy()
        
        if not isinstance(feature_df.index, pd.DatetimeIndex):
            return feature_df
        
        # 기본 달력 특징
        feature_df['year'] = feature_df.index.year
        feature_df['month'] = feature_df.index.month
        feature_df['day'] = feature_df.index.day
        feature_df['dayofweek'] = feature_df.index.dayofweek
        feature_df['dayofyear'] = feature_df.index.dayofyear
        feature_df['week'] = feature_df.index.isocalendar().week
        feature_df['quarter'] = feature_df.index.quarter
        
        # 순환적 특징 (월, 요일 등)
        feature_df['month_sin'] = np.sin(2 * np.pi * feature_df['month'] / 12)
        feature_df['month_cos'] = np.cos(2 * np.pi * feature_df['month'] / 12)
        feature_df['dayofweek_sin'] = np.sin(2 * np.pi * feature_df['dayofweek'] / 7)
        feature_df['dayofweek_cos'] = np.cos(2 * np.pi * feature_df['dayofweek'] / 7)
        feature_df['dayofyear_sin'] = np.sin(2 * np.pi * feature_df['dayofyear'] / 365)
        feature_df['dayofyear_cos'] = np.cos(2 * np.pi * feature_df['dayofyear'] / 365)
        
        seasonal_features = [
            'year', 'month', 'day', 'dayofweek', 'dayofyear', 'week', 'quarter',
            'month_sin', 'month_cos', 'dayofweek_sin', 'dayofweek_cos',
            'dayofyear_sin', 'dayofyear_cos'
        ]
        self.feature_categories['seasonal'].extend(seasonal_features)
        
        # 계절 특징 (석유업계 특화)
        feature_df['is_winter'] = feature_df['month'].isin([12, 1, 2]).astype(int)  # 난방 수요 증가
        feature_df['is_summer'] = feature_df['month'].isin([6, 7, 8]).astype(int)  # 휴가철 수요 증가
        feature_df['is_spring'] = feature_df['month'].isin([3, 4, 5]).astype(int)
        feature_df['is_autumn'] = feature_df['month'].isin([9, 10, 11]).astype(int)
        
        # 휴일 특징
        if self.config.holiday_features:
            feature_df['is_holiday'] = feature_df.index.map(
                lambda x: 1 if x in self.korean_holidays else 0
            )
            feature_df['is_weekend'] = (feature_df['dayofweek'] >= 5).astype(int)
            
            # 휴일 전후 효과
            feature_df['days_to_holiday'] = self._calculate_days_to_holiday(feature_df.index)
            feature_df['days_after_holiday'] = self._calculate_days_after_holiday(feature_df.index)
            
            holiday_features = ['is_winter', 'is_summer', 'is_spring', 'is_autumn',
                              'is_holiday', 'is_weekend', 'days_to_holiday', 'days_after_holiday']
            self.feature_categories['seasonal'].extend(holiday_features)
        
        return feature_df
    
    def _create_external_features(self, df: pd.DataFrame, 
                                external_columns: List[str]) -> pd.DataFrame:
        """외부 요인 특징 생성"""
        logger.info("외부 요인 특징 생성...")
        
        feature_df = df.copy()
        
        for col in external_columns:
            if col not in feature_df.columns:
                continue
            
            # 기본 lag 특징
            if 'oil' in col.lower() or 'dubai' in col.lower():
                lags = self.config.oil_price_lags
            elif 'exchange' in col.lower() or 'rate' in col.lower():
                lags = self.config.exchange_rate_lags
            else:
                lags = [0, 1, 2, 3]
            
            for lag in lags:
                if lag == 0:
                    continue
                col_name = f'{col}_lag_{lag}'
                feature_df[col_name] = feature_df[col].shift(lag)
                self.feature_categories['external'].append(col_name)
            
            # Rolling 통계
            for window in [7, 14, 30]:
                col_name = f'{col}_ma_{window}'
                feature_df[col_name] = feature_df[col].rolling(window=window).mean()
                self.feature_categories['external'].append(col_name)
                
                col_name = f'{col}_std_{window}'
                feature_df[col_name] = feature_df[col].rolling(window=window).std()
                self.feature_categories['external'].append(col_name)
            
            # 변화율 특징
            col_name = f'{col}_pct_change'
            feature_df[col_name] = feature_df[col].pct_change()
            self.feature_categories['external'].append(col_name)
            
            col_name = f'{col}_pct_change_7d'
            feature_df[col_name] = feature_df[col].pct_change(7)
            self.feature_categories['external'].append(col_name)
        
        return feature_df
    
    def _create_technical_indicators(self, df: pd.DataFrame, 
                                   target_column: str) -> pd.DataFrame:
        """기술적 지표 특징 생성"""
        logger.info("기술적 지표 생성...")
        
        feature_df = df.copy()
        price = feature_df[target_column]
        
        # RSI (Relative Strength Index)
        delta = price.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        feature_df['rsi_14'] = 100 - (100 / (1 + rs))
        self.feature_categories['technical'].append('rsi_14')
        
        # MACD (Moving Average Convergence Divergence)
        ema12 = price.ewm(span=12).mean()
        ema26 = price.ewm(span=26).mean()
        feature_df['macd'] = ema12 - ema26
        feature_df['macd_signal'] = feature_df['macd'].ewm(span=9).mean()
        feature_df['macd_histogram'] = feature_df['macd'] - feature_df['macd_signal']
        
        technical_features = ['macd', 'macd_signal', 'macd_histogram']
        self.feature_categories['technical'].extend(technical_features)
        
        # Bollinger Bands
        sma20 = price.rolling(window=20).mean()
        std20 = price.rolling(window=20).std()
        feature_df['bb_upper'] = sma20 + (2 * std20)
        feature_df['bb_lower'] = sma20 - (2 * std20)
        feature_df['bb_width'] = feature_df['bb_upper'] - feature_df['bb_lower']
        feature_df['bb_position'] = (price - feature_df['bb_lower']) / feature_df['bb_width']
        
        bb_features = ['bb_upper', 'bb_lower', 'bb_width', 'bb_position']
        self.feature_categories['technical'].extend(bb_features)
        
        # Momentum indicators
        feature_df['momentum_10'] = price / price.shift(10)
        feature_df['momentum_20'] = price / price.shift(20)
        feature_df['rate_of_change_10'] = (price - price.shift(10)) / price.shift(10) * 100
        
        momentum_features = ['momentum_10', 'momentum_20', 'rate_of_change_10']
        self.feature_categories['technical'].extend(momentum_features)
        
        return feature_df
    
    def _create_regional_features(self, df: pd.DataFrame, 
                                target_column: str) -> pd.DataFrame:
        """지역별 특성 특징 생성"""
        logger.info("지역별 특성 특징 생성...")
        
        feature_df = df.copy()
        
        # 가격 스프레드 특징 (전국 평균과의 차이)
        if 'national_' in target_column:
            # 이미 전국 평균 데이터인 경우 스킵
            return feature_df
        
        # 전국 평균 대비 스프레드 (추후 구현)
        # 현재는 기본적인 지역 특성만 구현
        
        return feature_df
    
    def _create_interaction_features(self, df: pd.DataFrame, 
                                   target_column: str) -> pd.DataFrame:
        """상호작용 특징 생성"""
        logger.info("상호작용 특징 생성...")
        
        feature_df = df.copy()
        
        # 국제유가 × 환율 상호작용
        oil_cols = [col for col in feature_df.columns if 'dubai' in col.lower() or 'oil' in col.lower()]
        exchange_cols = [col for col in feature_df.columns if 'exchange' in col.lower() or 'usd' in col.lower()]
        
        for oil_col in oil_cols[:2]:  # 처음 2개만 사용
            for exchange_col in exchange_cols[:2]:
                if oil_col in feature_df.columns and exchange_col in feature_df.columns:
                    col_name = f'{oil_col}_x_{exchange_col}'
                    feature_df[col_name] = feature_df[oil_col] * feature_df[exchange_col]
                    self.feature_categories['interaction'].append(col_name)
        
        # 계절성 × 가격 변동성 상호작용
        if 'month' in feature_df.columns:
            volatility_cols = [col for col in feature_df.columns if 'volatility' in col]
            for vol_col in volatility_cols[:2]:
                col_name = f'month_x_{vol_col}'
                feature_df[col_name] = feature_df['month'] * feature_df[vol_col]
                self.feature_categories['interaction'].append(col_name)
        
        return feature_df
    
    def _calculate_feature_importance(self, df: pd.DataFrame, 
                                    target_column: str) -> Dict[str, float]:
        """특징 중요도 계산"""
        logger.info("특징 중요도 계산...")
        
        # 결측값이 있는 행 제거
        clean_df = df.dropna()
        
        if len(clean_df) < 100:
            logger.warning("충분한 데이터가 없어 특징 중요도 계산 스킵")
            return {}
        
        feature_columns = [col for col in clean_df.columns if col != target_column]
        
        # 상관관계 기반 중요도
        correlations = {}
        for col in feature_columns:
            try:
                corr = abs(clean_df[col].corr(clean_df[target_column]))
                correlations[col] = corr if not np.isnan(corr) else 0.0
            except:
                correlations[col] = 0.0
        
        return correlations
    
    def _select_features(self, df: pd.DataFrame, 
                        target_column: str,
                        feature_importance: Dict[str, float]) -> List[str]:
        """특징 선택"""
        logger.info("특징 선택...")
        
        # 중요도 임계값 이상의 특징만 선택
        selected_features = [
            col for col, importance in feature_importance.items()
            if importance >= 0.01  # 최소 중요도 임계값
        ]
        
        # 중요도 순으로 정렬
        selected_features.sort(key=lambda x: feature_importance[x], reverse=True)
        
        # 최대 특징 수 제한
        max_features = min(100, len(selected_features))  # 최대 100개 특징
        selected_features = selected_features[:max_features]
        
        logger.info(f"특징 선택 완료: {len(selected_features)}개 선택")
        
        return selected_features
    
    def _calculate_days_to_holiday(self, date_index: pd.DatetimeIndex) -> pd.Series:
        """다음 휴일까지 남은 일수 계산"""
        days_to_holiday = []
        
        for date in date_index:
            future_dates = pd.date_range(start=date, end=date + timedelta(days=30), freq='D')
            holiday_distances = [
                (future_date - date).days 
                for future_date in future_dates 
                if future_date in self.korean_holidays
            ]
            
            days_to_holiday.append(min(holiday_distances) if holiday_distances else 30)
        
        return pd.Series(days_to_holiday, index=date_index)
    
    def _calculate_days_after_holiday(self, date_index: pd.DatetimeIndex) -> pd.Series:
        """가장 최근 휴일 이후 경과 일수 계산"""
        days_after_holiday = []
        
        for date in date_index:
            past_dates = pd.date_range(start=date - timedelta(days=30), end=date, freq='D')
            holiday_distances = [
                (date - past_date).days 
                for past_date in past_dates 
                if past_date in self.korean_holidays
            ]
            
            days_after_holiday.append(min(holiday_distances) if holiday_distances else 30)
        
        return pd.Series(days_after_holiday, index=date_index)