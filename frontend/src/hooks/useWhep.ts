'use client';

import { useEffect, useRef } from 'react';

export function useWhep(video: HTMLVideoElement | null, endpointOrTargetUrl: string | null) {
  const pcRef = useRef<RTCPeerConnection | null>(null);

  useEffect(() => {
    if (!video || !endpointOrTargetUrl) return;

    let stopped = false;
    const pc = new RTCPeerConnection();
    pcRef.current = pc;

    const ms = new MediaStream();
    pc.ontrack = (ev) => {
      ms.addTrack(ev.track);
      video.srcObject = ms;
    };

    pc.addTransceiver('video', { direction: 'recvonly' });
    // 필요 시 오디오도:
    // pc.addTransceiver('audio', { direction: 'recvonly' });

    (async () => {
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // CORS 회피를 위해 /api/whep 프록시 경유
        const url = `/api/whep?target=${encodeURIComponent(endpointOrTargetUrl)}`;

        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/sdp' },
          body: offer.sdp || '',
        });

        const answerSdp = await res.text();
        if (stopped) return;

        await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
      } catch (e) {
        console.error('WHEP error:', e);
      }
    })();

    return () => {
      stopped = true;
      try {
        pc.getTransceivers().forEach((t) => t.stop());
        pc.close();
      } catch {}
      pcRef.current = null;
      if (video) {
        video.srcObject = null;
        video.removeAttribute('src');
        video.load?.();
      }
    };
  }, [video, endpointOrTargetUrl]);
}
