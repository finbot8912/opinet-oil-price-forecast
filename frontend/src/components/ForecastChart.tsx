import React from 'react';
import { ForecastData } from '../types/api';

interface ForecastChartProps {
  forecastData: ForecastData;
  selectedRegion: string;
  selectedFuelType: 'gasoline' | 'diesel';
}

const ForecastChart: React.FC<ForecastChartProps> = ({
  forecastData,
  selectedRegion,
  selectedFuelType
}) => {
  const regionalData = forecastData.forecasts[selectedRegion];
  const fuelData = regionalData?.[selectedFuelType];

  if (!fuelData || !fuelData.forecasts.length) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500 py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-lg font-medium text-gray-900 mb-2">예측 데이터가 없습니다</p>
          <p className="text-gray-600">선택한 지역과 연료 종류에 대한 예측 데이터를 찾을 수 없습니다.</p>
          <div className="mt-4 text-sm text-gray-500">
            지역: {selectedRegion}, 연료: {selectedFuelType}
          </div>
        </div>
      </div>
    );
  }

  const currentPrice = fuelData.current_price;
  const forecasts = fuelData.forecasts;
  
  // 디버깅 정보 (개발 환경에서만)
  if (process.env.NODE_ENV === 'development') {
    console.log('ForecastChart Debug:', {
      selectedRegion,
      selectedFuelType,
      currentPrice,
      forecastsLength: forecasts.length,
      firstForecast: forecasts[0],
      lastForecast: forecasts[forecasts.length - 1]
    });
  }
  
  // 차트용 데이터 생성 (최대 28일)
  const maxDays = Math.min(28, forecasts.length);
  const chartData = [
    { day: 0, price: currentPrice, label: '현재', date: new Date().toISOString().split('T')[0] },
    ...forecasts.slice(0, maxDays).map((forecast, index) => ({
      day: index + 1,
      price: forecast.price,
      label: `${index + 1}일 후`,
      date: forecast.date ? new Date(forecast.date).toISOString().split('T')[0] : ''
    }))
  ];

  const minPrice = Math.min(...chartData.map(d => d.price));
  const maxPrice = Math.max(...chartData.map(d => d.price));
  const priceRange = maxPrice - minPrice;
  const padding = priceRange * 0.1;

  // SVG 좌표 계산 함수
  const getY = (price: number) => {
    const normalizedPrice = (price - (minPrice - padding)) / (priceRange + 2 * padding);
    return 200 - (normalizedPrice * 160); // 200px 높이에서 160px 사용
  };

  const getX = (day: number) => {
    return (day / Math.max(28, chartData.length - 1)) * 560 + 40; // 560px 너비에서 40px 오프셋
  };

  // 주별 구분선 (실제 데이터 길이에 맞춤)
  const weekLines = [7, 14, 21, 28].filter(day => day <= maxDays);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {selectedFuelType === 'gasoline' ? '휘발유' : '경유'} 가격 예측 차트
        </h3>
        <p className="text-sm text-gray-600">
          {selectedRegion} 지역 • {maxDays}일 예측 (총 {forecasts.length}일 데이터)
        </p>
      </div>

      <div className="relative">
        <svg width="640" height="240" className="w-full h-auto">
          {/* 배경 격자 */}
          <defs>
            <pattern id="grid" width="80" height="40" patternUnits="userSpaceOnUse">
              <path d="M 80 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Y축 레이블 */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio, index) => {
            const price = minPrice - padding + (priceRange + 2 * padding) * ratio;
            const y = 200 - (ratio * 160);
            return (
              <g key={index}>
                <line x1="35" y1={y} x2="600" y2={y} stroke="#e5e7eb" strokeWidth="1" opacity="0.5"/>
                <text x="30" y={y + 4} textAnchor="end" fontSize="12" fill="#6b7280">
                  {Math.round(price).toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* 주별 구분선 */}
          {weekLines.map(week => {
            const x = getX(week);
            return (
              <line
                key={week}
                x1={x}
                y1="20"
                x2={x}
                y2="200"
                stroke="#d1d5db"
                strokeWidth="1"
                strokeDasharray="4,4"
                opacity="0.7"
              />
            );
          })}

          {/* 현재 가격 기준선 */}
          <line
            x1="40"
            y1={getY(currentPrice)}
            x2="600"
            y2={getY(currentPrice)}
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="8,4"
            opacity="0.5"
          />

          {/* 예측 선 그래프 */}
          <path
            d={`M ${getX(0)} ${getY(currentPrice)} ${chartData.slice(1).map(d => 
              `L ${getX(d.day)} ${getY(d.price)}`
            ).join(' ')}`}
            fill="none"
            stroke="#ef4444"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* 현재 가격 포인트 */}
          <circle
            cx={getX(0)}
            cy={getY(currentPrice)}
            r="6"
            fill="#3b82f6"
            stroke="white"
            strokeWidth="2"
          />

          {/* 주별 포인트 */}
          {weekLines.map(week => {
            if (week < chartData.length) {
              const point = chartData[week];
              return (
                <circle
                  key={week}
                  cx={getX(point.day)}
                  cy={getY(point.price)}
                  r="5"
                  fill="#ef4444"
                  stroke="white"
                  strokeWidth="2"
                />
              );
            }
            return null;
          })}

          {/* X축 레이블 */}
          <text x="40" y="225" textAnchor="middle" fontSize="12" fill="#6b7280">현재</text>
          {weekLines.map(week => (
            <text key={week} x={getX(week)} y="225" textAnchor="middle" fontSize="12" fill="#6b7280">
              {week}일
            </text>
          ))}
        </svg>

        {/* 범례 */}
        <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-1 bg-blue-500 mr-2"></div>
            <span className="text-gray-600">현재 가격</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-1 bg-red-500 mr-2"></div>
            <span className="text-gray-600">예측 가격</span>
          </div>
        </div>
      </div>

      {/* 차트 하단 통계 */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500">현재 가격</div>
            <div className="font-semibold">{currentPrice.toLocaleString()}원</div>
          </div>
          <div>
            <div className="text-gray-500">{maxDays}일 후 예측</div>
            <div className="font-semibold">{chartData[chartData.length - 1]?.price.toLocaleString()}원</div>
          </div>
          <div>
            <div className="text-gray-500">최고 예측가</div>
            <div className="font-semibold text-red-600">{maxPrice.toLocaleString()}원</div>
          </div>
          <div>
            <div className="text-gray-500">최저 예측가</div>
            <div className="font-semibold text-green-600">{minPrice.toLocaleString()}원</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForecastChart;