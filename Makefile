.PHONY: setup dev backend frontend test build

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm install

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
