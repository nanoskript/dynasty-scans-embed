function isBot(request) {
  const agent = request.headers.get("User-Agent") || "";
  return agent.toUpperCase().includes("BOT");
}

// Edge worker for fast redirects for
// users using Cloudflare workers.
export default {
  async fetch(request) {
    if (!isBot(request)) {
      const url = new URL(request.url);
      const { pathname, search } = url;

      for (const prefix of ["/chapters", "/images"]) {
        if (pathname.startsWith(prefix)) {
          const base = `https://dynasty-scans.com`;
          const destinationURL = `${base}${pathname}${search}`;
          return Response.redirect(destinationURL, 302);
        }
      }
    }

    // Pass-through to original serer.
    return fetch(request);
  },
};
