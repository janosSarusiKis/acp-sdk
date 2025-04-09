.PHONY: generate-manifest

location=../examples/mailcomposer/mailcomposer
#location=../examples/echo-agent/echo_agent
#location=../examples/email_reviewer/email_reviewer

generate-manifest:
	@echo "Generating manifest..."
	poetry run python -m manifest_generator.main $(location) -o $(if $(output),$(output),manifest.json)