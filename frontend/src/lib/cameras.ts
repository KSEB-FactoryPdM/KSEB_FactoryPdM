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

import machines from '../../public/machines.json';

const FACTORY_URL = process.env.NEXT_PUBLIC_CCTV_FACTORY_URL || '';
const FACTORY_ZONE_BASE_URL = process.env.NEXT_PUBLIC_CCTV_FACTORY_ZONE_BASE_URL || '';
const MACHINE_BASE_URL = process.env.NEXT_PUBLIC_CCTV_MACHINE_BASE_URL || '';

type Machine = { id: string };

const overviewCameras: Camera[] = [
  {
    id: 'factory-overview',
    name: '공장 전체',
    kind: 'overview',
    protocol: inferProtocol(FACTORY_URL),
    url: FACTORY_URL,
    active: Boolean(FACTORY_URL),
    badge: FACTORY_URL ? 'LIVE' : undefined,
    note: FACTORY_URL ? undefined : '대기',
  },
  ...Array.from({ length: 4 }, (_, i) => {
    const url = FACTORY_ZONE_BASE_URL ? `${FACTORY_ZONE_BASE_URL}${i + 1}.m3u8` : '';
    const active = Boolean(FACTORY_ZONE_BASE_URL);
    return {
      id: `factory-zone${i + 1}`,
      name: `${i + 1}구역`,
      kind: 'overview' as const,
      protocol: inferProtocol(url),
      url,
      active,
      badge: active ? 'LIVE' : undefined,
      note: active ? undefined : '대기',
    } as Camera;
  }),
];

export const cameras: Camera[] = [
  ...overviewCameras,
  ...(machines as Machine[]).map((m) => {
    const url = MACHINE_BASE_URL ? `${MACHINE_BASE_URL}${m.id}.m3u8` : '';
    const active = Boolean(MACHINE_BASE_URL);
    return {
      id: m.id,
      name: m.id,
      kind: 'machine' as const,
      protocol: inferProtocol(url),
      url,
      active,
      badge: active ? 'LIVE' : undefined,
      note: active ? undefined : '대기',
    } as Camera;
  }),
];
