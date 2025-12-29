import api from './api';
import type { SessionStatus, LoginResponse, LogoutResponse } from '../types';

export const authService = {
  /**
   * Verifica status da sessão atual
   */
  async getStatus(): Promise<SessionStatus> {
    const response = await api.get<SessionStatus>('/auth/status');
    return response.data;
  },

  /**
   * Inicia login via Gov.br com certificado digital
   * Abre uma janela do Chrome para seleção do certificado
   */
  async login(): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login');
    return response.data;
  },

  /**
   * Encerra a sessão atual
   */
  async logout(): Promise<LogoutResponse> {
    const response = await api.post<LogoutResponse>('/auth/logout');
    return response.data;
  },

  /**
   * Obtém detalhes da sessão
   */
  async getSession(): Promise<SessionStatus> {
    const response = await api.get<SessionStatus>('/auth/session');
    return response.data;
  },
};

export default authService;
