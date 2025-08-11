import axios, { AxiosResponse } from 'axios';
import {
  ForecastData,
  Region,
  HistoricalData,
  SummaryData,
  ForecastParams,
  HistoricalParams
} from '../types/api';

// API 기본 설정
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 로깅
api.interceptors.request.use(
  (config) => {
    console.log(`API 요청: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API 요청 오류:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API 응답 오류:', error);
    
    // 네트워크 오류 처리
    if (!error.response) {
      throw new Error('서버와의 연결에 실패했습니다. 네트워크 상태를 확인해주세요.');
    }
    
    // HTTP 상태 코드별 처리
    switch (error.response.status) {
      case 404:
        throw new Error('요청한 데이터를 찾을 수 없습니다.');
      case 500:
        throw new Error('서버 내부 오류가 발생했습니다.');
      case 503:
        throw new Error('서비스를 일시적으로 사용할 수 없습니다.');
      default:
        throw new Error(error.response.data?.detail || '알 수 없는 오류가 발생했습니다.');
    }
  }
);

export const apiService = {
  // 헬스 체크
  async healthCheck(): Promise<any> {
    const response: AxiosResponse<any> = await api.get('/api/health');
    return response.data;
  },

  // 지역 목록 조회
  async getRegions(): Promise<Region[]> {
    const response: AxiosResponse<{ regions: Region[] }> = await api.get('/api/regions');
    return response.data.regions;
  },

  // 예측 데이터 조회
  async getForecast(params?: ForecastParams): Promise<ForecastData> {
    const queryParams = new URLSearchParams();
    
    if (params?.region) queryParams.append('region', params.region);
    if (params?.fuel_type) queryParams.append('fuel_type', params.fuel_type);
    if (params?.days) queryParams.append('days', params.days.toString());
    
    const url = `/api/forecast${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response: AxiosResponse<ForecastData> = await api.get(url);
    return response.data;
  },

  // 과거 데이터 조회
  async getHistoricalData(params?: HistoricalParams): Promise<HistoricalData> {
    const queryParams = new URLSearchParams();
    
    if (params?.region) queryParams.append('region', params.region);
    if (params?.fuel_type) queryParams.append('fuel_type', params.fuel_type);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    
    const url = `/api/historical${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response: AxiosResponse<HistoricalData> = await api.get(url);
    return response.data;
  },

  // 예측 요약 조회
  async getForecastSummary(): Promise<SummaryData> {
    const response: AxiosResponse<SummaryData> = await api.get('/api/forecast/summary');
    return response.data;
  },

  // 예측 데이터 갱신
  async refreshForecast(): Promise<any> {
    const response: AxiosResponse<any> = await api.post('/api/forecast/refresh');
    return response.data;
  },

  // 특정 지역의 연료별 현재 가격 조회
  async getCurrentPrice(region: string, fuelType: 'gasoline' | 'diesel'): Promise<number> {
    const forecast = await this.getForecast({ region, fuel_type: fuelType });
    const regionalData = forecast.forecasts[region];
    
    if (regionalData && regionalData[fuelType]) {
      return regionalData[fuelType]!.current_price;
    }
    
    return 0;
  },

  // 전국 평균 가격 조회
  async getNationalAverage(): Promise<{ gasoline: number; diesel: number }> {
    const forecast = await this.getForecast();
    const national = forecast.national_average;
    
    return {
      gasoline: national?.gasoline?.current_price || 0,
      diesel: national?.diesel?.current_price || 0
    };
  },

  // 가격 변화 트렌드 분석
  async getPriceTrend(region: string, fuelType: 'gasoline' | 'diesel'): Promise<{
    current: number;
    forecast: number;
    change: number;
    changePercent: number;
    trend: 'up' | 'down' | 'stable';
  }> {
    const forecast = await this.getForecast({ region, fuel_type: fuelType });
    const regionalData = forecast.forecasts[region];
    
    if (!regionalData || !regionalData[fuelType]) {
      return {
        current: 0,
        forecast: 0,
        change: 0,
        changePercent: 0,
        trend: 'stable'
      };
    }
    
    const fuelData = regionalData[fuelType]!;
    const currentPrice = fuelData.current_price;
    const forecasts = fuelData.forecasts;
    
    if (forecasts.length === 0) {
      return {
        current: currentPrice,
        forecast: currentPrice,
        change: 0,
        changePercent: 0,
        trend: 'stable'
      };
    }
    
    const finalForecast = forecasts[forecasts.length - 1].price;
    const change = finalForecast - currentPrice;
    const changePercent = (change / currentPrice) * 100;
    
    let trend: 'up' | 'down' | 'stable' = 'stable';
    if (Math.abs(changePercent) > 1) {
      trend = changePercent > 0 ? 'up' : 'down';
    }
    
    return {
      current: currentPrice,
      forecast: finalForecast,
      change,
      changePercent,
      trend
    };
  }
};

export default apiService;