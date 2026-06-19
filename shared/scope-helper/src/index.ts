// Inv-1 租戶隔離 (spec-kit/01-domain/invariants.md)
// Why: 所有資料存取強制注入 tenant_id，禁止跨租戶覆寫，杜絕越權讀寫。

export type TenantScope = { tenantId: string; seatId: string };

type ScopeCtx = { tenantId?: string } | null | undefined;

function resolveTenantId(ctx: ScopeCtx): string {
  if (!ctx || typeof ctx.tenantId !== 'string' || ctx.tenantId === '') {
    throw new Error('SCOPE_UNRESOLVED');
  }
  return ctx.tenantId;
}

export function assertScope(ctx: unknown): asserts ctx is TenantScope {
  resolveTenantId(ctx as ScopeCtx);
}

export function scopedWhere(
  ctx: unknown,
  filters: Record<string, unknown>,
): Record<string, unknown> {
  const tenantId = resolveTenantId(ctx as ScopeCtx);
  // Why: filters 已帶異租戶 tenant_id → 視為越權覆寫意圖，拒絕 (Inv-1)。
  if ('tenant_id' in filters && filters.tenant_id !== tenantId) {
    throw new Error('SCOPE_VIOLATION');
  }
  return { ...filters, tenant_id: tenantId };
}

export function buildSelect(
  ctx: unknown,
  table: string,
  filters: Record<string, unknown>,
): { table: string; where: Record<string, unknown> } {
  return { table, where: scopedWhere(ctx, filters) };
}
