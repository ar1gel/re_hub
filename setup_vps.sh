#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

REPO_URL="https://github.com/ar1gel/re_hub.git"
PROJECT_DIR="$HOME/re_hub"

echo -e "${GREEN}📦 Установка зависимостей...${NC}"
sudo apt-get update -qq
sudo apt-get install -y docker.io git curl > /dev/null
sudo apt-get install -y docker-compose-v2 2>/dev/null || sudo apt-get install -y docker-compose > /dev/null

if ! command -v docker &>/dev/null; then
  echo -e "${RED}❌ Docker не установился. Установи вручную: https://docs.docker.com/engine/install/ubuntu/${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Docker установлен.${NC}"
sudo systemctl enable docker --now 2>/dev/null || true

if [ -d "$PROJECT_DIR" ]; then
  echo -e "${GREEN}🔄 Обновляю код...${NC}"
  cd "$PROJECT_DIR"
  git pull
else
  echo -e "${GREEN}📥 Клонирую репозиторий...${NC}"
  git clone "$REPO_URL" "$PROJECT_DIR"
  cd "$PROJECT_DIR"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠️  Создан файл .env. Укажи BOT_TOKEN:${NC}"
  echo -e "${YELLOW}   nano .env${NC}"
  exit 1
fi

echo -e "${GREEN}🔨 Собираю и запускаю...${NC}"
sudo docker compose build
sudo docker compose up -d

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Бот запущен!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}📋 Логи:     sudo docker compose logs -f${NC}"
echo -e "${GREEN}🛑 Остановка: sudo docker compose down${NC}"
echo -e "${GREEN}🔄 Обновить:  git pull && sudo docker compose up -d --build${NC}"
