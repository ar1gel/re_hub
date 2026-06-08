#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ ! -f .env ]; then
  echo -e "${YELLOW}Файл .env не найден. Создаю из .env.example...${NC}"
  cp .env.example .env
  echo -e "${YELLOW}⚠️  Отредактируй .env и укажи BOT_TOKEN перед запуском!${NC}"
  exit 1
fi

echo -e "${GREEN}🔨 Собираю образ...${NC}"
docker compose build

echo -e "${GREEN}🚀 Запускаю контейнер...${NC}"
docker compose up -d

echo -e "${GREEN}✅ Бот запущен!${NC}"
echo -e "${GREEN}📋 Логи: docker compose logs -f${NC}"
echo -e "${GREEN}🛑 Остановить: docker compose down${NC}"
