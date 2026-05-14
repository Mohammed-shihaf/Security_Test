.PHONY: build up down logs ps health

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

health:
	@echo "Gateway health:" && curl -sS http://127.0.0.1:18080/health | head -c 2000 && echo
