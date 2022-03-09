BLOB_TO_SHARE_NAME=ingeniisolutions/utility-blob-to-share
$(eval BLOB_TO_SHARE_VERSION=$(shell grep '^* Blob to Share Version:' README.md | awk -F ':' '{print $$2}' | sed 's/ //g'))

build-blob-to-share:
	docker build blob_to_share -t ${BLOB_TO_SHARE_NAME}:${BLOB_TO_SHARE_VERSION}

push-blob-to-share:
	docker push ${BLOB_TO_SHARE_NAME}:${BLOB_TO_SHARE_VERSION}
