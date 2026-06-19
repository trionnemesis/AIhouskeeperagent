// Cucumber.js 設定（spec-kit BDD 執行）
// 用法：npx cucumber-js（於 spec-kit/ 下）
// 註：.feature 使用 # language: zh-TW；step 以中文 regex/expression 綁定（見 steps/definitions）
// paths/require 相對 spec-kit 根（由 package.json 以 --config 03-features/cucumber.js 自根執行）
// 同時涵蓋主 spec(03-features) 與資料層(05-data-mcp/features)
const PATHS = ['03-features/**/*.feature', '05-data-mcp/features/**/*.feature'];
const REQUIRE = ['03-features/steps/**/*.ts', '05-data-mcp/features/steps/**/*.ts'];

module.exports = {
  default: {
    paths: PATHS,
    require: REQUIRE,
    requireModule: ['ts-node/register'],
    format: ['progress-bar', 'summary'],
    publishQuiet: true,
  },
  // npm run bdd:gateB
  gateB: {
    paths: PATHS,
    require: REQUIRE,
    requireModule: ['ts-node/register'],
    tags: '@gateB',
    format: ['progress-bar', 'summary'],
  },
};
