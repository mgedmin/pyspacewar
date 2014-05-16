.PHONY: all
all:
	@echo "No build is necessary, just install PyGame and run ./pyspacewar"

.PHONY: test
test:
	./test.py

.PHONY: coverage
coverage:
	tox -e coverage
