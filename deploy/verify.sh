#!/usr/bin/env bash
# 本機 GKE manifest gate（CR-2026-007 GATE:RED/GREEN）。需 kustomize + docker。
# RED：故意壞 manifest 應被 conftest 抓；GREEN：真實 base/overlay 應 0 fail；schema：kubeconform。
set -euo pipefail
cd "$(dirname "$0")/.."

REND=deploy/_rendered
mkdir -p "$REND"
CONFTEST=(docker run --rm -v "$PWD:/project" -w /project openpolicyagent/conftest:latest test --combine -p deploy/policy)
KCONF=(docker run --rm -v "$PWD:/work" ghcr.io/yannh/kubeconform:latest -strict -summary -ignore-missing-schemas)

echo "== render =="
kustomize build deploy/k8s/base > "$REND/base.yaml"
for o in staging prod tenant-demo; do kustomize build "deploy/k8s/overlays/$o" > "$REND/$o.yaml"; done
echo "base + 3 overlays rendered"

echo "== kubeconform (schema) =="
"${KCONF[@]}" "/work/$REND/base.yaml"

echo "== conftest GREEN (base + overlays 應 0 fail) =="
"${CONFTEST[@]}" "$REND/base.yaml"
for o in staging prod tenant-demo; do "${CONFTEST[@]}" "$REND/$o.yaml" >/dev/null; done
echo "overlays GREEN"

echo "== conftest RED (壞 manifest 應 FAIL；此處期望 conftest 回非 0) =="
if "${CONFTEST[@]}" deploy/policy/testdata/bad.yaml >/dev/null 2>&1; then
  echo "✗ RED 失效：壞 manifest 竟通過" ; exit 1
else
  echo "✓ RED 成立：壞 manifest 被擋"
fi

rm -rf "$REND"
echo "✅ GKE manifest gate 通過（GREEN + RED + schema）"
