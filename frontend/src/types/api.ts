// API 응답 타입 정의

export interface Region {
  code: string;
  name: string;
  short_name?: string;
}

export interface ForecastItem {
  date: string;
  price: number;
  confidence?: number;
}

export interface FuelTypeData {
  current_price: number;
  trend?: number;
  volatility?: number;
  forecasts: ForecastItem[];
}

export interface RegionalForecast {
  gasoline?: FuelTypeData;
  diesel?: FuelTypeData;
}

export interface NationalAverageItem {
  date: string;
  price: number;
  min_price: number;
  max_price: number;
  std_dev: number;
}

export interface NationalAverage {
  gasoline?: {
    current_price: number;
    forecasts: NationalAverageItem[];
  };
  diesel?: {
    current_price: number;
    forecasts: NationalAverageItem[];
  };
}

export interface ForecastMetadata {
  generated_at: string;
  forecast_horizon_days: number;
  total_regions: number;
  fuel_types: string[];
}

export interface ForecastData {
  metadata: ForecastMetadata;
  forecasts: {
    [regionCode: string]: RegionalForecast;
  };
  national_average?: NationalAverage;
}

export interface HistoricalDataItem {
  date: string;
  gasoline: { [region: string]: number };
  diesel: { [region: string]: number };
}

export interface HistoricalData {
  metadata: {
    total_records: number;
    date_range: {
      start?: string;
      end?: string;
    };
    filters: {
      region?: string;
      fuel_type?: string;
    };
  };
  data: HistoricalDataItem[];
}

export interface SummaryData {
  metadata: ForecastMetadata;
  national_average: NationalAverage;
  regional_summary: {
    [regionCode: string]: {
      gasoline?: {
        current_price: number;
        forecast_price: number;
        change_amount: number;
        change_percent: number;
        trend: string;
      };
      diesel?: {
        current_price: number;
        forecast_price: number;
        change_amount: number;
        change_percent: number;
        trend: string;
      };
    };
  };
}

// API 요청 매개변수 타입
export interface ForecastParams {
  region?: string;
  fuel_type?: string;
  days?: number;
}

export interface HistoricalParams {
  region?: string;
  fuel_type?: string;
  start_date?: string;
  end_date?: string;
}

// API 응답 기본 형태
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}