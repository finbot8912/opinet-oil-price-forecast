#!/usr/bin/env python3
"""
엑셀 파일 구조 분석 스크립트
유가변동.xlsx, 유가변동1.xlsx, 유가변동2.xlsx 파일의 시트와 데이터 구조를 분석
"""

import pandas as pd
import json
from pathlib import Path

def analyze_excel_file(file_path):
    """단일 엑셀 파일 분석"""
    print(f"\n{'='*60}")
    print(f"파일 분석: {file_path}")
    print(f"{'='*60}")
    
    try:
        # 모든 시트 이름 가져오기
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"총 시트 수: {len(sheet_names)}")
        print(f"시트 목록: {sheet_names}")
        
        analysis_result = {
            'file_name': file_path,
            'sheet_count': len(sheet_names),
            'sheet_names': sheet_names,
            'sheets_data': {}
        }
        
        for sheet_name in sheet_names:
            print(f"\n[시트: {sheet_name}]")
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                sheet_info = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist(),
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                    'data_types': df.dtypes.to_dict()
                }
                
                print(f"  - 행 수: {len(df)}")
                print(f"  - 열 수: {len(df.columns)}")
                print(f"  - 컬럼명: {df.columns.tolist()}")
                
                # 특별히 주유소_지역별_평균판매가격 시트는 더 자세히 분석
                if "주유소_지역별_평균판매가격" in sheet_name:
                    print(f"  *** 핵심 시트 발견! ***")
                    print(f"  - 날짜 범위: {df.iloc[:, 0].min()} ~ {df.iloc[:, 0].max()}")
                    print(f"  - 샘플 데이터:")
                    print(df.head())
                
                analysis_result['sheets_data'][sheet_name] = sheet_info
                
            except Exception as e:
                print(f"  오류 발생: {str(e)}")
                analysis_result['sheets_data'][sheet_name] = {'error': str(e)}
        
        return analysis_result
        
    except Exception as e:
        print(f"파일 읽기 오류: {str(e)}")
        return {'error': str(e)}

def main():
    """메인 실행 함수"""
    print("유가 예측 시스템 - 엑셀 데이터 분석")
    print("="*60)
    
    excel_files = [
        "유가변동.xlsx",
        "유가변동1.xlsx", 
        "유가변동2.xlsx"
    ]
    
    all_analysis = {}
    
    for file_name in excel_files:
        file_path = Path(file_name)
        if file_path.exists():
            result = analyze_excel_file(file_name)
            all_analysis[file_name] = result
        else:
            print(f"파일을 찾을 수 없습니다: {file_name}")
    
    # 분석 결과를 JSON으로 저장
    with open('excel_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(all_analysis, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n{'='*60}")
    print("분석 완료! 결과는 excel_analysis.json에 저장되었습니다.")
    
    # 핵심 데이터 요약
    print("\n[핵심 발견사항]")
    for file_name, analysis in all_analysis.items():
        if 'sheets_data' in analysis:
            for sheet_name, sheet_data in analysis['sheets_data'].items():
                if "주유소_지역별_평균판매가격" in sheet_name:
                    print(f"✅ {file_name}에서 핵심 시트 발견: {sheet_name}")
                    print(f"   - 데이터 행 수: {sheet_data.get('rows', 0)}")

if __name__ == "__main__":
    main()