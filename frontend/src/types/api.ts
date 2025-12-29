// Auth Types
export interface SessionInfo {
  session_id: string;
  cpf: string | null;
  nome: string | null;
  is_valid: boolean;
  is_govbr_authenticated: boolean;
  is_sigef_authenticated: boolean;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

export interface SessionStatus {
  authenticated: boolean;
  session: SessionInfo | null;
  message: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  session: SessionInfo | null;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

// SIGEF Types
export interface ParcelaInfo {
  codigo: string;
  denominacao?: string | null;
  area?: number | null;
  area_ha?: number | null;
  perimetro_m?: number | null;
  municipio?: string | null;
  uf?: string | null;
  situacao?: string | null;
}

export interface DownloadRequest {
  codigo: string;
  tipos?: ('parcela' | 'vertice' | 'limite')[];
}

export interface BatchDownloadRequest {
  codigos: string[];
  tipos?: ('parcela' | 'vertice' | 'limite')[];
}

export interface DownloadResponse {
  success: boolean;
  codigo: string;
  files: DownloadedFile[];
  errors: string[];
}

export interface DownloadedFile {
  tipo: string;
  filename: string;
  size: number;
  path: string;
}

export interface BatchDownloadResponse {
  success: boolean;
  total: number;
  completed: number;
  failed: number;
  results: DownloadResponse[];
}

// API Error
export interface ApiError {
  detail: string;
  status_code?: number;
}
