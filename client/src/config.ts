// client/src/config.ts

export function getApiBaseUrl(): string {
  const currentUrl = window.location.origin;

  // On Replit production or preview, use the same origin
  if (currentUrl.includes(".repl.co") || currentUrl.includes(".replit.app") || currentUrl.includes(".replit.dev")) {
    return `${currentUrl}/api`;
  }

  // For local dev, point to Express on port 5000
  return "http://localhost:5000/api";
}