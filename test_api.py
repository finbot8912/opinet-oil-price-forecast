#!/usr/bin/env python3
"""
API 서버 테스트 스크립트
"""

import requests
import json
from datetime import datetime

def test_api():
    """API 엔드포인트 테스트"""
    base_url = "http://localhost:8000"
    
    print("유가 예측 API 테스트 시작...")
    print("="*50)
    
    # 1. 루트 엔드포인트 테스트
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 루트 엔드포인트: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   서버 시간: {data.get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"❌ 루트 엔드포인트 오류: {e}")
    
    # 2. 헬스 체크
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ 헬스 체크: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   상태: {data.get('status', 'N/A')}")
            print(f"   데이터 사용 가능: {data.get('data_available', False)}")
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")
    
    # 3. 지역 목록 조회
    try:
        response = requests.get(f"{base_url}/api/regions")
        print(f"✅ 지역 목록: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            regions = data.get('regions', [])
            print(f"   총 지역 수: {len(regions)}")
            if regions:
                print(f"   첫 번째 지역: {regions[0]}")
    except Exception as e:
        print(f"❌ 지역 목록 오류: {e}")
    
    # 4. 전체 예측 조회
    try:
        response = requests.get(f"{base_url}/api/forecast")
        print(f"✅ 전체 예측: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            metadata = data.get('metadata', {})
            forecasts = data.get('forecasts', {})
            national = data.get('national_average', {})
            
            print(f"   생성 시간: {metadata.get('generated_at', 'N/A')}")
            print(f"   예측 기간: {metadata.get('forecast_horizon_days', 0)}일")
            print(f"   지역 수: {len(forecasts)}")
            
            if national:
                print("   전국 평균 가격:")
                for fuel, data in national.items():
                    current = data.get('current_price', 0)
                    print(f"     {fuel}: 현재 {current}원")
    except Exception as e:
        print(f"❌ 전체 예측 오류: {e}")
    
    # 5. 서울 휘발유 예측 (특정 지역/연료)
    try:
        response = requests.get(f"{base_url}/api/forecast?region=seoul&fuel_type=gasoline")
        print(f"✅ 서울 휘발유: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            seoul_data = data.get('forecasts', {}).get('seoul', {}).get('gasoline', {})
            if seoul_data:
                current = seoul_data.get('current_price', 0)
                forecasts = seoul_data.get('forecasts', [])
                print(f"   현재가: {current}원")
                print(f"   예측 건수: {len(forecasts)}")
                if forecasts:
                    first_forecast = forecasts[0]
                    print(f"   1일 후: {first_forecast.get('price', 0)}원")
    except Exception as e:
        print(f"❌ 서울 휘발유 오류: {e}")
    
    # 6. 예측 요약
    try:
        response = requests.get(f"{base_url}/api/forecast/summary")
        print(f"✅ 예측 요약: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            regional_summary = data.get('regional_summary', {})
            print(f"   요약 지역 수: {len(regional_summary)}")
            
            # 서울 요약 출력
            if 'seoul' in regional_summary:
                seoul = regional_summary['seoul']
                if 'gasoline' in seoul:
                    gas_info = seoul['gasoline']
                    print(f"   서울 휘발유 변화: {gas_info.get('change_percent', 0):+.1f}% ({gas_info.get('trend', 'N/A')})")
    except Exception as e:
        print(f"❌ 예측 요약 오류: {e}")
    
    print("="*50)
    print("API 테스트 완료")

if __name__ == "__main__":
    test_api()