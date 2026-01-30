

.PHONY: default help docs aggregate_data transform_md_all test pytest serve

default: help

help:
	@echo todo

docs:
	$(MAKE) -C docs html

aggregate_data:
	python3 tools/aggregate_technical_data.py

transform_md_all:
	transform-md --indir data/chatoverlay/chats__all/ --outdir docs/chats/ --transform-cell-split m1 --out-format=myst,ipynb,chatexport_abc1

test: pytest

build: aggregate_data transform_md_all docs

pytest:
	pytest --cov=. --cov-report=term-missing .

serve:
	tree -a -L 2 ./docs/_build/html
	python -m http.server -p ./docs/_build/html