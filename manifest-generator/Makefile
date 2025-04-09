.PHONY: generate-manifest

location=../examples/mailcomposer/mailcomposer
#location=./example/mailcomposer/mailcomposer

generate-manifest:
	@echo "Generating manifest..."
	poetry run python -m manifest_generator.main $(location) -o $(if $(output),$(output),manifest.json)