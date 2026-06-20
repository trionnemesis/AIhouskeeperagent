#!/usr/bin/env bash
# GCE VM bootstrap（Debian 12）：裝 docker + compose，拉 repo，起 MVP 資料層。
# 用法：建 VM 時帶 --metadata-from-file startup-script=deploy/vm/startup-script.sh。
# secret 不放這裡：開機後由 Secret Manager 拉到 /opt/hermes/.env（見 README）。
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker

APP_DIR=/opt/hermes
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "${REPO_URL:-https://example.com/your/repo.git}" "$APP_DIR" || mkdir -p "$APP_DIR"
fi
cd "$APP_DIR/deploy/vm" 2>/dev/null || { echo "repo 未就緒，請手動部署"; exit 0; }

# secret：由 Secret Manager 拉成 .env（VM service account 需 secretAccessor）。
# gcloud secrets versions access latest --secret=hermes-mvp-env > .env  # 範例

# MVP 第一階段只起資料層（postgres/redis/lvr-mcp/public-safety-mcp）；加 --profile full 起全套。
docker compose --env-file .env up -d --build
