import React from 'react';

interface HeaderProps {
  onRefresh: () => void;
  loading: boolean;
}

const Header: React.FC<HeaderProps> = ({ onRefresh, loading }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          {/* 로고 및 제목 */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold text-gray-900">유가 예측 시스템</h1>
                <p className="text-sm text-gray-600">Oil Price Forecasting</p>
              </div>
            </div>
          </div>

          {/* 우측 액션 버튼들 */}
          <div className="flex items-center space-x-4">
            {/* 데이터 갱신 버튼 */}
            <button
              onClick={onRefresh}
              disabled={loading}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                loading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <svg 
                className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth="2" 
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
                />
              </svg>
              {loading ? '갱신 중...' : '데이터 갱신'}
            </button>

            {/* 현재 시간 표시 */}
            <div className="hidden md:flex items-center text-sm text-gray-500">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {new Date().toLocaleString('ko-KR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        </div>

        {/* 네비게이션 탭 (선택사항) */}
        <nav className="mt-4">
          <div className="flex space-x-8 border-b border-gray-200">
            <button className="py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm">
              가격 전망
            </button>
            <button className="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 font-medium text-sm">
              과거 데이터
            </button>
            <button className="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 font-medium text-sm">
              분석 리포트
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Header;