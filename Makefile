.PHONY: install docker run-docker test train run lint flask waitress
.DEFAULT: help

help:
	@echo "Use with docker:"
	@echo "================"
	@echo "make docker"
	@echo "       Prepare docker image"
	@echo "make run-docker"
	@echo "       Run docker with command line project"
	@echo "make run-docker-flask"
	@echo "       Run docker with flask app"
	@echo ""
	@echo "Local installation:"
	@echo "==================="
	@echo "make install"
	@echo "       Prepare development environment, use only once"
	@echo "make run"
	@echo "       Run command line project"
	@echo "make flask"
	@echo "       Run web UI"
	@echo "make train"
	@echo "       Train knowledge graph"
	@echo "make sim"
	@echo "       Non-interactive processing of tests/conversations.txt and diff to current state"
	@echo "make overwrite-sim"
	@echo "       Non-interactive processing of tests/conversations.txt and replacement with current state"
	@echo "make test"
	@echo "       Run unit tests"

docker:
	docker image rm -f demochatbot
	docker build -t demochatbot .

run-docker:
	docker run -it --rm -p 8080:8080 demochatbot run

run-docker-flask:
	docker run -it --rm -p 8080:8080 demochatbot flask

install:
	pip3 install -r requirements.txt
	python3 -m nltk.downloader all

lint:
	pylint *py botstory/*py example/*py | grep -v -e E1101 -e C0301 -e E0611 -e E0401 -e R0903 -e C0413 #tests/*py

test:
	python3 -m unittest discover -s tests

train:
	python3 main.py --train

overwrite-sim:
	tmpfile="$(mktemp)"
	python3 main.py --sim > $tmpfile
	cat $tmpfile
	mv $tmpfile tests/conversations_processed.txt

sim:
	tmpfile="$(mktemp)"
	python3 main.py --sim > $tmpfile
	echo "Temp file: $tmpfile"
	diff $tmpfile tests/conversations_processed.txt
	cat $tmpfile
	rm $tmpfile

run:
	python3 main.py

flask:
	python3 app.py

waitress:
	waitress-serve --call 'app:create_app'

