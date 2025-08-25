import { cameras } from '@/lib/cameras';
import CctvPlayer from '@/components/CctvPlayer';

export const dynamic = 'force-dynamic';

export default function CctvPage() {
  const overview = cameras.find((c) => c.kind === 'overview');
  const machines = cameras.filter((c) => c.kind === 'machine');

  return (
    <main className="p-6 space-y-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">CCTV</h1>
        <p className="text-sm text-zinc-400">
          공장 전체와 주요 설비 화면을 실시간으로 확인합니다. (UI에는 여러 대가 보이지만 실제 재생은 일부만 활성화)
        </p>
      </header>

      {/* 공장 전체 */}
      {overview ? (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">공장 전체</h2>
          {overview.active ? (
            <CctvPlayer
              title={overview.name}
              url={overview.url}
              protocol={overview.protocol}
              badge={overview.badge}
              initialMuted={true}
            />
          ) : (
            <DisabledTile name={overview.name} note={overview.note || '대기'} />
          )}
        </section>
      ) : null}

      {/* 기계 카메라들 */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">기계</h2>
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {machines.map((cam) =>
            cam.active ? (
              <CctvPlayer
                key={cam.id}
                title={cam.name}
                url={cam.url}
                protocol={cam.protocol}
                badge={cam.badge}
                initialMuted={true}
              />
            ) : (
              <DisabledTile key={cam.id} name={cam.name} note={cam.note} />
            )
          )}
        </div>
      </section>
    </main>
  );
}

function DisabledTile({ name, note }: { name: string; note?: string }) {
  return (
    <div className="relative rounded-2xl border border-zinc-800 overflow-hidden bg-zinc-950">
      <div className="aspect-video bg-[linear-gradient(135deg,#0a0a0a,#111827)]" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="px-3 py-1 rounded-full bg-zinc-900/70 text-zinc-300 text-xs border border-zinc-700">
          {note || '비활성'}
        </div>
      </div>
      <div className="px-4 py-2 border-t border-zinc-800">
        <div className="text-zinc-200 font-medium">{name}</div>
        <div className="text-xs text-zinc-500">등록되었지만 현재는 비활성</div>
      </div>
    </div>
  );
}
