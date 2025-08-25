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

import mockDevices from '../../public/mock-devices.json';

const FACTORY_URL = process.env.NEXT_PUBLIC_CCTV_FACTORY_URL || '';
const MACHINE_BASE_URL = process.env.NEXT_PUBLIC_CCTV_MACHINE_BASE_URL || '';

type MockDevice = { id: string; name: string; status: string };

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
  ...((mockDevices as MockDevice[]).map((dev) => {
    const url = MACHINE_BASE_URL ? `${MACHINE_BASE_URL}${dev.id}.m3u8` : '';
    return {
      id: dev.id,
      name: dev.name,
      kind: 'machine' as const,
      protocol: inferProtocol(url),
      url,
      active: dev.status === 'online',
      badge: dev.status === 'online' ? 'LIVE' : undefined,
      note: dev.status !== 'online' ? 'offline' : undefined,
    } as Camera;
  })),
];
