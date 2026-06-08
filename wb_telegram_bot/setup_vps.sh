#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_URL="https://github.com/ar1gel/re_hub.git"
PROJECT_DIR="$HOME/re_hub"

echo -e "${GREEN}📦 Установка зависимостей...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq docker.io docker-compose-v2 git curl > /dev/null 2>&1

if [ -d "$PROJECT_DIR" ]; then
  echo -e "${GREEN}🔄 Обновляю код...${NC}"
  cd "$PROJECT_DIR"
  git pull
else
  echo -e "${GREEN}📥 Клонирую репозиторий...${NC}"
  git clone "$REPO_URL" "$PROJECT_DIR"
  cd "$PROJECT_DIR"
fi

cd wb_telegram_bot

if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠️  Файл .env создан. Отредактируй его: nano .env${NC}"
  echo -e "${YELLOW}   Укажи BOT_TOKEN (получить у @BotFather)${NC}"
  exit 1
fi

echo -e "${GREEN}🔨 Собираю и запускаю...${NC}"
sudo docker compose build
sudo docker compose up -d

echo -e "${GREEN}✅ Бот запущен!${NC}"
echo -e "${GREEN}📋 Логи: cd $PROJECT_DIR/wb_telegram_bot && sudo docker compose logs -f${NC}"
echo -e "${GREEN}🛑 Остановить: cd $PROJECT_DIR/wb_telegram_bot && sudo docker compose down${NC}"
echo -e "${GREEN}🔄 Обновить: cd $PROJECT_DIR && git pull && cd wb_telegram_bot && sudo docker compose up -d --build${NC}"
