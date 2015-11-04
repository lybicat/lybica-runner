.PHONY: all clean test
all: clean test

test:
	@echo building test...
	python tst/run_all_tests.py

clean:
	@echo cleaning...

