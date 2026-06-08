#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

REPO_URL="https://github.com/ar1gel/re_hub.git"
PROJECT_DIR="$HOME/re_hub"

if ! command -v docker &>/dev/null; then
  echo -e "${GREEN}📦 Установка Docker через официальный скрипт...${NC}"
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
  echo -e "${GREEN}✅ Docker установлен: $(docker --version)${NC}"
else
  echo -e "${GREEN}✅ Docker уже установлен: $(docker --version)${NC}"
fi

sudo systemctl enable docker --now 2>/dev/null || true

if ! command -v git &>/dev/null; then
  echo -e "${GREEN}📦 Установка Git...${NC}"
  sudo apt-get update -qq
  sudo apt-get install -y git -qq
fi

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
  echo ""
  echo -e "${YELLOW}════════════════════════════════════════${NC}"
  echo -e "${YELLOW}⚠️  Файл .env создан. Укажи BOT_TOKEN:${NC}"
  echo -e "${YELLOW}   nano .env${NC}"
  echo -e "${YELLOW}   Затем запусти: sudo docker compose up -d${NC}"
  echo -e "${YELLOW}════════════════════════════════════════${NC}"
  exit 0
fi

echo -e "${GREEN}🔨 Собираю образ...${NC}"
sudo docker compose build

echo -e "${GREEN}🚀 Запускаю контейнер...${NC}"
sudo docker compose up -d

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Бот запущен!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}📋 Логи:     sudo docker compose logs -f${NC}"
echo -e "${GREEN}🛑 Остановка: sudo docker compose down${NC}"
echo -e "${GREEN}🔄 Обновить:  git pull && sudo docker compose up -d --build${NC}"
