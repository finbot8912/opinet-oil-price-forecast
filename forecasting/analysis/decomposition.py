"""
Time Series Decomposition for Oil Price Analysis
Advanced decomposition techniques with petroleum industry insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from scipy import signal
from scipy.stats import zscore
from statsmodels.tsa.seasonal import seasonal_decompose, STL
from statsmodels.tsa.filters.hp_filter import hpfilter
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DecompositionResult:
    """시계열 분해 결과"""
    original: pd.Series
    trend: pd.Series
    seasonal: pd.Series
    residual: pd.Series
    seasonal_strength: float
    trend_strength: float
    decomposition_method: str
    metadata: Dict[str, Any]

@dataclass
class SeasonalPatterns:
    """계절성 패턴 분석 결과"""
    yearly_pattern: pd.Series
    monthly_pattern: pd.Series
    weekly_pattern: pd.Series
    dominant_frequencies: List[Tuple[float, float]]  # (frequency, power)
    seasonality_score: float

class TimeSeriesDecomposer:
    """
    석유업계 특화 시계열 분해기
    - 계절성, 추세, 잡음 분리
    - 석유 가격의 복합 주기성 분석
    - 지정학적 이벤트 영향 분리
    - 구조적 변화점 탐지
    """
    
    def __init__(self):
        logger.info("TimeSeriesDecomposer 초기화 완료")
    
    def decompose_series(self, 
                        series: pd.Series,
                        method: str = "stl",
                        seasonal_period: int = 365,
                        **kwargs) -> DecompositionResult:
        """
        시계열 분해 수행
        
        Args:
            series: 시계열 데이터
            method: 분해 방법 ('classical', 'stl', 'x13')
            seasonal_period: 계절성 주기
            **kwargs: 추가 파라미터
        
        Returns:
            DecompositionResult
        """
        logger.info(f"시계열 분해 시작: {method}, 주기={seasonal_period}")
        
        # 데이터 전처리
        clean_series = self._prepare_series(series)
        
        if method == "classical":
            result = self._classical_decomposition(clean_series, seasonal_period, **kwargs)
        elif method == "stl":
            result = self._stl_decomposition(clean_series, seasonal_period, **kwargs)
        elif method == "hp":
            result = self._hp_filter_decomposition(clean_series, **kwargs)
        elif method == "advanced":
            result = self._advanced_decomposition(clean_series, seasonal_period, **kwargs)
        else:
            raise ValueError(f"Unknown decomposition method: {method}")
        
        # 계절성/추세 강도 계산
        seasonal_strength = self._calculate_seasonal_strength(result)
        trend_strength = self._calculate_trend_strength(result)
        
        decomposition_result = DecompositionResult(
            original=clean_series,
            trend=result['trend'],
            seasonal=result['seasonal'],
            residual=result['residual'],
            seasonal_strength=seasonal_strength,
            trend_strength=trend_strength,
            decomposition_method=method,
            metadata=result.get('metadata', {})
        )
        
        logger.info(f"시계열 분해 완료: 계절성 강도={seasonal_strength:.3f}, 추세 강도={trend_strength:.3f}")
        
        return decomposition_result
    
    def analyze_seasonality(self, 
                          series: pd.Series,
                          max_period: int = 365) -> SeasonalPatterns:
        """
        계절성 패턴 상세 분석
        
        Args:
            series: 시계열 데이터
            max_period: 최대 분석 주기
        
        Returns:
            SeasonalPatterns
        """
        logger.info("계절성 패턴 분석 시작...")
        
        clean_series = self._prepare_series(series)
        
        # 연간 패턴 (일별 평균)
        yearly_pattern = self._extract_yearly_pattern(clean_series)
        
        # 월별 패턴
        monthly_pattern = self._extract_monthly_pattern(clean_series)
        
        # 주별 패턴
        weekly_pattern = self._extract_weekly_pattern(clean_series)
        
        # 주파수 영역 분석
        dominant_frequencies = self._frequency_analysis(clean_series, max_period)
        
        # 계절성 점수 계산
        seasonality_score = self._calculate_seasonality_score(clean_series)
        
        return SeasonalPatterns(
            yearly_pattern=yearly_pattern,
            monthly_pattern=monthly_pattern,
            weekly_pattern=weekly_pattern,
            dominant_frequencies=dominant_frequencies,
            seasonality_score=seasonality_score
        )
    
    def detect_structural_breaks(self, 
                               series: pd.Series,
                               min_segment_length: int = 30) -> List[Tuple[datetime, str, float]]:
        """
        구조적 변화점 탐지
        
        Args:
            series: 시계열 데이터
            min_segment_length: 최소 세그먼트 길이
        
        Returns:
            List of (date, break_type, significance)
        """
        logger.info("구조적 변화점 탐지 시작...")
        
        clean_series = self._prepare_series(series)
        breaks = []
        
        # CUSUM 기반 변화점 탐지
        cusum_breaks = self._cusum_detection(clean_series, min_segment_length)
        breaks.extend([(date, "level_shift", significance) for date, significance in cusum_breaks])
        
        # 분산 변화점 탐지
        variance_breaks = self._variance_change_detection(clean_series, min_segment_length)
        breaks.extend([(date, "variance_change", significance) for date, significance in variance_breaks])
        
        # 추세 변화점 탐지
        trend_breaks = self._trend_change_detection(clean_series, min_segment_length)
        breaks.extend([(date, "trend_change", significance) for date, significance in trend_breaks])
        
        # 날짜순 정렬
        breaks.sort(key=lambda x: x[0])
        
        logger.info(f"구조적 변화점 탐지 완료: {len(breaks)}개 발견")
        
        return breaks
    
    def _prepare_series(self, series: pd.Series) -> pd.Series:
        """시계열 데이터 전처리"""
        # 결측값 처리
        clean_series = series.dropna()
        
        # 너무 짧은 시계열 확인
        if len(clean_series) < 100:
            raise ValueError(f"시계열이 너무 짧습니다: {len(clean_series)}개 관측값")
        
        # 이상치 제거 (선택적)
        q99 = clean_series.quantile(0.99)
        q01 = clean_series.quantile(0.01)
        clean_series = clean_series.clip(lower=q01, upper=q99)
        
        return clean_series
    
    def _classical_decomposition(self, 
                               series: pd.Series,
                               seasonal_period: int,
                               model: str = "multiplicative") -> Dict[str, Any]:
        """고전적 분해 방법"""
        try:
            decomposition = seasonal_decompose(
                series, 
                model=model, 
                period=seasonal_period,
                extrapolate_trend='freq'
            )
            
            return {
                'trend': decomposition.trend,
                'seasonal': decomposition.seasonal,
                'residual': decomposition.resid,
                'metadata': {'model': model, 'period': seasonal_period}
            }
        except Exception as e:
            logger.warning(f"고전적 분해 실패, 가법 모델로 재시도: {e}")
            decomposition = seasonal_decompose(
                series, 
                model="additive", 
                period=seasonal_period,
                extrapolate_trend='freq'
            )
            
            return {
                'trend': decomposition.trend,
                'seasonal': decomposition.seasonal,
                'residual': decomposition.resid,
                'metadata': {'model': 'additive', 'period': seasonal_period}
            }
    
    def _stl_decomposition(self, 
                         series: pd.Series,
                         seasonal_period: int,
                         **kwargs) -> Dict[str, Any]:
        """STL(Seasonal and Trend decomposition using Loess) 분해"""
        try:
            # STL 파라미터 설정
            stl_params = {
                'seasonal': kwargs.get('seasonal', 7),  # 계절성 강도
                'trend': kwargs.get('trend', None),      # 추세 강도
                'low_pass': kwargs.get('low_pass', None),
                'seasonal_deg': kwargs.get('seasonal_deg', 1),
                'trend_deg': kwargs.get('trend_deg', 1),
                'low_pass_deg': kwargs.get('low_pass_deg', 1),
                'robust': kwargs.get('robust', True)
            }
            
            stl = STL(series, period=seasonal_period, **stl_params)
            result = stl.fit()
            
            return {
                'trend': result.trend,
                'seasonal': result.seasonal,
                'residual': result.resid,
                'metadata': {'method': 'STL', 'period': seasonal_period, 'params': stl_params}
            }
        except Exception as e:
            logger.warning(f"STL 분해 실패, 고전적 분해로 대체: {e}")
            return self._classical_decomposition(series, seasonal_period)
    
    def _hp_filter_decomposition(self, 
                               series: pd.Series,
                               lamb: Optional[float] = None) -> Dict[str, Any]:
        """Hodrick-Prescott 필터 분해"""
        if lamb is None:
            # 데이터 주기에 따른 람다 값 자동 설정
            if len(series) > 365:
                lamb = 129600  # 일별 데이터
            else:
                lamb = 1600    # 기본값
        
        try:
            trend, residual = hpfilter(series, lamb=lamb)
            seasonal = pd.Series(0, index=series.index)  # HP 필터는 계절성 분리 안함
            
            return {
                'trend': trend,
                'seasonal': seasonal,
                'residual': residual,
                'metadata': {'method': 'HP', 'lambda': lamb}
            }
        except Exception as e:
            logger.error(f"HP 필터 실패: {e}")
            raise
    
    def _advanced_decomposition(self, 
                              series: pd.Series,
                              seasonal_period: int,
                              **kwargs) -> Dict[str, Any]:
        """고급 분해 방법 (STL + 추가 처리)"""
        # 기본 STL 분해
        stl_result = self._stl_decomposition(series, seasonal_period, **kwargs)
        
        # 잔차에서 추가 패턴 탐지
        residual = stl_result['residual']
        
        # 고주파 노이즈 제거
        from scipy.signal import savgol_filter
        if len(residual) > 21:
            smoothed_residual = pd.Series(
                savgol_filter(residual.values, window_length=21, polyorder=3),
                index=residual.index
            )
        else:
            smoothed_residual = residual
        
        # 추세 성분 개선
        enhanced_trend = stl_result['trend'] + (residual - smoothed_residual)
        
        return {
            'trend': enhanced_trend,
            'seasonal': stl_result['seasonal'],
            'residual': smoothed_residual,
            'metadata': {'method': 'Advanced STL', 'period': seasonal_period}
        }
    
    def _extract_yearly_pattern(self, series: pd.Series) -> pd.Series:
        """연간 계절 패턴 추출"""
        if not isinstance(series.index, pd.DatetimeIndex):
            return pd.Series()
        
        # 일별 평균 계산
        series_df = pd.DataFrame({'value': series, 'dayofyear': series.index.dayofyear})
        yearly_pattern = series_df.groupby('dayofyear')['value'].mean()
        
        return yearly_pattern
    
    def _extract_monthly_pattern(self, series: pd.Series) -> pd.Series:
        """월별 패턴 추출"""
        if not isinstance(series.index, pd.DatetimeIndex):
            return pd.Series()
        
        series_df = pd.DataFrame({'value': series, 'month': series.index.month})
        monthly_pattern = series_df.groupby('month')['value'].mean()
        
        return monthly_pattern
    
    def _extract_weekly_pattern(self, series: pd.Series) -> pd.Series:
        """주별 패턴 추출"""
        if not isinstance(series.index, pd.DatetimeIndex):
            return pd.Series()
        
        series_df = pd.DataFrame({'value': series, 'dayofweek': series.index.dayofweek})
        weekly_pattern = series_df.groupby('dayofweek')['value'].mean()
        
        return weekly_pattern
    
    def _frequency_analysis(self, 
                           series: pd.Series, 
                           max_period: int) -> List[Tuple[float, float]]:
        """주파수 영역 분석"""
        try:
            # FFT 수행
            fft_values = np.fft.fft(series.values)
            frequencies = np.fft.fftfreq(len(series))
            
            # 파워 스펙트럼 계산
            power_spectrum = np.abs(fft_values) ** 2
            
            # 양수 주파수만 선택
            positive_freq_mask = frequencies > 0
            frequencies = frequencies[positive_freq_mask]
            power_spectrum = power_spectrum[positive_freq_mask]
            
            # 주요 주파수 선택 (상위 5개)
            top_indices = np.argsort(power_spectrum)[-5:][::-1]
            
            dominant_frequencies = []
            for idx in top_indices:
                freq = frequencies[idx]
                power = power_spectrum[idx]
                period = 1 / freq if freq != 0 else float('inf')
                
                if period <= max_period:
                    dominant_frequencies.append((freq, power))
            
            return dominant_frequencies
            
        except Exception as e:
            logger.warning(f"주파수 분석 실패: {e}")
            return []
    
    def _calculate_seasonal_strength(self, result: Dict[str, Any]) -> float:
        """계절성 강도 계산"""
        try:
            seasonal = result['seasonal']
            residual = result['residual']
            
            # 계절성 분산 / (계절성 분산 + 잔차 분산)
            seasonal_var = seasonal.var()
            residual_var = residual.var()
            
            if seasonal_var + residual_var == 0:
                return 0.0
            
            strength = seasonal_var / (seasonal_var + residual_var)
            return max(0.0, min(1.0, strength))
            
        except Exception:
            return 0.0
    
    def _calculate_trend_strength(self, result: Dict[str, Any]) -> float:
        """추세 강도 계산"""
        try:
            trend = result['trend'].dropna()
            residual = result['residual'].dropna()
            
            # 추세 분산 / (추세 분산 + 잔차 분산)
            trend_var = trend.var()
            residual_var = residual.var()
            
            if trend_var + residual_var == 0:
                return 0.0
            
            strength = trend_var / (trend_var + residual_var)
            return max(0.0, min(1.0, strength))
            
        except Exception:
            return 0.0
    
    def _calculate_seasonality_score(self, series: pd.Series) -> float:
        """전체 계절성 점수 계산"""
        try:
            # 자기상관 기반 계절성 점수
            max_lag = min(365, len(series) // 4)
            
            seasonal_lags = [7, 30, 91, 182, 365]  # 주, 월, 분기, 반기, 년
            seasonal_lags = [lag for lag in seasonal_lags if lag < max_lag]
            
            autocorr_scores = []
            for lag in seasonal_lags:
                if lag < len(series):
                    autocorr = series.autocorr(lag)
                    if not np.isnan(autocorr):
                        autocorr_scores.append(abs(autocorr))
            
            if autocorr_scores:
                return np.mean(autocorr_scores)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _cusum_detection(self, 
                        series: pd.Series, 
                        min_segment_length: int) -> List[Tuple[datetime, float]]:
        """CUSUM 기반 수준 변화 탐지"""
        try:
            values = series.values
            dates = series.index
            
            # CUSUM 통계량 계산
            mean_val = np.mean(values)
            cusum_pos = np.zeros(len(values))
            cusum_neg = np.zeros(len(values))
            
            h = 4 * np.std(values)  # 임계값
            
            breaks = []
            
            for i in range(1, len(values)):
                cusum_pos[i] = max(0, cusum_pos[i-1] + values[i] - mean_val - 0.5*np.std(values))
                cusum_neg[i] = max(0, cusum_neg[i-1] - values[i] + mean_val - 0.5*np.std(values))
                
                # 변화점 탐지
                if cusum_pos[i] > h or cusum_neg[i] > h:
                    if i >= min_segment_length and (len(breaks) == 0 or i - breaks[-1][1] >= min_segment_length):
                        significance = max(cusum_pos[i], cusum_neg[i]) / h
                        breaks.append((dates[i], significance))
                        
                        # CUSUM 리셋
                        cusum_pos[i] = 0
                        cusum_neg[i] = 0
            
            return [(date, sig) for date, sig in breaks]
            
        except Exception as e:
            logger.warning(f"CUSUM 탐지 실패: {e}")
            return []
    
    def _variance_change_detection(self, 
                                 series: pd.Series, 
                                 min_segment_length: int) -> List[Tuple[datetime, float]]:
        """분산 변화 탐지"""
        try:
            window_size = max(30, min_segment_length)
            rolling_std = series.rolling(window=window_size).std()
            
            # 분산 변화율 계산
            variance_change = rolling_std.pct_change().abs()
            
            # 임계값 설정 (상위 5%)
            threshold = variance_change.quantile(0.95)
            
            # 변화점 탐지
            change_points = variance_change[variance_change > threshold]
            
            breaks = []
            for date, change_rate in change_points.items():
                significance = min(1.0, change_rate / threshold)
                breaks.append((date, significance))
            
            return breaks
            
        except Exception as e:
            logger.warning(f"분산 변화 탐지 실패: {e}")
            return []
    
    def _trend_change_detection(self, 
                              series: pd.Series, 
                              min_segment_length: int) -> List[Tuple[datetime, float]]:
        """추세 변화 탐지"""
        try:
            # 이동 평균의 기울기 계산
            window_size = max(30, min_segment_length)
            rolling_mean = series.rolling(window=window_size).mean()
            trend_slope = rolling_mean.diff()
            
            # 기울기 변화율 계산
            slope_change = trend_slope.diff().abs()
            
            # 임계값 설정
            threshold = slope_change.quantile(0.95)
            
            # 변화점 탐지
            change_points = slope_change[slope_change > threshold]
            
            breaks = []
            for date, change_rate in change_points.items():
                significance = min(1.0, change_rate / threshold)
                breaks.append((date, significance))
            
            return breaks
            
        except Exception as e:
            logger.warning(f"추세 변화 탐지 실패: {e}")
            return []