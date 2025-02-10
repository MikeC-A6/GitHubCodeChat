import { QueryClient, QueryFunction } from "@tanstack/react-query";
import { getApiBaseUrl } from "../config";

const API_BASE_URL = getApiBaseUrl();
console.log('API Base URL configured as:', API_BASE_URL);

async function throwIfResNotOk(res: Response) {
  if (!res.ok) {
    let errorMessage;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || res.statusText;
    } catch (e) {
      // If we can't parse JSON, try to get text
      try {
        errorMessage = await res.text();
      } catch (e2) {
        errorMessage = res.statusText;
      }
    }
    throw new Error(`${res.status}: ${errorMessage}`);
  }
}

export async function apiRequest(
  method: string,
  path: string,
  data?: unknown | undefined,
): Promise<Response> {
  // Ensure path starts with /
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${API_BASE_URL}${cleanPath}`;
  
  const headers: Record<string, string> = {
    "Accept": "application/json",
  };

  if (data) {
    headers["Content-Type"] = "application/json";
  }

  console.log('Making API request:', {
    method,
    url,
    data,
    headers,
  });
  
  try {
    const res = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    console.log('Response received:', {
      status: res.status,
      statusText: res.statusText,
      headers: Object.fromEntries(res.headers.entries()),
      url: res.url,
    });
    
    return res;
  } catch (error) {
    console.error('API request failed:', {
      method,
      url,
      data,
      error: error instanceof Error ? error.message : String(error),
    });
    throw error;
  }
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const path = queryKey[0] as string;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const url = `${API_BASE_URL}${cleanPath}`;
    
    console.log('Making query request:', {
      url,
      queryKey,
    });
    
    try {
      const res = await fetch(url, {
        headers: {
          "Accept": "application/json",
        },
      });

      console.log('Query response:', {
        status: res.status,
        statusText: res.statusText,
        url: res.url,
      });

      if (unauthorizedBehavior === "returnNull" && res.status === 401) {
        return null;
      }

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`${res.status}: ${errorText}`);
      }

      return res.json();
    } catch (error) {
      console.error('Query failed:', {
        url,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
  },
});
