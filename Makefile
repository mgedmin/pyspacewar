PYTHON = python
FILE_WITH_VERSION = src/pyspacewar/version.py
FILE_WITH_CHANGELOG = NEWS.rst
VCS_STATUS = git status --porcelain
VCS_EXPORT = git archive --format=tar --prefix=tmp/tree/ HEAD | tar -xf -
VCS_TAG = git tag
VCS_COMMIT_AND_PUSH = git commit -av -m "Post-release version bump" && git push && git push --tags

.PHONY: all
all:
	@echo "No build is necessary, just install PyGame and run ./pyspacewar"

.PHONY: test check
test check:
	./test.py

.PHONY: coverage
coverage:
	coverage run test.py
	coverage report

.PHONY: dist
dist:
	$(PYTHON) setup.py sdist

.PHONY: distcheck
distcheck:
	# Bit of a chicken-and-egg here, but if the tree is unclean, make
	# distcheck will fail.
	@test -z "`$(VCS_STATUS) 2>&1`" || { echo; echo "Your working tree is not clean" 1>&2; $(VCS_STATUS); exit 1; }
	make dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	rm -rf tmp && \
	mkdir tmp && \
	$(VCS_EXPORT) && \
	cd tmp && \
	tar xvzf ../dist/$$pkg_and_version.tar.gz && \
	diff -ur $$pkg_and_version tree -x PKG-INFO -x setup.cfg -x '*.egg-info' && \
	cd $$pkg_and_version && \
	make dist check && \
	cd .. && \
	mkdir one two && \
	cd one && \
	tar xvzf ../../dist/$$pkg_and_version.tar.gz && \
	cd ../two/ && \
	tar xvzf ../$$pkg_and_version/dist/$$pkg_and_version.tar.gz && \
	cd .. && \
	diff -ur one two -x SOURCES.txt && \
	cd .. && \
	rm -rf tmp && \
	echo "sdist seems to be ok"

.PHONY: releasechecklist
releasechecklist:
	@$(PYTHON) setup.py --version | grep -qv dev || { \
	    echo "Please remove the 'dev' suffix from the version number in $(FILE_WITH_VERSION)"; exit 1; }
	@$(PYTHON) setup.py --long-description | rst2html --exit-status=2 > /dev/null
	@ver_and_date="`LC_ALL=C date +"%B %d, %Y"`: Released version `$(PYTHON) setup.py --version`:" && \
	    grep -q "^$$ver_and_date$$" $(FILE_WITH_CHANGELOG) || { \
	        echo "$(FILE_WITH_CHANGELOG) has no entry for $$ver_and_date"; exit 1; }
	make distcheck

.PHONY: release
release: releasechecklist
	# I'm chicken so I won't actually do these things yet
	@echo "Please run"
	@echo
	@echo "  rm -rf dist && $(PYTHON) setup.py -q sdist bdist_wheel && twine upload dist/* && git tag `$(PYTHON) setup.py --version`"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo
