# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
.PHONY: default generate_acp_client \
	generate_acp_server generate \
	generate_async_acp_client update_python_subpackage

default: test

ACP_SPEC_DIR=acp-spec
ACP_CLIENT_DIR:=acp-sync-client-generated
ACP_SUBPACKAGE_PREFIX=acp_v
ACP_SPEC_FILE:=$(ACP_SPEC_DIR)/openapi.json
GEN_ACP_SYNC_PACKAGE_PREFIX:=acp_client_v
SDK_ACP_SYNC_PACKAGE_NAME:=sync_client

$(ACP_SPEC_FILE): 
	git submodule update $(ACP_SPEC_DIR)

# Generate client and correct models for convenience.
generate_acp_client $(ACP_CLIENT_DIR)/README.md : $(ACP_SPEC_FILE)
	export SPEC_FILE="$(ACP_SPEC_FILE)" ; \
	SPEC_VERSION=$$(jq -r '.info.version | capture("(?<version>\\d+)\\.\\d+"; "") | .version' "$${SPEC_FILE}") ; \
	export CLIENT_DIR="$(ACP_CLIENT_DIR)" ; \
	export GEN_PACKAGE_NAME="$(GEN_ACP_SYNC_PACKAGE_PREFIX)$${SPEC_VERSION}" ; \
	export SDK_SUBPACKAGE_NAME="agntcy_acp.$(ACP_SUBPACKAGE_PREFIX)$${SPEC_VERSION}" ; \
	export OPENAPI_GENERATOR_CLI_ARGS="--additional-properties=library=urllib3" ; \
	./scripts/openapi_generate_client.sh && \
	export SDK_SYNC_SUBPACKAGE_NAME="$${SDK_SUBPACKAGE_NAME}.$(SDK_ACP_SYNC_PACKAGE_NAME)" ; \
	for genfile in $$(find "$${CLIENT_DIR}" -name '*.py'); do \
		sed -i '' -E -e "s/$${GEN_PACKAGE_NAME}.api_client/$${SDK_SYNC_SUBPACKAGE_NAME}.api_client/" \
	    	-e "s/^from[[:space:]]+$${GEN_PACKAGE_NAME}[[:space:]]+import[[:space:]]+rest$$/from . import rest/" \
	    	-e "s/$${GEN_PACKAGE_NAME}.rest/$${SDK_SYNC_SUBPACKAGE_NAME}.rest/" \
	    	-e "s/$${GEN_PACKAGE_NAME}.api\\./$${SDK_SYNC_SUBPACKAGE_NAME}.api./" \
	    	-e "s/$${GEN_PACKAGE_NAME}/$${SDK_SUBPACKAGE_NAME}/" $${genfile} ; \
	done

ACP_ASYNC_CLIENT_DIR:=acp-async-client-generated
GEN_ACP_ASYNC_PACKAGE_PREFIX:=acp_async_client_v
SDK_ACP_ASYNC_PACKAGE_NAME:=async_client

generate_acp_async_client $(ACP_ASYNC_CLIENT_DIR)/README.md : $(ACP_SPEC_FILE)
	export SPEC_FILE="$(ACP_SPEC_FILE)" ; \
	SPEC_VERSION=$$(jq -r '.info.version | capture("(?<version>\\d+)\\.\\d+"; "") | .version' "$${SPEC_FILE}") ; \
	export CLIENT_DIR="$(ACP_ASYNC_CLIENT_DIR)" ; \
	export GEN_PACKAGE_NAME="$(GEN_ACP_ASYNC_PACKAGE_PREFIX)$${SPEC_VERSION}" ; \
	export SDK_SUBPACKAGE_NAME="agntcy_acp.$(ACP_SUBPACKAGE_PREFIX)$${SPEC_VERSION}" ; \
	export OPENAPI_GENERATOR_CLI_ARGS="--additional-properties=library=asyncio" ; \
	./scripts/openapi_generate_client.sh && \
	export SDK_ASYNC_SUBPACKAGE_NAME="$${SDK_SUBPACKAGE_NAME}.$(SDK_ACP_ASYNC_PACKAGE_NAME)" ; \
	for genfile in $$(find "$${CLIENT_DIR}" -name '*.py'); do \
		sed -i '' -E -e "s/$${GEN_PACKAGE_NAME}.api_client/$${SDK_ASYNC_SUBPACKAGE_NAME}.api_client/" \
	    	-e "s/^from[[:space:]]+$${GEN_PACKAGE_NAME}[[:space:]]+import[[:space:]]+rest$$/from . import rest/" \
	    	-e "s/$${GEN_PACKAGE_NAME}.rest/$${SDK_ASYNC_SUBPACKAGE_NAME}.rest/" \
	    	-e "s/$${GEN_PACKAGE_NAME}.api\\./$${SDK_ASYNC_SUBPACKAGE_NAME}.api./" \
	    	-e "s/$${GEN_PACKAGE_NAME}/$${SDK_SUBPACKAGE_NAME}/" $${genfile} ; \
	done

AGENT_WORKFLOW_DIR:=workflow-srv-mgr
AGNT_WKFW_SPEC_FILE:=$(AGENT_WORKFLOW_DIR)/wfsm/spec/manifest.yaml

