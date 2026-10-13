# make data      download open sources (data/raw)
# make db        build data/build/taigi.db and data/build/core_vocab.csv
# make db-nc     same, including non-commercial English glosses (Maryknoll, Embree)
# make lookup W=喜歡
PY = python3 -I
RAW = data/raw
OUT = data/build

.PHONY: data db db-nc lookup clean lint test app coverage
data:
	sh data/fetch.sh

db: data
	mkdir -p $(OUT)
	$(PY) tools/build_db.py $(RAW) $(OUT)/taigi.db
	$(PY) tools/freq_align.py $(RAW) $(OUT)/taigi.db
	$(PY) tools/enrich.py $(OUT)/taigi.db
	$(PY) tools/export.py $(OUT)/taigi.db $(OUT)/core_vocab.csv

db-nc:
	TAIGI_INCLUDE_NC=1 $(MAKE) db

lookup:
	$(PY) tools/lookup.py $(OUT)/taigi.db "$(W)"

clean:
	rm -rf $(OUT)

lint:
	$(PY) tools/lint.py

test:
	$(PY) tools/sandhi.py --test

app:
	$(PY) tools/build_app.py

coverage:
	$(PY) tools/coverage.py
