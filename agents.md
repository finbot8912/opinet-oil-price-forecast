# AGENTS.MD - 오피넷 유가 예측 시스템 AI 에이전트 역할 정의서

## 🏗️ 시스템 아키텍처

**프로젝트**: 한국석유공사 오피넷 실시간 유가 예측 시스템  
**목표**: 15개 변동 요인 기반 7일간 휘발유/경유 가격 예측  
**기술 스택**: Python Flask + JavaScript + 오피넷 API + 15개 AI 모델  

---

## 📋 에이전트 역할 분담

### 🎯 기획1 에이전트 (Strategic Planning Agent)
**역할**: 비즈니스 전략 기획 및 시장 분석 전문가

#### 핵심 책임
1. **시장 환경 분석**
   - 한국 유가 시장의 특성 및 트렌드 분석
   - 오피넷 시스템의 투명성과 정부 정책 영향도 평가
   - 국제 유가와 국내 유가의 연동성 분석
   - 계절별/지역별 소비 패턴 연구

2. **사업 기획 및 전략 수립**
   - 유가 예측 서비스의 비즈니스 모델 설계
   - 타겟 사용자 정의 (일반 소비자, 운송업계, 정유사 등)
   - 경쟁사 분석 및 차별화 전략 수립
   - ROI 및 비즈니스 임팩트 측정 방법론 정의

3. **요구사항 정의 및 우선순위 결정**
   - 사용자 니즈 분석 및 기능 우선순위 설정
   - 예측 정확도 vs 사용자 경험 균형점 찾기
   - 실시간성 vs 정확성 트레이드오프 분석
   - 지역별/연료별 예측 세분화 전략

4. **성과 지표 및 KPI 설계**
   - 예측 정확도 측정 방법론 (MAPE, RMSE, MAE)
   - 사용자 만족도 지표 정의
   - 시스템 성능 벤치마크 설정
   - 비즈니스 성과 추적 체계 구축

#### 전문 지식 영역
- 석유 산업 밸류체인 및 가격 결정 메커니즘
- 한국 에너지 정책 및 유류세 체계
- 국제 원유 시장 동향 및 지정학적 리스크
- 소비자 행동 패턴 및 시장 세분화

### 🎯 기획2 에이전트 (Technical Planning Agent)
**역할**: 기술 기획 및 시스템 설계 전문가

#### 핵심 책임
1. **기술 아키텍처 설계**
   - 15개 AI 모델의 통합 아키텍처 설계
   - 실시간 데이터 처리 파이프라인 설계
   - 모델 앙상블 및 가중치 최적화 전략
   - 확장 가능한 마이크로서비스 아키텍처 설계

2. **데이터 전략 수립**
   - 15개 변동 요인별 데이터 소스 정의 및 품질 관리
   - 실시간 데이터 수집 및 전처리 파이프라인 설계
   - 데이터 거버넌스 및 품질 보증 체계 구축
   - 외부 API 연동 및 장애 복구 전략

3. **AI/ML 모델 전략**
   - 15개 변동 요인별 최적 AI 모델 선택 및 조합
   - 모델 성능 평가 및 지속적 개선 체계
   - A/B 테스트 및 모델 배포 전략
   - 모델 해석 가능성 및 신뢰성 보장

4. **기술 로드맵 및 구현 계획**
   - 단계별 개발 계획 및 마일스톤 설정
   - 기술 부채 관리 및 리팩토링 전략
   - 성능 최적화 및 스케일링 계획
   - 보안 및 규정 준수 체계 구축

#### 전문 지식 영역
- 시계열 분석 및 예측 모델링
- 실시간 데이터 처리 및 스트리밍 아키텍처
- 머신러닝 모델 운영 및 MLOps
- API 설계 및 마이크로서비스 아키텍처

### 🔬 데이터 사이언티스트 에이전트
**역할**: 15개 AI 모델 개발 및 최적화

#### 핵심 책임
- 15개 변동 요인별 예측 모델 개발
- 모델 성능 평가 및 하이퍼파라미터 튜닝
- 앙상블 모델 및 가중치 최적화
- 이상치 탐지 및 데이터 품질 관리

