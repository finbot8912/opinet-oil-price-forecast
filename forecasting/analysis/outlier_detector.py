"""
Advanced Outlier Detection for Oil Price Data
Petroleum industry specialized anomaly detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from scipy import stats
from scipy.signal import find_peaks
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OutlierResult:
    """이상치 탐지 결과"""
    outlier_indices: List[int]
    outlier_scores: List[float]
    outlier_types: List[str]
    outlier_dates: List[datetime]
    outlier_values: List[float]
    total_outliers: int
    outlier_percentage: float
    detection_method: str
    threshold: float

@dataclass
class AnomalyProfile:
    """이상 패턴 프로필"""
    geopolitical_events: List[Tuple[datetime, str, float]]  # 지정학적 이벤트
    market_crashes: List[Tuple[datetime, str, float]]       # 시장 급락
    supply_disruptions: List[Tuple[datetime, str, float]]   # 공급 차질
    demand_shocks: List[Tuple[datetime, str, float]]        # 수요 충격
    technical_anomalies: List[Tuple[datetime, str, float]]  # 기술적 이상

class OutlierDetector:
    """
    석유업계 특화 이상치 탐지기
    - 지정학적 이벤트로 인한 급등/급락 탐지
    - 공급망 차질로 인한 이상 패턴 식별  
    - COVID-19 같은 구조적 변화 탐지
    - 계절성을 고려한 이상치 판별
    - 다중 방법 앙상블 탐지
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.detection_history = []
        
        # 석유업계 도메인 지식 기반 임계값
        self.domain_thresholds = {
            'daily_change_limit': 0.10,      # 일일 변동률 10% 초과 시 이상
            'weekly_volatility_limit': 0.15,  # 주간 변동성 15% 초과 시 이상
            'price_spike_threshold': 3.0,     # Z-score 3.0 초과 시 급등/급락
            'supply_disruption_threshold': 0.20,  # 20% 이상 급변동 시 공급차질 의심
        }
        
        logger.info("OutlierDetector 초기화 완료")
    
    def detect_outliers(self, 
                       series: pd.Series,
                       method: str = "ensemble",
                       contamination: float = 0.1,
                       **kwargs) -> OutlierResult:
        """
        이상치 탐지 수행
        
        Args:
            series: 시계열 데이터
            method: 탐지 방법 ('isolation_forest', 'statistical', 'domain_based', 'ensemble')
            contamination: 예상 이상치 비율
            **kwargs: 추가 파라미터
        
        Returns:
            OutlierResult
        """
        logger.info(f"이상치 탐지 시작: {method}, contamination={contamination}")
        
        clean_series = series.dropna()
        
        if len(clean_series) < 30:
            logger.warning("데이터가 너무 적어 이상치 탐지 스킵")
            return self._empty_result(method, 0.0)
        
        if method == "isolation_forest":
            result = self._isolation_forest_detection(clean_series, contamination, **kwargs)
        elif method == "statistical":
            result = self._statistical_detection(clean_series, **kwargs)
        elif method == "domain_based":
            result = self._domain_based_detection(clean_series, **kwargs)
        elif method == "ensemble":
            result = self._ensemble_detection(clean_series, contamination, **kwargs)
        else:
            raise ValueError(f"Unknown detection method: {method}")
        
        logger.info(f"이상치 탐지 완료: {result.total_outliers}개 ({result.outlier_percentage:.1f}%)")
        
        return result
    
    def analyze_anomaly_patterns(self, 
                               series: pd.Series,
                               price_changes: Optional[pd.Series] = None) -> AnomalyProfile:
        """
        이상 패턴 유형별 분석
        
        Args:
            series: 가격 시계열
            price_changes: 가격 변화율 시계열
            
        Returns:
            AnomalyProfile
        """
        logger.info("이상 패턴 분석 시작...")
        
        if price_changes is None:
            price_changes = series.pct_change().dropna()
        
        # 각 유형별 이상 패턴 탐지
        geopolitical = self._detect_geopolitical_events(series, price_changes)
        crashes = self._detect_market_crashes(series, price_changes)
        supply_disruptions = self._detect_supply_disruptions(series, price_changes)
        demand_shocks = self._detect_demand_shocks(series, price_changes)
        technical = self._detect_technical_anomalies(series, price_changes)
        
        return AnomalyProfile(
            geopolitical_events=geopolitical,
            market_crashes=crashes,
            supply_disruptions=supply_disruptions,
            demand_shocks=demand_shocks,
            technical_anomalies=technical
        )
    
    def _isolation_forest_detection(self, 
                                   series: pd.Series,
                                   contamination: float,
                                   **kwargs) -> OutlierResult:
        """Isolation Forest 기반 탐지"""
        try:
            # 특징 생성
            features = self._create_anomaly_features(series)
            
            # 모델 학습
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=kwargs.get('n_estimators', 100)
            )
            
            outlier_labels = iso_forest.fit_predict(features)
            outlier_scores = iso_forest.score_samples(features)
            
            # 결과 정리
            outlier_mask = outlier_labels == -1
            outlier_indices = np.where(outlier_mask)[0]
            
            return OutlierResult(
                outlier_indices=outlier_indices.tolist(),
                outlier_scores=outlier_scores[outlier_mask].tolist(),
                outlier_types=['isolation_forest'] * len(outlier_indices),
                outlier_dates=[series.index[i] for i in outlier_indices],
                outlier_values=[series.iloc[i] for i in outlier_indices],
                total_outliers=len(outlier_indices),
                outlier_percentage=(len(outlier_indices) / len(series)) * 100,
                detection_method='isolation_forest',
                threshold=contamination
            )
            
        except Exception as e:
            logger.error(f"Isolation Forest 탐지 실패: {e}")
            return self._empty_result('isolation_forest', contamination)
    
    def _statistical_detection(self, 
                             series: pd.Series,
                             z_threshold: float = 3.0,
                             **kwargs) -> OutlierResult:
        """통계적 방법 기반 탐지"""
        try:
            # Z-score 계산
            z_scores = np.abs(stats.zscore(series.values))
            
            # Modified Z-score (더 robust)
            median = np.median(series.values)
            mad = np.median(np.abs(series.values - median))
            modified_z_scores = 0.6745 * (series.values - median) / mad
            
            # IQR 방법
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            iqr_lower = Q1 - 1.5 * IQR
            iqr_upper = Q3 + 1.5 * IQR
            
            # 복합 이상치 판별
            outlier_mask = (
                (z_scores > z_threshold) |
                (np.abs(modified_z_scores) > 3.5) |
                (series < iqr_lower) |
                (series > iqr_upper)
            )
            
            outlier_indices = np.where(outlier_mask)[0]
            outlier_scores = z_scores[outlier_mask]
            
            return OutlierResult(
                outlier_indices=outlier_indices.tolist(),
                outlier_scores=outlier_scores.tolist(),
                outlier_types=['statistical'] * len(outlier_indices),
                outlier_dates=[series.index[i] for i in outlier_indices],
                outlier_values=[series.iloc[i] for i in outlier_indices],
                total_outliers=len(outlier_indices),
                outlier_percentage=(len(outlier_indices) / len(series)) * 100,
                detection_method='statistical',
                threshold=z_threshold
            )
            
        except Exception as e:
            logger.error(f"통계적 탐지 실패: {e}")
            return self._empty_result('statistical', z_threshold)
    
    def _domain_based_detection(self, 
                              series: pd.Series,
                              **kwargs) -> OutlierResult:
        """석유업계 도메인 지식 기반 탐지"""
        try:
            outlier_indices = []
            outlier_scores = []
            outlier_types = []
            
            # 일일 변동률 이상치
            daily_changes = series.pct_change().abs()
            daily_outliers = daily_changes > self.domain_thresholds['daily_change_limit']
            
            for idx in daily_changes[daily_outliers].index:
                pos = series.index.get_loc(idx)
                outlier_indices.append(pos)
                outlier_scores.append(daily_changes[idx])
                outlier_types.append('daily_spike')
            
            # 주간 변동성 이상치
            weekly_volatility = series.rolling(window=7).std()
            weekly_outliers = weekly_volatility > self.domain_thresholds['weekly_volatility_limit'] * series.std()
            
            for idx in weekly_volatility[weekly_outliers].index:
                pos = series.index.get_loc(idx)
                if pos not in outlier_indices:
                    outlier_indices.append(pos)
                    outlier_scores.append(weekly_volatility[idx])
                    outlier_types.append('volatility_spike')
            
            # 연속적 급등/급락 (공급 차질 가능성)
            consecutive_changes = self._detect_consecutive_changes(series)
            for pos, score in consecutive_changes:
                if pos not in outlier_indices:
                    outlier_indices.append(pos)
                    outlier_scores.append(score)
                    outlier_types.append('supply_disruption')
            
            return OutlierResult(
                outlier_indices=outlier_indices,
                outlier_scores=outlier_scores,
                outlier_types=outlier_types,
                outlier_dates=[series.index[i] for i in outlier_indices],
                outlier_values=[series.iloc[i] for i in outlier_indices],
                total_outliers=len(outlier_indices),
                outlier_percentage=(len(outlier_indices) / len(series)) * 100,
                detection_method='domain_based',
                threshold=self.domain_thresholds['daily_change_limit']
            )
            
        except Exception as e:
            logger.error(f"도메인 기반 탐지 실패: {e}")
            return self._empty_result('domain_based', 0.1)
    
    def _ensemble_detection(self, 
                          series: pd.Series,
                          contamination: float,
                          **kwargs) -> OutlierResult:
        """앙상블 방법 기반 탐지"""
        try:
            # 각 방법별 탐지 수행
            iso_result = self._isolation_forest_detection(series, contamination)
            stat_result = self._statistical_detection(series)
            domain_result = self._domain_based_detection(series)
            
            # 투표 기반 앙상블
            all_indices = set()
            vote_counts = {}
            score_sums = {}
            type_info = {}
            
            # 각 방법의 결과 집계
            for result, method in [(iso_result, 'iso'), (stat_result, 'stat'), (domain_result, 'domain')]:
                for i, idx in enumerate(result.outlier_indices):
                    all_indices.add(idx)
                    vote_counts[idx] = vote_counts.get(idx, 0) + 1
                    score_sums[idx] = score_sums.get(idx, 0) + result.outlier_scores[i]
                    
                    if idx not in type_info:
                        type_info[idx] = []
                    type_info[idx].append(f"{method}:{result.outlier_types[i]}")
            
            # 2표 이상 받은 이상치만 선택
            min_votes = kwargs.get('min_votes', 2)
            final_outliers = [idx for idx in all_indices if vote_counts[idx] >= min_votes]
            
            return OutlierResult(
                outlier_indices=final_outliers,
                outlier_scores=[score_sums[idx] / vote_counts[idx] for idx in final_outliers],
                outlier_types=[','.join(type_info[idx]) for idx in final_outliers],
                outlier_dates=[series.index[i] for i in final_outliers],
                outlier_values=[series.iloc[i] for i in final_outliers],
                total_outliers=len(final_outliers),
                outlier_percentage=(len(final_outliers) / len(series)) * 100,
                detection_method='ensemble',
                threshold=min_votes
            )
            
        except Exception as e:
            logger.error(f"앙상블 탐지 실패: {e}")
            return self._empty_result('ensemble', contamination)
    
    def _create_anomaly_features(self, series: pd.Series) -> np.ndarray:
        """이상치 탐지를 위한 특징 생성"""
        features = []
        
        # 원본 값
        features.append(series.values)
        
        # 변화율
        pct_changes = series.pct_change().fillna(0).values
        features.append(pct_changes)
        
        # 이동평균과의 차이
        ma7 = series.rolling(window=7).mean().fillna(series.mean()).values
        ma30 = series.rolling(window=30).mean().fillna(series.mean()).values
        features.append(series.values - ma7)
        features.append(series.values - ma30)
        
        # 변동성
        volatility = series.rolling(window=7).std().fillna(series.std()).values
        features.append(volatility)
        
        # Z-score
        z_scores = stats.zscore(series.values)
        features.append(z_scores)
        
        return np.column_stack(features)
    
    def _detect_consecutive_changes(self, series: pd.Series) -> List[Tuple[int, float]]:
        """연속적 급변동 탐지"""
        changes = series.pct_change().abs()
        threshold = self.domain_thresholds['supply_disruption_threshold']
        
        consecutive_outliers = []
        consecutive_count = 0
        
        for i, change in enumerate(changes):
            if pd.isna(change):
                continue
                
            if change > threshold:
                consecutive_count += 1
            else:
                if consecutive_count >= 3:  # 3일 이상 연속 급변동
                    # 연속 급변동 구간의 최고점 찾기
                    start_idx = max(0, i - consecutive_count)
                    end_idx = min(len(series), i)
                    max_change_idx = start_idx + changes.iloc[start_idx:end_idx].idxmax()
                    max_change_score = changes.iloc[max_change_idx]
                    
                    consecutive_outliers.append((max_change_idx, max_change_score))
                
                consecutive_count = 0
        
        return consecutive_outliers
    
    def _detect_geopolitical_events(self, 
                                   series: pd.Series, 
                                   price_changes: pd.Series) -> List[Tuple[datetime, str, float]]:
        """지정학적 이벤트 탐지 (급등 패턴)"""
        events = []
        
        # 급격한 가격 상승 (3% 이상)
        sharp_increases = price_changes > 0.03
        
        for date in price_changes[sharp_increases].index:
            # 이후 5일간 지속적 상승 확인
            future_window = price_changes.loc[date:date + timedelta(days=5)]
            if len(future_window) >= 3 and future_window.mean() > 0.01:
                severity = price_changes[date]
                events.append((date, "geopolitical_tension", severity))
        
        return events
    
    def _detect_market_crashes(self, 
                              series: pd.Series, 
                              price_changes: pd.Series) -> List[Tuple[datetime, str, float]]:
        """시장 급락 탐지"""
        crashes = []
        
        # 급격한 가격 하락 (5% 이상)
        sharp_decreases = price_changes < -0.05
        
        for date in price_changes[sharp_decreases].index:
            # 이후 복구 패턴 확인
            future_window = price_changes.loc[date:date + timedelta(days=10)]
            if len(future_window) >= 5:
                recovery_rate = future_window[future_window > 0].sum()
                if recovery_rate > 0.02:  # 2% 이상 복구
                    severity = abs(price_changes[date])
                    crashes.append((date, "market_crash", severity))
        
        return crashes
    
    def _detect_supply_disruptions(self, 
                                  series: pd.Series, 
                                  price_changes: pd.Series) -> List[Tuple[datetime, str, float]]:
        """공급 차질 탐지"""
        disruptions = []
        
        # 점진적 가격 상승 패턴
        for i in range(7, len(price_changes)):
            week_changes = price_changes.iloc[i-7:i]
            if len(week_changes[week_changes > 0]) >= 5:  # 7일 중 5일 이상 상승
                cumulative_increase = week_changes.sum()
                if cumulative_increase > 0.05:  # 누적 5% 이상 상승
                    date = price_changes.index[i]
                    disruptions.append((date, "supply_disruption", cumulative_increase))
        
        return disruptions
    
    def _detect_demand_shocks(self, 
                             series: pd.Series, 
                             price_changes: pd.Series) -> List[Tuple[datetime, str, float]]:
        """수요 충격 탐지"""
        shocks = []
        
        # 급격한 수요 변화 (계절성 고려)
        if isinstance(series.index, pd.DatetimeIndex):
            # 같은 월 평균과 비교
            for date in series.index:
                month = date.month
                same_month_data = series[series.index.month == month]
                same_month_mean = same_month_data.mean()
                
                current_value = series[date]
                deviation = abs(current_value - same_month_mean) / same_month_mean
                
                if deviation > 0.08:  # 같은 월 평균 대비 8% 이상 차이
                    shocks.append((date, "demand_shock", deviation))
        
        return shocks
    
    def _detect_technical_anomalies(self, 
                                   series: pd.Series, 
                                   price_changes: pd.Series) -> List[Tuple[datetime, str, float]]:
        """기술적 이상 탐지"""
        anomalies = []
        
        # 비정상적 변동성 스파이크
        volatility = price_changes.rolling(window=7).std()
        vol_threshold = volatility.quantile(0.95)
        
        high_vol_periods = volatility > vol_threshold
        
        for date in volatility[high_vol_periods].index:
            severity = volatility[date] / volatility.median()
            anomalies.append((date, "volatility_anomaly", severity))
        
        return anomalies
    
    def _empty_result(self, method: str, threshold: float) -> OutlierResult:
        """빈 결과 반환"""
        return OutlierResult(
            outlier_indices=[],
            outlier_scores=[],
            outlier_types=[],
            outlier_dates=[],
            outlier_values=[],
            total_outliers=0,
            outlier_percentage=0.0,
            detection_method=method,
            threshold=threshold
        )