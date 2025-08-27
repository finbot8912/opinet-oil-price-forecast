#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지역별 연료별 예측 정확도 계산 시스템
8월 24일 기준 예측 vs 실제 오피넷 데이터 비교
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class RegionalAccuracyCalculator:
    """지역별 예측 정확도 계산기"""
    
    def __init__(self, base_date: str = "2025-08-24"):
        self.base_date = base_date
        self.regions = {
            "seoul": "서울",
            "busan": "부산", 
            "daegu": "대구",
            "incheon": "인천",
            "gwangju": "광주",
            "daejeon": "대전",
            "ulsan": "울산",
            "gyeonggi": "경기",
            "gangwon": "강원",
            "chungbuk": "충북",
            "chungnam": "충남",
            "jeonbuk": "전북",
            "jeonnam": "전남",
            "gyeongbuk": "경북",
            "gyeongnam": "경남",
            "jeju": "제주",
            "sejong": "세종"
        }
        
        # 8월 24일 기준 예측 데이터 로드
        self.forecast_data = self._load_forecast_data()
        
        # 실제 데이터 저장소 (수동 업데이트)
        self.actual_data = self._initialize_actual_data_structure()
    
    def _load_forecast_data(self) -> Dict:
        """8월 24일 기준 예측 데이터 로드"""
        try:
            with open("7day_regional_forecast.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ 예측 데이터 파일을 찾을 수 없습니다. 기본 구조를 생성합니다.")
            return {"forecasts": {}, "metadata": {"base_date": self.base_date}}
    
    def _initialize_actual_data_structure(self) -> Dict:
        """실제 데이터 저장 구조 초기화"""
        actual_data = {
            "metadata": {
                "last_updated": None,
                "data_source": "오피넷 수동 입력"
            },
            "daily_actual": {}
        }
        
        # 7일간 날짜별 구조 생성
        base = datetime.strptime(self.base_date, "%Y-%m-%d")
        for day in range(1, 8):  # 1일 후 ~ 7일 후
            target_date = base + timedelta(days=day)
            date_str = target_date.strftime("%Y-%m-%d")
            
            actual_data["daily_actual"][date_str] = {
                "date_label": f"{day}일 후",
                "target_date": date_str,
                "regions": {},
                "is_available": False,
                "updated_at": None
            }
            
            # 각 지역별 구조 생성
            for region_en, region_ko in self.regions.items():
                actual_data["daily_actual"][date_str]["regions"][region_en] = {
                    "region_name": region_ko,
                    "gasoline": None,  # 실제 보통휘발유 가격 (수동 입력)
                    "diesel": None,    # 실제 자동차경유 가격 (수동 입력)
                    "gasoline_forecast": None,  # 예측한 보통휘발유 가격
                    "diesel_forecast": None,    # 예측한 자동차경유 가격
                    "gasoline_accuracy": None,  # 보통휘발유 정확도
                    "diesel_accuracy": None     # 자동차경유 정확도
                }
        
        return actual_data
    
    def get_forecast_price(self, region: str, fuel_type: str, days_after: int) -> Optional[float]:
        """예측 가격 조회"""
        try:
            if region in self.forecast_data["forecasts"]:
                forecast_list = self.forecast_data["forecasts"][region]["daily_forecast"]
                if 0 <= days_after - 1 < len(forecast_list):
                    return forecast_list[days_after - 1][fuel_type]
            return None
        except (KeyError, IndexError, TypeError):
            return None
    
    def calculate_accuracy(self, predicted: float, actual: float) -> float:
        """
        예측 정확도 계산
        
        공식: 정확도 = max(0, 100 - |예측값 - 실제값| / 실제값 * 100)
        
        Args:
            predicted: 예측 가격
            actual: 실제 가격
        
        Returns:
            정확도 (0-100%)
        """
        if actual == 0:
            return 0.0
        
        # 절대 오차율 계산
        error_rate = abs(predicted - actual) / actual * 100
        
        # 정확도 계산 (최대 100%, 최소 0%)
        accuracy = max(0, 100 - error_rate)
        
        return round(accuracy, 2)
    
    def update_actual_data(self, date: str, region: str, gasoline_price: float, diesel_price: float):
        """
        실제 데이터 수동 업데이트
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            region: 지역 영문명
            gasoline_price: 실제 보통휘발유 가격
            diesel_price: 실제 자동차경유 가격
        """
        if date not in self.actual_data["daily_actual"]:
            print(f"❌ 잘못된 날짜입니다: {date}")
            return False
        
        if region not in self.regions:
            print(f"❌ 잘못된 지역입니다: {region}")
            return False
        
        # 해당 날짜의 며칠 후인지 계산
        base = datetime.strptime(self.base_date, "%Y-%m-%d")
        target = datetime.strptime(date, "%Y-%m-%d")
        days_after = (target - base).days
        
        # 예측 가격 조회
        gasoline_forecast = self.get_forecast_price(region, "gasoline", days_after)
        diesel_forecast = self.get_forecast_price(region, "diesel", days_after)
        
        # 실제 데이터 업데이트
        region_data = self.actual_data["daily_actual"][date]["regions"][region]
        region_data["gasoline"] = gasoline_price
        region_data["diesel"] = diesel_price
        region_data["gasoline_forecast"] = gasoline_forecast
        region_data["diesel_forecast"] = diesel_forecast
        
        # 정확도 계산
        if gasoline_forecast is not None:
            region_data["gasoline_accuracy"] = self.calculate_accuracy(gasoline_forecast, gasoline_price)
        
        if diesel_forecast is not None:
            region_data["diesel_accuracy"] = self.calculate_accuracy(diesel_forecast, diesel_price)
        
        # 메타데이터 업데이트
        self.actual_data["daily_actual"][date]["is_available"] = True
        self.actual_data["daily_actual"][date]["updated_at"] = datetime.now().isoformat()
        self.actual_data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        print(f"✅ {date} {self.regions[region]} 지역 실제 데이터 업데이트 완료")
        print(f"   보통휘발유: 예측 {gasoline_forecast}원 → 실제 {gasoline_price}원 (정확도: {region_data['gasoline_accuracy']}%)")
        print(f"   자동차경유: 예측 {diesel_forecast}원 → 실제 {diesel_price}원 (정확도: {region_data['diesel_accuracy']}%)")
        
        return True
    
    def bulk_update_daily_data(self, date: str, regional_data: Dict[str, Dict[str, float]]):
        """
        특정 날짜의 모든 지역 데이터 일괄 업데이트
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            regional_data: {"region_en": {"gasoline": price, "diesel": price}, ...}
        """
        print(f"\n🔄 {date} 전체 지역 데이터 일괄 업데이트 중...")
        
        success_count = 0
        for region, prices in regional_data.items():
            if self.update_actual_data(date, region, prices["gasoline"], prices["diesel"]):
                success_count += 1
        
        print(f"✅ {success_count}/{len(regional_data)}개 지역 업데이트 완료")
    
    def get_regional_accuracy_summary(self, region: str) -> Dict:
        """특정 지역의 7일간 정확도 요약"""
        summary = {
            "region_name": self.regions.get(region, region),
            "region_code": region,
            "daily_accuracy": {},
            "overall_gasoline_accuracy": None,
            "overall_diesel_accuracy": None,
            "available_days": 0
        }
        
        gasoline_accuracies = []
        diesel_accuracies = []
        
        for date_str, day_data in self.actual_data["daily_actual"].items():
            if day_data["is_available"] and region in day_data["regions"]:
                region_data = day_data["regions"][region]
                
                day_label = day_data["date_label"]
                summary["daily_accuracy"][day_label] = {
                    "date": date_str,
                    "gasoline_accuracy": region_data["gasoline_accuracy"],
                    "diesel_accuracy": region_data["diesel_accuracy"],
                    "gasoline_predicted": region_data["gasoline_forecast"],
                    "gasoline_actual": region_data["gasoline"],
                    "diesel_predicted": region_data["diesel_forecast"],
                    "diesel_actual": region_data["diesel"]
                }
                
                if region_data["gasoline_accuracy"] is not None:
                    gasoline_accuracies.append(region_data["gasoline_accuracy"])
                
                if region_data["diesel_accuracy"] is not None:
                    diesel_accuracies.append(region_data["diesel_accuracy"])
                
                summary["available_days"] += 1
        
        # 전체 평균 정확도 계산
        if gasoline_accuracies:
            summary["overall_gasoline_accuracy"] = round(sum(gasoline_accuracies) / len(gasoline_accuracies), 2)
        
        if diesel_accuracies:
            summary["overall_diesel_accuracy"] = round(sum(diesel_accuracies) / len(diesel_accuracies), 2)
        
        return summary
    
    def get_all_regions_accuracy(self) -> Dict:
        """전체 지역 정확도 요약"""
        all_regions = {}
        
        for region_en in self.regions.keys():
            all_regions[region_en] = self.get_regional_accuracy_summary(region_en)
        
        return all_regions
    
    def save_accuracy_data(self, filename: str = "regional_accuracy_data.json"):
        """정확도 데이터 저장"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.actual_data, f, ensure_ascii=False, indent=2)
        print(f"💾 정확도 데이터가 {filename}에 저장되었습니다.")
    
    def load_accuracy_data(self, filename: str = "regional_accuracy_data.json"):
        """저장된 정확도 데이터 로드"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.actual_data = json.load(f)
            print(f"📁 {filename}에서 정확도 데이터를 로드했습니다.")
            return True
        except FileNotFoundError:
            print(f"⚠️ {filename} 파일을 찾을 수 없습니다.")
            return False

