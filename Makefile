.PHONY: install api test lint contracts infra
install:
	pwsh -File tools/dev.ps1 install
api:
	pwsh -File tools/dev.ps1 api
test:
	pwsh -File tools/dev.ps1 test
lint:
	pwsh -File tools/dev.ps1 lint
contracts:
	pwsh -File tools/dev.ps1 contracts
infra:
	pwsh -File tools/dev.ps1 infra
