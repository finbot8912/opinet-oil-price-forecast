"""
Data Preprocessor for Oil Price Forecasting
Advanced preprocessing with petroleum industry domain knowledge
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
import logging
from dataclasses import dataclass

from ..config.model_config import TimeSeriesConfig

logger = logging.getLogger(__name__)

@dataclass
class PreprocessingResult:
    """전처리 결과"""
    processed_data: pd.DataFrame
    scaler_info: Dict[str, Any]
    outliers_removed: int
    missing_values_filled: int
    processing_summary: Dict[str, Any]

class DataPreprocessor:
    """
    석유업계 특화 데이터 전처리기
    - COVID-19 기간 등 이상 데이터 처리
    - 계절성 및 추세 고려한 결측값 보간
    - 유가 특성을 반영한 이상치 탐지
    - 다중 스케일링 전략
    """
    
    def __init__(self, config: TimeSeriesConfig):
        self.config = config
        self.scalers = {}
        self.imputers = {}
        
        # COVID-19 기간 정의
        self.covid_start = pd.to_datetime(config.covid_start)
        self.covid_end = pd.to_datetime(config.covid_end)
        
        logger.info("DataPreprocessor 초기화 완료")
    
    def preprocess_data(self, df: pd.DataFrame, 
                       target_columns: List[str],
                       feature_columns: Optional[List[str]] = None) -> PreprocessingResult:
        """
        전체 데이터 전처리 파이프라인
        
        Args:
            df: 원본 데이터프레임
            target_columns: 예측 대상 컬럼들
            feature_columns: 특징 컬럼들
        
        Returns:
            PreprocessingResult
        """
        logger.info("데이터 전처리 시작...")
        
        processed_df = df.copy()
        processing_summary = {}
        
        # 1. 날짜 인덱스 설정
        processed_df = self._setup_date_index(processed_df)
        processing_summary['date_setup'] = "완료"
        
        # 2. COVID-19 기간 처리
        covid_result = self._handle_covid_period(processed_df, target_columns)
        processed_df = covid_result['data']
        processing_summary['covid_handling'] = covid_result['summary']
        
        # 3. 이상치 탐지 및 처리
        outlier_result = self._handle_outliers(processed_df, target_columns)
        processed_df = outlier_result['data']
        processing_summary['outlier_handling'] = outlier_result['summary']
        
        # 4. 결측값 처리
        missing_result = self._handle_missing_values(processed_df, target_columns)
        processed_df = missing_result['data']
        processing_summary['missing_handling'] = missing_result['summary']
        
        # 5. 데이터 스케일링
        scaling_result = self._scale_data(processed_df, target_columns, feature_columns)
        processed_df = scaling_result['data']
        processing_summary['scaling'] = scaling_result['summary']
        
        # 6. 데이터 품질 검증
        quality_score = self._validate_processed_data(processed_df)
        processing_summary['quality_score'] = quality_score
        
        logger.info(f"데이터 전처리 완료: 품질 점수 {quality_score:.3f}")
        
        return PreprocessingResult(
            processed_data=processed_df,
            scaler_info=self.scalers,
            outliers_removed=outlier_result['summary']['outliers_removed'],
            missing_values_filled=missing_result['summary']['values_filled'],
            processing_summary=processing_summary
        )
    
    def _setup_date_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """날짜 인덱스 설정 및 정규화"""
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
        
        # 중복 날짜 제거 (평균값 사용)
        df = df.groupby(df.index).mean()
        
        # 날짜 범위 보간 (일별 데이터로 정규화)
        full_date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
        df = df.reindex(full_date_range)
        
        return df
    
    def _handle_covid_period(self, df: pd.DataFrame, 
                           target_columns: List[str]) -> Dict[str, Any]:
        """COVID-19 기간 데이터 처리"""
        covid_mask = (df.index >= self.covid_start) & (df.index <= self.covid_end)
        covid_data_count = covid_mask.sum()
        
        if covid_data_count == 0:
            return {
                'data': df,
                'summary': {'method': 'no_covid_data', 'affected_records': 0}
            }
        
        logger.info(f"COVID-19 기간 데이터 처리: {covid_data_count}개 레코드")
        
        if self.config.covid_handling == "remove":
            # COVID-19 기간 데이터 제거
            df_processed = df[~covid_mask].copy()
            method = "removed"
            
        elif self.config.covid_handling == "interpolate":
            # 고급 보간 기법 사용
            df_processed = df.copy()
            
            for col in target_columns:
                if col in df_processed.columns:
                    # COVID 이전/이후 추세를 고려한 보간
                    pre_covid = df_processed[df_processed.index < self.covid_start][col]
                    post_covid = df_processed[df_processed.index > self.covid_end][col]
                    
                    if len(pre_covid) > 30 and len(post_covid) > 30:
                        # 선형 보간으로 COVID 기간 데이터 대체
                        pre_trend = pre_covid.tail(30).mean()
                        post_trend = post_covid.head(30).mean()
                        
                        covid_indices = df_processed[covid_mask].index
                        interpolated_values = np.linspace(pre_trend, post_trend, len(covid_indices))
                        
                        df_processed.loc[covid_mask, col] = interpolated_values
            
            method = "interpolated"
            
        elif self.config.covid_handling == "weight":
            # 가중치 감소 (모델에서 처리)
            df_processed = df.copy()
            df_processed.loc[covid_mask, 'covid_weight'] = 0.3  # 30% 가중치
            method = "weighted"
            
        else:
            df_processed = df.copy()
            method = "unchanged"
        
        return {
            'data': df_processed,
            'summary': {
                'method': method,
                'affected_records': covid_data_count,
                'covid_start': self.covid_start.strftime('%Y-%m-%d'),
                'covid_end': self.covid_end.strftime('%Y-%m-%d')
            }
        }
    
    def _handle_outliers(self, df: pd.DataFrame, 
                        target_columns: List[str]) -> Dict[str, Any]:
        """이상치 탐지 및 처리"""
        df_processed = df.copy()
        outliers_removed = 0
        outlier_details = {}
        
        for col in target_columns:
            if col not in df_processed.columns:
                continue
            
            values = df_processed[col].dropna()
            
            if self.config.outlier_method == "z_score":
                # Z-score 기반 이상치 탐지
                z_scores = np.abs((values - values.mean()) / values.std())
                outlier_mask = z_scores > 3
                
            elif self.config.outlier_method == "iqr":
                # IQR 기반 이상치 탐지 (석유업계 맞춤)
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                
                # 석유 가격 특성상 더 넓은 범위 사용
                lower_bound = Q1 - 2.0 * IQR
                upper_bound = Q3 + 2.0 * IQR
                
                outlier_mask = (values < lower_bound) | (values > upper_bound)
                
            elif self.config.outlier_method == "isolation_forest":
                # Isolation Forest (더 정교한 탐지)
                from sklearn.ensemble import IsolationForest
                
                iso_forest = IsolationForest(
                    contamination=self.config.outlier_threshold,
                    random_state=42
                )
                outlier_labels = iso_forest.fit_predict(values.values.reshape(-1, 1))
                outlier_mask = pd.Series(outlier_labels == -1, index=values.index)
            
            # 이상치 개수 계산
            outlier_count = outlier_mask.sum()
            outliers_removed += outlier_count
            
            outlier_details[col] = {
                'count': int(outlier_count),
                'percentage': float(outlier_count / len(values) * 100)
            }
            
            # 이상치 처리 (보간으로 대체)
            if outlier_count > 0:
                outlier_indices = values[outlier_mask].index
                
                # 선형 보간으로 대체
                df_processed.loc[outlier_indices, col] = np.nan
                df_processed[col] = df_processed[col].interpolate(method='linear')
        
        logger.info(f"이상치 처리 완료: {outliers_removed}개 제거")
        
        return {
            'data': df_processed,
            'summary': {
                'outliers_removed': outliers_removed,
                'method': self.config.outlier_method,
                'details': outlier_details
            }
        }
    
    def _handle_missing_values(self, df: pd.DataFrame, 
                             target_columns: List[str]) -> Dict[str, Any]:
        """결측값 처리"""
        df_processed = df.copy()
        initial_missing = df_processed.isnull().sum().sum()
        
        # 시계열 특성을 고려한 보간 전략
        for col in target_columns:
            if col not in df_processed.columns:
                continue
            
            missing_count = df_processed[col].isnull().sum()
            
            if missing_count > 0:
                # 1. 선형 보간 (짧은 구간)
                df_processed[col] = df_processed[col].interpolate(method='linear')
                
                # 2. 계절성 고려 보간 (긴 구간)
                if df_processed[col].isnull().sum() > 0:
                    # 같은 요일/월 평균값 사용
                    df_processed['dayofweek'] = df_processed.index.dayofweek
                    df_processed['month'] = df_processed.index.month
                    
                    for dow in range(7):
                        for month in range(1, 13):
                            mask = (df_processed['dayofweek'] == dow) & (df_processed['month'] == month)
                            mean_val = df_processed.loc[mask, col].mean()
                            
                            if not np.isnan(mean_val):
                                df_processed.loc[mask & df_processed[col].isnull(), col] = mean_val
                    
                    df_processed.drop(['dayofweek', 'month'], axis=1, inplace=True)
                
                # 3. 앞/뒤 값으로 채우기 (마지막 수단)
                df_processed[col] = df_processed[col].fillna(method='bfill').fillna(method='ffill')
        
        final_missing = df_processed.isnull().sum().sum()
        values_filled = initial_missing - final_missing
        
        logger.info(f"결측값 처리 완료: {values_filled}개 채움")
        
        return {
            'data': df_processed,
            'summary': {
                'values_filled': int(values_filled),
                'initial_missing': int(initial_missing),
                'final_missing': int(final_missing)
            }
        }
    
    def _scale_data(self, df: pd.DataFrame, 
                   target_columns: List[str],
                   feature_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """데이터 스케일링"""
        df_processed = df.copy()
        scaling_info = {}
        
        # 스케일러 선택
        scaler_types = {
            'minmax': MinMaxScaler(),
            'standard': StandardScaler(),
            'robust': RobustScaler()
        }
        
        # 타겟 컬럼 스케일링 (일반적으로 MinMax 사용)
        for col in target_columns:
            if col not in df_processed.columns:
                continue
            
            scaler_type = 'minmax'  # 유가 데이터는 MinMax가 적합
            scaler = scaler_types[scaler_type]
            
            # 스케일링 적용
            values = df_processed[col].values.reshape(-1, 1)
            scaled_values = scaler.fit_transform(values)
            
            df_processed[f'{col}_scaled'] = scaled_values.flatten()
            
            # 스케일러 저장
            self.scalers[col] = {
                'scaler': scaler,
                'type': scaler_type,
                'original_range': [df_processed[col].min(), df_processed[col].max()]
            }
            
            scaling_info[col] = scaler_type
        
        # 특징 컬럼 스케일링
        if feature_columns:
            for col in feature_columns:
                if col not in df_processed.columns:
                    continue
                
                # 특징에 따라 다른 스케일러 사용
                if 'rate' in col.lower() or 'ratio' in col.lower():
                    scaler_type = 'standard'
                else:
                    scaler_type = 'robust'
                
                scaler = scaler_types[scaler_type]
                
                values = df_processed[col].values.reshape(-1, 1)
                scaled_values = scaler.fit_transform(values)
                
                df_processed[f'{col}_scaled'] = scaled_values.flatten()
                
                self.scalers[col] = {
                    'scaler': scaler,
                    'type': scaler_type,
                    'original_range': [df_processed[col].min(), df_processed[col].max()]
                }
                
                scaling_info[col] = scaler_type
        
        logger.info(f"데이터 스케일링 완료: {len(scaling_info)}개 컬럼")
        
        return {
            'data': df_processed,
            'summary': scaling_info
        }
    
    def inverse_transform(self, scaled_data: np.ndarray, 
                         column_name: str) -> np.ndarray:
        """스케일링 역변환"""
        if column_name not in self.scalers:
            raise ValueError(f"Column {column_name} not found in scalers")
        
        scaler = self.scalers[column_name]['scaler']
        
        if scaled_data.ndim == 1:
            scaled_data = scaled_data.reshape(-1, 1)
        
        return scaler.inverse_transform(scaled_data).flatten()
    
    def _validate_processed_data(self, df: pd.DataFrame) -> float:
        """전처리된 데이터 품질 검증"""
        total_values = df.size
        missing_values = df.isnull().sum().sum()
        
        # 기본 품질 점수
        quality_score = 1 - (missing_values / total_values)
        
        # 연속성 검증 (날짜 인덱스)
        if isinstance(df.index, pd.DatetimeIndex):
            expected_days = (df.index.max() - df.index.min()).days + 1
            actual_days = len(df)
            continuity_score = actual_days / expected_days
            quality_score *= continuity_score
        
        # 분산 검증 (너무 균일한 데이터는 의심)
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        variance_scores = []
        
        for col in numeric_columns:
            if df[col].var() > 0:
                # 정규화된 분산 점수
                cv = df[col].std() / df[col].mean() if df[col].mean() != 0 else 0
                variance_score = min(1.0, cv / 0.5)  # 적정 변동계수 기준
                variance_scores.append(variance_score)
        
        if variance_scores:
            quality_score *= np.mean(variance_scores)
        
        return min(1.0, quality_score)
    
    def get_preprocessing_report(self, result: PreprocessingResult) -> Dict[str, Any]:
        """전처리 결과 리포트"""
        df = result.processed_data
        
        report = {
            'data_shape': df.shape,
            'date_range': {
                'start': df.index.min().isoformat() if isinstance(df.index, pd.DatetimeIndex) else None,
                'end': df.index.max().isoformat() if isinstance(df.index, pd.DatetimeIndex) else None
            },
            'processing_summary': result.processing_summary,
            'outliers_removed': result.outliers_removed,
            'missing_values_filled': result.missing_values_filled,
            'scaled_columns': list(result.scaler_info.keys()),
            'data_quality_metrics': {
                'missing_percentage': (df.isnull().sum().sum() / df.size) * 100,
                'numeric_columns': len(df.select_dtypes(include=[np.number]).columns),
                'quality_score': result.processing_summary.get('quality_score', 0)
            }
        }
        
        return report