### 🏗️ 백엔드 개발 에이전트
**역할**: Flask API 서버 및 데이터 처리

#### 핵심 책임
- RESTful API 설계 및 구현
- 오피넷 API 연동 및 실시간 데이터 처리
- 데이터베이스 설계 및 성능 최적화
- 보안 및 에러 핸들링

### 🎨 프론트엔드 개발 에이전트
**역할**: 사용자 인터페이스 개발

#### 핵심 책임
- 반응형 웹 인터페이스 개발
- 데이터 시각화 및 차트 구현
- 사용자 경험 최적화
- 성능 및 접근성 보장

### 🧪 QA 테스트 에이전트
**역할**: 품질 보증 및 테스트

#### 핵심 책임
- 예측 정확도 검증 및 성능 테스트
- API 테스트 및 통합 테스트
- 사용자 시나리오 테스트
- 보안 및 부하 테스트

---

## 🤖 18개 변동 요인별 AI 모델 상세

### 1. 국제 요인 (40% 가중치)

#### 1.1 Dubai 국제원유가격 (25% 가중치)
**AI 모델**: ARIMA + LSTM 하이브리드 모델
```python
# ARIMA-LSTM 하이브리드 모델
def dubai_oil_price_model():
    # ARIMA 컴포넌트 (선형 트렌드)
    arima_trend = ARIMA(order=(2,1,2)).fit(historical_data)
    
    # LSTM 컴포넌트 (비선형 패턴)
    lstm_model = Sequential([
        LSTM(50, return_sequences=True),
        Dropout(0.2),
        LSTM(50),
        Dense(1)
    ])
    
    # 앙상블 예측
    prediction = 0.6 * arima_trend + 0.4 * lstm_model
    return prediction

# 계산식
dubai_impact = (dubai_price_change / dubai_base_price) * 0.25 * fuel_sensitivity
```

#### 1.2 싱가포르 국제제품가격 (8% 가중치)
**AI 모델**: Vector Autoregression (VAR) 모델
```python
# VAR 모델 (다변량 시계열)
def singapore_product_model():
    # 휘발유, 경유, 제트연료 가격 간 상관관계 모델링
    model = VAR(endog_data[['gasoline', 'diesel', 'jet_fuel']])
    results = model.fit(maxlags=7)
    forecast = results.forecast(steps=7)
    return forecast

# 계산식
singapore_impact = (product_price_change / base_price) * 0.08 * regional_factor
```

#### 1.3 싱가포르 정제마진 (7% 가중치)
**AI 모델**: Gaussian Process Regression
```python
# 가우시안 프로세스 회귀
def refinery_margin_model():
    kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
    gp = GaussianProcessRegressor(kernel=kernel)
    gp.fit(X_train, y_train)
    prediction, std = gp.predict(X_test, return_std=True)
    return prediction, std

# 계산식
margin_impact = (margin_change / historical_avg_margin) * 0.07 * volatility_factor
```

### 2. 환율 요인 (15% 가중치)

#### 2.1 USD/KRW 환율 (15% 가중치)
**AI 모델**: GARCH-LSTM 모델
```python
# GARCH-LSTM 변동성 모델
def exchange_rate_model():
    # GARCH 모델로 변동성 예측
    garch = arch_model(returns, vol='Garch', p=1, q=1)
    garch_result = garch.fit()
    volatility_forecast = garch_result.forecast(horizon=7)
    
    # LSTM으로 가격 예측
    lstm = Sequential([
        LSTM(64, activation='tanh'),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    
    return lstm_prediction * volatility_forecast

# 계산식
exchange_impact = (usd_krw_change / base_rate) * 0.15 * oil_import_ratio
```

### 3. 국내 정책 요인 (20% 가중치)

