# all our targets are phony (no files to check).
.PHONY: help build rebuild prune publish

BUILD_NUMBER_FILE=build-number.txt

# Regular Makefile part for buildpypi itself
help:
	@echo ''
	@echo 'Usage: make [TARGET] [EXTRA_ARGUMENTS]'
	@echo 'Targets:'
	@echo '  build    	build Docker image'
	@echo '  prune    	shortcut for docker system prune -af; cleans up inactive containers and cache'
	@echo ''

build:
	@echo $$(($$(cat $(BUILD_NUMBER_FILE)) + 1)) > $(BUILD_NUMBER_FILE)
	docker build --no-cache -t cloudwallcapital/serenity:`date +%Y.%m.%d`-b`cat $(BUILD_NUMBER_FILE)` .

push:
	docker push cloudwallcapital/serenity:`date +%Y.%m.%d`-b`cat $(BUILD_NUMBER_FILE)`

prune:
	# clean all that is not actively used
	docker system prune -af

publish:
	python3 setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg serenity-trading.egg-info
