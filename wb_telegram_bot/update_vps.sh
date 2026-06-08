#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$HOME/re_hub"

if [ ! -d "$PROJECT_DIR" ]; then
  echo -e "${RED}❌ Проект не найден в $PROJECT_DIR${NC}"
  echo -e "${YELLOW}Сначала выполни setup_vps.sh${NC}"
  exit 1
fi

echo -e "${GREEN}🔄 Обновляю код из GitHub...${NC}"
cd "$PROJECT_DIR"
git pull

echo -e "${GREEN}🔨 Пересобираю и запускаю контейнер...${NC}"
cd wb_telegram_bot
sudo docker compose up -d --build

echo -e "${GREEN}✅ Готово!${NC}"
echo -e "${GREEN}📋 Логи: sudo docker compose logs -f${NC}"
