import api from './api';
import type { SessionStatus, LogoutResponse, BrowserLoginResponse } from '../types';

export const authService = {
  /**
   * Verifica status da sessão atual
   */
  async getStatus(): Promise<SessionStatus> {
    const response = await api.get<SessionStatus>('/auth/status');
    return response.data;
  },

  /**
   * Inicia login via Gov.br usando browser remoto
   * Retorna uma URL que o usuário deve abrir no navegador
   */
  async browserLogin(): Promise<BrowserLoginResponse> {
    const response = await api.post<BrowserLoginResponse>('/auth/browser-login');
    return response.data;
  },

  /**
   * Alias para browserLogin (compatibilidade)
   */
  async login(): Promise<BrowserLoginResponse> {
    return this.browserLogin();
  },

  /**
   * Abre a URL de login em uma nova aba do navegador
   */
  openLoginWindow(loginUrl: string): Window | null {
    return window.open(loginUrl, '_blank', 'width=800,height=700');
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

  /**
   * Polling para verificar se a autenticação foi concluída
   */
  async waitForAuth(maxAttempts = 60, intervalMs = 2000): Promise<SessionStatus> {
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, intervalMs));
      const status = await this.getStatus();
      if (status.authenticated) {
        return status;
      }
    }
    throw new Error('Timeout aguardando autenticação');
  },
};

export default authService;