#### 3.1 유류세 정책 (12% 가중치)
**AI 모델**: Policy Change Detection + Rule-Based System
```python
# 정책 변화 탐지 모델
def fuel_tax_model():
    # NLP 기반 정책 변화 탐지
    policy_changes = detect_policy_changes(news_data, policy_docs)
    
    # 룰 기반 영향도 계산
    tax_impact = 0
    if policy_changes['tax_cut']:
        tax_impact = -policy_changes['cut_amount'] / current_price
    elif policy_changes['tax_increase']:
        tax_impact = policy_changes['increase_amount'] / current_price
    
    return tax_impact * 0.12

# 계산식
tax_impact = (tax_change_amount / base_price) * 0.12 * policy_certainty
```

#### 3.2 원유수입단가 CIF기준 (8% 가중치)
**AI 모델**: Multiple Linear Regression with Lasso Regularization
```python
# 정규화된 다중선형회귀
def import_price_model():
    features = ['dubai_oil', 'freight_cost', 'insurance', 'exchange_rate']
    model = Lasso(alpha=0.1)
    model.fit(X_train[features], y_train)
    prediction = model.predict(X_test)
    return prediction

# 계산식
import_impact = (cif_price_change / base_cif) * 0.08 * import_dependency
```

### 4. 국내 수급 요인 (15% 가중치)

#### 4.1 국내 석유재고 (6% 가중치)
**AI 모델**: Inventory Optimization + Prophet
```python
# Prophet 시계열 예측 + 재고 최적화
def inventory_model():
    # Prophet으로 계절성 고려
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    model.fit(inventory_df)
    forecast = model.predict(future_df)
    
    # 재고-가격 탄성도 적용
    elasticity = -0.15  # 재고 증가 시 가격 하락
    price_impact = elasticity * (forecast_inventory - normal_inventory) / normal_inventory
    
    return price_impact * 0.06

# 계산식
inventory_impact = -0.15 * (current_inventory - avg_inventory) / avg_inventory * 0.06
```

#### 4.2 국내 제품소비량 (5% 가중치)
**AI 모델**: Seasonal ARIMA + External Regressors
```python
# SARIMAX 모델 (계절성 + 외부 변수)
def consumption_model():
    model = SARIMAX(
        consumption_data,
        exog=external_vars,  # GDP, 온도, 휴일 등
        order=(2,1,2),
        seasonal_order=(1,1,1,12)
    )
    results = model.fit()
    forecast = results.forecast(steps=7, exog=future_exog)
    return forecast

# 계산식
consumption_impact = (forecast_consumption - base_consumption) / base_consumption * 0.05
```

#### 4.3 지역별 소비량 (4% 가중치)
**AI 모델**: Hierarchical Time Series + Spatial Analysis
```python
# 계층적 시계열 + 공간 분석
def regional_consumption_model():
    # 지역 간 공간 상관관계 모델링
    spatial_weights = calculate_spatial_weights(regions)
    
    # 계층적 예측 (전국 → 지역)
    national_forecast = national_model.forecast(7)
    regional_forecasts = []
    
    for region in regions:
        regional_model = ARIMA(order=(1,1,1))
        regional_forecast = regional_model.forecast(7)
        
        # 공간 조정
        spatial_adjustment = np.dot(spatial_weights[region], neighbor_forecasts)
        adjusted_forecast = 0.7 * regional_forecast + 0.3 * spatial_adjustment
        
        regional_forecasts.append(adjusted_forecast)
    
    return regional_forecasts

# 계산식
regional_impact = sum(region_weight[i] * region_change[i] for i in regions) * 0.04
```

### 5. 경제 요인 (7% 가중치)

#### 5.1 소비자 물가지수 (3% 가중치)
**AI 모델**: Cointegration + Error Correction Model
```python
# 공적분 및 오차수정 모델
def cpi_model():
    # 공적분 관계 확인
    coint_result = coint(oil_prices, cpi_data)
    
    if coint_result[1] < 0.05:  # 공적분 존재
        # 오차수정 모델
        ecm = VECM(np.column_stack([oil_prices, cpi_data]), k_ar_diff=2)
        ecm_result = ecm.fit()
        forecast = ecm_result.predict(steps=7)
        return forecast
    else:
        # VAR 모델로 대체
        var_model = VAR(np.column_stack([oil_prices, cpi_data]))
        return var_model.fit().forecast(steps=7)

# 계산식
cpi_impact = (cpi_change / base_cpi) * correlation_coefficient * 0.03
```

