import axios, { AxiosError } from 'axios';
import type { ApiError } from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 min para operações longas como login
});

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message || 'Erro desconhecido';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

export default api;
