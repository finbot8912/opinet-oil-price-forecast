#!/usr/bin/env python3
"""
지역별 유가 차이 및 변동성 조정 모듈
한국 17개 시도별 유가 특성 반영
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class RegionalAdjustmentEngine:
    """지역별 유가 특성 조정 엔진"""
    
    def __init__(self):
        # 지역별 특성 계수 (실제 한국 지역별 유가 특성 기반)
        self.REGIONAL_CHARACTERISTICS = {
            # 수도권 (높은 경쟁, 상대적 안정성)
            'seoul': {
                'price_premium': 0.02,      # 서울 프리미엄 2%
                'volatility_factor': 0.95,   # 안정성 높음
                'competition_index': 0.9,    # 높은 경쟁
                'infrastructure_score': 1.0   # 최고 인프라
            },
            'gyeonggi': {
                'price_premium': -0.01,     # 경기도 할인 1%
                'volatility_factor': 0.98,   
                'competition_index': 0.85,
                'infrastructure_score': 0.95
            },
            'incheon': {
                'price_premium': 0.005,     
                'volatility_factor': 1.02,
                'competition_index': 0.8,
                'infrastructure_score': 0.9
            },
            
            # 광역시 (중간 수준 경쟁 및 안정성)
            'busan': {
                'price_premium': 0.01,
                'volatility_factor': 1.05,
                'competition_index': 0.75,
                'infrastructure_score': 0.85
            },
            'daegu': {
                'price_premium': 0.008,
                'volatility_factor': 1.08,
                'competition_index': 0.7,
                'infrastructure_score': 0.8
            },
            'gwangju': {
                'price_premium': 0.012,
                'volatility_factor': 1.1,
                'competition_index': 0.65,
                'infrastructure_score': 0.75
            },
            'daejeon': {
                'price_premium': 0.01,
                'volatility_factor': 1.06,
                'competition_index': 0.72,
                'infrastructure_score': 0.8
            },
            'ulsan': {
                'price_premium': -0.015,    # 정유도시 할인
                'volatility_factor': 1.03,
                'competition_index': 0.68,
                'infrastructure_score': 0.82
            },
            
            # 특별자치시/도
            'sejong': {
                'price_premium': 0.02,
                'volatility_factor': 1.12,
                'competition_index': 0.6,
                'infrastructure_score': 0.75
            },
            
            # 일반 도 지역 (높은 변동성, 낮은 경쟁)
            'gangwon': {
                'price_premium': 0.025,     # 산간지역 프리미엄
                'volatility_factor': 1.15,
                'competition_index': 0.55,
                'infrastructure_score': 0.65
            },
            'chungbuk': {
                'price_premium': 0.018,
                'volatility_factor': 1.12,
                'competition_index': 0.6,
                'infrastructure_score': 0.7
            },
            'chungnam': {
                'price_premium': 0.008,
                'volatility_factor': 1.08,
                'competition_index': 0.65,
                'infrastructure_score': 0.75
            },
            'jeonbuk': {
                'price_premium': 0.02,
                'volatility_factor': 1.18,
                'competition_index': 0.5,
                'infrastructure_score': 0.65
            },
            'jeonnam': {
                'price_premium': 0.015,
                'volatility_factor': 1.15,
                'competition_index': 0.55,
                'infrastructure_score': 0.7
            },
            'gyeongbuk': {
                'price_premium': 0.022,
                'volatility_factor': 1.2,
                'competition_index': 0.48,
                'infrastructure_score': 0.6
            },
            'gyeongnam': {
                'price_premium': 0.01,
                'volatility_factor': 1.1,
                'competition_index': 0.62,
                'infrastructure_score': 0.72
            },
            
            # 도서지역 (최고 프리미엄, 높은 변동성)
            'jeju': {
                'price_premium': 0.04,      # 도서지역 프리미엄 4%
                'volatility_factor': 1.25,  # 높은 변동성
                'competition_index': 0.4,    # 낮은 경쟁
                'infrastructure_score': 0.55 # 제한적 인프라
            }
        }
        
        # 연료별 지역 민감도
        self.FUEL_REGIONAL_SENSITIVITY = {
            'gasoline': {
                'price_sensitivity': 1.0,    # 기준값
                'volatility_sensitivity': 1.0, 
                'seasonal_sensitivity': 1.0
            },
            'diesel': {
                'price_sensitivity': 0.8,    # 경유는 가격 민감도 낮음
                'volatility_sensitivity': 1.2, # 변동성 민감도 높음
                'seasonal_sensitivity': 1.1   # 계절성 민감도 높음
            }
        }
    
    def get_regional_characteristics(self, region: str) -> Dict[str, float]:
        """지역 특성 반환"""
        return self.REGIONAL_CHARACTERISTICS.get(region, {
            'price_premium': 0.01,
            'volatility_factor': 1.1,
            'competition_index': 0.6,
            'infrastructure_score': 0.7
        })
    
    def calculate_regional_price_adjustment(self, base_price: float, region: str, fuel_type: str) -> float:
        """지역별 가격 조정 계산"""
        
        regional_chars = self.get_regional_characteristics(region)
        fuel_sensitivity = self.FUEL_REGIONAL_SENSITIVITY[fuel_type]
        
        # 기본 지역 프리미엄/할인
        price_premium = regional_chars['price_premium'] * fuel_sensitivity['price_sensitivity']
        
        # 인프라 점수에 따른 추가 조정
        infra_adjustment = (1.0 - regional_chars['infrastructure_score']) * 0.01
        
        # 경쟁 지수에 따른 조정 (경쟁이 낮으면 가격 높음)
        competition_adjustment = (1.0 - regional_chars['competition_index']) * 0.005
        
        total_adjustment = price_premium + infra_adjustment + competition_adjustment
        
        return base_price * (1 + total_adjustment)
    
    def calculate_regional_volatility_adjustment(self, base_volatility: float, region: str, fuel_type: str) -> float:
        """지역별 변동성 조정 계산"""
        
        regional_chars = self.get_regional_characteristics(region)
        fuel_sensitivity = self.FUEL_REGIONAL_SENSITIVITY[fuel_type]
        
        # 지역 변동성 팩터 적용
        volatility_factor = regional_chars['volatility_factor']
        
        # 연료별 민감도 반영
        adjusted_factor = 1.0 + (volatility_factor - 1.0) * fuel_sensitivity['volatility_sensitivity']
        
        return base_volatility * adjusted_factor
    
    def apply_regional_seasonal_adjustment(self, seasonal_factor: float, region: str, fuel_type: str) -> float:
        """지역별 계절성 조정"""
        
        regional_chars = self.get_regional_characteristics(region)
        fuel_sensitivity = self.FUEL_REGIONAL_SENSITIVITY[fuel_type]
        
        # 인프라 점수가 낮을수록 계절적 영향 증가
        infra_effect = (1.0 - regional_chars['infrastructure_score']) * 0.2
        
        # 경쟁이 낮을수록 계절적 변동 증가
        competition_effect = (1.0 - regional_chars['competition_index']) * 0.1
        
        # 지역별 계절성 증폭
        seasonal_amplification = 1.0 + infra_effect + competition_effect
        
        # 연료별 민감도 반영
        final_amplification = seasonal_amplification * fuel_sensitivity['seasonal_sensitivity']
        
        # 계절성 팩터 조정 (기준값 1.0에서의 편차를 증폭)
        adjusted_seasonal_factor = 1.0 + (seasonal_factor - 1.0) * final_amplification
        
        return adjusted_seasonal_factor
    
    def calculate_regional_forecast_confidence(self, base_confidence: float, region: str, fuel_type: str, days_ahead: int) -> float:
        """지역별 예측 신뢰도 계산"""
        
        regional_chars = self.get_regional_characteristics(region)
        
        # 지역 안정성 점수 계산
        stability_score = (
            regional_chars['competition_index'] * 0.4 +      # 경쟁도
            regional_chars['infrastructure_score'] * 0.3 +   # 인프라
            (2.0 - regional_chars['volatility_factor']) * 0.3 # 안정성
        )
        
        # 시간에 따른 신뢰도 감소 (지역별 차등 적용)
        time_decay = days_ahead * 0.01 * (2.0 - stability_score)
        
        # 최종 신뢰도 계산
        adjusted_confidence = base_confidence * stability_score - time_decay
        
        return max(adjusted_confidence, 0.5)  # 최소 50% 신뢰도 보장
    
    def generate_regional_adjustment_report(self) -> Dict:
        """지역별 조정 특성 리포트 생성"""
        
        report = {
            'summary': {
                'total_regions': len(self.REGIONAL_CHARACTERISTICS),
                'highest_premium_region': None,
                'lowest_premium_region': None,
                'most_volatile_region': None,
                'most_stable_region': None
            },
            'regional_analysis': {}
        }
        
        # 분석을 위한 데이터 수집
        premiums = []
        volatilities = []
        
        for region, chars in self.REGIONAL_CHARACTERISTICS.items():
            premiums.append((region, chars['price_premium']))
            volatilities.append((region, chars['volatility_factor']))
            
            # 지역별 상세 분석
            report['regional_analysis'][region] = {
                'characteristics': chars,
                'classification': self._classify_region(chars),
                'risk_level': self._calculate_risk_level(chars)
            }
        
        # 요약 정보 업데이트
        premiums.sort(key=lambda x: x[1])
        volatilities.sort(key=lambda x: x[1])
        
        report['summary']['highest_premium_region'] = premiums[-1][0]
        report['summary']['lowest_premium_region'] = premiums[0][0]
        report['summary']['most_volatile_region'] = volatilities[-1][0]
        report['summary']['most_stable_region'] = volatilities[0][0]
        
        return report
    
    def _classify_region(self, characteristics: Dict[str, float]) -> str:
        """지역 분류"""
        price_premium = characteristics['price_premium']
        volatility = characteristics['volatility_factor']
        
        if price_premium > 0.02 and volatility > 1.15:
            return "고비용_고변동"
        elif price_premium > 0.02:
            return "고비용_안정"
        elif volatility > 1.15:
            return "저비용_고변동"
        else:
            return "저비용_안정"
    
    def _calculate_risk_level(self, characteristics: Dict[str, float]) -> str:
        """위험 수준 계산"""
        risk_score = (
            characteristics['price_premium'] * 50 +
            (characteristics['volatility_factor'] - 1.0) * 20 +
            (1.0 - characteristics['competition_index']) * 30 +
            (1.0 - characteristics['infrastructure_score']) * 25
        )
        
        if risk_score > 0.05:
            return "높음"
        elif risk_score > 0.02:
            return "보통"
        else:
            return "낮음"

def main():
    """테스트 실행"""
    engine = RegionalAdjustmentEngine()
    
    print("지역별 유가 조정 특성 분석")
    print("=" * 60)
    
    # 리포트 생성
    report = engine.generate_regional_adjustment_report()
    
    print(f"\n전체 분석 지역 수: {report['summary']['total_regions']}")
    print(f"최고 프리미엄 지역: {report['summary']['highest_premium_region']}")
    print(f"최저 프리미엄 지역: {report['summary']['lowest_premium_region']}")
    print(f"최고 변동성 지역: {report['summary']['most_volatile_region']}")
    print(f"최고 안정성 지역: {report['summary']['most_stable_region']}")
    
    print("\n지역별 분류:")
    classifications = {}
    for region, analysis in report['regional_analysis'].items():
        classification = analysis['classification']
        risk_level = analysis['risk_level']
        
        if classification not in classifications:
            classifications[classification] = []
        classifications[classification].append(f"{region}({risk_level})")
    
    for classification, regions in classifications.items():
        print(f"  {classification}: {', '.join(regions)}")
    
    print("\n샘플 가격 조정 (기준가 1500원):")
    base_price = 1500
    
    for region in ['seoul', 'jeju', 'ulsan', 'gyeongbuk']:
        gasoline_price = engine.calculate_regional_price_adjustment(base_price, region, 'gasoline')
        diesel_price = engine.calculate_regional_price_adjustment(base_price, region, 'diesel')
        
        print(f"  {region:10s}: 휘발유 {gasoline_price:7.2f}원, 경유 {diesel_price:7.2f}원")

if __name__ == "__main__":
    main()