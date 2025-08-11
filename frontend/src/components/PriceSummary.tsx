import React from 'react';
import { ForecastData } from '../types/api';

interface PriceSummaryProps {
  forecastData: ForecastData;
  selectedRegion: string;
  selectedFuelType: 'gasoline' | 'diesel';
}

const PriceSummary: React.FC<PriceSummaryProps> = ({
  forecastData,
  selectedRegion,
  selectedFuelType
}) => {
  const regionalData = forecastData.forecasts[selectedRegion];
  const fuelData = regionalData?.[selectedFuelType];
  const nationalData = forecastData.national_average?.[selectedFuelType];

  if (!fuelData) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-gray-500">
          <p>선택한 지역/연료 타입의 데이터를 찾을 수 없습니다.</p>
        </div>
      </div>
    );
  }

  const currentPrice = fuelData.current_price;
  const forecasts = fuelData.forecasts;
  const finalPrice = forecasts.length > 0 ? forecasts[forecasts.length - 1].price : currentPrice;
  const priceChange = finalPrice - currentPrice;
  const priceChangePercent = (priceChange / currentPrice) * 100;

  // 1주, 2주, 4주 후 예측가
  const oneWeekPrice = forecasts.length >= 7 ? forecasts[6].price : currentPrice;
  const twoWeekPrice = forecasts.length >= 14 ? forecasts[13].price : currentPrice;
  const fourWeekPrice = forecasts.length >= 28 ? forecasts[27].price : finalPrice;

  const formatPrice = (price: number) => price.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(0)}`;
  };
  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(1)}%`;
  };

  const getTrendColor = (change: number) => {
    if (Math.abs(change) < 1) return 'text-gray-600';
    return change > 0 ? 'text-red-600' : 'text-green-600';
  };

  const getTrendIcon = (change: number) => {
    if (Math.abs(change) < 1) return '→';
    return change > 0 ? '↗' : '↘';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* 현재 가격 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">현재 가격</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPrice(currentPrice)}
              <span className="text-sm font-normal text-gray-500 ml-1">원</span>
            </p>
          </div>
          <div className="p-3 bg-blue-100 rounded-full">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
          </div>
        </div>
      </div>

      {/* 1주 후 예측 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">1주 후</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPrice(oneWeekPrice)}
              <span className="text-sm font-normal text-gray-500 ml-1">원</span>
            </p>
            <p className={`text-sm font-medium ${getTrendColor(oneWeekPrice - currentPrice)}`}>
              {getTrendIcon(oneWeekPrice - currentPrice)} {formatChange(oneWeekPrice - currentPrice)}원
            </p>
          </div>
          <div className="text-2xl">📊</div>
        </div>
      </div>

      {/* 2주 후 예측 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">2주 후</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPrice(twoWeekPrice)}
              <span className="text-sm font-normal text-gray-500 ml-1">원</span>
            </p>
            <p className={`text-sm font-medium ${getTrendColor(twoWeekPrice - currentPrice)}`}>
              {getTrendIcon(twoWeekPrice - currentPrice)} {formatChange(twoWeekPrice - currentPrice)}원
            </p>
          </div>
          <div className="text-2xl">📈</div>
        </div>
      </div>

      {/* 4주 후 예측 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">4주 후</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPrice(fourWeekPrice)}
              <span className="text-sm font-normal text-gray-500 ml-1">원</span>
            </p>
            <p className={`text-sm font-medium ${getTrendColor(priceChange)}`}>
              {getTrendIcon(priceChange)} {formatChange(priceChange)}원 ({formatPercent(priceChangePercent)})
            </p>
          </div>
          <div className="text-2xl">🎯</div>
        </div>
      </div>

      {/* 전국 평균 비교 */}
      {nationalData && (
        <div className="bg-white rounded-lg shadow-md p-6 md:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">전국 평균 대비</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">현재 전국 평균</span>
              <span className="font-medium">{formatPrice(nationalData.current_price)}원</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">지역 가격</span>
              <span className="font-medium">{formatPrice(currentPrice)}원</span>
            </div>
            <div className="border-t pt-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">차이</span>
                <span className={`font-bold ${getTrendColor(currentPrice - nationalData.current_price)}`}>
                  {formatChange(currentPrice - nationalData.current_price)}원 
                  ({formatPercent(((currentPrice - nationalData.current_price) / nationalData.current_price) * 100)})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 예측 통계 */}
      <div className="bg-white rounded-lg shadow-md p-6 md:col-span-2">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">예측 통계</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">변동성</span>
            <span className="font-medium">
              {fuelData.volatility ? `${(fuelData.volatility * 100).toFixed(1)}%` : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">예측 기간</span>
            <span className="font-medium">{forecasts.length}일</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">최고 예측가</span>
            <span className="font-medium">
              {formatPrice(Math.max(...forecasts.map(f => f.price)))}원
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">최저 예측가</span>
            <span className="font-medium">
              {formatPrice(Math.min(...forecasts.map(f => f.price)))}원
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PriceSummary;