"""
ARIMA Model for Oil Price Forecasting
Advanced ARIMA implementation with petroleum industry optimizations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.stats.diagnostic import acorr_ljungbox
from pmdarima import auto_arima
import logging
from dataclasses import dataclass

from ..config.model_config import ARIMAConfig

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

@dataclass
class ARIMAModelResult:
    """ARIMA 모델 결과"""
    model: Any  # ARIMA model object
    fitted_values: pd.Series
    residuals: pd.Series
    aic: float
    bic: float
    order: Tuple[int, int, int]
    seasonal_order: Optional[Tuple[int, int, int, int]]
    ljung_box_p_value: float
    model_summary: str

@dataclass
class ARIMAForecastResult:
    """ARIMA 예측 결과"""
    forecast: pd.Series
    confidence_intervals: pd.DataFrame
    forecast_dates: pd.DatetimeIndex
    model_info: Dict[str, Any]

class ARIMAForecaster:
    """
    석유업계 특화 ARIMA 예측기
    - 자동 차수 선택 (auto_arima)
    - 계절성 ARIMA 지원
    - 구조적 변화 고려
    - 잔차 진단 및 모델 검증
    - 석유가격 특성 반영 (변동성, 추세)
    """
    
    def __init__(self, config: ARIMAConfig):
        self.config = config
        self.model = None
        self.model_result = None
        self.is_fitted = False
        
        # 석유업계 특화 설정
        self.oil_price_params = {
            'information_criterion': config.information_criterion,
            'seasonal': config.seasonal,
            'stepwise': config.stepwise,
            'suppress_warnings': config.suppress_warnings,
            'error_action': 'ignore',
            'max_order': 8  # 석유가격은 복잡한 패턴 가능
        }
        
        logger.info("ARIMAForecaster 초기화 완료")
    
    def fit(self, 
            series: pd.Series, 
            exog: Optional[pd.DataFrame] = None,
            auto_select: bool = None) -> ARIMAModelResult:
        """
        ARIMA 모델 학습
        
        Args:
            series: 학습용 시계열 데이터
            exog: 외부 변수 (예: Dubai 유가, 환율)
            auto_select: 자동 차수 선택 여부
        
        Returns:
            ARIMAModelResult
        """
        logger.info("ARIMA 모델 학습 시작...")
        
        if auto_select is None:
            auto_select = self.config.auto_arima
        
        # 데이터 전처리
        clean_series = self._prepare_data(series)
        
        # 정상성 검정
        stationarity_info = self._check_stationarity(clean_series)
        logger.info(f"정상성 검정 결과: {stationarity_info}")
        
        try:
            if auto_select:
                # 자동 ARIMA 차수 선택
                self.model = self._auto_arima_selection(clean_series, exog)
                order = self.model.order
                seasonal_order = self.model.seasonal_order if hasattr(self.model, 'seasonal_order') else None
            else:
                # 수동 차수 선택
                order = self._manual_order_selection(clean_series)
                seasonal_order = self._get_seasonal_order() if self.config.seasonal else None
                
                # ARIMA 모델 생성
                self.model = ARIMA(
                    clean_series, 
                    order=order,
                    seasonal_order=seasonal_order,
                    exog=exog
                )
                self.model = self.model.fit(
                    method=self.config.method,
                    maxiter=self.config.maxiter
                )
            
            # 모델 결과 생성
            fitted_values = pd.Series(self.model.fittedvalues, index=clean_series.index)
            residuals = pd.Series(self.model.resid, index=clean_series.index)
            
            # 잔차 진단
            ljung_box_result = acorr_ljungbox(residuals, lags=10, return_df=True)
            ljung_box_p = ljung_box_result['lb_pvalue'].iloc[-1]
            
            self.model_result = ARIMAModelResult(
                model=self.model,
                fitted_values=fitted_values,
                residuals=residuals,
                aic=self.model.aic,
                bic=self.model.bic,
                order=order,
                seasonal_order=seasonal_order,
                ljung_box_p_value=ljung_box_p,
                model_summary=str(self.model.summary())
            )
            
            self.is_fitted = True
            
            logger.info(f"ARIMA 모델 학습 완료: 차수{order}, AIC={self.model.aic:.2f}, BIC={self.model.bic:.2f}")
            
            return self.model_result
            
        except Exception as e:
            logger.error(f"ARIMA 모델 학습 실패: {e}")
            raise
    
    def forecast(self, 
                steps: int,
                exog: Optional[pd.DataFrame] = None,
                alpha: float = 0.05) -> ARIMAForecastResult:
        """
        ARIMA 예측 수행
        
        Args:
            steps: 예측 스텝 수
            exog: 예측용 외부 변수
            alpha: 신뢰구간 알파 (0.05 = 95% 신뢰구간)
        
        Returns:
            ARIMAForecastResult
        """
        if not self.is_fitted:
            raise ValueError("모델이 학습되지 않았습니다. fit() 메서드를 먼저 호출하세요.")
        
        logger.info(f"ARIMA 예측 시작: {steps} 스텝")
        
        try:
            # 예측 수행
            forecast_result = self.model.forecast(
                steps=steps, 
                exog=exog,
                alpha=alpha
            )
            
            if isinstance(forecast_result, tuple):
                forecast_values, conf_int = forecast_result
            else:
                forecast_values = forecast_result
                conf_int = None
            
            # 예측 날짜 생성
            last_date = self.model_result.model.data.orig_endog.index[-1]
            forecast_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=steps,
                freq='D'
            )
            
            forecast_series = pd.Series(forecast_values, index=forecast_dates)
            
            # 신뢰구간 정리
            if conf_int is not None:
                confidence_df = pd.DataFrame(
                    conf_int,
                    index=forecast_dates,
                    columns=['lower_ci', 'upper_ci']
                )
            else:
                # 신뢰구간이 없는 경우 근사치 계산
                residual_std = self.model_result.residuals.std()
                confidence_df = pd.DataFrame({
                    'lower_ci': forecast_series - 1.96 * residual_std,
                    'upper_ci': forecast_series + 1.96 * residual_std
                }, index=forecast_dates)
            
            model_info = {
                'order': self.model_result.order,
                'seasonal_order': self.model_result.seasonal_order,
                'aic': self.model_result.aic,
                'bic': self.model_result.bic,
                'ljung_box_p_value': self.model_result.ljung_box_p_value
            }
            
            result = ARIMAForecastResult(
                forecast=forecast_series,
                confidence_intervals=confidence_df,
                forecast_dates=forecast_dates,
                model_info=model_info
            )
            
            logger.info(f"ARIMA 예측 완료: 평균 예측값 {forecast_series.mean():.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"ARIMA 예측 실패: {e}")
            raise
    
    def _prepare_data(self, series: pd.Series) -> pd.Series:
        """데이터 전처리"""
        # 결측값 제거
        clean_series = series.dropna()
        
        # 너무 짧은 시계열 확인
        if len(clean_series) < 50:
            raise ValueError(f"시계열이 너무 짧습니다: {len(clean_series)}개 관측값")
        
        # 이상치 제거 (선택적)
        q99 = clean_series.quantile(0.99)
        q01 = clean_series.quantile(0.01)
        clean_series = clean_series.clip(lower=q01, upper=q99)
        
        return clean_series
    
    def _check_stationarity(self, series: pd.Series) -> Dict[str, Any]:
        """정상성 검정"""
        try:
            # ADF 검정 (단위근 검정)
            adf_result = adfuller(series, autolag='AIC')
            adf_statistic = adf_result[0]
            adf_p_value = adf_result[1]
            adf_is_stationary = adf_p_value < 0.05
            
            # KPSS 검정 (정상성 검정)
            kpss_result = kpss(series, regression='ct', nlags='auto')
            kpss_statistic = kpss_result[0]
            kpss_p_value = kpss_result[1]
            kpss_is_stationary = kpss_p_value > 0.05
            
            return {
                'adf_statistic': adf_statistic,
                'adf_p_value': adf_p_value,
                'adf_is_stationary': adf_is_stationary,
                'kpss_statistic': kpss_statistic,
                'kpss_p_value': kpss_p_value,
                'kpss_is_stationary': kpss_is_stationary,
                'overall_stationary': adf_is_stationary and kpss_is_stationary
            }
            
        except Exception as e:
            logger.warning(f"정상성 검정 실패: {e}")
            return {
                'adf_is_stationary': False,
                'kpss_is_stationary': False,
                'overall_stationary': False
            }
    
    def _auto_arima_selection(self, 
                            series: pd.Series,
                            exog: Optional[pd.DataFrame] = None) -> Any:
        """자동 ARIMA 차수 선택"""
        logger.info("자동 ARIMA 차수 선택 시작...")
        
        try:
            auto_model = auto_arima(
                series,
                exogenous=exog,
                start_p=0, 
                start_q=0,
                max_p=self.config.max_p, 
                max_q=self.config.max_q,
                max_d=self.config.max_d,
                seasonal=self.config.seasonal,
                m=self.config.seasonal_period if self.config.seasonal else 1,
                information_criterion=self.config.information_criterion,
                stepwise=self.config.stepwise,
                suppress_warnings=self.config.suppress_warnings,
                error_action='ignore',
                trace=False,
                random_state=42
            )
            
            logger.info(f"자동 선택된 ARIMA 차수: {auto_model.order}")
            
            return auto_model
            
        except Exception as e:
            logger.error(f"자동 ARIMA 선택 실패: {e}")
            # 폴백: 기본 ARIMA(1,1,1) 모델
            logger.info("기본 ARIMA(1,1,1) 모델로 대체")
            model = ARIMA(series, order=(1, 1, 1), exog=exog)
            return model.fit(method=self.config.method, maxiter=self.config.maxiter)
    
    def _manual_order_selection(self, series: pd.Series) -> Tuple[int, int, int]:
        """수동 차수 선택 (정보 기준에 기반)"""
        logger.info("수동 ARIMA 차수 선택...")
        
        best_aic = float('inf')
        best_bic = float('inf')
        best_order_aic = (1, 1, 1)
        best_order_bic = (1, 1, 1)
        
        for p in range(self.config.max_p + 1):
            for d in range(self.config.max_d + 1):
                for q in range(self.config.max_q + 1):
                    try:
                        model = ARIMA(series, order=(p, d, q))
                        fitted_model = model.fit(
                            method=self.config.method,
                            maxiter=self.config.maxiter
                        )
                        
                        if fitted_model.aic < best_aic:
                            best_aic = fitted_model.aic
                            best_order_aic = (p, d, q)
                        
                        if fitted_model.bic < best_bic:
                            best_bic = fitted_model.bic
                            best_order_bic = (p, d, q)
                            
                    except Exception:
                        continue
        
        # 정보 기준에 따라 최적 차수 선택
        if self.config.information_criterion == 'aic':
            best_order = best_order_aic
        else:
            best_order = best_order_bic
        
        logger.info(f"수동 선택된 ARIMA 차수: {best_order}")
        return best_order
    
    def _get_seasonal_order(self) -> Tuple[int, int, int, int]:
        """계절 차수 설정"""
        # 기본 계절 차수 (석유업계 경험 기반)
        return (1, 1, 1, self.config.seasonal_period)
    
    def get_model_diagnostics(self) -> Dict[str, Any]:
        """모델 진단 정보"""
        if not self.is_fitted:
            return {}
        
        residuals = self.model_result.residuals
        
        return {
            'model_order': self.model_result.order,
            'seasonal_order': self.model_result.seasonal_order,
            'aic': self.model_result.aic,
            'bic': self.model_result.bic,
            'ljung_box_p_value': self.model_result.ljung_box_p_value,
            'residuals_mean': residuals.mean(),
            'residuals_std': residuals.std(),
            'residuals_skewness': residuals.skew(),
            'residuals_kurtosis': residuals.kurtosis(),
            'model_summary': self.model_result.model_summary[:500] + "..." if len(self.model_result.model_summary) > 500 else self.model_result.model_summary
        }
    
    def validate_model(self) -> Dict[str, Any]:
        """모델 검증"""
        if not self.is_fitted:
            return {'valid': False, 'reason': '모델이 학습되지 않음'}
        
        validation_results = {'valid': True, 'issues': []}
        
        # 잔차 검정
        if self.model_result.ljung_box_p_value < 0.05:
            validation_results['issues'].append('잔차에 자기상관이 존재함')
        
        # AIC/BIC 검정
        if self.model_result.aic > 1000:  # 임의 임계값
            validation_results['issues'].append('AIC 값이 너무 높음')
        
        # 잔차 분포 검정
        residuals = self.model_result.residuals
        if abs(residuals.skew()) > 2:
            validation_results['issues'].append('잔차 분포가 치우쳐짐')
        
        if len(validation_results['issues']) > 0:
            validation_results['valid'] = False
        
        return validation_results