#### 5.2 전국 지가변동률 (2% 가중치)
**AI 모델**: Ridge Regression with Polynomial Features
```python
# 다항 특성 회귀
def land_price_model():
    # 다항 특성 생성
    poly_features = PolynomialFeatures(degree=2)
    X_poly = poly_features.fit_transform(land_price_features)
    
    # Ridge 회귀로 과적합 방지
    model = Ridge(alpha=1.0)
    model.fit(X_poly, oil_price_changes)
    
    prediction = model.predict(poly_features.transform(current_features))
    return prediction

# 계산식
land_impact = polynomial_function(land_price_change, gdp_growth, interest_rate) * 0.02
```

#### 5.3 전국 자동차등록현황 (2% 가중치)
**AI 모델**: Logistic Growth Model + Trend Analysis
```python
# 로지스틱 성장 모델
def vehicle_registration_model():
    # 로지스틱 성장 곡선 피팅
    def logistic_growth(t, K, r, t0):
        return K / (1 + np.exp(-r * (t - t0)))
    
    popt, _ = curve_fit(logistic_growth, time_data, vehicle_data)
    K, r, t0 = popt
    
    # 미래 등록 대수 예측
    future_vehicles = logistic_growth(future_time, K, r, t0)
    
    # 전기차 보급률 고려
    ev_penetration = predict_ev_penetration(future_time)
    fuel_demand_impact = -(ev_penetration * future_vehicles) / total_vehicles
    
    return fuel_demand_impact * 0.02

# 계산식
vehicle_impact = (new_registrations - ev_registrations) / total_vehicles * elasticity * 0.02
```

### 6. 유통 요인 (3% 가중치)

#### 6.1 정유사-대리점-주유소 마진 (2% 가중치)
**AI 모델**: Game Theory + Nash Equilibrium
```python
# 게임 이론 기반 마진 예측
def retail_margin_model():
    # 플레이어: 정유사, 대리점, 주유소
    players = ['refinery', 'distributor', 'gas_station']
    
    # 각 플레이어의 비용 함수
    cost_functions = {
        'refinery': lambda q: a1 * q**2 + b1 * q + c1,
        'distributor': lambda q: a2 * q**2 + b2 * q + c2,
        'gas_station': lambda q: a3 * q**2 + b3 * q + c3
    }
    
    # 내쉬 균형점 계산
    equilibrium = solve_nash_equilibrium(cost_functions, demand_function)
    optimal_margins = calculate_margins(equilibrium)
    
    return optimal_margins

# 계산식
margin_impact = (current_margin - equilibrium_margin) / base_margin * 0.02
```

#### 6.2 물류비용 및 유통비용 (1% 가중치)
**AI 모델**: Transport Cost Optimization + Fuel Efficiency Analysis
```python
# 운송비용 최적화 모델
def distribution_cost_model():
    # 운송 네트워크 그래프
    G = create_distribution_network()
    
    # 최단 경로 알고리즘
    shortest_paths = {}
    for source in refineries:
        for destination in gas_stations:
            path = nx.shortest_path(G, source, destination, weight='cost')
            shortest_paths[(source, destination)] = path
    
    # 총 운송비용 계산
    total_cost = 0
    for route, path in shortest_paths.items():
        distance = calculate_route_distance(path)
        fuel_cost = distance * fuel_efficiency * diesel_price
        driver_cost = distance * driver_rate
        total_cost += fuel_cost + driver_cost
    
    # 인플레이션 및 유가 변동 고려
    inflation_factor = predict_inflation()
    cost_forecast = total_cost * (1 + inflation_factor)
    
    return (cost_forecast - base_cost) / base_cost * 0.01

# 계산식
distribution_impact = (transport_cost_change + storage_cost_change + labor_cost_change) / base_cost * 0.01
```

