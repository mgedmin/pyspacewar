FILE_WITH_VERSION = src/pyspacewar/version.py
FILE_WITH_CHANGELOG = NEWS.rst
CHANGELOG_DATE_FORMAT = %B %-d, %Y
CHANGELOG_FORMAT = $(changelog_date): Released version $(changelog_ver):

.PHONY: all
all:
	@echo "No build is necessary, just install PyGame and run ./pyspacewar"

.PHONY: test
test:                           ##: run tests
	tox -p auto

.PHONY: coverage
coverage:                       ##: measure test coverage
	tox -p auto -e coverage,coverage3 -- -p
	coverage combine
	coverage report -m


include release.mk
