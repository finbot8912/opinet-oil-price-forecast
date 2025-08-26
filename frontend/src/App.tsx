import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// 컴포넌트 임포트
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import RegionSelector from './components/RegionSelector';
import ForecastChart from './components/ForecastChart';
import PriceSummary from './components/PriceSummary';
import LoadingSpinner from './components/LoadingSpinner';

// API 서비스
import { apiService } from './services/apiService';

// 타입 정의
import { ForecastData, Region } from './types/api';

function App() {
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('seoul');
  const [selectedFuelType, setSelectedFuelType] = useState<'gasoline' | 'diesel'>('gasoline');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 초기 데이터 로드
  useEffect(() => {
    loadInitialData();
  }, []);

  // 선택된 지역/연료 변경시 데이터 업데이트
  useEffect(() => {
    if (selectedRegion || selectedFuelType) {
      loadForecastData();
    }
  }, [selectedRegion, selectedFuelType, loadForecastData]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 지역 목록과 전체 예측 데이터를 병렬로 로드
      const [regionsResponse, forecastResponse] = await Promise.all([
        apiService.getRegions(),
        apiService.getForecast()
      ]);

      setRegions(regionsResponse);
      setForecastData(forecastResponse);
      
    } catch (err) {
      console.error('초기 데이터 로드 실패:', err);
      setError('데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const loadForecastData = useCallback(async () => {
    try {
      setError(null);
      
      const data = await apiService.getForecast({
        region: selectedRegion,
        fuel_type: selectedFuelType
      });
      
      setForecastData(data);
    } catch (err) {
      console.error('예측 데이터 로드 실패:', err);
      setError('예측 데이터를 불러오는 중 오류가 발생했습니다.');
    }
  }, [selectedRegion, selectedFuelType]);

  const refreshData = async () => {
    try {
      setLoading(true);
      await apiService.refreshForecast();
      await loadForecastData();
    } catch (err) {
      console.error('데이터 갱신 실패:', err);
      setError('데이터 갱신 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegionChange = (region: string) => {
    setSelectedRegion(region);
  };

  const handleFuelTypeChange = (fuelType: 'gasoline' | 'diesel') => {
    setSelectedFuelType(fuelType);
  };

  if (loading && !forecastData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner message="유가 예측 데이터를 불러오는 중..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onRefresh={refreshData} loading={loading} />
      
      <main className="container mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">오류 발생</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => setError(null)}
                    className="bg-red-100 px-2 py-1 text-sm font-medium text-red-800 rounded-md hover:bg-red-200"
                  >
                    닫기
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 왼쪽 사이드바 - 지역/연료 선택 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">설정</h2>
              
              <RegionSelector
                regions={regions}
                selectedRegion={selectedRegion}
                onRegionChange={handleRegionChange}
              />

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  연료 종류
                </label>
                <div className="space-y-2">
                  <button
                    onClick={() => handleFuelTypeChange('gasoline')}
                    className={`w-full px-4 py-2 text-left rounded-md transition-colors ${
                      selectedFuelType === 'gasoline'
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    🚗 보통휘발유
                  </button>
                  <button
                    onClick={() => handleFuelTypeChange('diesel')}
                    className={`w-full px-4 py-2 text-left rounded-md transition-colors ${
                      selectedFuelType === 'diesel'
                        ? 'bg-blue-100 text-blue-800 border-blue-300'
                        : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    🚛 자동차경유
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 메인 콘텐츠 */}
          <div className="lg:col-span-3 space-y-6">
            {/* 대시보드 요약 */}
            {forecastData && (
              <Dashboard
                forecastData={forecastData}
                selectedRegion={selectedRegion}
                selectedFuelType={selectedFuelType}
              />
            )}

            {/* 가격 요약 카드 */}
            {forecastData && (
              <PriceSummary
                forecastData={forecastData}
                selectedRegion={selectedRegion}
                selectedFuelType={selectedFuelType}
              />
            )}

            {/* 예측 차트 */}
            {forecastData && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    4주 가격 전망
                  </h2>
                  <div className="text-sm text-gray-500">
                    {regions.find(r => r.code === selectedRegion)?.name || selectedRegion} • {selectedFuelType === 'gasoline' ? '보통휘발유' : '자동차경유'}
                  </div>
                </div>
                
                <ForecastChart
                  forecastData={forecastData}
                  selectedRegion={selectedRegion}
                  selectedFuelType={selectedFuelType}
                />
              </div>
            )}

            {/* 전국 평균 비교 */}
            {forecastData?.national_average && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  전국 평균 대비 비교
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {['gasoline', 'diesel'].map((fuelType) => {
                    const nationalData = forecastData.national_average?.[fuelType as 'gasoline' | 'diesel'];
                    const regionalData = forecastData.forecasts?.[selectedRegion]?.[fuelType as 'gasoline' | 'diesel'];
                    
                    if (!nationalData || !regionalData) return null;
                    
                    const nationalPrice = nationalData.current_price || 0;
                    const regionalPrice = regionalData.current_price || 0;
                    const difference = regionalPrice - nationalPrice;
                    const percentage = nationalPrice > 0 ? ((difference / nationalPrice) * 100) : 0;
                    
                    return (
                      <div key={fuelType} className="bg-gray-50 rounded-lg p-4">
                        <h3 className="font-medium text-gray-900 mb-2">
                          {fuelType === 'gasoline' ? '보통휘발유' : '자동차경유'}
                        </h3>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">전국 평균:</span>
                            <span className="font-medium">{nationalPrice.toLocaleString()}원</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">지역 가격:</span>
                            <span className="font-medium">{regionalPrice.toLocaleString()}원</span>
                          </div>
                          <div className="flex justify-between border-t pt-2">
                            <span className="text-gray-600">차이:</span>
                            <span className={`font-medium ${difference >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {difference >= 0 ? '+' : ''}{difference.toFixed(0)}원 ({percentage >= 0 ? '+' : ''}{percentage.toFixed(1)}%)
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t border-gray-200 py-8 mt-12">
        <div className="container mx-auto px-4">
          <div className="text-center text-gray-600 text-sm">
            <p>유가 예측 시스템 • 한국석유공사 오피넷 데이터 기반</p>
            <p className="mt-1">예측 결과는 참고용이며, 실제 가격과 다를 수 있습니다.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;