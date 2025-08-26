import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// 컴포넌트 임포트
import ForecastChart from './components/ForecastChart';
import Dashboard from './components/Dashboard';

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
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p className="text-neutral-600">유가 예측 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* 헤더 */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <h1 className="header-title">⛽ 오피넷 유가예측</h1>
            <button
              onClick={refreshData}
              disabled={loading}
              className="btn btn-secondary btn-sm"
              aria-label="데이터 새로고침"
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: '16px', height: '16px' }}></div>
                  <span className="ml-2">새로고침</span>
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <polyline points="1 20 1 14 7 14"></polyline>
                    <path d="m3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                  </svg>
                  새로고침
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="container py-8">
        {/* 에러 알림 */}
        {error && (
          <div className="alert alert-error mb-6 component-gap">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="ml-3 flex-1">
                <h3 className="font-medium text-error-800">오류 발생</h3>
                <p className="mt-2 text-sm text-error-700">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-3 btn btn-sm bg-error-100 text-error-800 hover:bg-error-200 border-error-300"
                >
                  닫기
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 모바일 설정 패널 (767px 이하에서만 표시) */}
        <div className="md:hidden mb-6">
          <div className="card">
            <div className="card-body">
              <h2 className="h3 mb-4">설정</h2>
              
              {/* 연료 타입 선택 */}
              <div className="mb-6">
                <label className="label">연료 종류</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleFuelTypeChange('gasoline')}
                    className={`btn ${
                      selectedFuelType === 'gasoline' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    ⛽ 휘발유
                  </button>
                  <button
                    onClick={() => handleFuelTypeChange('diesel')}
                    className={`btn ${
                      selectedFuelType === 'diesel' 
                        ? 'btn-primary' 
                        : 'btn-secondary'
                    }`}
                  >
                    🚛 경유
                  </button>
                </div>
              </div>

              {/* 지역 선택 */}
              <div>
                <label className="label">지역 선택</label>
                <select
                  value={selectedRegion}
                  onChange={(e) => handleRegionChange(e.target.value)}
                  className="input"
                >
                  {regions.map((region) => (
                    <option key={region.code} value={region.code}>
                      {region.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 데스크톱/태블릿 레이아웃 */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* 데스크톱 설정 사이드바 (768px 이상에서만 표시) */}
          <div className="hidden md:block lg:col-span-1">
            <div className="card sticky" style={{ top: '120px' }}>
              <div className="card-body">
                <h2 className="h3 mb-6">설정</h2>
                
                {/* 연료 타입 선택 */}
                <div className="mb-8">
                  <label className="label">연료 종류</label>
                  <div className="space-y-2">
                    <button
                      onClick={() => handleFuelTypeChange('gasoline')}
                      className={`w-full btn text-left ${
                        selectedFuelType === 'gasoline' 
                          ? 'btn-primary' 
                          : 'btn-secondary'
                      }`}
                    >
                      ⛽ 보통휘발유
                    </button>
                    <button
                      onClick={() => handleFuelTypeChange('diesel')}
                      className={`w-full btn text-left ${
                        selectedFuelType === 'diesel' 
                          ? 'btn-primary' 
                          : 'btn-secondary'
                      }`}
                    >
                      🚛 자동차경유
                    </button>
                  </div>
                </div>

                {/* 지역 선택 */}
                <div>
                  <label className="label">지역 선택</label>
                  <select
                    value={selectedRegion}
                    onChange={(e) => handleRegionChange(e.target.value)}
                    className="input"
                  >
                    {regions.map((region) => (
                      <option key={region.code} value={region.code}>
                        {region.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* 메인 콘텐츠 */}
          <div className="lg:col-span-4 space-y-6">
            {/* 대시보드 요약 */}
            {forecastData && (
              <Dashboard
                forecastData={forecastData}
                selectedRegion={selectedRegion}
                selectedFuelType={selectedFuelType}
              />
            )}

            {/* 핵심 지표 요약 카드 */}
            {forecastData && (
              <div className="card">
                <div className="card-body">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="h2 m-0">
                      {regions.find(r => r.code === selectedRegion)?.name || '지역'} 
                      {selectedFuelType === 'gasoline' ? ' 휘발유' : ' 경유'} 가격
                    </h2>
                    <span className="badge badge-primary">
                      {new Date().toLocaleDateString('ko-KR')}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="price-card">
                      <div className="price-card-title">현재 가격</div>
                      <div className="price-value text-numeric">
                        {forecastData?.forecasts?.[selectedRegion]?.[selectedFuelType]?.current_price?.toLocaleString() || '---'}원
                      </div>
                    </div>
                    
                    <div className="price-card">
                      <div className="price-card-title">내일 예상</div>
                      <div className="price-value text-numeric">
                        {forecastData?.forecasts?.[selectedRegion]?.[selectedFuelType]?.next_day_prediction?.toLocaleString() || '---'}원
                      </div>
                      {forecastData?.forecasts?.[selectedRegion]?.[selectedFuelType] && (
                        <div className={`price-change mt-2 ${
                          (forecastData.forecasts[selectedRegion][selectedFuelType].next_day_prediction || 0) > 
                          (forecastData.forecasts[selectedRegion][selectedFuelType].current_price || 0) 
                            ? 'positive' : 'negative'
                        }`}>
                          {(forecastData.forecasts[selectedRegion][selectedFuelType].next_day_prediction || 0) > 
                           (forecastData.forecasts[selectedRegion][selectedFuelType].current_price || 0) 
                            ? '↗️ 상승 예상' : '↘️ 하락 예상'}
                        </div>
                      )}
                    </div>

                    <div className="price-card">
                      <div className="price-card-title">1주 후 예상</div>
                      <div className="price-value text-numeric">
                        {forecastData?.forecasts?.[selectedRegion]?.[selectedFuelType]?.week_prediction?.toLocaleString() || '---'}원
                      </div>
                      {forecastData?.forecasts?.[selectedRegion]?.[selectedFuelType] && (
                        <div className={`price-change mt-2 ${
                          (forecastData.forecasts[selectedRegion][selectedFuelType].week_prediction || 0) > 
                          (forecastData.forecasts[selectedRegion][selectedFuelType].current_price || 0) 
                            ? 'positive' : 'negative'
                        }`}>
                          {Math.abs(
                            ((forecastData.forecasts[selectedRegion][selectedFuelType].week_prediction || 0) - 
                             (forecastData.forecasts[selectedRegion][selectedFuelType].current_price || 0))
                          ).toFixed(0)}원 변화
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 예측 차트 */}
            {forecastData && (
              <div className="card">
                <div className="card-header">
                  <h3 className="h3 m-0">4주 가격 전망</h3>
                  <p className="text-sm text-neutral-600 mt-1">
                    AI 기반 예측 결과 (참고용)
                  </p>
                </div>
                <div className="card-body">
                  <ForecastChart
                    forecastData={forecastData}
                    selectedRegion={selectedRegion}
                    selectedFuelType={selectedFuelType}
                  />
                </div>
              </div>
            )}

            {/* 전국 비교 */}
            {forecastData?.national_average && (
              <div className="card">
                <div className="card-header">
                  <h3 className="h3 m-0">전국 평균과 비교</h3>
                  <p className="text-sm text-neutral-600 mt-1">
                    현재 지역 가격과 전국 평균의 차이
                  </p>
                </div>
                <div className="card-body">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {['gasoline', 'diesel'].map((fuelType) => {
                      const nationalData = forecastData.national_average?.[fuelType as 'gasoline' | 'diesel'];
                      const regionalData = forecastData.forecasts?.[selectedRegion]?.[fuelType as 'gasoline' | 'diesel'];
                      
                      if (!nationalData || !regionalData) return null;
                      
                      const nationalPrice = nationalData.current_price || 0;
                      const regionalPrice = regionalData.current_price || 0;
                      const difference = regionalPrice - nationalPrice;
                      const percentage = nationalPrice > 0 ? ((difference / nationalPrice) * 100) : 0;
                      
                      return (
                        <div key={fuelType} className="price-card">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="metric-card-title">
                              {fuelType === 'gasoline' ? '⛽ 전국 휘발유' : '🚛 전국 자동차경유'}
                            </h4>
                            <span className={`badge ${difference >= 0 ? 'badge-error' : 'badge-success'}`}>
                              {difference >= 0 ? '+' : ''}{difference.toFixed(0)}원
                            </span>
                          </div>
                          
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-neutral-600">전국 평균</span>
                              <span className="font-medium text-numeric">{nationalPrice.toLocaleString()}원</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-neutral-600">지역 가격</span>
                              <span className="font-medium text-numeric">{regionalPrice.toLocaleString()}원</span>
                            </div>
                            <div className="flex justify-between pt-2 border-t">
                              <span className="text-neutral-600">차이율</span>
                              <span className={`font-medium ${difference >= 0 ? 'text-error' : 'text-success'}`}>
                                {percentage >= 0 ? '+' : ''}{percentage.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 모바일 하단 네비게이션 (767px 이하에서만 표시) */}
        <nav className="mobile-nav" aria-label="메인 네비게이션">
          <a href="#home" className="mobile-nav-item active">
            <svg className="mobile-nav-icon" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
            홈
          </a>
          <a href="#forecast" className="mobile-nav-item">
            <svg className="mobile-nav-icon" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
              <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
            </svg>
            예측
          </a>
          <a href="#compare" className="mobile-nav-item">
            <svg className="mobile-nav-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            비교
          </a>
          <a href="#settings" className="mobile-nav-item">
            <svg className="mobile-nav-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
            설정
          </a>
        </nav>
      </main>

      {/* 푸터 */}
      <footer className="footer">
        <div className="container">
          <div className="text-center text-neutral-600 text-sm">
            <p><strong>오피넷 유가예측 시스템</strong></p>
            <p className="mt-2">한국석유공사 오피넷 데이터 기반 AI 예측 서비스</p>
            <p className="text-xs text-neutral-500 mt-3">
              ⚠️ 예측 결과는 참고용이며, 실제 가격과 다를 수 있습니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;