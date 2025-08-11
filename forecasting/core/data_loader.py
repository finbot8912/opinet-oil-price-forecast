"""
Data Loader for Oil Price Forecasting System
Optimized for petroleum industry data with 30+ years of domain expertise
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
from dataclasses import dataclass

from ..config.model_config import DataConfig

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataValidationResult:
    """데이터 검증 결과"""
    is_valid: bool
    missing_dates: List[str]
    outliers: List[Dict]
    data_quality_score: float
    recommendations: List[str]

class DataLoader:
    """
    석유업계 특화 데이터 로더
    - JSON 형식의 처리된 데이터 로드
    - 데이터 품질 검증 및 이상치 탐지
    - 지역별/전국 유가 데이터 통합
    - Dubai 유가, 환율, 유류세 데이터 연결
    """
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.data_path = Path(config.data_path)
        
        # 캐시된 데이터
        self._regional_data = None
        self._dubai_data = None
        self._exchange_rate_data = None
        self._fuel_tax_data = None
        self._national_data = None
        
        logger.info(f"DataLoader 초기화 완료: {self.data_path}")
    
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        모든 데이터 소스를 로드하고 통합
        
        Returns:
            Dict containing all loaded datasets
        """
        logger.info("전체 데이터 로딩 시작...")
        
        data = {}
        
        # 지역별 유가 데이터
        data['regional'] = self.load_regional_gas_prices()
        
        # Dubai 국제유가 데이터
        data['dubai'] = self.load_dubai_oil_prices()
        
        # 환율 데이터
        data['exchange_rate'] = self.load_exchange_rate()
        
        # 유류세 데이터
        data['fuel_tax'] = self.load_fuel_tax()
        
        # 전국 평균 유가 데이터
        data['national'] = self.load_national_gas_prices()
        
        logger.info(f"전체 데이터 로딩 완료: {len(data)}개 데이터셋")
        
        return data
    
    def load_regional_gas_prices(self) -> pd.DataFrame:
        """지역별 유가 데이터 로드"""
        if self._regional_data is not None:
            return self._regional_data
        
        file_path = self.data_path / self.config.regional_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 메타데이터 추출
            metadata = json_data.get('metadata', {})
            regions = metadata.get('regions', self.config.regions)
            fuel_types = metadata.get('fuel_types', self.config.fuel_types)
            
            # 데이터 변환
            records = []
            for item in json_data['data']:
                date = self._parse_date(item['date'])
                
                for fuel_type in fuel_types:
                    if fuel_type in item:
                        for region in regions:
                            if region in item[fuel_type]:
                                records.append({
                                    'date': date,
                                    'fuel_type': fuel_type,
                                    'region': region,
                                    'price': item[fuel_type][region]
                                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['date', 'fuel_type', 'region'])
            
            # 데이터 검증
            validation_result = self._validate_data(df, 'regional')
            if not validation_result.is_valid:
                logger.warning(f"지역별 데이터 품질 이슈 발견: {validation_result.recommendations}")
            
            self._regional_data = df
            logger.info(f"지역별 유가 데이터 로드 완료: {len(df)} 레코드")
            
            return df
            
        except Exception as e:
            logger.error(f"지역별 유가 데이터 로드 실패: {e}")
            raise
    
    def load_dubai_oil_prices(self) -> pd.DataFrame:
        """Dubai 국제유가 데이터 로드"""
        if self._dubai_data is not None:
            return self._dubai_data
        
        file_path = self.data_path / self.config.dubai_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 데이터 변환
            records = []
            for item in json_data['data']:
                date = self._parse_date(item['date'])
                records.append({
                    'date': date,
                    'dubai_krw_per_liter': item.get('krw_per_liter'),
                    'dubai_usd_per_barrel': item.get('usd_per_barrel')
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 결측값 처리
            df['dubai_krw_per_liter'] = df['dubai_krw_per_liter'].interpolate(method='linear')
            df['dubai_usd_per_barrel'] = df['dubai_usd_per_barrel'].interpolate(method='linear')
            
            self._dubai_data = df
            logger.info(f"Dubai 유가 데이터 로드 완료: {len(df)} 레코드")
            
            return df
            
        except Exception as e:
            logger.error(f"Dubai 유가 데이터 로드 실패: {e}")
            raise
    
    def load_exchange_rate(self) -> pd.DataFrame:
        """환율 데이터 로드"""
        if self._exchange_rate_data is not None:
            return self._exchange_rate_data
        
        file_path = self.data_path / self.config.exchange_rate_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 데이터 변환
            records = []
            for item in json_data['data']:
                date = self._parse_date(item['date'])
                records.append({
                    'date': date,
                    'usd_krw_rate': item.get('rate'),
                    'exchange_rate_change': item.get('change', 0)
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 환율 변동성 계산
            df['exchange_rate_volatility'] = df['usd_krw_rate'].rolling(window=7).std()
            df['exchange_rate_ma7'] = df['usd_krw_rate'].rolling(window=7).mean()
            df['exchange_rate_ma30'] = df['usd_krw_rate'].rolling(window=30).mean()
            
            self._exchange_rate_data = df
            logger.info(f"환율 데이터 로드 완료: {len(df)} 레코드")
            
            return df
            
        except Exception as e:
            logger.error(f"환율 데이터 로드 실패: {e}")
            raise
    
    def load_fuel_tax(self) -> pd.DataFrame:
        """유류세 데이터 로드"""
        if self._fuel_tax_data is not None:
            return self._fuel_tax_data
        
        file_path = self.data_path / self.config.fuel_tax_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 데이터 변환
            records = []
            for item in json_data['data']:
                date = self._parse_date(item['date'])
                records.append({
                    'date': date,
                    'gasoline_tax': item.get('gasoline_tax'),
                    'diesel_tax': item.get('diesel_tax'),
                    'tax_change_gasoline': item.get('gasoline_tax_change', 0),
                    'tax_change_diesel': item.get('diesel_tax_change', 0)
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 유류세 변화율 계산
            df['gasoline_tax_pct_change'] = df['gasoline_tax'].pct_change()
            df['diesel_tax_pct_change'] = df['diesel_tax'].pct_change()
            
            self._fuel_tax_data = df
            logger.info(f"유류세 데이터 로드 완료: {len(df)} 레코드")
            
            return df
            
        except Exception as e:
            logger.error(f"유류세 데이터 로드 실패: {e}")
            raise
    
    def load_national_gas_prices(self) -> pd.DataFrame:
        """전국 평균 유가 데이터 로드"""
        if self._national_data is not None:
            return self._national_data
        
        file_path = self.data_path / self.config.national_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 데이터 변환
            records = []
            for item in json_data['data']:
                date = self._parse_date(item['date'])
                records.append({
                    'date': date,
                    'national_gasoline': item.get('gasoline'),
                    'national_diesel': item.get('diesel'),
                    'national_kerosene': item.get('kerosene', None),
                    'national_lpg': item.get('lpg', None)
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 전국 평균 변동률 계산
            df['gasoline_change'] = df['national_gasoline'].pct_change()
            df['diesel_change'] = df['national_diesel'].pct_change()
            
            # 전국 평균 이동평균
            for period in [7, 14, 30]:
                df[f'gasoline_ma{period}'] = df['national_gasoline'].rolling(window=period).mean()
                df[f'diesel_ma{period}'] = df['national_diesel'].rolling(window=period).mean()
            
            self._national_data = df
            logger.info(f"전국 유가 데이터 로드 완료: {len(df)} 레코드")
            
            return df
            
        except Exception as e:
            logger.error(f"전국 유가 데이터 로드 실패: {e}")
            raise
    
    def get_integrated_dataset(self, 
                             fuel_type: str = 'gasoline',
                             region: Optional[str] = None) -> pd.DataFrame:
        """
        통합 데이터셋 생성 (예측 모델링용)
        
        Args:
            fuel_type: 연료 타입 ('gasoline' or 'diesel')
            region: 지역 (None이면 전국 평균)
        
        Returns:
            통합된 데이터프레임
        """
        logger.info(f"통합 데이터셋 생성 시작: {fuel_type}, {region}")
        
        # 모든 데이터 로드
        data = self.load_all_data()
        
        # 기준 데이터 설정
        if region:
            # 지역별 데이터
            base_df = data['regional'][
                (data['regional']['fuel_type'] == fuel_type) &
                (data['regional']['region'] == region)
            ][['date', 'price']].copy()
            base_df = base_df.rename(columns={'price': f'{region}_{fuel_type}'})
        else:
            # 전국 평균 데이터
            base_df = data['national'][['date', f'national_{fuel_type}']].copy()
        
        # Dubai 유가 데이터 병합
        base_df = pd.merge(base_df, data['dubai'], on='date', how='left')
        
        # 환율 데이터 병합
        base_df = pd.merge(base_df, data['exchange_rate'], on='date', how='left')
        
        # 유류세 데이터 병합
        base_df = pd.merge(base_df, data['fuel_tax'], on='date', how='left')
        
        # 날짜 순 정렬
        base_df = base_df.sort_values('date').reset_index(drop=True)
        
        # 결측값 처리
        base_df = base_df.fillna(method='forward').fillna(method='backward')
        
        logger.info(f"통합 데이터셋 생성 완료: {len(base_df)} 레코드, {len(base_df.columns)} 컬럼")
        
        return base_df
    
    def _parse_date(self, date_str: str) -> datetime:
        """다양한 날짜 형식 파싱"""
        try:
            # 표준 ISO 형식
            if '-' in date_str and len(date_str) == 10:
                return datetime.strptime(date_str, '%Y-%m-%d')
            
            # 한국식 형식 (09-1218일-01)
            if '일' in date_str:
                # 복잡한 한국식 날짜 파싱 로직
                parts = date_str.replace('일', '').split('-')
                if len(parts) == 3:
                    year = f"20{parts[0]}"
                    month_day = parts[1]
                    if len(month_day) == 4:  # MMDD
                        month = month_day[:2]
                        day = month_day[2:]
                    else:
                        month = "01"
                        day = "01"
                    return datetime(int(year), int(month), int(day))
            
            # 기본 파싱 시도
            return pd.to_datetime(date_str).to_pydatetime()
            
        except Exception as e:
            logger.warning(f"날짜 파싱 실패: {date_str}, 기본값 사용")
            return datetime.now()
    
    def _validate_data(self, df: pd.DataFrame, data_type: str) -> DataValidationResult:
        """데이터 품질 검증"""
        missing_dates = []
        outliers = []
        recommendations = []
        
        # 기본 통계
        total_records = len(df)
        missing_values = df.isnull().sum().sum()
        
        # 날짜 연속성 검증
        if 'date' in df.columns:
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())
            missing_dates = [d.strftime('%Y-%m-%d') for d in date_range 
                           if d not in df['date'].values]
        
        # 가격 데이터 이상치 검증 (석유업계 경험 기반)
        price_columns = [col for col in df.columns if 'price' in col or 'tax' in col]
        for col in price_columns:
            if col in df.columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                outlier_indices = df[outlier_mask].index.tolist()
                
                if len(outlier_indices) > 0:
                    outliers.extend([
                        {
                            'column': col,
                            'index': idx,
                            'value': df.loc[idx, col],
                            'date': df.loc[idx, 'date'] if 'date' in df.columns else None
                        }
                        for idx in outlier_indices[:10]  # 처음 10개만
                    ])
        
        # 데이터 품질 점수 계산
        quality_score = max(0, 1 - (missing_values / total_records) - (len(outliers) / total_records))
        
        # 권장사항 생성
        if missing_values > 0:
            recommendations.append(f"결측값 {missing_values}개 보간 필요")
        if len(missing_dates) > 0:
            recommendations.append(f"누락된 날짜 {len(missing_dates)}개 보완 필요")
        if len(outliers) > 0:
            recommendations.append(f"이상치 {len(outliers)}개 검토 필요")
        
        return DataValidationResult(
            is_valid=(quality_score >= 0.9),
            missing_dates=missing_dates[:10],  # 처음 10개만
            outliers=outliers,
            data_quality_score=quality_score,
            recommendations=recommendations
        )
    
    def get_data_info(self) -> Dict[str, Any]:
        """데이터 정보 요약"""
        data = self.load_all_data()
        
        info = {}
        for key, df in data.items():
            info[key] = {
                'records': len(df),
                'columns': list(df.columns),
                'date_range': {
                    'start': df['date'].min().isoformat() if 'date' in df.columns else None,
                    'end': df['date'].max().isoformat() if 'date' in df.columns else None
                },
                'missing_values': df.isnull().sum().sum(),
                'data_quality': self._validate_data(df, key).data_quality_score
            }
        
        return info