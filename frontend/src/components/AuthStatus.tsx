import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader2, LogIn, LogOut, RefreshCw } from 'lucide-react';
import { authService } from '../services';
import type { SessionStatus } from '../types';

export function AuthStatus() {
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await authService.getStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao verificar status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleLogin = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await authService.login();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setActionLoading(true);
      setError(null);
      await authService.logout();
      await fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer logout');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-8">
        <Loader2 className="w-8 h-8 animate-spin text-govbr-primary" />
        <span className="ml-3 text-gray-600">Verificando status...</span>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Status da Autenticação</h2>
        <button
          onClick={fetchStatus}
          disabled={actionLoading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Atualizar"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="flex items-center gap-4 mb-6">
        {status?.authenticated && status.session ? (
          <>
            <CheckCircle className="w-12 h-12 text-govbr-success" />
            <div>
              <p className="text-lg font-medium text-govbr-success">Autenticado</p>
              {status.session.nome && (
                <p className="text-sm font-medium text-gray-700">
                  {status.session.nome}
                </p>
              )}
              <p className="text-sm text-gray-500">
                Sessão: {status.session.session_id.slice(0, 8)}...
              </p>
              {status.session.expires_at && (
                <p className="text-sm text-gray-500">
                  Expira: {new Date(status.session.expires_at).toLocaleString('pt-BR')}
                </p>
              )}
            </div>
          </>
        ) : (
          <>
            <XCircle className="w-12 h-12 text-gray-400" />
            <div>
              <p className="text-lg font-medium text-gray-600">Não autenticado</p>
              <p className="text-sm text-gray-500">Faça login para acessar o SIGEF</p>
            </div>
          </>
        )}
      </div>

      {status?.session && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium mb-2">Informações da Sessão</h3>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {status.session.cpf && (
              <div>
                <dt className="text-gray-500">CPF</dt>
                <dd className="font-medium">{status.session.cpf}</dd>
              </div>
            )}
            <div>
              <dt className="text-gray-500">Gov.br</dt>
              <dd className="font-medium">
                {status.session.is_govbr_authenticated ? '✅ Autenticado' : '❌ Não'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">SIGEF</dt>
              <dd className="font-medium">
                {status.session.is_sigef_authenticated ? '✅ Autenticado' : '❌ Não'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Criada em</dt>
              <dd className="font-medium">
                {new Date(status.session.created_at).toLocaleString('pt-BR')}
              </dd>
            </div>
          </dl>
        </div>
      )}

      <div className="flex gap-3">
        {status?.authenticated ? (
          <button
            onClick={handleLogout}
            disabled={actionLoading}
            className="btn-danger flex items-center gap-2"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <LogOut className="w-4 h-4" />
            )}
            Encerrar Sessão
          </button>
        ) : (
          <button
            onClick={handleLogin}
            disabled={actionLoading}
            className="btn-primary flex items-center gap-2"
          >
            {actionLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            Login Gov.br
          </button>
        )}
      </div>

      {actionLoading && (
        <p className="mt-4 text-sm text-gray-500">
          ⏳ Uma janela do Chrome será aberta para autenticação com certificado digital...
        </p>
      )}
    </div>
  );
}
