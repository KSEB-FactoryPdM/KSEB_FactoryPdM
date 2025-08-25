export type CameraProtocol = 'hls' | 'webrtc' | 'mjpeg';
export type CameraKind = 'overview' | 'machine';

export type Camera = {
  id: string;
  name: string;
  kind: CameraKind;
  protocol: CameraProtocol;
  url: string;
  active: boolean;       // true면 실제 재생, false면 UI에만 노출(비활성 타일)
  badge?: string;        // 'LIVE' 등 배지 표기
  note?: string;         // 비활성 타일 설명
};

function inferProtocol(url: string): CameraProtocol {
  const u = url.toLowerCase();
  if (u.startsWith('webrtc://') || u.startsWith('whep://') || u.includes('/whep')) return 'webrtc';
  if (u.endsWith('.m3u8')) return 'hls';
  if (u.endsWith('.mjpeg') || u.endsWith('.mjpg') || u.includes('mjpeg')) return 'mjpeg';
  // 기본은 HLS로 가정
  return 'hls';
}

const FACTORY_URL = process.env.NEXT_PUBLIC_CCTV_FACTORY_URL || '';
const MACHINE1_URL = process.env.NEXT_PUBLIC_CCTV_MACHINE1_URL || '';
const MACHINE2_URL = process.env.NEXT_PUBLIC_CCTV_MACHINE2_URL || '';

export const cameras: Camera[] = [
  {
    id: 'factory-overview',
    name: '공장 전체',
    kind: 'overview',
    protocol: inferProtocol(FACTORY_URL),
    url: FACTORY_URL,
    active: true,
    badge: 'LIVE',
  },
  {
    id: 'L-CAHU-01R',
    name: 'L-CAHU-01R',
    kind: 'machine',
    protocol: inferProtocol(MACHINE1_URL),
    url: MACHINE1_URL,
    active: true,
    badge: 'LIVE',
  },
  {
    id: 'R-CAHU-01R',
    name: 'R-CAHU-01R',
    kind: 'machine',
    protocol: inferProtocol(MACHINE2_URL),
    url: MACHINE2_URL,
    active: true,
    badge: 'LIVE',
  },

  // ===== 아래부터는 "있어 보이는" 비활성 타일들 =====
  { id: 'M-VFD-11kW', name: 'M-VFD-11kW', kind: 'machine', protocol: 'hls', url: '#', active: false, note: '관리자 권한 필요' },
  { id: 'M-PUMP-22kW', name: 'M-PUMP-22kW', kind: 'machine', protocol: 'hls', url: '#', active: false, note: '노드 오프라인' },
  { id: 'M-FAN-2_2kW', name: 'M-FAN-2.2kW', kind: 'machine', protocol: 'hls', url: '#', active: false, note: '점검 중' },
  { id: 'M-GEAR-55kW', name: 'M-GEAR-55kW', kind: 'machine', protocol: 'hls', url: '#', active: false, note: '대기' },
  { id: 'M-MIXER-7_5kW', name: 'M-MIXER-7.5kW', kind: 'machine', protocol: 'hls', url: '#', active: false, note: '배정 대기' },
];
