// BDD World：注入 TenantScope/ctx 與測試替身。
// 這是骨架（spec-level）——實作 repo 會以真實 adapter 取代 in-memory 替身。
import { setWorldConstructor, World, IWorldOptions } from '@cucumber/cucumber';

export interface TenantScope {
  tenantId: string;
  seatId: string;
}

export interface DomainEvent {
  event: string;
  tenantId: string;
  payload?: Record<string, unknown>;
}

export class SpecWorld extends World {
  ctx: TenantScope | null = null;
  // 收集本場景發出的領域事件，供 Then 斷言（如「應發出事件 AuditTrailRecorded」）
  emittedEvents: DomainEvent[] = [];
  // 收集查詢結果/錯誤碼/HITL 狀態
  lastResult: unknown = null;
  lastErrorCode: string | null = null;
  // in-memory 測試資料（dual-tenant fixture 由 Background 注入）
  store: Record<string, unknown[]> = {};

  constructor(options: IWorldOptions) {
    super(options);
  }

  emitted(name: string): DomainEvent[] {
    return this.emittedEvents.filter((e) => e.event === name);
  }
}

setWorldConstructor(SpecWorld);
