IMAGE_NAME := ingeniisolutions/azure-data-platform-iac-runtime

setup:
	@docker login

build:
	@mkdir -p tmp
	@cp ../../requirements*.txt tmp/
	@cp -r ../../python tmp/
	@docker build . -t ${IMAGE_NAME}
	@rm -rf tmp

publish:
	@if test -z "${TAG_NAME}"; then echo "TAG_NAME not set. Try 'make publish TAG_NAME=xxx"; exit 1; fi
	@docker tag ${IMAGE_NAME} "${IMAGE_NAME}:${TAG_NAME}"
	@docker push "${IMAGE_NAME}:${TAG_NAME}"