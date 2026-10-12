import csv
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1])
out = sys.argv[2]
cols = ['rank', 'hanji', 'tailo', 'reading_layer', 'mandarin', 'hsk_old', 'hsk_new', 'vs_mandarin',
        'english_nc', 'moe_definition_zh', 'corpus_freq', 'moe_example_hanji', 'moe_example_tailo',
        'moe_example_mandarin']
with open(out, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(cols)
    for r in con.execute('SELECT freq_rank, hanji, tailo, wenbai, mandarin_best, hsk_old, hsk_new, cognate, english, '
                         'definition_zh, freq, entry_id FROM v_core'):
        ex = con.execute("SELECT hanji, tailo, mandarin FROM example WHERE entry_id=? AND length(hanji)>3 "
                         "ORDER BY id LIMIT 1", (r[-1],)).fetchone() or ('', '', '')
        w.writerow(list(r[:-1]) + list(ex))
print('rows', con.execute('SELECT count(*) FROM v_core').fetchone()[0])
