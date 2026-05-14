.PHONY: build up down logs ps health test test-iac001 test-iac002 test-iac003 test-iac004 install-dev

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

install-dev:
	pip install -r requirements-dev.txt

test:
	@mkdir -p reports
	pytest tests/ -v

test-iac001:
	@mkdir -p reports
	pytest tests/test_iac001_open_firewall_rules.py -v -m iac001

test-iac002:
	@mkdir -p reports
	pytest tests/test_iac002_unencrypted_storage.py -v -m iac002

test-iac003:
	@mkdir -p reports
	pytest tests/test_iac003_public_storage_access.py -v -m iac003

test-iac004:
	@mkdir -p reports
	pytest tests/test_iac004_cis_benchmark.py -v -m iac004
