// REQ: tw-utils 統編檢查碼驗證
// 追溯：spec-kit/05-data-mcp/company-registry-mcp.md（resolve_company 統編驗證）、
//       twinkle-hub-alignment.md §3（重實作 twtools 統編 checksum）
// 演算法：財政部統一編號檢查碼（公開規則）。deterministic、無外部依賴。

const WEIGHTS = [1, 2, 1, 2, 1, 2, 4, 1] as const;

/**
 * 驗證台灣統一編號（8 位）檢查碼。
 * 規則：各位 digit×weight 後取「乘積各位數字和」，總和 % 5 == 0；
 *       第 7 碼為 7 時，(總和 + 1) % 5 == 0 亦為有效（特例）。
 */
export function validateUbn(ubn: string): boolean {
  if (!/^\d{8}$/.test(ubn)) return false;
  const digits = [...ubn].map(Number);
  let total = 0;
  for (let i = 0; i < 8; i++) {
    const product = digits[i] * WEIGHTS[i];
    total += Math.floor(product / 10) + (product % 10); // 乘積各位數字和
  }
  if (total % 5 === 0) return true;
  return digits[6] === 7 && (total + 1) % 5 === 0; // 第7碼為7的特例
}