$(AGNT_WKFW_SPEC_FILE):
	git submodule update $(AGENT_WORKFLOW_DIR)

generate_manifest_models: $(AGNT_WKFW_SPEC_FILE)
	ACP_SPEC_VERSION=$$(yq '.info.version | sub("\.\d+", "")' "$(AGNT_WKFW_SPEC_FILE)") ; \
	AGNT_WKFW_MODEL_PACKAGE_DIR="agntcy_acp/agws_v$${ACP_SPEC_VERSION}" ; \
	{ mkdir "$${AGNT_WKFW_MODEL_PACKAGE_DIR}" || true ; } ; \
	uv run --with datamodel-code-generator -- \
	  datamodel-codegen \
		--input $(AGNT_WKFW_SPEC_FILE) \
		--input-file-type openapi \
		--output-model-type pydantic_v2.BaseModel \
		--output "$${AGNT_WKFW_MODEL_PACKAGE_DIR}"/models.py \
		--disable-timestamp && \
	cp .spdx_header "$${AGNT_WKFW_MODEL_PACKAGE_DIR}/spec_version.py" && \
	echo VERSION="\""$$(yq '.info.version' "$(AGNT_WKFW_SPEC_FILE)")"\"" >>"$${AGNT_WKFW_MODEL_PACKAGE_DIR}/spec_version.py" && \
	echo MAJOR_VERSION="\"$${ACP_SPEC_VERSION}\"" >>"$${AGNT_WKFW_MODEL_PACKAGE_DIR}/spec_version.py" && \
	echo MINOR_VERSION="\""$$(yq '.info.version | sub("\d+\.", "")' "$(AGNT_WKFW_SPEC_FILE)")"\"" >>"$${AGNT_WKFW_MODEL_PACKAGE_DIR}/spec_version.py"

update_python_subpackage: $(ACP_CLIENT_DIR)/README.md $(ACP_ASYNC_CLIENT_DIR)/README.md
	ACP_SPEC_VERSION=$$(jq -r '.info.version | capture("(?<version>\\d+)\\.\\d+"; "") | .version' $(ACP_SPEC_FILE)) ; \
	ACP_CLIENT_PACKAGE_DIR="$(ACP_CLIENT_DIR)/$(GEN_ACP_SYNC_PACKAGE_PREFIX)$${ACP_SPEC_VERSION}" ; \
	ACP_ASYNC_CLIENT_PACKAGE_DIR="$(ACP_ASYNC_CLIENT_DIR)/$(GEN_ACP_ASYNC_PACKAGE_PREFIX)$${ACP_SPEC_VERSION}" ; \
	cp -pR "$${ACP_CLIENT_PACKAGE_DIR}/__init__.py" \
		"$${ACP_CLIENT_PACKAGE_DIR}/exceptions.py" \
		"$${ACP_CLIENT_PACKAGE_DIR}/configuration.py" \
		"$${ACP_CLIENT_PACKAGE_DIR}/api_response.py" \
		"$${ACP_CLIENT_PACKAGE_DIR}/models" \
		"$${ACP_CLIENT_PACKAGE_DIR}/spec_version.py" \
		"agntcy_acp/$(ACP_SUBPACKAGE_PREFIX)$${ACP_SPEC_VERSION}/" && \
	cp -pR "$${ACP_CLIENT_PACKAGE_DIR}/api" \
		"$${ACP_CLIENT_PACKAGE_DIR}/api_client.py" \
		"$${ACP_CLIENT_PACKAGE_DIR}/rest.py" \
		"agntcy_acp/$(ACP_SUBPACKAGE_PREFIX)$${ACP_SPEC_VERSION}/$(SDK_ACP_SYNC_PACKAGE_NAME)/" && \
	cp -pR "$${ACP_ASYNC_CLIENT_PACKAGE_DIR}/api" \
		"$${ACP_ASYNC_CLIENT_PACKAGE_DIR}/api_client.py" \
		"$${ACP_ASYNC_CLIENT_PACKAGE_DIR}/rest.py" \
		"agntcy_acp/$(ACP_SUBPACKAGE_PREFIX)$${ACP_SPEC_VERSION}/$(SDK_ACP_ASYNC_PACKAGE_NAME)/"


generate: generate_acp_client generate_acp_server

.PHONY: sphinx
sphinx docs/sphinx/agntcy_acp.rst: agntcy_acp/*.py agntcy_acp/*/*.py
	uv run --with sphinx -- \
	  sphinx-apidoc -o docs/sphinx/ --full agntcy_acp 'agntcy_acp/agws_v*' 'agntcy_acp/acp_v*'

.PHONY: docs
docs docs/html/index.html: docs/sphinx/agntcy_acp.rst
	$(MAKE) -C docs/sphinx html

.PHONY: test
test:
	ACP_SPEC_PATH="$(ACP_SPEC_DIR)/openapi.yaml" \
	uv run --locked --with pytest --group test -- \
	  pytest --exitfirst -vv tests/

.PHONY: check
check: test
	scripts/check-models.sh

.PHONY: test_gha
test_gha:
	uv run --locked --with pytest --group test -- \
	  pytest --exitfirst -vv -m "not needs_acp_spec" tests/

.PHONY: all
all: generate test
