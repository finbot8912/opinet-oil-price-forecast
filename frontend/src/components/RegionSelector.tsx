import React from 'react';
import { Region } from '../types/api';

interface RegionSelectorProps {
  regions: Region[];
  selectedRegion: string;
  onRegionChange: (region: string) => void;
}

const RegionSelector: React.FC<RegionSelectorProps> = ({ 
  regions, 
  selectedRegion, 
  onRegionChange 
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        지역 선택
      </label>
      <select
        value={selectedRegion}
        onChange={(e) => onRegionChange(e.target.value)}
        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
      >
        {regions.map((region) => (
          <option key={region.code} value={region.code}>
            {region.short_name || region.name}
          </option>
        ))}
      </select>

      {/* 주요 지역 퀵 선택 버튼 */}
      <div className="mt-3">
        <div className="text-xs font-medium text-gray-500 mb-2">주요 지역</div>
        <div className="grid grid-cols-3 gap-2">
          {['seoul', 'busan', 'daegu', 'incheon', 'gwangju', 'daejeon'].map((regionCode) => {
            const region = regions.find(r => r.code === regionCode);
            if (!region) return null;

            return (
              <button
                key={regionCode}
                onClick={() => onRegionChange(regionCode)}
                className={`px-3 py-2 text-xs rounded-md transition-colors ${
                  selectedRegion === regionCode
                    ? 'bg-blue-100 text-blue-800 border border-blue-300'
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                }`}
              >
                {region.short_name || region.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* 지역별 특성 표시 (선택사항) */}
      <div className="mt-4 p-3 bg-gray-50 rounded-md">
        <div className="text-xs font-medium text-gray-700 mb-1">지역 정보</div>
        <div className="text-xs text-gray-600">
          {selectedRegion === 'seoul' && '수도권 • 높은 교통량 • 인구 밀집지역'}
          {selectedRegion === 'busan' && '동남권 • 항만도시 • 해운물류 중심'}
          {selectedRegion === 'daegu' && '영남권 • 내륙 중심지 • 섬유산업'}
          {selectedRegion === 'incheon' && '수도권 • 국제공항 • 항만물류'}
          {selectedRegion === 'gwangju' && '호남권 • 지역 중심지 • 광공업'}
          {selectedRegion === 'daejeon' && '충청권 • 교통 요충지 • 과학기술'}
          {selectedRegion === 'ulsan' && '동남권 • 산업도시 • 석유화학'}
          {selectedRegion === 'sejong' && '행정중심 • 신도시 • 정부청사'}
          {selectedRegion === 'gyeonggi' && '수도권 • 인구 밀집 • 산업단지'}
          {selectedRegion === 'gangwon' && '영동/영서 • 관광지 • 산간지역'}
          {selectedRegion === 'chungbuk' && '내륙지역 • 교통중심 • 반도체산업'}
          {selectedRegion === 'chungnam' && '서해안 • 석유화학 • 항만'}
          {selectedRegion === 'jeonbuk' && '농업중심 • 전통문화 • 새만금'}
          {selectedRegion === 'jeonnam' && '남해안 • 조선업 • 농수산업'}
          {selectedRegion === 'gyeongbuk' && '내륙지역 • 전통문화 • 농업'}
          {selectedRegion === 'gyeongnam' && '남해안 • 기계공업 • 항만'}
          {selectedRegion === 'jeju' && '섬 지역 • 관광/물류 • 특별자치도'}
          {!['seoul', 'busan', 'daegu', 'incheon', 'gwangju', 'daejeon', 'ulsan', 'sejong', 'gyeonggi', 'gangwon', 'chungbuk', 'chungnam', 'jeonbuk', 'jeonnam', 'gyeongbuk', 'gyeongnam', 'jeju'].includes(selectedRegion) && 
            regions.find(r => r.code === selectedRegion)?.name
          }
        </div>
      </div>
    </div>
  );
};

export default RegionSelector;