PY ?= python

.PHONY: setup build app test eval clean

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

clean:
	rm -rf data/interim data/ethnohack.db
