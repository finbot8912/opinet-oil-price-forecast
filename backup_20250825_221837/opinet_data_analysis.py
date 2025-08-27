#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오피넷 유가 데이터 분석 스크립트
2025년 8월 24일 지역별 평균 판매가격 분석
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

# 오피넷에서 수집한 지역별 유가 데이터 (2025년 8월 24일 기준)
OPINET_DATA = {
    "date": "2025년 8월 24일",
    "regions": [
        {"region": "서울", "premium_gasoline": 1971.33, "regular_gasoline": 1721.30, "diesel": 1604.21, "kerosene": 1527.64},
        {"region": "부산", "premium_gasoline": 1900.73, "regular_gasoline": 1654.47, "diesel": 1527.09, "kerosene": 1433.20},
        {"region": "대구", "premium_gasoline": 1913.95, "regular_gasoline": 1633.07, "diesel": 1497.56, "kerosene": 1335.64},
        {"region": "인천", "premium_gasoline": 1891.22, "regular_gasoline": 1648.71, "diesel": 1523.55, "kerosene": 1347.28},
        {"region": "광주", "premium_gasoline": 1866.16, "regular_gasoline": 1645.48, "diesel": 1520.51, "kerosene": 1435.25},
        {"region": "대전", "premium_gasoline": 1921.79, "regular_gasoline": 1641.97, "diesel": 1523.35, "kerosene": 1366.38},
        {"region": "울산", "premium_gasoline": 1940.71, "regular_gasoline": 1633.45, "diesel": 1513.51, "kerosene": 1404.29},
        {"region": "경기", "premium_gasoline": 1905.32, "regular_gasoline": 1659.73, "diesel": 1526.05, "kerosene": 1341.44},
        {"region": "강원", "premium_gasoline": 1896.12, "regular_gasoline": 1679.62, "diesel": 1551.62, "kerosene": 1242.79},
        {"region": "충북", "premium_gasoline": 1903.79, "regular_gasoline": 1666.71, "diesel": 1538.10, "kerosene": 1259.16},
        {"region": "충남", "premium_gasoline": 1907.58, "regular_gasoline": 1668.87, "diesel": 1537.73, "kerosene": 1253.03},
        {"region": "전북", "premium_gasoline": 1896.46, "regular_gasoline": 1654.08, "diesel": 1525.38, "kerosene": 1234.47},
        {"region": "전남", "premium_gasoline": 1922.02, "regular_gasoline": 1668.66, "diesel": 1539.42, "kerosene": 1258.60},
        {"region": "경북", "premium_gasoline": 1901.26, "regular_gasoline": 1653.09, "diesel": 1520.99, "kerosene": 1260.33},
        {"region": "경남", "premium_gasoline": 1896.60, "regular_gasoline": 1654.24, "diesel": 1524.91, "kerosene": 1307.03},
        {"region": "제주", "premium_gasoline": 2029.00, "regular_gasoline": 1708.39, "diesel": 1584.30, "kerosene": 1243.40},
        {"region": "세종", "premium_gasoline": 1902.25, "regular_gasoline": 1649.70, "diesel": 1527.33, "kerosene": 1300.00}
    ]
}


