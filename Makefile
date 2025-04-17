DC = docker compose
DE = docker exec -it
APP_FILE = docker_compose/app.yaml
NEURAL_NETWORK = docker_compose/neural_network.yaml

.PHONY: pull-mistral
pull-mistral:
	${DE} ollama bash -c "ollama pull mistral"

.PHONY: pull-nomic-embed-text
pull-nomic-embed-text:
	${DE} ollama bash -c "ollama pull nomic-embed-text"

.PHONY: pull-models
pull-models: pull-mistral pull-nomic-embed-text
	@echo "Все модели были успешно загружены."

.PHONY: build
build:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK} up --build -d

.PHONY: drop-all
drop-all:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK} down

.PHONY: logs
logs:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK}  logs -f
