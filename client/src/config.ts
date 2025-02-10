// client/src/config.ts

export function getApiBaseUrl(): string {
  const currentUrl = window.location.origin;
  
  // On Replit, use the domain plus /api (proxied by Express).
  if (currentUrl.includes(".repl.co") || currentUrl.includes(".replit.dev")) {
    return `${currentUrl}/api`;
  }
  
  // For local dev, point to Express on port 5000,
  // which in turn proxies to FastAPI on 8000.
  return "http://localhost:5000/api";
}