class OpinetDataAnalyzer:
    """오피넷 유가 데이터 분석 클래스"""
    
    def __init__(self, data: Dict):
        self.data = data
        self.regions = data["regions"]
        self.fuel_types = ["premium_gasoline", "regular_gasoline", "diesel", "kerosene"]
        self.fuel_names = {
            "premium_gasoline": "고급휘발유",
            "regular_gasoline": "보통휘발유", 
            "diesel": "자동차용경유",
            "kerosene": "실내등유"
        }
    
    def 전국_평균_계산(self) -> Dict[str, float]:
        """전국 평균 유가 계산"""
        averages = {}
        
        for fuel_type in self.fuel_types:
            prices = [region[fuel_type] for region in self.regions]
            averages[fuel_type] = round(statistics.mean(prices), 2)
            
        return averages
    
    def 지역별_순위_계산(self, fuel_type: str, ascending: bool = True) -> List[Tuple[str, float]]:
        """특정 연료별 지역 순위 계산"""
        prices = [(region["region"], region[fuel_type]) for region in self.regions]
        return sorted(prices, key=lambda x: x[1], reverse=not ascending)
    
    def 최고_최저_가격_찾기(self) -> Dict:
        """연료별 최고/최저 가격과 지역 찾기"""
        result = {}
        
        for fuel_type in self.fuel_types:
            prices = [(region["region"], region[fuel_type]) for region in self.regions]
            
            # 최고가
            max_price = max(prices, key=lambda x: x[1])
            # 최저가
            min_price = min(prices, key=lambda x: x[1])
            
            result[fuel_type] = {
                "highest": {"region": max_price[0], "price": max_price[1]},
                "lowest": {"region": min_price[0], "price": min_price[1]},
                "price_gap": round(max_price[1] - min_price[1], 2)
            }
            
        return result
    
    def 지역별_가격_차이_분석(self) -> Dict:
        """지역별 가격 차이 분석 (전국 평균 대비)"""
        national_avg = self.전국_평균_계산()
        result = {}
        
        for region_data in self.regions:
            region_name = region_data["region"]
            result[region_name] = {}
            
            for fuel_type in self.fuel_types:
                current_price = region_data[fuel_type]
                avg_price = national_avg[fuel_type]
                diff = round(current_price - avg_price, 2)
                diff_percent = round((diff / avg_price) * 100, 2)
                
                result[region_name][fuel_type] = {
                    "price": current_price,
                    "diff_from_avg": diff,
                    "diff_percent": diff_percent
                }
                
        return result
    
    def 연료별_가격_분포_통계(self) -> Dict:
        """연료별 가격 분포 통계"""
        result = {}
        
        for fuel_type in self.fuel_types:
            prices = [region[fuel_type] for region in self.regions]
            
            result[fuel_type] = {
                "mean": round(statistics.mean(prices), 2),
                "median": round(statistics.median(prices), 2),
                "std_dev": round(statistics.stdev(prices), 2),
                "min": min(prices),
                "max": max(prices),
                "range": round(max(prices) - min(prices), 2)
            }
            
        return result
    
    def 서울_기준_가격_비교(self) -> Dict:
        """서울 기준 다른 지역 가격 비교"""
        seoul_data = next(region for region in self.regions if region["region"] == "서울")
        result = {}
        
        for region_data in self.regions:
            if region_data["region"] == "서울":
                continue
                
            region_name = region_data["region"]
            result[region_name] = {}
            
            for fuel_type in self.fuel_types:
                seoul_price = seoul_data[fuel_type]
                region_price = region_data[fuel_type]
                diff = round(region_price - seoul_price, 2)
                diff_percent = round((diff / seoul_price) * 100, 2)
                
                result[region_name][fuel_type] = {
                    "price": region_price,
                    "seoul_price": seoul_price,
                    "diff": diff,
                    "diff_percent": diff_percent,
                    "cheaper": diff < 0
                }
                
        return result
    
    def 종합_분석_보고서_생성(self) -> Dict:
        """종합 분석 보고서 생성"""
        return {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_date": self.data["date"],
            "total_regions": len(self.regions),
            "national_averages": self.전국_평균_계산(),
            "price_extremes": self.최고_최저_가격_찾기(),
            "price_statistics": self.연료별_가격_분포_통계(),
            "regional_comparison": self.지역별_가격_차이_분석(),
            "seoul_comparison": self.서울_기준_가격_비교()
        }


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("오피넷 유가 데이터 분석 결과")
    print(f"데이터 기준일: {OPINET_DATA['date']}")
    print("=" * 60)
    
    # 분석기 초기화
    analyzer = OpinetDataAnalyzer(OPINET_DATA)
    
    # 1. 전국 평균 유가
    print("\n📊 전국 평균 유가 (원/리터)")
    print("-" * 40)
    national_avg = analyzer.전국_평균_계산()
    for fuel_type, avg_price in national_avg.items():
        fuel_name = analyzer.fuel_names[fuel_type]
        print(f"{fuel_name:10}: {avg_price:>8.2f}원")
    
    # 2. 연료별 최고/최저 가격
    print("\n🔥 연료별 최고/최저 가격")
    print("-" * 40)
    extremes = analyzer.최고_최저_가격_찾기()
    for fuel_type, data in extremes.items():
        fuel_name = analyzer.fuel_names[fuel_type]
        print(f"\n{fuel_name}:")
        print(f"  최고가: {data['highest']['region']:6} {data['highest']['price']:>8.2f}원")
        print(f"  최저가: {data['lowest']['region']:6} {data['lowest']['price']:>8.2f}원")
        print(f"  가격차: {data['price_gap']:>8.2f}원")
    
    # 3. 보통휘발유 지역별 순위 (저렴한 순)
    print("\n⛽ 보통휘발유 지역별 가격 순위 (저렴한 순)")
    print("-" * 40)
    gasoline_ranking = analyzer.지역별_순위_계산("regular_gasoline", ascending=True)
    for i, (region, price) in enumerate(gasoline_ranking, 1):
        print(f"{i:2d}. {region:6}: {price:>8.2f}원")
    
    # 4. 경유 지역별 순위 (저렴한 순)
    print("\n🚛 자동차용경유 지역별 가격 순위 (저렴한 순)")
    print("-" * 40)
    diesel_ranking = analyzer.지역별_순위_계산("diesel", ascending=True)
    for i, (region, price) in enumerate(diesel_ranking, 1):
        print(f"{i:2d}. {region:6}: {price:>8.2f}원")
    
    # 5. 서울 기준 가격 차이 (보통휘발유)
    print("\n🏢 서울 기준 보통휘발유 가격 차이")
    print("-" * 40)
    seoul_comparison = analyzer.서울_기준_가격_비교()
    seoul_gasoline_price = next(region["regular_gasoline"] for region in analyzer.regions if region["region"] == "서울")
    print(f"서울 기준 가격: {seoul_gasoline_price:>8.2f}원")
    print()
    
    # 저렴한 지역들
    cheaper_regions = []
    expensive_regions = []
    
    for region, data in seoul_comparison.items():
        gasoline_data = data["regular_gasoline"]
        if gasoline_data["cheaper"]:
            cheaper_regions.append((region, gasoline_data["diff"]))
        else:
            expensive_regions.append((region, gasoline_data["diff"]))
    
    # 저렴한 지역 정렬 (차이가 큰 순)
    cheaper_regions.sort(key=lambda x: x[1])
    print("서울보다 저렴한 지역:")
    for region, diff in cheaper_regions:
        print(f"  {region:6}: {diff:>7.2f}원 저렴")
    
    # 비싼 지역 정렬 (차이가 큰 순)
    expensive_regions.sort(key=lambda x: x[1], reverse=True)
    print("\n서울보다 비싼 지역:")
    for region, diff in expensive_regions:
        print(f"  {region:6}: +{diff:>6.2f}원 비쌈")
    
    # 6. 가격 분포 통계
    print("\n📈 연료별 가격 분포 통계")
    print("-" * 40)
    statistics_data = analyzer.연료별_가격_분포_통계()
    for fuel_type, stats in statistics_data.items():
        fuel_name = analyzer.fuel_names[fuel_type]
        print(f"\n{fuel_name}:")
        print(f"  평균:     {stats['mean']:>8.2f}원")
        print(f"  중앙값:   {stats['median']:>8.2f}원")
        print(f"  표준편차: {stats['std_dev']:>8.2f}원")
        print(f"  최소값:   {stats['min']:>8.2f}원")
        print(f"  최대값:   {stats['max']:>8.2f}원")
        print(f"  범위:     {stats['range']:>8.2f}원")
    
    # 7. 종합 분석 보고서를 JSON으로 저장
    report = analyzer.종합_분석_보고서_생성()
    
    # 분석 결과를 JSON 파일로 저장
    with open("opinet_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n💾 상세 분석 보고서가 'opinet_analysis_report.json' 파일로 저장되었습니다.")
    print("=" * 60)


if __name__ == "__main__":
    main()
