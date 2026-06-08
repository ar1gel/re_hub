#!/usr/bin/env bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_URL="https://github.com/ar1gel/re_hub.git"
PROJECT_DIR="$HOME/re_hub"

echo "=== ШАГ 1: Проверка Docker ==="
if command -v docker &>/dev/null; then
  echo "Docker найден: $(docker --version)"
else
  echo "Docker НЕ найден."
  echo "Установи: curl -fsSL https://get.docker.com | sudo sh"
  exit 1
fi

echo "=== ШАГ 2: Проверка Git ==="
if command -v git &>/dev/null; then
  echo "Git найден: $(git --version)"
else
  echo "Устанавливаю Git..."
  apt-get update && apt-get install -y git
fi

echo "=== ШАГ 3: Клонирование/обновление ==="
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  git pull
else
  git clone "$REPO_URL" "$PROJECT_DIR"
  cd "$PROJECT_DIR"
fi

echo "=== ШАГ 4: Файл .env ==="
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "${YELLOW}⚠️  Создан .env. Укажи BOT_TOKEN: nano .env${NC}"
  echo "${YELLOW}   Потом запусти: sudo docker compose up -d${NC}"
  exit 0
fi

echo "=== ШАГ 5: Сборка и запуск ==="
sudo docker compose build
sudo docker compose up -d

echo ""
echo "${GREEN}✅ Бот запущен!${NC}"
echo "${GREEN}📋 Логи: sudo docker compose logs -f${NC}"
echo "${GREEN}🛑 Остановка: sudo docker compose down${NC}"
echo "${GREEN}🔄 Обновить: git pull && sudo docker compose up -d --build${NC}"