def demo_usage():
    """사용 예시"""
    print("=" * 80)
    print("지역별 연료별 예측 정확도 계산 시스템 - 사용 예시")
    print("=" * 80)
    
    # 계산기 초기화
    calculator = RegionalAccuracyCalculator()
    
    # 8월 25일 서울 지역 실제 데이터 예시 (수동 입력)
    print("\n📝 8월 25일 서울 지역 실제 데이터 입력 예시:")
    calculator.update_actual_data(
        date="2025-08-25",  # 1일 후
        region="seoul",
        gasoline_price=1722.50,  # 실제 보통휘발유 가격
        diesel_price=1605.80     # 실제 자동차경유 가격
    )
    
    # 8월 26일 서울 지역 실제 데이터 예시 (수동 입력)
    print("\n📝 8월 26일 서울 지역 실제 데이터 입력 예시:")
    calculator.update_actual_data(
        date="2025-08-26",  # 2일 후
        region="seoul",
        gasoline_price=1720.10,  # 실제 보통휘발유 가격
        diesel_price=1603.40     # 실제 자동차경유 가격
    )
    
    # 서울 지역 정확도 요약
    print("\n📊 서울 지역 정확도 요약:")
    seoul_summary = calculator.get_regional_accuracy_summary("seoul")
    print(f"지역: {seoul_summary['region_name']}")
    print(f"데이터 가용 일수: {seoul_summary['available_days']}일")
    print(f"전체 보통휘발유 정확도: {seoul_summary['overall_gasoline_accuracy']}%")
    print(f"전체 자동차경유 정확도: {seoul_summary['overall_diesel_accuracy']}%")
    
    for day_label, day_data in seoul_summary['daily_accuracy'].items():
        print(f"\n  {day_label} ({day_data['date']}):")
        print(f"    보통휘발유: 예측 {day_data['gasoline_predicted']}원 vs 실제 {day_data['gasoline_actual']}원 → 정확도 {day_data['gasoline_accuracy']}%")
        print(f"    자동차경유: 예측 {day_data['diesel_predicted']}원 vs 실제 {day_data['diesel_actual']}원 → 정확도 {day_data['diesel_accuracy']}%")
    
    # 데이터 저장
    calculator.save_accuracy_data()
    
    print("\n" + "=" * 80)
    print("🔄 실제 사용 시:")
    print("1. 매일 오피넷에서 실제 데이터 수집")
    print("2. calculator.update_actual_data() 또는 calculator.bulk_update_daily_data() 사용")
    print("3. calculator.get_regional_accuracy_summary()로 정확도 확인")
    print("4. index.html에서 이 정확도 데이터를 실시간 표시")
    print("=" * 80)

if __name__ == "__main__":
    demo_usage()
