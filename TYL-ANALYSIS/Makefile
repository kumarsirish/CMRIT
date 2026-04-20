.PHONY: all build test run clean

all: clean build test

build:
	pip install -r requirements.txt

test:
	PYTHONPATH=src pytest tests/test_tyl_dashboard.py

run:
	streamlit run src/streamlit_app.py

clean:
	rm -rf .pytest_cache __pycache__ **/__pycache__ tests/__pycache__ tests/.pytest_cache test-output.xml 


