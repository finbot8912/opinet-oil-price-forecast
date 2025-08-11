#!/usr/bin/env python3
"""
데이터 처리 모듈
엑셀 파일을 읽어서 유가 예측에 사용할 수 있는 JSON 형태로 변환
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import numpy as np
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OilPriceDataProcessor:
    """유가 데이터 처리 클래스"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # 디렉토리 생성
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 지역 코드 매핑
        self.region_mapping = {
            "서울": "seoul", "부산": "busan", "대구": "daegu", "인천": "incheon",
            "광주": "gwangju", "대전": "daejeon", "울산": "ulsan", "경기": "gyeonggi",
            "강원": "gangwon", "충북": "chungbuk", "충남": "chungnam", 
            "전북": "jeonbuk", "전남": "jeonnam", "경북": "gyeongbuk", 
            "경남": "gyeongnam", "제주": "jeju", "세종": "sejong"
        }
    
    def clean_excel_data(self, df: pd.DataFrame, skip_rows: int = 0) -> pd.DataFrame:
        """엑셀 데이터 정리"""
        # 빈 행 제거
        df = df.dropna(how='all')
        
        # 헤더가 여러 행에 걸쳐 있는 경우 처리
        if skip_rows > 0:
            df = df.iloc[skip_rows:]
        
        # 인덱스 리셋
        df = df.reset_index(drop=True)
        
        return df
    
    def parse_date_column(self, date_str: str) -> Optional[str]:
        """날짜 문자열을 표준 형식으로 변환"""
        if pd.isna(date_str) or str(date_str).strip() == "":
            return None
            
        date_str = str(date_str).strip()
        
        try:
            # 다양한 날짜 형식 처리
            if "년" in date_str and "월" in date_str:
                if "주" in date_str:
                    # "2008년05월1주" 형식
                    parts = date_str.replace("년", "-").replace("월", "-").replace("주", "")
                    year, month, week = parts.split("-")
                    # 주차를 일자로 변환 (1주 = 1일, 2주 = 8일, etc.)
                    day = int(week) * 7 - 6
                    return f"{year}-{month.zfill(2)}-{str(day).zfill(2)}"
                else:
                    # "2010년01월" 형식
                    parts = date_str.replace("년", "-").replace("월", "")
                    return f"{parts}-01"
            
            # ISO 형식 (YYYY-MM-DD)
            if len(date_str) == 10 and "-" in date_str:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            
            # 기타 형식들...
            return date_str
            
        except Exception as e:
            logger.warning(f"날짜 변환 실패: {date_str} -> {e}")
            return date_str
    
    def process_regional_gas_prices(self) -> Dict:
        """지역별 주유소 평균 판매가격 처리"""
        logger.info("지역별 주유소 평균 판매가격 데이터 처리 중...")
        
        try:
            # 유가변동1.xlsx의 "5.지역별주유소 판매가" 시트
            df = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx", 
                sheet_name="5.지역별주유소 판매가",
                header=None
            )
            
            # 첫 번째 행에서 지역명과 연료 타입 추출
            regions_gasoline = []
            regions_diesel = []
            
            for i, col in enumerate(df.columns[1:18]):  # 휘발유 지역들
                region_name = str(df.iloc[0, i+1])
                if region_name in self.region_mapping:
                    regions_gasoline.append(self.region_mapping[region_name])
                    
            for i, col in enumerate(df.columns[18:35]):  # 경유 지역들  
                region_name = str(df.iloc[0, i+18])
                if region_name in self.region_mapping:
                    regions_diesel.append(self.region_mapping[region_name])
            
            # 데이터 처리
            processed_data = {
                "metadata": {
                    "source": "지역별주유소 판매가",
                    "fuel_types": ["gasoline", "diesel"],
                    "regions": list(self.region_mapping.values()),
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            # 각 월별 데이터 처리
            for idx in range(1, len(df)):
                row = df.iloc[idx]
                date_raw = str(row.iloc[0])
                
                if pd.isna(date_raw) or date_raw.strip() == "":
                    continue
                    
                date_parsed = self.parse_date_column(date_raw)
                
                monthly_data = {
                    "date": date_parsed,
                    "gasoline": {},
                    "diesel": {}
                }
                
                # 휘발유 가격
                for i, region in enumerate(regions_gasoline):
                    if i + 1 < len(row):
                        price = row.iloc[i + 1]
                        if pd.notna(price) and str(price).strip() != "0":
                            monthly_data["gasoline"][region] = float(price)
                
                # 경유 가격  
                for i, region in enumerate(regions_diesel):
                    if i + 18 < len(row):
                        price = row.iloc[i + 18]
                        if pd.notna(price) and str(price).strip() != "0":
                            monthly_data["diesel"][region] = float(price)
                
                processed_data["data"].append(monthly_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"지역별 주유소 가격 처리 중 오류: {e}")
            return {}
    
    def process_national_gas_prices(self) -> Dict:
        """전국 주유소 판매가 처리 (일별 데이터)"""
        logger.info("전국 주유소 판매가 데이터 처리 중...")
        
        try:
            df = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx",
                sheet_name="4.전국주유소 판매가"
            )
            
            processed_data = {
                "metadata": {
                    "source": "전국주유소 판매가",
                    "fuel_types": ["gasoline", "diesel"],
                    "frequency": "daily",
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            for _, row in df.iterrows():
                date_raw = str(row.iloc[0])
                gasoline_price = row.iloc[1]
                diesel_price = row.iloc[2]
                
                if pd.isna(date_raw):
                    continue
                    
                # 날짜 파싱
                try:
                    if "년" in date_raw:
                        date_parsed = self.parse_date_column(date_raw)
                    else:
                        # 이미 표준 형식인 경우
                        date_parsed = date_raw
                        
                    daily_data = {
                        "date": date_parsed,
                        "gasoline": float(gasoline_price) if pd.notna(gasoline_price) else None,
                        "diesel": float(diesel_price) if pd.notna(diesel_price) else None
                    }
                    
                    processed_data["data"].append(daily_data)
                    
                except Exception as e:
                    logger.warning(f"일별 데이터 처리 실패: {date_raw} -> {e}")
                    continue
            
            return processed_data
            
        except Exception as e:
            logger.error(f"전국 주유소 가격 처리 중 오류: {e}")
            return {}
    
    def process_international_oil_prices(self) -> Dict:
        """국제 유가 데이터 처리"""
        logger.info("국제 유가 데이터 처리 중...")
        
        try:
            # Dubai 국제유가
            df_dubai = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx",
                sheet_name="7.Dubai 국제유가"
            )
            
            # 싱가포르 국제제품가격  
            df_singapore = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx",
                sheet_name="8.싱가포르 국제제품가격"
            )
            
            processed_data = {
                "metadata": {
                    "source": "국제유가",
                    "currencies": ["krw", "usd"],
                    "processed_at": datetime.now().isoformat()
                },
                "dubai_crude": [],
                "singapore_products": []
            }
            
            # Dubai 유가 처리
            for _, row in df_dubai.iterrows():
                date_raw = str(row.iloc[0])
                if pd.isna(date_raw) or "기간" in date_raw:
                    continue
                    
                krw_price = row.iloc[1] if len(row) > 1 else None
                usd_price = row.iloc[2] if len(row) > 2 else None
                
                if pd.notna(krw_price) or pd.notna(usd_price):
                    dubai_data = {
                        "date": self.parse_date_column(date_raw),
                        "krw_per_liter": float(krw_price) if pd.notna(krw_price) else None,
                        "usd_per_barrel": float(usd_price) if pd.notna(usd_price) else None
                    }
                    processed_data["dubai_crude"].append(dubai_data)
            
            # 싱가포르 제품 가격 처리
            for _, row in df_singapore.iterrows():
                date_raw = str(row.iloc[0])
                if pd.isna(date_raw) or "날짜" in date_raw:
                    continue
                    
                singapore_data = {
                    "date": self.parse_date_column(date_raw),
                    "gasoline_krw": float(row.iloc[1]) if pd.notna(row.iloc[1]) else None,
                    "diesel_low_sulfur_krw": float(row.iloc[2]) if pd.notna(row.iloc[2]) else None,
                    "diesel_high_sulfur_krw": float(row.iloc[3]) if pd.notna(row.iloc[3]) else None,
                    "gasoline_usd": float(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else None,
                    "diesel_low_sulfur_usd": float(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else None,
                    "diesel_high_sulfur_usd": float(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else None
                }
                processed_data["singapore_products"].append(singapore_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"국제 유가 처리 중 오류: {e}")
            return {}
    
    def process_exchange_rate(self) -> Dict:
        """환율 데이터 처리"""
        logger.info("환율 데이터 처리 중...")
        
        try:
            df = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx",
                sheet_name="11.환율"
            )
            
            processed_data = {
                "metadata": {
                    "source": "환율",
                    "currency_pair": "USD/KRW",
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            for _, row in df.iterrows():
                date_raw = str(row.iloc[0])
                exchange_rate = row.iloc[1]
                
                if pd.isna(date_raw) or pd.isna(exchange_rate):
                    continue
                    
                rate_data = {
                    "date": self.parse_date_column(date_raw),
                    "usd_krw": float(exchange_rate)
                }
                processed_data["data"].append(rate_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"환율 처리 중 오류: {e}")
            return {}
    
    def process_fuel_tax(self) -> Dict:
        """유류세 데이터 처리"""
        logger.info("유류세 데이터 처리 중...")
        
        try:
            df = pd.read_excel(
                self.raw_dir / "유가변동1.xlsx", 
                sheet_name="3.유류세"
            )
            
            processed_data = {
                "metadata": {
                    "source": "유류세",
                    "fuel_types": ["gasoline", "diesel"],
                    "tax_components": ["개별소비세", "교통에너지환경세", "교육세", "주행세"],
                    "processed_at": datetime.now().isoformat()
                },
                "data": []
            }
            
            for _, row in df.iterrows():
                if pd.isna(row.iloc[0]) or "변동일자" in str(row.iloc[0]):
                    continue
                    
                tax_data = {
                    "date": self.parse_date_column(str(row.iloc[0])),
                    "gasoline": {
                        "individual_consumption_tax": float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0,
                        "transportation_tax": float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                        "education_tax": float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0,
                        "driving_tax": float(row.iloc[4]) if pd.notna(row.iloc[4]) else 0,
                        "total": float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                    },
                    "diesel": {
                        "individual_consumption_tax": float(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else 0,
                        "transportation_tax": float(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else 0,
                        "education_tax": float(row.iloc[9]) if len(row) > 9 and pd.notna(row.iloc[9]) else 0,
                        "driving_tax": float(row.iloc[10]) if len(row) > 10 and pd.notna(row.iloc[10]) else 0,
                        "total": float(row.iloc[11]) if len(row) > 11 and pd.notna(row.iloc[11]) else 0
                    }
                }
                processed_data["data"].append(tax_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"유류세 처리 중 오류: {e}")
            return {}
    
    def save_processed_data(self, data: Dict, filename: str) -> bool:
        """처리된 데이터를 JSON 파일로 저장"""
        try:
            filepath = self.processed_dir / f"{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"데이터 저장 완료: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {filename} -> {e}")
            return False
    
    def process_all_data(self) -> Dict[str, bool]:
        """모든 데이터 처리 및 저장"""
        logger.info("전체 데이터 처리 시작...")
        
        results = {}
        
        # 1. 지역별 주유소 가격
        regional_data = self.process_regional_gas_prices()
        if regional_data:
            results["regional_prices"] = self.save_processed_data(regional_data, "regional_gas_prices")
        
        # 2. 전국 주유소 가격
        national_data = self.process_national_gas_prices()
        if national_data:
            results["national_prices"] = self.save_processed_data(national_data, "national_gas_prices")
        
        # 3. 국제 유가
        international_data = self.process_international_oil_prices()
        if international_data:
            results["international_prices"] = self.save_processed_data(international_data, "international_oil_prices")
        
        # 4. 환율
        exchange_data = self.process_exchange_rate()
        if exchange_data:
            results["exchange_rate"] = self.save_processed_data(exchange_data, "exchange_rate")
        
        # 5. 유류세
        tax_data = self.process_fuel_tax()
        if tax_data:
            results["fuel_tax"] = self.save_processed_data(tax_data, "fuel_tax")
        
        logger.info(f"데이터 처리 완료. 결과: {results}")
        return results

def main():
    """메인 실행 함수"""
    processor = OilPriceDataProcessor()
    
    # 원본 데이터 파일들을 data/raw/ 디렉토리로 복사
    import shutil
    raw_files = ["유가변동.xlsx", "유가변동1.xlsx", "유가변동2.xlsx"]
    
    for file in raw_files:
        src = Path(file)
        dst = processor.raw_dir / file
        if src.exists() and not dst.exists():
            processor.raw_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logger.info(f"파일 복사 완료: {file}")
    
    # 모든 데이터 처리
    results = processor.process_all_data()
    
    print("\n" + "="*60)
    print("데이터 처리 결과:")
    print("="*60)
    for key, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{key}: {status}")
    print("="*60)

if __name__ == "__main__":
    main()