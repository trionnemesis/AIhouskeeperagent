package main

import rego.v1

# GKE manifest 合規政策（CR-2026-007 GATE:RED/GREEN/VDD 的 gate）。
# 以 conftest --combine 對 `kustomize build` 結果評估。
# 對應不可違背約束：OPS-1（image pin）、DI-4（不可繞過 egress）、Pod 安全、Inv-1（每 ns default-deny）。

# --combine 時 input 為 [{path, contents}]；非 combine 時 input 為單一 doc。兩者皆容忍。
doc(x) := x.contents if x.contents
doc(x) := x if not x.contents

docs contains d if {
	some i
	d := doc(input[i])
}

# ── workload 抽象 ──────────────────────────────────────────
is_workload(o) if o.kind == "Deployment"
is_workload(o) if o.kind == "StatefulSet"
is_workload(o) if o.kind == "CronJob"

pod_spec(o) := o.spec.jobTemplate.spec.template.spec if o.kind == "CronJob"
pod_spec(o) := o.spec.template.spec if o.kind != "CronJob"

no_tag(img) if {
	parts := split(img, "/")
	last := parts[count(parts) - 1]
	not contains(last, ":")
}

# ── OPS-1：image 必須 pin（禁 :latest / 無 tag）────────────
deny contains msg if {
	some o in docs
	is_workload(o)
	some c in pod_spec(o).containers
	endswith(c.image, ":latest")
	msg := sprintf("[OPS-1] image 使用 :latest（禁）：%s → %s", [o.metadata.name, c.image])
}

deny contains msg if {
	some o in docs
	is_workload(o)
	some c in pod_spec(o).containers
	no_tag(c.image)
	msg := sprintf("[OPS-1] image 無固定 tag：%s → %s", [o.metadata.name, c.image])
}

# ── Pod 安全：runAsNonRoot 必須為真（container 或 pod 層）──
deny contains msg if {
	some o in docs
	is_workload(o)
	ps := pod_spec(o)
	some c in ps.containers
	not c.securityContext.runAsNonRoot == true
	not ps.securityContext.runAsNonRoot == true
	msg := sprintf("[SEC] container 未設 runAsNonRoot:true：%s → %s", [o.metadata.name, c.name])
}

# ── DI-4：廣域 egress(0.0.0.0/0) 僅允許 gateway ns ─────────
deny contains msg if {
	some o in docs
	o.kind == "NetworkPolicy"
	o.metadata.namespace != "gateway"
	some e in o.spec.egress
	some t in e.to
	t.ipBlock.cidr == "0.0.0.0/0"
	msg := sprintf("[DI-4] 非 gateway ns 開放 0.0.0.0/0 egress（egress 可被繞過）：%s/%s", [o.metadata.namespace, o.metadata.name])
}

# ── Inv-1：每個 app namespace 必須有 default-deny ──────────
app_namespaces := {"tenant-demo", "data-mcp", "gateway", "platform"}

has_default_deny(ns) if {
	some o in docs
	o.kind == "NetworkPolicy"
	o.metadata.namespace == ns
	o.spec.podSelector == {}
	"Ingress" in o.spec.policyTypes
	"Egress" in o.spec.policyTypes
	not o.spec.egress
	not o.spec.ingress
}

deny contains msg if {
	some ns in app_namespaces
	not has_default_deny(ns)
	msg := sprintf("[Inv-1] namespace 缺 default-deny NetworkPolicy：%s", [ns])
}
