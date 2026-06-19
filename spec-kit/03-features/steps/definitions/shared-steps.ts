// 共用 step 定義骨架（中文 regex/cucumber-expression 綁定範例）。
// 標記 @pending 的步驟待實作 repo 接上真實 SUT；此處示範 zh-TW 綁定法與斷言形狀。
import { Given, When, Then } from '@cucumber/cucumber';
import { strict as assert } from 'assert';
import { SpecWorld } from '../support/world';

// ── scope（多檔共用）────────────────────────────────
Given('目前 scope 為 tenant={string}, seat={string}', function (this: SpecWorld, tenant: string, seat: string) {
  this.ctx = { tenantId: tenant, seatId: seat };
});

Given('存在租戶 {string} 與其經紀人 {string}', function (this: SpecWorld, tenant: string, seat: string) {
  (this.store.tenants ??= []).push({ tenant, seat });
});

// ── 事件斷言（event-first 模式）─────────────────────
Then('應發出事件 {string}', function (this: SpecWorld, name: string) {
  assert.ok(this.emitted(name).length > 0, `expected domain event ${name} to be emitted`);
});

// ── 隔離斷言（Inv-1）────────────────────────────────
Then('結果只包含 {string}', function (this: SpecWorld, name: string) {
  const rows = (this.lastResult as { name: string }[]) ?? [];
  assert.ok(rows.every((r) => r.name === name), `cross-tenant leakage: ${JSON.stringify(rows)}`);
});

Then('查詢結果為空', function (this: SpecWorld) {
  assert.equal(((this.lastResult as unknown[]) ?? []).length, 0);
});

// ── 錯誤碼斷言（error-model.md）─────────────────────
Then('應回傳錯誤碼 {string}', function (this: SpecWorld, code: string) {
  assert.equal(this.lastErrorCode, code);
});

// ── 稽核斷言（Inv-3）────────────────────────────────
Then('應記錄一筆 append-only 稽核', function (this: SpecWorld) {
  assert.ok(this.emitted('AuditTrailRecorded').length > 0);
});

// NOTE: 其餘領域特定步驟（行情防呆/HITL/冪等/並發）由各 .feature 對應的
// steps/definitions/<feature>.ts 實作；此檔僅放跨檔共用步驟。
// 實作 repo 接上真實 SUT 前，未綁定步驟會被 cucumber 報為 undefined（CI 視為失敗）。
