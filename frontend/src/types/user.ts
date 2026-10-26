/** Papel do usuário, igual ao Role do backend (apps/accounts/models.py). */
export type Role = "AUCTIONEER" | "BIDDER";

/** O que a API devolve sobre o usuário (UserSerializer do backend). */
export type User = {
  id: string;
  email: string;
  name: string;
  role: Role;
  public_alias: string;
};