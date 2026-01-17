import { AuthStatus } from '../components';

export function AuthPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Autenticação Gov.br</h1>
      
      <div className="max-w-2xl">
        <AuthStatus />
        
        <div className="mt-6 card bg-yellow-50 border border-yellow-200">
          <h3 className="font-medium text-yellow-800">⚠️ Requisitos</h3>
          <ul className="text-yellow-700 text-sm mt-2 space-y-1">
            <li>• Certificado digital A1 ou A3 instalado</li>
            <li>• Navegador moderno (Chrome, Firefox, Edge)</li>
            <li>• Conexão com internet</li>
          </ul>
        </div>

        <div className="mt-4 card">
          <h3 className="font-medium mb-3">📋 Como funciona</h3>
          <ol className="text-gray-600 text-sm space-y-2">
            <li><strong>1.</strong> Clique em "Login Gov.br"</li>
            <li><strong>2.</strong> Uma nova aba será aberta com a página de login</li>
            <li><strong>3.</strong> Selecione seu certificado digital quando solicitado</li>
            <li><strong>4.</strong> Complete a autenticação no Gov.br</li>
            <li><strong>5.</strong> Retorne a esta página - a sessão será detectada automaticamente</li>
          </ol>
        </div>

        <div className="mt-4 card bg-green-50 border border-green-200">
          <h3 className="font-medium text-green-800">✅ Compatível com Docker</h3>
          <p className="text-green-700 text-sm mt-1">
            Este sistema funciona mesmo quando a API está rodando em container Docker,
            pois a autenticação acontece no seu navegador local.
          </p>
        </div>
      </div>
    </div>
  );
}
