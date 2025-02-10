// Function to get the API base URL based on the environment
export function getApiBaseUrl(): string {
  const currentUrl = window.location.origin;
  
  // Check if we're in Replit
  if (currentUrl.includes('.repl.co') || currentUrl.includes('.replit.dev')) {
    // Add /api prefix for the Express proxy
    return `${currentUrl}/api`;
  }
  
  // Local development
  return 'http://localhost:8000';
} 