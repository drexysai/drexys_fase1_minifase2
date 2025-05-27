import axios from 'axios';

const API_BASE_URL = 'http://192.168.1.4:8081/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token JWT médico automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('medical_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratar erros de autenticação médica
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token médico expirado ou inválido
      localStorage.removeItem('medical_access_token');
      localStorage.removeItem('medical_refresh_token');
      localStorage.removeItem('medical_user');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export default api;