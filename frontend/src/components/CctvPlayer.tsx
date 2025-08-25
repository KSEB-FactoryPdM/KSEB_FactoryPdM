'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { CameraProtocol } from '@/lib/cameras';
import { useWhep } from '@/hooks/useWhep';
import type Hls from 'hls.js';

type Props = {
  title: string;
  url: string;
  protocol: CameraProtocol; // 'hls' | 'webrtc' | 'mjpeg'
  badge?: string;
  initialMuted?: boolean;
};

export default function CctvPlayer({ title, url, protocol, badge, initialMuted = true }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [muted, setMuted] = useState(initialMuted);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const keyRef = useRef<number>(0); // reload용

  const isHls = protocol === 'hls';
  const isWebrtc = protocol === 'webrtc';
  const isMjpeg = protocol === 'mjpeg';

  // WebRTC(WHEP)
  useWhep(videoRef.current, isWebrtc ? url : null);

  // HLS(.m3u8)
  useEffect(() => {
    if (!isHls) return;
    const el = videoRef.current;
    if (!el) return;
    let hls: Hls | null = null;
    let canceled = false;

    (async () => {
      try {
        setLoading(true);
        setError(null);

        const canNative = el.canPlayType('application/vnd.apple.mpegurl');
        if (canNative) {
          el.src = url;
          await el.play().catch(() => {});
        } else {
          const mod = await import('hls.js');
          const Hls = mod.default;
          if (Hls.isSupported()) {
            hls = new Hls({ enableWorker: true, lowLatencyMode: true });
            hls.loadSource(url);
            hls.attachMedia(el);
            hls.on(Hls.Events.MANIFEST_PARSED, () => {
              el.play().catch(() => {});
            });
            hls.on(Hls.Events.ERROR, (_evt: unknown, data: unknown) => {
              console.error('HLS error', data);
              setError((data as { details?: string })?.details || 'HLS error');
            });
          } else {
            setError('HLS not supported in this browser');
          }
        }
      } catch (e: unknown) {
        if (!canceled) {
          const msg = e instanceof Error ? e.message : String(e);
          setError(msg);
        }
      } finally {
        if (!canceled) setLoading(false);
      }
    })();

    return () => {
      canceled = true;
      try {
        if (hls) {
          hls.destroy();
          hls = null;
        }
        if (el) {
          el.pause?.();
          el.removeAttribute('src');
          el.srcObject = null;
          el.load?.();
        }
      } catch {}
    };
  }, [isHls, url, keyRef.current]);

  // MJPEG는 <img>로 표시
  const mjpegEl = useMemo(() => {
    if (!isMjpeg) return null;
    return (
      <img
        key={keyRef.current}
        src={url}
        alt={title}
        className="w-full h-full object-cover rounded-lg"
        onLoad={() => setLoading(false)}
        onError={() => {
          setError('MJPEG load error');
          setLoading(false);
        }}
      />
    );
  }, [isMjpeg, url, title, keyRef.current]);

  function handleReload() {
    setError(null);
    setLoading(true);
    keyRef.current += 1; // 재마운트
  }

  function handleFullscreen() {
    const container = videoRef.current?.parentElement;
    if (!container) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else {
      container.requestFullscreen().catch(() => {});
    }
  }

  useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    el.muted = muted;
  }, [muted]);

  return (
    <div className="relative bg-black rounded-2xl overflow-hidden shadow-lg border border-zinc-800">
      {/* 헤더 */}
      <div className="absolute left-3 top-3 z-10">
        {badge ? (
          <span className="px-2 py-0.5 text-xs font-semibold rounded bg-red-500/90 text-white shadow">
            {badge}
          </span>
        ) : null}
      </div>
      <div className="absolute right-3 top-3 z-10 flex items-center gap-1">
        <button
          onClick={() => setMuted((m) => !m)}
          className="px-2 py-1 text-xs rounded bg-zinc-900/70 text-zinc-100 hover:bg-zinc-800"
          title={muted ? 'Unmute' : 'Mute'}
        >
          {muted ? '🔇' : '🔊'}
        </button>
        <button
          onClick={handleReload}
          className="px-2 py-1 text-xs rounded bg-zinc-900/70 text-zinc-100 hover:bg-zinc-800"
          title="Reload"
        >
          ⟳
        </button>
        <button
          onClick={handleFullscreen}
          className="px-2 py-1 text-xs rounded bg-zinc-900/70 text-zinc-100 hover:bg-zinc-800"
          title="Fullscreen"
        >
          ⛶
        </button>
      </div>

      {/* 비디오/이미지 */}
      <div className="aspect-video bg-zinc-950">
        {isMjpeg ? (
          mjpegEl
        ) : (
          <video
            key={keyRef.current}
            ref={videoRef}
            playsInline
            autoPlay
            muted={muted}
            controls={false}
            className="w-full h-full object-cover rounded-lg"
            onPlay={() => setLoading(false)}
            onError={() => {
              setError('Playback error');
              setLoading(false);
            }}
          />
        )}
      </div>

      {/* 푸터(제목/상태) */}
      <div className="px-4 py-2 border-t border-zinc-800 bg-zinc-950/70 text-zinc-100">
        <div className="flex items-center justify-between">
          <div className="font-medium">{title}</div>
          <div className="text-xs text-zinc-400">
            {loading ? '연결 중…' : error ? '오류' : '재생 중'}
          </div>
        </div>
        {error ? (
          <div className="mt-1 text-xs text-red-400">{error}</div>
        ) : null}
      </div>
    </div>
  );
}
