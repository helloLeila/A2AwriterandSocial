const jsonHeaders = {
  'content-type': 'application/json; charset=utf-8',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith('/api/')) {
      return proxyApiRequest(request, env, url);
    }

    return env.ASSETS.fetch(request);
  },
};

async function proxyApiRequest(request, env, sourceUrl) {
  if (!env.API_BASE_URL) {
    return new Response(
      JSON.stringify({
        error: 'missing_api_base_url',
        message: 'Set API_BASE_URL in Cloudflare Worker variables.',
      }),
      { status: 502, headers: jsonHeaders },
    );
  }

  const targetUrl = new URL(
    `${sourceUrl.pathname}${sourceUrl.search}`,
    ensureTrailingSlash(env.API_BASE_URL),
  );
  const headers = new Headers(request.headers);
  headers.delete('host');

  const init = {
    method: request.method,
    headers,
    redirect: 'manual',
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = request.body;
  }

  const response = await fetch(new Request(targetUrl.toString(), init));
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

function ensureTrailingSlash(value) {
  return value.endsWith('/') ? value : `${value}/`;
}
