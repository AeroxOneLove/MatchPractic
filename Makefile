DC = docker compose
APP_FILE = docker_compose/app.yaml
NEURAL_NETWORK = docker_compose/neural_network.yaml

.PHONY: build
build:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK} up --build -d

.PHONY: drop-all
drop-all:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK} down

.PHONY: logs
logs:
	${DC} -f ${APP_FILE} -f ${NEURAL_NETWORK}  logs -f