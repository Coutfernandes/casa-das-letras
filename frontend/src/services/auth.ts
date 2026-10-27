/** Chamadas às rotas de autenticação do backend (/api/auth/). */

import type { Role, User } from "../types/user";
import { apiRequest } from "./api";

export type Credentials = {
  email: string;
  password: string;
};

export type Registration = Credentials & {
  name: string;
  role: Role;
};

/** Pede o cookie csrftoken. Precisa vir antes do primeiro POST. */
export function fetchCsrfCookie() {
  return apiRequest<null>("/api/auth/csrf/");
}

export function fetchCurrentUser() {
  return apiRequest<User>("/api/auth/me/");
}

export function login(credentials: Credentials) {
  return apiRequest<User>("/api/auth/login/", { method: "POST", body: credentials });
}

export function register(registration: Registration) {
  return apiRequest<User>("/api/auth/register/", { method: "POST", body: registration });
}

export function logout() {
  return apiRequest<null>("/api/auth/logout/", { method: "POST" });
}
