PY ?= python

.PHONY: setup build app test eval stats slides clean

setup:
	$(PY) -m pip install -r requirements.txt

build:          ## Rebuild the database from data/raw
	$(PY) -m pipeline.build

app:            ## Open the demo
	$(PY) -m streamlit run app/app.py

test:
	$(PY) -m pytest -q

eval:           ## Accuracy against the hand-checked gold sample
	$(PY) -m eval.evaluate

stats:          ## Headline numbers, computed from the database
	$(PY) -m eval.stats

CHROME ?= google-chrome
slides:         ## Print docs/submission/slides.html to slides.pdf (needs Chrome or Chromium)
	cd docs/submission && $(CHROME) --headless=new --no-pdf-header-footer --virtual-time-budget=5000 \
		--print-to-pdf=slides.pdf "file://$(CURDIR)/docs/submission/slides.html"

clean:
	rm -rf data/interim data/ethnohack.db
