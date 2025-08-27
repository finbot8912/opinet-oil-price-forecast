import React from 'react';
import { ForecastData } from '../types/api';

interface DashboardProps {
  forecastData: ForecastData;
  selectedRegion: string;
  selectedFuelType: 'gasoline' | 'diesel';
}

const Dashboard: React.FC<DashboardProps> = ({
  forecastData,
  selectedRegion,
  selectedFuelType
}) => {
  const metadata = forecastData.metadata;
  const nationalData = forecastData.national_average;
  
  // 전국 통계 계산
  const calculateNationalStats = () => {
    const gasolineData = nationalData?.gasoline;
    const dieselData = nationalData?.diesel;
    
    if (!gasolineData || !dieselData) return null;
    
    const gasolineFinal = gasolineData.forecasts?.[gasolineData.forecasts.length - 1];
    const dieselFinal = dieselData.forecasts?.[dieselData.forecasts.length - 1];
    
    const gasolineChange = gasolineFinal ? 
      ((gasolineFinal.price - gasolineData.current_price) / gasolineData.current_price) * 100 : 0;
    const dieselChange = dieselFinal ? 
      ((dieselFinal.price - dieselData.current_price) / dieselData.current_price) * 100 : 0;
    
    return {
      gasoline: {
        current: gasolineData.current_price,
        change: gasolineChange
      },
      diesel: {
        current: dieselData.current_price,
        change: dieselChange
      }
    };
  };
  
  const stats = calculateNationalStats();
  
  return (
    <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg shadow-lg text-white p-6">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* 시스템 정보 */}
        <div>
          <h2 className="text-lg font-semibold mb-3" style={{ fontSize: 'calc(1.125rem * 1.2)', fontWeight: '700' }}>활성 지역 {metadata.total_regions}개</h2>
          <div className="space-y-2">
            <div className="text-2xl font-bold">
              {metadata.total_regions}개
            </div>
            <div className="text-blue-100 text-sm">
              📍 전국 예측 지역수
            </div>
            <div className="text-blue-200 text-xs mt-2">
              갱신: {new Date(metadata.generated_at).toLocaleString('ko-KR', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        </div>

        {/* 전국 휘발유 평균 */}
        {stats && (
          <div>
            <h2 className="text-lg font-semibold mb-3" style={{ fontSize: 'calc(1.125rem * 1.2)', fontWeight: '700' }}>전국 휘발유</h2>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {stats.gasoline.current.toLocaleString()}원
              </div>
              <div className={`text-sm font-medium ${
                stats.gasoline.change > 0 ? 'text-red-200' : 
                stats.gasoline.change < 0 ? 'text-green-200' : 'text-blue-200'
              }`}>
                4주 예상 변화: {stats.gasoline.change > 0 ? '+' : ''}{stats.gasoline.change.toFixed(1)}%
              </div>
              <div className="text-blue-100 text-sm">
                {stats.gasoline.change > 1 ? '🔺 상승 전망' : 
                 stats.gasoline.change < -1 ? '🔻 하락 전망' : '➡️ 보합 전망'}
              </div>
            </div>
          </div>
        )}

        {/* 전국 경유 평균 */}
        {stats && (
          <div>
            <h2 className="text-lg font-semibold mb-3" style={{ fontSize: 'calc(1.125rem * 1.2)', fontWeight: '700' }}>전국 자동차경유</h2>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {stats.diesel.current.toLocaleString()}원
              </div>
              <div className={`text-sm font-medium ${
                stats.diesel.change > 0 ? 'text-red-200' : 
                stats.diesel.change < 0 ? 'text-green-200' : 'text-blue-200'
              }`}>
                4주 예상 변화: {stats.diesel.change > 0 ? '+' : ''}{stats.diesel.change.toFixed(1)}%
              </div>
              <div className="text-blue-100 text-sm">
                {stats.diesel.change > 1 ? '🔺 상승 전망' : 
                 stats.diesel.change < -1 ? '🔻 하락 전망' : '➡️ 보합 전망'}
              </div>
            </div>
          </div>
        )}

        {/* 보통휘발유 예측정확도 */}
        <div>
          <h2 className="text-lg font-semibold mb-3" style={{ fontSize: 'calc(1.125rem * 1.2)', fontWeight: '700' }}>보통휘발유 예측정확도</h2>
          <div className="space-y-2">
            <div className="text-2xl font-bold">
              {metadata.model_accuracy?.gasoline ? `${(metadata.model_accuracy.gasoline * 100).toFixed(1)}%` : '0.0%'}
            </div>
            <div className="text-blue-100 text-sm">
              📊 7일 예측 신뢰도
            </div>
          </div>
        </div>

        {/* 자동차경유 예측정확도 */}
        <div>
          <h2 className="text-lg font-semibold mb-3" style={{ fontSize: 'calc(1.125rem * 1.2)', fontWeight: '700' }}>자동차경유 예측정확도</h2>
          <div className="space-y-2">
            <div className="text-2xl font-bold">
              {metadata.model_accuracy?.diesel ? `${(metadata.model_accuracy.diesel * 100).toFixed(1)}%` : '0.0%'}
            </div>
            <div className="text-blue-100 text-sm">
              📊 7일 예측 신뢰도
            </div>
          </div>
        </div>
      </div>

      {/* 알림 및 주요 정보 */}
      <div className="mt-6 pt-4 border-t border-blue-500">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-yellow-300" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-blue-100 text-sm">
            예측 결과는 참고용이며, 실제 가격은 시장 상황에 따라 달라질 수 있습니다.
          </span>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;