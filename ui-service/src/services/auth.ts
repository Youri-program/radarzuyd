// src/services/auth.ts - FIXED VERSION

import { AWS_LOGIN_URL } from "../config";

const TOKEN_KEY = 'access_token';
const USERNAME_KEY = 'username';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  username: string;
}

/**
 * Login to API Gateway /login endpoint
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  try {
    console.log('🔐 Logging in to:', AWS_LOGIN_URL);

    const response = await fetch(AWS_LOGIN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: credentials.username,
        password: credentials.password,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Login failed' }));
      throw new Error(error.error || error.message || `Login failed: ${response.status}`);
    }

    const data = await response.json();
    
    console.log(' Login successful');

    // Store token
    sessionStorage.setItem(TOKEN_KEY, data.access_token);
    sessionStorage.setItem(USERNAME_KEY, credentials.username);

    return {
      access_token: data.access_token,
      username: credentials.username,
    };

  } catch (error) {
    console.error(' Login error:', error);
    throw error;
  }
}

/**
 * Logout - clear stored token
 */
export function logout(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USERNAME_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USERNAME_KEY);
  console.log(' Logged out');
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getToken() !== null;
}

/**
 * Get stored access token
 */
export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

/**
 * Get stored username
 */
export function getUsername(): string | null {
  return sessionStorage.getItem(USERNAME_KEY) || localStorage.getItem(USERNAME_KEY);
}

/**
 * Make an authenticated request to API Gateway
 * ALWAYS includes Authorization header (backend has CORS enabled)
 */
export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found. Please login.');
  }

  console.log(' Making authenticated request to:', url);

  // Build headers - ALWAYS include Authorization
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge existing headers if provided
  if (options.headers) {
    const existingHeaders = new Headers(options.headers);
    existingHeaders.forEach((value, key) => {
      headers[key] = value;
    });
  }

  // ALWAYS include Authorization header
  headers['Authorization'] = `Bearer ${token}`;
  console.log(' Authorization header included');

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If 401, token expired - logout
  if (response.status === 401) {
    console.warn(' Token expired (401)');
    logout();
    throw new Error('Session expired. Please login again.');
  }

  return response;
}