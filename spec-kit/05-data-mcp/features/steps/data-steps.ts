// 資料層 BDD step 骨架（spec-level）。沿用主 spec 的 World 與共用 step
// (../../../03-features/steps/support/world.ts、shared-steps.ts 由 cucumber require glob 一併載入)。
// 領域特定步驟（data_as_of/顯名/脫敏/geocoding 信心…）待實作 repo 接真實 SUT；
// 未綁定步驟 cucumber 報 undefined（CI 視為 Gate B 未過）——這正是合規關卡不被虛設的保證。
import { Then } from '@cucumber/cucumber';
import { strict as assert } from 'assert';
import { SpecWorld } from '../../../03-features/steps/support/world';

// 領域工具回傳 outcome（provided/refused）
Then('結果 outcome 應 為 {string}', function (this: SpecWorld, outcome: string) {
  const r = this.lastResult as { outcome?: string } | null;
  assert.equal(r?.outcome, outcome, `expected outcome=${outcome}`);
});

// outcome + 領域 refused reason（同一行，全形逗號）
Then('結果 outcome 應 為 {string}，reason={string}', function (this: SpecWorld, outcome: string, reason: string) {
  const r = this.lastResult as { outcome?: string; reason?: string } | null;
  assert.equal(r?.outcome, outcome);
  assert.equal(r?.reason, reason, `expected refused reason=${reason}`);
});
