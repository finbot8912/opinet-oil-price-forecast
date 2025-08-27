#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오피넷 실제 데이터 기반 지역별 조정 계수 계산
"""

# 오늘 수집한 실제 오피넷 데이터 (2025년 8월 24일)
ACTUAL_DATA = {
    "서울": {"regular_gasoline": 1721.30, "diesel": 1604.21},
    "부산": {"regular_gasoline": 1654.47, "diesel": 1527.09},
    "대구": {"regular_gasoline": 1633.07, "diesel": 1497.56},
    "인천": {"regular_gasoline": 1648.71, "diesel": 1523.55},
    "광주": {"regular_gasoline": 1645.48, "diesel": 1520.51},
    "대전": {"regular_gasoline": 1641.97, "diesel": 1523.35},
    "울산": {"regular_gasoline": 1633.45, "diesel": 1513.51},
    "경기": {"regular_gasoline": 1659.73, "diesel": 1526.05},
    "강원": {"regular_gasoline": 1679.62, "diesel": 1551.62},
    "충북": {"regular_gasoline": 1666.71, "diesel": 1538.10},
    "충남": {"regular_gasoline": 1668.87, "diesel": 1537.73},
    "전북": {"regular_gasoline": 1654.08, "diesel": 1525.38},
    "전남": {"regular_gasoline": 1668.66, "diesel": 1539.42},
    "경북": {"regular_gasoline": 1653.09, "diesel": 1520.99},
    "경남": {"regular_gasoline": 1654.24, "diesel": 1524.91},
    "제주": {"regular_gasoline": 1708.39, "diesel": 1584.30},
    "세종": {"regular_gasoline": 1649.70, "diesel": 1527.33}
}

# 전국 평균 계산
def calculate_national_average():
    gasoline_prices = [data["regular_gasoline"] for data in ACTUAL_DATA.values()]
    diesel_prices = [data["diesel"] for data in ACTUAL_DATA.values()]
    
    gasoline_avg = sum(gasoline_prices) / len(gasoline_prices)
    diesel_avg = sum(diesel_prices) / len(diesel_prices)
    
    return {
        "gasoline": round(gasoline_avg, 2),
        "diesel": round(diesel_avg, 2)
    }

# 지역별 조정 계수 계산
def calculate_regional_multipliers():
    national_avg = calculate_national_average()
    
    # 지역명 매핑 (한글 -> 영문)
    region_mapping = {
        "서울": "seoul",
        "부산": "busan", 
        "대구": "daegu",
        "인천": "incheon",
        "광주": "gwangju",
        "대전": "daejeon",
        "울산": "ulsan",
        "경기": "gyeonggi",
        "강원": "gangwon",
        "충북": "chungbuk",
        "충남": "chungnam",
        "전북": "jeonbuk",
        "전남": "jeonnam",
        "경북": "gyeongbuk",
        "경남": "gyeongnam",
        "제주": "jeju",
        "세종": "sejong"
    }
    
    multipliers = {}
    
    for korean_name, english_name in region_mapping.items():
        if korean_name in ACTUAL_DATA:
            region_data = ACTUAL_DATA[korean_name]
            
            gasoline_multiplier = round(region_data["regular_gasoline"] / national_avg["gasoline"], 4)
            diesel_multiplier = round(region_data["diesel"] / national_avg["diesel"], 4)
            
            multipliers[english_name] = {
                "gasoline": gasoline_multiplier,
                "diesel": diesel_multiplier
            }
    
    return multipliers

def generate_javascript_code():
    """JavaScript 코드 생성"""
    national_avg = calculate_national_average()
    multipliers = calculate_regional_multipliers()
    
    print("=" * 60)
    print("오피넷 실제 데이터 기반 업데이트 코드")
    print("=" * 60)
    
    print(f"\n// 전국 평균 (2025년 8월 24일 기준)")
    print(f"const basePrices = {{")
    print(f"    gasoline: {national_avg['gasoline']},  // 오피넷 전국 평균 보통휘발유 가격")
    print(f"    diesel: {national_avg['diesel']}     // 오피넷 전국 평균 자동차경유 가격")
    print(f"}};")
    
    print(f"\n// 지역별 조정 계수")
    print(f"const regionalMultipliers = {{")
    
    for region, data in multipliers.items():
        korean_name = {v: k for k, v in {
            "서울": "seoul", "부산": "busan", "대구": "daegu", "인천": "incheon",
            "광주": "gwangju", "대전": "daejeon", "울산": "ulsan", "경기": "gyeonggi",
            "강원": "gangwon", "충북": "chungbuk", "충남": "chungnam", "전북": "jeonbuk",
            "전남": "jeonnam", "경북": "gyeongbuk", "경남": "gyeongnam", "제주": "jeju", "세종": "sejong"
        }.items()}[region]
        
        actual_gasoline = ACTUAL_DATA[korean_name]["regular_gasoline"]
        actual_diesel = ACTUAL_DATA[korean_name]["diesel"]
        
        print(f"    {region}: {{ gasoline: {data['gasoline']}, diesel: {data['diesel']} }},  // 실제: 휘발유 {actual_gasoline:.0f}원, 경유 {actual_diesel:.0f}원")
    
    print(f"}};")
    
    print(f"\n데이터 기준일: 2025년 8월 24일")
    print(f"데이터 출처: 오피넷(OPINET)")

if __name__ == "__main__":
    generate_javascript_code()