---

## 🔄 모델 통합 및 앙상블

### 앙상블 가중치 최적화
```python
# Bayesian Optimization으로 가중치 최적화
def optimize_ensemble_weights():
    def objective(weights):
        # 가중치 정규화
        normalized_weights = weights / np.sum(weights)
        
        # 앙상블 예측
        ensemble_pred = np.sum([
            w * model_pred for w, model_pred 
            in zip(normalized_weights, individual_predictions)
        ], axis=0)
        
        # 검증 데이터로 성능 평가
        mape = mean_absolute_percentage_error(y_true, ensemble_pred)
        return mape
    
    # Bayesian Optimization
    optimizer = BayesianOptimization(
        f=objective,
        pbounds={(f'weight_{i}': (0.01, 1.0) for i in range(15))},
        random_state=42
    )
    
    optimizer.maximize(init_points=10, n_iter=50)
    optimal_weights = optimizer.max['params']
    
    return optimal_weights
```

### 최종 예측 계산
```python
def generate_final_forecast():
    # 15개 모델의 개별 예측
    predictions = {
        'dubai_oil': dubai_oil_price_model(),
        'singapore_product': singapore_product_model(),
        'refinery_margin': refinery_margin_model(),
        'exchange_rate': exchange_rate_model(),
        'fuel_tax': fuel_tax_model(),
        'import_price': import_price_model(),
        'inventory': inventory_model(),
        'consumption': consumption_model(),
        'regional_consumption': regional_consumption_model(),
        'cpi': cpi_model(),
        'land_price': land_price_model(),
        'vehicle_registration': vehicle_registration_model(),
        'retail_margin': retail_margin_model(),
        'distribution_cost': distribution_cost_model()
    }
    
    # 가중치 적용
    weights = load_optimal_weights()
    
    # 최종 예측 계산
    final_prediction = sum(
        weights[factor] * prediction 
        for factor, prediction in predictions.items()
    )
    
    # 불확실성 정량화
    prediction_intervals = calculate_prediction_intervals(
        predictions, weights, confidence_level=0.95
    )
    
    return {
        'point_forecast': final_prediction,
        'lower_bound': prediction_intervals['lower'],
        'upper_bound': prediction_intervals['upper'],
        'confidence_level': 0.95
    }
```

---

## 📊 성과 평가 지표

### 정확도 지표
- **MAPE** (Mean Absolute Percentage Error): < 3%
- **RMSE** (Root Mean Square Error): < 50원
- **MAE** (Mean Absolute Error): < 30원
- **방향성 정확도**: > 85%

### 비즈니스 지표
- **사용자 만족도**: > 4.5/5.0
- **API 응답 시간**: < 200ms
- **시스템 가용성**: > 99.9%
- **예측 업데이트 주기**: 실시간 (매시간)

### 모델 신뢰성 지표
- **백테스팅 성능**: 과거 2년 데이터 기준 > 90% 정확도
- **교차 검증 점수**: 5-fold CV > 0.85
- **특성 중요도 안정성**: 상위 5개 요인 일관성 > 95%
- **예측 구간 적중률**: 95% 신뢰구간 실제 적중률 > 93%

---

## 🚀 배포 및 운영

### CI/CD 파이프라인
```yaml
# .github/workflows/deploy.yml
name: Oil Price Forecast Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run model tests
        run: pytest tests/model_tests.py
      
      - name: Deploy to production
        run: |
          docker build -t oil-forecast .
          docker push $ECR_REGISTRY/oil-forecast:latest
```

### 모니터링 및 알림
- **모델 드리프트 감지**: 매일 성능 모니터링
- **데이터 품질 검사**: 실시간 이상치 탐지
- **API 성능 모니터링**: Prometheus + Grafana
- **장애 알림**: Slack/이메일 자동 알림

이 에이전트 시스템을 통해 15개 변동 요인을 종합적으로 분석하여 정확하고 신뢰할 수 있는 유가 예측 서비스를 제공합니다.