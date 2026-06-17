export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserInfo {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'planner' | 'operator' | 'manager' | 'executive';
  tenant_id: string;
}
