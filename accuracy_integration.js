// 지역별 연료별 정확도 시스템 통합 JavaScript
// index.html에 삽입할 코드

// 지역별 정확도 데이터 관리
class RegionalAccuracyManager {
    constructor() {
        this.accuracyData = this.initializeAccuracyStructure();
        this.currentRegion = 'ulsan';  // 기본 선택 지역
        this.currentFuel = 'gasoline'; // 기본 선택 연료
    }
    
    initializeAccuracyStructure() {
        return {
            metadata: {
                last_updated: null,
                base_date: "2025-08-24"
            },
            regions: {
                seoul: { name: "서울", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                busan: { name: "부산", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                daegu: { name: "대구", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                incheon: { name: "인천", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                gwangju: { name: "광주", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                daejeon: { name: "대전", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                ulsan: { name: "울산", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                gyeonggi: { name: "경기", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                gangwon: { name: "강원", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                chungbuk: { name: "충북", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                chungnam: { name: "충남", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                jeonbuk: { name: "전북", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                jeonnam: { name: "전남", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                gyeongbuk: { name: "경북", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                gyeongnam: { name: "경남", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                jeju: { name: "제주", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} },
                sejong: { name: "세종", gasoline_accuracy: null, diesel_accuracy: null, daily_data: {} }
            }
        };
    }
    
    // 정확도 계산 공식
    calculateAccuracy(predicted, actual) {
        if (actual === 0) return 0;
        const errorRate = Math.abs(predicted - actual) / actual * 100;
        return Math.max(0, 100 - errorRate);
    }
    
    // 실제 데이터 수동 입력
    updateActualData(region, date, gasolinePrice, dieselPrice, forecastData) {
        if (!this.accuracyData.regions[region]) {
            console.error(`잘못된 지역: ${region}`);
            return false;
        }
        
        // 예측 데이터에서 해당 날짜의 예측 가격 조회
        const daysAfter = this.getDaysAfter(date);
        const gasolineForecast = this.getForecastPrice(region, 'gasoline', daysAfter, forecastData);
        const dieselForecast = this.getForecastPrice(region, 'diesel', daysAfter, forecastData);
        
        // 정확도 계산
        const gasolineAccuracy = gasolineForecast ? this.calculateAccuracy(gasolineForecast, gasolinePrice) : null;
        const dieselAccuracy = dieselForecast ? this.calculateAccuracy(dieselForecast, dieselPrice) : null;
        
        // 데이터 저장
        this.accuracyData.regions[region].daily_data[date] = {
            gasoline_actual: gasolinePrice,
            diesel_actual: dieselPrice,
            gasoline_forecast: gasolineForecast,
            diesel_forecast: dieselForecast,
            gasoline_accuracy: gasolineAccuracy,
            diesel_accuracy: dieselAccuracy,
            updated_at: new Date().toISOString()
        };
        
        // 전체 평균 정확도 재계산
        this.recalculateOverallAccuracy(region);
        
        console.log(`✅ ${region} ${date} 데이터 업데이트 완료`);
        console.log(`보통휘발유 정확도: ${gasolineAccuracy?.toFixed(2)}%`);
        console.log(`자동차경유 정확도: ${dieselAccuracy?.toFixed(2)}%`);
        
        return true;
    }
    
    getDaysAfter(dateStr) {
        const baseDate = new Date("2025-08-24");
        const targetDate = new Date(dateStr);
        return Math.ceil((targetDate - baseDate) / (1000 * 60 * 60 * 24));
    }
    
    getForecastPrice(region, fuelType, daysAfter, forecastData) {
        try {
            if (forecastData?.forecasts?.[region]?.daily_forecast) {
                const forecast = forecastData.forecasts[region].daily_forecast[daysAfter - 1];
                return forecast ? forecast[fuelType] : null;
            }
            return null;
        } catch (error) {
            console.error('예측 가격 조회 오류:', error);
            return null;
        }
    }
    
    recalculateOverallAccuracy(region) {
        const dailyData = Object.values(this.accuracyData.regions[region].daily_data);
        
        if (dailyData.length === 0) return;
        
        // 보통휘발유 평균 정확도
        const gasolineAccuracies = dailyData
            .map(d => d.gasoline_accuracy)
            .filter(acc => acc !== null);
        
        if (gasolineAccuracies.length > 0) {
            this.accuracyData.regions[region].gasoline_accuracy = 
                gasolineAccuracies.reduce((a, b) => a + b) / gasolineAccuracies.length;
        }
        
        // 자동차경유 평균 정확도
        const dieselAccuracies = dailyData
            .map(d => d.diesel_accuracy)
            .filter(acc => acc !== null);
        
        if (dieselAccuracies.length > 0) {
            this.accuracyData.regions[region].diesel_accuracy = 
                dieselAccuracies.reduce((a, b) => a + b) / dieselAccuracies.length;
        }
    }
    
    // 현재 선택된 지역의 정확도 반환
    getCurrentAccuracy() {
        const regionData = this.accuracyData.regions[this.currentRegion];
        if (!regionData) return 99.9; // 기본값
        
        if (this.currentFuel === 'gasoline') {
            return regionData.gasoline_accuracy || 99.9;
        } else {
            return regionData.diesel_accuracy || 99.9;
        }
    }
    
    // 지역 변경
    setCurrentRegion(region) {
        if (this.accuracyData.regions[region]) {
            this.currentRegion = region;
            console.log(`지역 변경: ${this.accuracyData.regions[region].name}`);
            return true;
        }
        return false;
    }
    
    // 연료 변경
    setCurrentFuel(fuel) {
        if (fuel === 'gasoline' || fuel === 'diesel') {
            this.currentFuel = fuel;
            console.log(`연료 변경: ${fuel === 'gasoline' ? '보통휘발유' : '자동차경유'}`);
            return true;
        }
        return false;
    }
    
    // 지역별 정확도 요약 조회
    getRegionSummary(region) {
        const regionData = this.accuracyData.regions[region];
        if (!regionData) return null;
        
        return {
            name: regionData.name,
            gasoline_accuracy: regionData.gasoline_accuracy,
            diesel_accuracy: regionData.diesel_accuracy,
            daily_count: Object.keys(regionData.daily_data).length,
            latest_update: this.getLatestUpdate(region)
        };
    }
    
    getLatestUpdate(region) {
        const dailyData = Object.values(this.accuracyData.regions[region].daily_data);
        if (dailyData.length === 0) return null;
        
        return dailyData
            .map(d => new Date(d.updated_at))
            .sort((a, b) => b - a)[0]
            .toISOString();
    }
    
    // 수동 데이터 입력을 위한 예시 함수들
    addSampleData() {
        // 8월 25일 서울 데이터 예시
        const sampleForecastData = window.currentData; // 전역 예측 데이터 사용
        
        this.updateActualData('seoul', '2025-08-25', 1722.5, 1605.8, sampleForecastData);
        this.updateActualData('seoul', '2025-08-26', 1720.1, 1603.4, sampleForecastData);
        
        // 울산 데이터 예시
        this.updateActualData('ulsan', '2025-08-25', 1634.2, 1514.1, sampleForecastData);
        this.updateActualData('ulsan', '2025-08-26', 1635.8, 1515.3, sampleForecastData);
        
        console.log('📊 샘플 정확도 데이터가 추가되었습니다.');
        return this.accuracyData;
    }
}
