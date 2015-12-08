.PHONY: all clean test
all: clean test

package:
	@echo generating egg...
	python setup.py bdist_egg

test:
	@echo building test...
	python tst/run_all_tests.py

clean:
	@echo cleaning...
	-rm -rf build
	-rm -rf dist
	-rm -rf src/lybica.egg-info

