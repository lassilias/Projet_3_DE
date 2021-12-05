.PHONY: run build

build:
	docker build --rm -t my_image:latest .

run: build
	docker run -d -p 8080:8080 my_image:latest
	@echo airflow running on http://localhost:8080

kill:
	@echo "Killing docker-airflow containers"
	docker kill test_container_test

tty:
	docker exec -it test_container_test  /bin/bash

