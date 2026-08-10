.PHONY: setup dev backend frontend test build kakao-login

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/python -m playwright install chromium
	cd frontend && npm install

kakao-login:
	.venv/bin/python -m blog_place_collector.clients.kakao_login

dev:
	.venv/bin/python main.py --reload

backend:
	.venv/bin/python main.py

frontend:
	cd frontend && npm run dev

test:
	.venv/bin/python -m unittest discover -s tests -v

build:
	cd frontend && npm run build
