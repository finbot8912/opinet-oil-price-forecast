#!/usr/bin/env python3
"""
개선된 데이터 처리기
엑셀 파일 구조를 정확히 파악하여 올바른 데이터 추출
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedOilPriceDataProcessor:
    """개선된 유가 데이터 처리 클래스"""
    
    def __init__(self):
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 지역 매핑
        self.regions = [
            "seoul", "busan", "daegu", "incheon", "gwangju", "daejeon", 
            "ulsan", "gyeonggi", "gangwon", "chungbuk", "chungnam", 
            "jeonbuk", "jeonnam", "gyeongbuk", "gyeongnam", "jeju", "sejong"
        ]
    
    def parse_korean_date(self, date_str):
        """한국어 날짜 형식을 표준 형식으로 변환"""
        if pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # "2010년01월" -> "2010-01-01"
        if "년" in date_str and "월" in date_str:
            try:
                parts = date_str.replace("년", "-").replace("월", "")
                if "주" in parts:
                    # 주차 정보가 있는 경우
                    year, month, week = parts.replace("주", "").split("-")
                    day = min(int(week) * 7 - 6, 28)  # 주차를 일로 변환
                    return f"{year}-{month.zfill(2)}-{str(day).zfill(2)}"
                else:
                    return f"{parts}-01"
            except:
                return date_str
        
        return date_str
    
    def process_regional_gas_prices(self):
        """지역별 주유소 판매가 데이터 처리"""
        logger.info("지역별 주유소 판매가 처리 시작...")
        
        try:
            df = pd.read_excel("유가변동1.xlsx", sheet_name="5.지역별주유소 판매가", header=None)
            
            processed_data = {
                "metadata": {
                    "source": "지역별주유소 판매가",
                    "fuel_types": ["gasoline", "diesel"],
                    "regions": self.regions,
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            # 첫 번째 행 건너뛰고 두 번째 행부터 시작 (헤더 정보)
            # 실제 데이터는 세 번째 행부터 시작
            for i in range(2, len(df)):
                row = df.iloc[i]
                date_raw = row.iloc[0]
                
                if pd.isna(date_raw):
                    continue
                
                date_parsed = self.parse_korean_date(date_raw)
                
                monthly_data = {
                    "date": date_parsed,
                    "gasoline": {},
                    "diesel": {}
                }
                
                # 휘발유 가격 (컬럼 1-17)
                for j, region in enumerate(self.regions):
                    if j + 1 < len(row):
                        price = row.iloc[j + 1]
                        if pd.notna(price) and isinstance(price, (int, float)) and price > 0:
                            monthly_data["gasoline"][region] = float(price)
                
                # 경유 가격 (컬럼 18-34)
                for j, region in enumerate(self.regions):
                    if j + 18 < len(row):
                        price = row.iloc[j + 18]
                        if pd.notna(price) and isinstance(price, (int, float)) and price > 0:
                            monthly_data["diesel"][region] = float(price)
                
                # 데이터가 있는 경우만 추가
                if monthly_data["gasoline"] or monthly_data["diesel"]:
                    processed_data["data"].append(monthly_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"지역별 가격 처리 오류: {e}")
            return {}
    
    def process_national_gas_prices(self):
        """전국 주유소 판매가 처리"""
        logger.info("전국 주유소 판매가 처리 시작...")
        
        try:
            df = pd.read_excel("유가변동1.xlsx", sheet_name="4.전국주유소 판매가")
            
            processed_data = {
                "metadata": {
                    "source": "전국주유소 판매가",
                    "frequency": "daily",
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            for _, row in df.iterrows():
                date_raw = row.iloc[0]
                gasoline_price = row.iloc[1] if len(row) > 1 else None
                diesel_price = row.iloc[2] if len(row) > 2 else None
                
                if pd.isna(date_raw):
                    continue
                
                # 날짜 변환
                date_parsed = self.parse_korean_date(date_raw)
                
                daily_data = {
                    "date": date_parsed,
                    "gasoline": float(gasoline_price) if pd.notna(gasoline_price) else None,
                    "diesel": float(diesel_price) if pd.notna(diesel_price) else None
                }
                
                processed_data["data"].append(daily_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"전국 가격 처리 오류: {e}")
            return {}
    
    def process_dubai_oil_prices(self):
        """Dubai 국제유가 처리"""
        logger.info("Dubai 국제유가 처리 시작...")
        
        try:
            df = pd.read_excel("유가변동1.xlsx", sheet_name="7.Dubai 국제유가", header=None)
            
            processed_data = {
                "metadata": {
                    "source": "Dubai 국제유가",
                    "units": {"krw": "원/리터", "usd": "달러/배럴"},
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            # 첫 번째 행은 헤더이므로 건너뛰기
            for i in range(1, len(df)):
                row = df.iloc[i]
                date_raw = row.iloc[0]
                
                if pd.isna(date_raw) or not isinstance(date_raw, str):
                    continue
                
                krw_price = row.iloc[1] if len(row) > 1 else None
                usd_price = row.iloc[2] if len(row) > 2 else None
                
                # 숫자가 아닌 값들 필터링
                if pd.notna(krw_price) and not isinstance(krw_price, (int, float)):
                    if str(krw_price) in ["원/리터", "Dubai"]:
                        continue
                
                if pd.notna(usd_price) and not isinstance(usd_price, (int, float)):
                    if str(usd_price) in ["달러/배럴"]:
                        continue
                
                oil_data = {
                    "date": self.parse_korean_date(date_raw),
                    "krw_per_liter": float(krw_price) if pd.notna(krw_price) else None,
                    "usd_per_barrel": float(usd_price) if pd.notna(usd_price) else None
                }
                
                processed_data["data"].append(oil_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Dubai 유가 처리 오류: {e}")
            return {}
    
    def process_exchange_rate(self):
        """환율 데이터 처리"""
        logger.info("환율 데이터 처리 시작...")
        
        try:
            df = pd.read_excel("유가변동1.xlsx", sheet_name="11.환율")
            
            processed_data = {
                "metadata": {
                    "source": "환율",
                    "currency_pair": "USD/KRW",
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            for _, row in df.iterrows():
                date_raw = row.iloc[0]
                rate = row.iloc[1] if len(row) > 1 else None
                
                if pd.isna(date_raw) or pd.isna(rate):
                    continue
                
                rate_data = {
                    "date": self.parse_korean_date(str(date_raw)),
                    "usd_krw": float(rate)
                }
                
                processed_data["data"].append(rate_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"환율 처리 오류: {e}")
            return {}
    
    def process_fuel_tax(self):
        """유류세 데이터 처리"""
        logger.info("유류세 데이터 처리 시작...")
        
        try:
            df = pd.read_excel("유가변동1.xlsx", sheet_name="3.유류세", header=None)
            
            processed_data = {
                "metadata": {
                    "source": "유류세",
                    "components": ["개별소비세", "교통에너지환경세", "교육세", "주행세"],
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            # 헤더 정보를 건너뛰고 실제 데이터만 처리
            for i in range(2, len(df)):
                row = df.iloc[i]
                
                # 첫 번째 컬럼이 날짜인 행만 처리
                if pd.isna(row.iloc[0]) or not isinstance(row.iloc[0], str):
                    continue
                
                date_str = str(row.iloc[0])
                if "일" not in date_str:
                    continue
                
                tax_data = {
                    "date": self.parse_korean_date(date_str),
                    "gasoline": {
                        "individual_consumption": float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0,
                        "transportation_energy": float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                        "education": float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0,
                        "driving": float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0,
                        "total": float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                    },
                    "diesel": {
                        "individual_consumption": float(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else 0,
                        "transportation_energy": float(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else 0,
                        "education": float(row.iloc[9]) if len(row) > 9 and pd.notna(row.iloc[9]) else 0,
                        "driving": float(row.iloc[10]) if len(row) > 10 and pd.notna(row.iloc[10]) else 0,
                        "total": float(row.iloc[11]) if len(row) > 11 and pd.notna(row.iloc[11]) else 0
                    }
                }
                
                processed_data["data"].append(tax_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"유류세 처리 오류: {e}")
            return {}
    
    def save_json(self, data, filename):
        """JSON 파일 저장"""
        if not data:
            logger.warning(f"빈 데이터: {filename}")
            return False
            
        try:
            filepath = self.processed_dir / f"{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"저장 완료: {filepath} ({len(data.get('data', []))}개 레코드)")
            return True
            
        except Exception as e:
            logger.error(f"저장 실패: {filename} -> {e}")
            return False
    
    def process_all(self):
        """모든 데이터 처리"""
        logger.info("=== 데이터 처리 시작 ===")
        
        results = {}
        
        # 1. 지역별 주유소 가격
        regional_data = self.process_regional_gas_prices()
        results["regional_prices"] = self.save_json(regional_data, "regional_gas_prices")
        
        # 2. 전국 주유소 가격
        national_data = self.process_national_gas_prices()
        results["national_prices"] = self.save_json(national_data, "national_gas_prices")
        
        # 3. Dubai 국제유가
        dubai_data = self.process_dubai_oil_prices()
        results["dubai_oil"] = self.save_json(dubai_data, "dubai_oil_prices")
        
        # 4. 환율
        exchange_data = self.process_exchange_rate()
        results["exchange_rate"] = self.save_json(exchange_data, "exchange_rate")
        
        # 5. 유류세
        tax_data = self.process_fuel_tax()
        results["fuel_tax"] = self.save_json(tax_data, "fuel_tax")
        
        # 결과 요약
        logger.info("=== 처리 결과 ===")
        for key, success in results.items():
            status = "성공" if success else "실패"
            logger.info(f"{key}: {status}")
        
        return results

def main():
    processor = ImprovedOilPriceDataProcessor()
    processor.process_all()

if __name__ == "__main__":
    main()