#!/usr/bin/env python3
"""
엑셀 파일 상세 분석 도구
데이터 구조를 파악하고 올바른 파싱 방법을 찾기 위한 분석 도구
"""

import pandas as pd
import json
from pathlib import Path
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelAnalyzer:
    """엑셀 파일 분석 클래스"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
    
    def analyze_sheet_structure(self, file_path: str, sheet_name: str, max_rows: int = 10) -> Dict:
        """시트 구조 상세 분석"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=max_rows)
            
            analysis = {
                "file": file_path,
                "sheet": sheet_name,
                "dimensions": {"rows": len(df), "cols": len(df.columns)},
                "sample_data": []
            }
            
            for i in range(min(max_rows, len(df))):
                row_data = {}
                for j in range(len(df.columns)):
                    cell_value = df.iloc[i, j]
                    if pd.notna(cell_value):
                        row_data[f"col_{j}"] = str(cell_value)
                    else:
                        row_data[f"col_{j}"] = None
                analysis["sample_data"].append(row_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"시트 분석 실패: {sheet_name} -> {e}")
            return {}
    
    def find_header_row(self, file_path: str, sheet_name: str) -> int:
        """헤더 행 위치 찾기"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
            
            for i in range(len(df)):
                row = df.iloc[i]
                non_null_count = row.notna().sum()
                
                # 대부분의 셀이 채워져 있고, 날짜/지역명 등이 포함된 행을 헤더로 판단
                if non_null_count > len(row) * 0.5:
                    row_str = ' '.join([str(x) for x in row if pd.notna(x)])
                    if any(keyword in row_str for keyword in ['서울', '부산', '대구', '기간', '날짜', '구분']):
                        return i
            
            return 0  # 기본값
            
        except Exception as e:
            logger.error(f"헤더 행 찾기 실패: {sheet_name} -> {e}")
            return 0
    
    def analyze_regional_prices_sheet(self):
        """지역별 주유소 판매가 시트 상세 분석"""
        file_path = self.raw_dir / "유가변동1.xlsx"
        sheet_name = "5.지역별주유소 판매가"
        
        print(f"\n=== {sheet_name} 분석 ===")
        
        # 전체 시트 구조 파악
        analysis = self.analyze_sheet_structure(file_path, sheet_name, 5)
        
        print("첫 5행 데이터:")
        for i, row in enumerate(analysis["sample_data"]):
            print(f"Row {i}: {row}")
        
        # 헤더 행 찾기
        header_row = self.find_header_row(file_path, sheet_name)
        print(f"\n예상 헤더 행: {header_row}")
        
        # 실제 데이터 구조 분석
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        print(f"\n시트 크기: {len(df)}행 x {len(df.columns)}열")
        
        # 첫 번째 행 (지역명) 분석
        first_row = df.iloc[0]
        print(f"\n첫 번째 행 (지역명):")
        for i, value in enumerate(first_row):
            if pd.notna(value):
                print(f"  Col {i}: {value}")
        
        # 두 번째 행 분석 (실제 데이터 시작점으로 추정)
        if len(df) > 1:
            second_row = df.iloc[1]
            print(f"\n두 번째 행 (첫 번째 데이터):")
            for i, value in enumerate(second_row):
                if pd.notna(value):
                    print(f"  Col {i}: {value}")
    
    def analyze_national_prices_sheet(self):
        """전국 주유소 판매가 시트 분석"""
        file_path = self.raw_dir / "유가변동1.xlsx"
        sheet_name = "4.전국주유소 판매가"
        
        print(f"\n=== {sheet_name} 분석 ===")
        
        analysis = self.analyze_sheet_structure(file_path, sheet_name, 10)
        
        print("첫 10행 데이터:")
        for i, row in enumerate(analysis["sample_data"]):
            print(f"Row {i}: {row}")
    
    def run_comprehensive_analysis(self):
        """종합 분석 실행"""
        print("🔍 엑셀 파일 종합 분석 시작...")
        
        # 1. 지역별 주유소 판매가 분석
        self.analyze_regional_prices_sheet()
        
        # 2. 전국 주유소 판매가 분석
        self.analyze_national_prices_sheet()
        
        # 3. 기타 주요 시트들 간단 분석
        important_sheets = [
            ("유가변동1.xlsx", "7.Dubai 국제유가"),
            ("유가변동1.xlsx", "11.환율"),
            ("유가변동1.xlsx", "3.유류세")
        ]
        
        for file, sheet in important_sheets:
            try:
                file_path = self.raw_dir / file
                analysis = self.analyze_sheet_structure(file_path, sheet, 5)
                print(f"\n=== {sheet} ===")
                for i, row in enumerate(analysis["sample_data"]):
                    print(f"Row {i}: {row}")
            except Exception as e:
                print(f"❌ {sheet} 분석 실패: {e}")

def main():
    analyzer = ExcelAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()