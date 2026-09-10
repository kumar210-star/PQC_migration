export type Finding = {
  id: number; asset: string; file: string; line: number; algorithm: string; category: string; role: string;
  risk: string; risk_reason: string; recommended_replacement: string; recommendation_reason: string;
  migration_action: string; priority: string; status: string;
}
export type Task = {
  id: number; inventory_id: number; asset: string; current_algorithm: string; cryptographic_role: string;
  target_algorithm: string; reason: string; priority: string; dependencies: string[]; status: string;
}
export type RiskSummary = { total: number; quantum_vulnerable: number; counts: Record<string, number>; note: string }
export type Recommendation = {
  inventory_id:number; current_algorithm:string; cryptographic_role:string; risk:string;
  recommended_algorithm:string; reason:string; migration_action:string; priority:string; alternative_algorithms:string[];
}
