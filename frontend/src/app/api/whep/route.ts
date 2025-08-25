export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const target = url.searchParams.get('target');
    if (!target) {
      return new Response('Missing target', { status: 400 });
    }

    const sdp = await req.text();
    const upstream = await fetch(target, {
      method: 'POST',
      headers: { 'Content-Type': 'application/sdp' },
      body: sdp,
    });

    const answer = await upstream.text();
    return new Response(answer, {
      status: upstream.status,
      headers: { 'Content-Type': 'application/sdp' },
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return new Response(`Proxy error: ${msg}`, { status: 500 });
  }
}
