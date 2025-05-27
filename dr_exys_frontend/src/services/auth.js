import api from './api.js';

export const authService = {
  // Registro de novo profissional de saúde
  async register(medicalData) {
    try {
      const response = await api.post('/auth/register/', medicalData);
      
      if (response.data.tokens) {
        localStorage.setItem('medical_access_token', response.data.tokens.access);
        localStorage.setItem('medical_refresh_token', response.data.tokens.refresh);
        localStorage.setItem('medical_user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Login de profissional de saúde
  async login(credentials) {
    try {
      const response = await api.post('/auth/login/', credentials);
      
      if (response.data.tokens) {
        localStorage.setItem('medical_access_token', response.data.tokens.access);
        localStorage.setItem('medical_refresh_token', response.data.tokens.refresh);
        localStorage.setItem('medical_user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Logout médico
  async logout() {
    try {
      const refreshToken = localStorage.getItem('medical_refresh_token');
      if (refreshToken) {
        await api.post('/auth/logout/', { refresh: refreshToken });
      }
    } catch (error) {
      console.log('Erro no logout médico:', error);
    } finally {
      localStorage.removeItem('medical_access_token');
      localStorage.removeItem('medical_refresh_token');
      localStorage.removeItem('medical_user');
    }
  },

  // Obter profissional de saúde logado
  getCurrentMedical() {
    const userStr = localStorage.getItem('medical_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // Verificar se profissional está autenticado
  isAuthenticated() {
    return !!localStorage.getItem('medical_access_token');
  },

  // Obter perfil médico atualizado do servidor
  async getMedicalProfile() {
    try {
      const response = await api.get('/auth/profile/');
      localStorage.setItem('medical_user', JSON.stringify(response.data.user));
      return response.data.user;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Verificar se é médico validado
  isMedicalVerified() {
    const user = this.getCurrentMedical();
    return user?.medical_profile?.crm_verified || false;
  },

  // Obter especialidade médica
  getMedicalSpecialty() {
    const user = this.getCurrentMedical();
    return user?.medical_profile?.specialty || 'Não informado';
  }
};