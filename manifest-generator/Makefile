.PHONY: generate-manifest

location=../examples/mailcomposer/mailcomposer
#location=../examples/echo-agent/echo_agent
#location=../examples/email_reviewer/email_reviewer

generate-manifest:
	@echo "Generating manifest..."
	poetry run generator $(location) -o $(if $(output),$(output),manifest.json) 