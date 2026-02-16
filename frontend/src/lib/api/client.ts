// `window` only exists in the browser, not on the server (Node.js).
// Next.js may run this code on the server first (SSR), where localStorage doesn't exist.
// `typeof window !== "undefined"` = "only run this in the browser."

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export function clearAuthStorage() {
  localStorage.removeItem('access_token');
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

api.interceptors.response.use(
  (respone) => respone,
  (error) => {
    if (
      error.response?.status == 401 &&
      typeof window !== 'undefined' &&
      !window.location.pathname.includes('/login')
    ) {
      clearAuthStorage();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
