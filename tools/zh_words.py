"""Mandarin text -> tappable words, each with its pinyin (chosen for the sentence) and CC-CEDICT senses: ONE
implementation for the app and the private module (the 華語 · Mandarin sheet: `zhLine()` in app/index.template.html).
Automatic: neither the cut nor the readings are checked by a person.

The cut (the Shūjià reader's model, jieba-style)
  * In each run of Han characters, the cut with the highest total score, a word scoring round(1000 · ln f) minus
    QT = round(1000 · ln total): f is its frequency in jieba's dictionary (data/raw/jieba/dict.txt, simplified, MIT).
    Words up to 8 characters; equal totals keep the longer first word.
  * Traditional / Taiwan text: a written word is looked up under every simplified form its characters can have
    (CC-CEDICT's traditional/simplified pairs + VARIANT_FORMS: 裏 裡, 著 着, 份 分, 臺 台…), the best one counts; the
    cut stays on the written characters. 過份 finds 过分, 看著 看着.
  * A CC-CEDICT word jieba's dictionary lacks (过多, 太过: jieba finds those with its HMM, which is not used here)
    gets the frequency its weight in jieba's idf.txt (same repository, MIT) stands for, mapped onto the dictionary's
    scale by a least-squares line over the words both files have; a word in neither file gets f = 20 (one character)
    or 3, as in Shūjià. Any other single character f = 1.
  * A jieba word CC-CEDICT lacks (很快, 看著, 睡不著, 太過份) counts in the cut, but the app shows it as the CC-CEDICT
    words it is made of, cut by the same rule among CC-CEDICT words (太 過份, 睡 不著), each its own tappable word: every
    tap opens a real CC-CEDICT entry.
  * Integer scores: the browser repeats the exact same cut from the table (zhCut in the template).

The readings (numbered pinyin, CC-CEDICT's, mainland standard; 一 and 不 in their citation tones, as dictionaries write)
  * Each word has a default reading, a pure function of the word: SINGLE (particles and a few characters), WORD_PY
    (word overrides), else for one character the reading used by the most frequent words (CC-CEDICT × jieba, as
    Shūjià's READ_MAIN), for a longer word its HSK reading, else pypinyin's reading of the word (phrase dictionary),
    else the CC-CEDICT reading with most senses; "used in / variant / archaic" readings and names last.
  * Per occurrence: a single character standing as a word gets the reading `rule()` gives from its neighbours in the
    computed cut (V得 de, 我得 děi, 不著 zháo, 長大 zhǎng, 還錢 huán, 為了 wèi…), kept only if CC-CEDICT lists it for
    that character. A longer word keeps its default (pypinyin's phrase dictionary reads a word, not a sentence).
  * Where an occurrence's reading differs from its word's default, the text gets an exception
    {key(text): "token.line,…"} (the word's position among the text's words, the line of its entry).

Shipped: one table {word: entry} (DATA.zh in the app page; exam/zh.json "w" in the private module: only the words
the app's table lacks) and the exceptions (DATA.zhx, exam/zh.json "x"); no per-text cut. Entry:
  "score|pinyin<TAB>English" lines (CC-CEDICT word, the default reading first), or
  "score|=part part…"  (jieba-only word: the CC-CEDICT words the app shows in its place)
`check()` runs the browser's rule here.

    import zh_words
    L = zh_words.Lexicon()
    for t in texts: L.add(t)
    DATA['zh'], DATA['zhx'] = L.table(), L.exceptions()
    zh_words.check(texts, DATA['zh'], DATA['zhx'])   # -> number of texts the browser would show differently (0)

Data: data/raw/cedict (CC-CEDICT, CC BY-SA 4.0, MDBG), data/raw/jieba (dict.txt, idf.txt; MIT),
data/raw/complete-hsk-vocabulary (MIT), all fetched by `make data`. pypinyin (requirements.txt) for the default reading
of words HSK does not list; without it, CC-CEDICT's order.
"""
import itertools
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CEDICT = os.environ.get('CEDICT') or os.path.join(ROOT, 'data/raw/cedict/package/cedict.json')
JIEBA = os.path.join(ROOT, 'data/raw/jieba/dict.txt')
IDF = os.path.join(ROOT, 'data/raw/jieba/idf.txt')
HSK = os.path.join(ROOT, 'data/raw/complete-hsk-vocabulary/complete.min.json')
HAN_CLASS = '㐀-鿿豈-﫿\U00020000-\U0003134f'   # same class as ZH_RUN in the app
HAN = re.compile(f'[{HAN_CLASS}]')
RUN = re.compile(f'([{HAN_CLASS}]+)')
MAXN = 8          # longest word looked up
SCALE = 1000      # scores are round(SCALE · ln f)
SENSES = 6        # readings kept per word
CL = ('CL:',)     # CC-CEDICT English items left out (measure words)
MINOR = re.compile(r'archaic|obsolete|^old variant of|^variant of|^used in |radical|^see |Japanese variant|\(old\)|'
                   r'^\(dialect\)|^\(Cantonese\)|^surname |^\(Tw\)', re.I)
# Taiwan / old variant characters -> the forms CC-CEDICT and jieba use (besides CC-CEDICT's own pairs)
VARIANT_FORMS = {'裏': '裡里', '峯': '峰', '牀': '床', '綫': '線线', '麪': '麵面', '衆': '眾众', '爲': '為为', '僞': '偽伪',
                 '眞': '真', '敎': '教', '値': '值', '着': '著着', '著': '着著', '啓': '啟启', '敍': '敘叙', '溼': '濕湿',
                 '箇': '個个', '纔': '才', '粧': '妝妆', '菸': '煙烟', '綑': '捆', '份': '份分', '臺': '台', '台': '臺台',
                 '佈': '布', '祕': '秘', '汙': '污', '恆': '恒', '吋': '寸', '踴': '踊', '撐': '撑', '囉': '啰', '喫': '吃'}
# a single character standing as a word: its default reading (rule() may change it per occurrence)
SINGLE = {'著': 'zhe5', '着': 'zhe5', '得': 'de5', '地': 'di4', '了': 'le5', '嗎': 'ma5', '呢': 'ne5', '吧': 'ba5',
          '個': 'ge4', '麼': 'me5', '的': 'de5', '一': 'yi1', '不': 'bu4', '都': 'dou1', '還': 'hai2', '為': 'wei2',
          '和': 'he2', '只': 'zhi3', '要': 'yao4', '長': 'chang2', '重': 'zhong4', '行': 'xing2', '會': 'hui4',
          '便': 'bian4', '當': 'dang1', '種': 'zhong3', '數': 'shu4', '好': 'hao3', '倒': 'dao4', '樂': 'le4',
          '發': 'fa1', '乾': 'gan1', '幹': 'gan4', '少': 'shao3', '中': 'zhong1', '大': 'da4', '分': 'fen1',
          '相': 'xiang1', '看': 'kan4', '說': 'shuo1', '傳': 'chuan2', '藏': 'cang2', '應': 'ying1', '切': 'qie1',
          '與': 'yu3', '載': 'zai4', '盛': 'sheng4', '處': 'chu4', '調': 'diao4', '差': 'cha4', '空': 'kong1',
          '量': 'liang4', '正': 'zheng4', '將': 'jiang1', '朝': 'chao2', '教': 'jiao1', '覺': 'jue2', '省': 'sheng3',
          '背': 'bei4', '血': 'xue4', '薄': 'bao2', '給': 'gei3', '似': 'si4', '露': 'lu4', '假': 'jia3', '答': 'da2',
          '結': 'jie2', '曾': 'ceng2', '沒': 'mei2', '把': 'ba3', '上': 'shang4', '參': 'can1', '興': 'xing4',
          '降': 'jiang4', '供': 'gong1', '扇': 'shan4', '熟': 'shu2', '削': 'xiao1', '塞': 'sai1', '縫': 'feng2',
          '轉': 'zhuan3', '散': 'san4', '難': 'nan2', '間': 'jian1', '奇': 'qi2', '晃': 'huang4', '彈': 'tan2',
          '模': 'mo2', '冲': 'chong1', '衝': 'chong1', '佔': 'zhan4', '占': 'zhan4', '咽': 'yan4', '吐': 'tu3',
          '畜': 'chu4', '卡': 'ka3', '鑽': 'zuan1', '釘': 'ding1', '擔': 'dan1', '劃': 'hua4', '扎': 'zha1', '號': 'hao4',
          '漂': 'piao1', '佛': 'fo2', '兒': 'er2', '那': 'na4', '哪': 'na3', '啊': 'a5', '呀': 'ya5', '喔': 'o5',
          '哦': 'o4', '嘛': 'ma5', '啦': 'la5', '喲': 'yo5', '亡': 'wang2', '仔': 'zai3'}
# word readings CC-CEDICT gives in another order, or several, where one is far more usual
WORD_PY = {'地方': 'di4 fang5', '生意': 'sheng1 yi5', '教授': 'jiao4 shou4', '所長': 'suo3 zhang3', '到了': 'dao4 le5',
           '都會': 'dou1 hui4', '不了': 'bu4 liao3', '起來': 'qi3 lai5', '東西': 'dong1 xi5', '便宜': 'pian2 yi5',
           '大夫': 'dai4 fu5', '妻子': 'qi1 zi5', '結果': 'jie2 guo3', '得到': 'de2 dao4', '了解': 'liao3 jie3',
           '拜拜': 'bai4 bai5', '覺得': 'jue2 de5', '記得': 'ji4 de5', '曉得': 'xiao3 de5', '值得': 'zhi2 de5',
           '捨得': 'she3 de5', '倒是': 'dao4 shi5', '一會兒': 'yi1 hui4 r5', '這個': 'zhe4 ge5', '那個': 'na4 ge5',
           '一個': 'yi1 ge4', '什麼': 'shen2 me5', '怎麼': 'zen3 me5', '多少': 'duo1 shao5', '意思': 'yi4 si5',
           '時候': 'shi2 hou5', '漂亮': 'piao4 liang5', '朋友': 'peng2 you5', '出來': 'chu1 lai5', '下來': 'xia4 lai5',
           '上來': 'shang4 lai5', '過來': 'guo4 lai5', '回來': 'hui2 lai5', '進來': 'jin4 lai5', '出去': 'chu1 qu5',
           '下去': 'xia4 qu5', '上去': 'shang4 qu5', '過去': 'guo4 qu4', '人家': 'ren2 jia1', '大意': 'da4 yi4',
           '地道': 'di4 dao5', '兄弟': 'xiong1 di4', '運氣': 'yun4 qi5', '本事': 'ben3 shi5', '大方': 'da4 fang5',
           '多數': 'duo1 shu4', '少數': 'shao3 shu4', '重複': 'chong2 fu4', '重量': 'zhong4 liang4', '長大': 'zhang3 da4'}
PRON = set('我你他她它您咱們们誰谁人家')
NUM = set('一二三四五六七八九十兩百千萬幾半每這那哪某各此數')
_M = None


def marks(numbered):
    """CC-CEDICT 'zhong1 guo2' -> 'zhōng guó'"""
    tones = {'a': 'āáǎàa', 'e': 'ēéěèe', 'i': 'īíǐìi', 'o': 'ōóǒòo', 'u': 'ūúǔùu', 'ü': 'ǖǘǚǜü'}
    out = []
    for syl in numbered.split():
        m = re.fullmatch(r'([A-Za-zü:]+)([1-5])', syl.replace('u:', 'ü').replace('U:', 'Ü'))
        if not m:
            out.append(syl)
            continue
        b, t = m.group(1), int(m.group(2)) - 1
        low = b.lower()
        i = low.find('a') if 'a' in low else low.find('e') if 'e' in low else low.find('ou') if 'ou' in low \
            else max(low.rfind(v) for v in 'iouü')
        if i < 0:
            out.append(b)
            continue
        mk = tones[low[i]][t]
        out.append(b[:i] + (mk.upper() if b[i].isupper() else mk) + b[i + 1:])
    return ' '.join(out)


def norm_num(p):
    """numbered pinyin, compared form: lower case, ü as v, neutral tone 5"""
    out = []
    for s in p.lower().replace('u:', 'v').replace('ü', 'v').split():
        out.append(s if s[-1:].isdigit() else s + '5')
    return ' '.join(out)


def rule(c, prev, nxt):
    """the reading of a single character standing as a word, from its neighbours in the cut (strings, '' at the
    edge of a run of Han characters, i.e. at punctuation), or None: the default. Numbered pinyin."""
    p1, n1 = prev[-1:], nxt[:1]
    if c == '得':
        if n1 == '了' and not prev:
            return 'de2'                           # 得了: that's enough / obtained
        if p1 and p1 in PRON and n1 and n1 not in '到了出以知益失分獎勝':
            return 'dei3'                          # 我得走, 你們得去: must
        if prev in ('就', '還', '也', '都', '總', '非', '可') and n1 and n1 not in '到了出以知益失分':
            return 'dei3'
        if not prev or prev in ('而', '所', '可', '獲', '取', '求', '心', '難', '各', '自', '應', '不可', '必'):
            return 'de2'                           # 得之, 所得, 各得其所: obtain
        return None                                # V得 / A得: de
    if c in '著着':
        if p1 in ('不', '得', '沒') or prev in ('找', '睡', '猜', '摸', '夠', '用', '見'):
            return 'zhao2'                         # 睡不著, 找著, 用不著: reach / succeed
        if not prev and n1:
            return 'zhuo2' if n1 and n1 in '手重眼力落陸裝想' else 'zhao2'   # 著重, 著急 (words); 著火, 著涼
        if n1 and n1 in '火涼迷急慌':
            return 'zhao2'
        return None
    if c == '了':
        if p1 in ('不', '得') and (not nxt or n1 and n1 in '的'):
            return 'liao3'                         # V不了, V得了: be able to
        return None
    if c == '地':
        if len(prev) >= 2 and nxt and (prev[-1] == prev[-2] or prev[-1] in '然地般樣些勁心意力真實速快慢輕重靜默悄緩好細'):
            return 'de5'                           # 慢慢地, 突然地, 偷偷地: -ly
        return None
    if c == '還':
        if n1 and n1 in '錢債給清本原手擊鄉俗願' or prev in ('歸', '償', '退', '交', '送', '借', '討', '要', '把'):
            return 'huan2'
        return None
    if c == '長':
        if n1 and (n1 and n1 in '得大出滿成高胖肉毛葉芽牙鬍鬚瘡蟲' or nxt in ('了', '著', '在')):
            return 'zhang3'                        # 長得, 長出, 長滿: grow
        if prev in ('生', '成', '增', '助', '滋', '瘋', '又', '再', '也', '會', '已', '正在', '開始') and n1 != '的':
            return 'zhang3'
        return None
    if c == '為':
        if n1 and n1 in '了何什甚此' or nxt in ('他', '她', '我', '你', '您', '大家', '人民', '國家', '自己', '別人', '誰'):
            return 'wei4'                          # 為了, 為何, 為他: for
        return None
    if c == '重':
        if n1 and n1 in '做寫來讀考說打畫裝新蓋建修編排播申返回演選印':
            return 'chong2'                        # 重做, 重寫: again
        return None
    if c == '行':
        if p1 and p1 in NUM or prev in ('同', '這', '那', '哪', '本', '外', '內', '銀', '改'):
            return 'hang2'                         # 一行, 兩行, 這行: row / trade
        return None
    if c == '種':
        if n1 and n1 in '樹花菜豆稻瓜果草苗田地麥茶菸' and not (p1 and p1 in NUM):
            return 'zhong4'                        # 種樹, 種花: plant
        return None
    if c == '數':
        if (prev == '數' or nxt in ('一', '數', '錢', '不', '著', '到', '過', '了', '清', '得')) and not (p1 and p1 in NUM):
            return 'shu3'                          # 數一數, 數錢: count
        return None
    if c == '倒':
        if prev in ('推', '撞', '摔', '跌', '絆', '滑', '打', '翻', '碰', '壓', '砍', '放', '病', '累', '醉', '嚇', '昏',
                    '踢', '吹', '颳', '拉', '扳', '弄', '震', '傾', '撲') or n1 and n1 in '下塌閉地臺台':
            return 'dao3'                          # 推倒, 倒下: fall
        return None
    if c == '處':
        if n1 and n1 in '在於理置罰事世':
            return 'chu3'                          # 處在, 處於: be in; 處理
        return None
    if c == '量':
        if n1 and n1 in '體身尺血一量長寬高溫重':
            return 'liang2'                        # 量體重: measure
        return None
    if c == '背':
        if n1 and n1 in '著包書孩小起走' or nxt in ('著', '起來'):
            return 'bei1'                          # 背著, 背書包: carry on the back
        return None
    if c == '盛':
        if n1 and n1 in '飯湯水菜粥酒滿裝':
            return 'cheng2'                        # 盛飯: fill
        return None
    if c == '好':
        if prev in ('愛', '喜', '所', '嗜', '偏', '最') or nxt in ('學', '吃', '色', '奇', '客', '動', '強', '勝', '辯'):
            return None if nxt == '吃' else 'hao4'
        return None
    if c == '教':
        if n1 and n1 in '育室堂師授條會徒派':
            return 'jiao4'
        return None
    if c == '當':
        if n1 and n1 in '作成做真':
            return 'dang4'                         # 當作, 當真: take as
        return None
    if c == '空':
        if n1 and n1 in '出下閒地位隙' or p1 in ('有', '沒', '抽', '得'):
            return 'kong4'                         # 空出, 有空: free (time / space)
        return None
    if c == '差':
        if n1 and n1 in '別異距額價錯':
            return 'cha1'                          # 差別, 差距: difference
        return None
    if c == '調':
        if n1 and n1 in '整和節皮配解劑味':
            return 'tiao2'                         # 調整, 調味: adjust
        return None
    if c == '應':
        if n1 and n1 in '對付用聘徵邀變急':
            return 'ying4'                         # 應付, 應邀: respond
        return None
    if c == '相':
        if n1 and n1 in '片貌機館聲' or prev in ('照', '長', '真', '首', '宰', '外', '丞', '面'):
            return 'xiang4'                        # 相片, 照相: appearance
        return None
    if c == '藏':
        if n1 and n1 in '民族獒語文區人醫藥袍戲曆經傳':
            return 'zang4'                         # 藏民: Tibet (Shūjià's CTX_READ)
        return None
    if c == '間':
        if n1 and n1 in '隔斷接諜歇':
            return 'jian4'
        return None
    if c == '興':
        if n1 and n1 in '起建旺盛奮':
            return 'xing1'
        return None
    if c == '難':
        if n1 and n1 in '民友胞':
            return 'nan4'
        return None
    if c == '覺':
        if prev in ('睡', '午', '一'):
            return 'jiao4'
        return None
    if c == '降':
        if n1 and n1 in '服伏':
            return 'xiang2'
        return None
    if c == '散':
        if n1 and n1 in '文裝漫' or prev in ('懶', '鬆'):
            return 'san3'
        return None
    if c == '彈':
        if n1 and n1 in '藥頭殼丸珠':
            return 'dan4'
        return None
    if c == '塞':
        if n1 and n1 in '外北翁':
            return 'sai4'
        return None
    if c == '傳':
        if n1 and n1 in '記略' or prev in ('自', '列', '外', '正', '經', '水滸'):
            return 'zhuan4'
        return None
    if c == '便':
        if n1 and n1 in '宜':
            return 'pian2'
        return None
    if c == '薄':
        if n1 and n1 in '弱情命荷利' or prev in ('淺', '單', '刻', '微', '稀'):
            return 'bo2'
        return None
    return None


class Model:
    def __init__(self):
        self.ced, self.simp = {}, {}            # trad -> [[numbered, [English…]]…]; simp -> [trad…]
        self.freq, self.total, self.idf = {}, 1, {}
        self.t2s = {}                           # trad char -> [simplified forms, most usual first]
        self.hsk = {}
        if os.path.exists(CEDICT):
            rows = json.load(open(CEDICT, encoding='utf-8')) if CEDICT.endswith('.json') else []
            pair = {}
            for e in rows:
                t, s, p, en = e['traditional'], e['simplified'], e['pinyin'], e['english']
                if not t or not all(HAN.match(c) for c in t) or len(t) > MAXN:
                    continue
                self.ced.setdefault(t, []).append([p, list(en)])
                self.simp.setdefault(s, []).append(t)
                if len(t) == len(s):
                    for a, b in zip(t, s):
                        pair.setdefault(a, {}).setdefault(b, 0)
                        pair[a][b] += 1
            simps = {b for v in pair.values() for b in v}
            for a, v in pair.items():
                opts = sorted(v, key=lambda b: (-v[b], b != a))
                if a in simps and a not in opts:
                    opts.append(a)
                self.t2s[a] = opts[:3]
        for a, fs in VARIANT_FORMS.items():
            opts = []
            for f in fs:
                opts += [f] + self.t2s.get(f, [])
            self.t2s[a] = list(dict.fromkeys(opts + self.t2s.get(a, [])))[:4]
        if os.path.exists(JIEBA):
            tot = 0
            for line in open(JIEBA, encoding='utf-8'):
                x = line.split()
                if len(x) >= 2 and not line.startswith('#'):
                    self.freq[x[0]] = int(x[1])
                    tot += int(x[1])
            self.total = max(tot, 1)
        else:
            print('zh_words: no jieba dictionary at', JIEBA, '(make data): words are cut by CC-CEDICT alone')
        if os.path.exists(IDF):
            # idf -> frequency on the dictionary's scale: ln f = a + b · idf, least squares over the words of two or
            # more characters both files have; used only for CC-CEDICT words the dictionary lacks
            idf = {}
            for line in open(IDF, encoding='utf-8'):
                x = line.split()
                if len(x) == 2:
                    idf[x[0]] = float(x[1])
            xs = [(v, math.log(self.freq[w])) for w, v in idf.items() if len(w) > 1 and self.freq.get(w)]
            if len(xs) > 100:
                n = len(xs)
                mx, my = sum(a for a, _ in xs) / n, sum(b for _, b in xs) / n
                b = sum((a - mx) * (c - my) for a, c in xs) / sum((a - mx) ** 2 for a, _ in xs)
                a = my - b * mx
                self.idf = {w: max(3, round(math.exp(a + b * v))) for w, v in idf.items()
                            if len(w) > 1 and w not in self.freq}
        if os.path.exists(HSK):
            for e in json.load(open(HSK, encoding='utf-8')):
                for f in e['f']:
                    self.hsk.setdefault(f['t'], f['i']['n'])
        self.QT = round(SCALE * math.log(self.total))
        self._score, self._entry, self._main, self._rd, self._parts = {}, {}, None, {}, {}
        try:
            from pypinyin import lazy_pinyin, Style
            self.py = lambda s: lazy_pinyin([s], style=Style.TONE3, neutral_tone_with_five=True, errors=lambda x: list(x))
        except ImportError:
            self.py = None

    # ---- the cut
    def forms(self, w):
        """simplified forms a written word can have (its characters' forms combined), the written form first"""
        opts = [[c] + [x for x in self.t2s.get(c, []) if x != c] for c in w]
        return [''.join(combo) for combo in itertools.islice(itertools.product(*opts), 64)]

    def score(self, w):
        """(score, simplified form, kind) of a written word, kind 'c' (CC-CEDICT word) or 'j' (jieba word shown as
        its parts), or None when it is no word (longer than one character)"""
        r = self._score.get(w)
        if r is None:
            fs = self.forms(w)
            f, sw = max(((self.freq.get(x, 0), x) for x in fs), key=lambda y: y[0])
            ck = self.cedict_key(w)
            kind = 'c' if ck else 'j'
            if not ck and len(w) > 1 and (not f or not self.parts(w)):
                f = 0                          # neither dictionary's word, or one the sheet could not show
            elif not f:
                if ck and len(w) > 1:
                    f, sw = max(((self.idf.get(x, 0), x) for x in fs), key=lambda y: y[0])
                    f = f or 3
                elif ck:
                    f = 20
                else:
                    f = 1                      # a single character CC-CEDICT lacks: plain text
            if not f:
                r = False
            else:
                if not self.freq.get(sw) and not self.idf.get(sw):
                    sw = next((x for x in fs if x in self.simp), fs[-1])
                r = (round(SCALE * math.log(f)), sw, kind)
            self._score[w] = r
        return r or None

    def cut_run(self, cs, known=None):
        """one run of Han characters (list of characters) -> list of words: highest total score, longer first word on
        a tie. known(w) -> score or None. The browser's zhCut() is the same."""
        known = known or (lambda w: (self.score(w) or (None,))[0])
        n = len(cs)
        best, step = [0] * (n + 1), [1] * (n + 1)
        for i in range(n - 1, -1, -1):
            b = None
            for k in range(min(MAXN, n - i), 0, -1):
                q = known(''.join(cs[i:i + k]))
                if q is None:
                    if k > 1:
                        continue
                    q = 0
                c = q - self.QT + best[i + k]
                if b is None or c > b:
                    b, step[i] = c, k
            best[i] = b
        out, i = [], 0
        while i < n:
            out.append(''.join(cs[i:i + step[i]]))
            i += step[i]
        return out

    # ---- what a word shows
    def cedict_key(self, w):
        """the CC-CEDICT traditional headword for a written word: itself, or one with the same simplified form"""
        if w in self.ced:
            return w
        for x in self.forms(w):
            if x in self.ced:
                return x
            for t in self.simp.get(x, []):
                return t
        return None

    def parts(self, w):
        """a jieba word CC-CEDICT lacks -> the CC-CEDICT words it is made of, cut by the same rule among CC-CEDICT
        words only (太過份 -> 太 過份), or [] when it is one character"""
        r = self._parts.get(w)
        if r is None:
            def known(x):
                if x == w or (len(x) > 1 and not self.cedict_key(x)):
                    return None
                sc = self.score(x)
                return sc[0] if sc else None
            r = self.cut_run(list(w), known) if len(w) > 1 else []
            self._parts[w] = r
        return r

    def readings(self, w):
        """[[numbered, [English]]] for a CC-CEDICT word, one line per reading, "variant of" entries resolved"""
        if w in self._rd:
            return self._rd[w]
        k = self.cedict_key(w)
        lines = {}
        for p, en in (self.ced[k] if k else []):
            en2 = [g for g in en if not g.startswith(CL)]
            if en2 and all(re.match(r'(old )?variant of ', g) for g in en2):   # 過份 'variant of 過分': show 過分's senses
                m = re.match(r'(?:old )?variant of ([^|\[\s,;]+)', en2[0])
                tgt = m and self.ced.get(m.group(1))
                if tgt:
                    en2 = en2 + [g for q, e2 in tgt if norm_num(q) == norm_num(p) for g in e2 if not g.startswith(CL)][:6]
            q = norm_num(p)
            if q in lines:   # the same reading twice (a surname entry and a word): one line, lower case first
                a = lines[q]
                lines[q] = [p, en2 + a[1]] if a[0][:1].isupper() and not p[:1].isupper() else [a[0], a[1] + en2]
            else:
                lines[q] = [p, en2]
        self._rd[w] = list(lines.values())
        return self._rd[w]

    def main_reading(self):
        """single character -> its reading in the most frequent words that use it (CC-CEDICT × jieba)"""
        if self._main is None:
            w = {}
            for t, es in self.ced.items():
                fs = self.forms(t)
                f = max(self.freq.get(x, 0) for x in fs[:8])
                for p, en in es:
                    if p[:1].isupper():
                        continue
                    sy = norm_num(p).split()
                    if len(sy) != len(t):
                        continue
                    for c, y in zip(t, sy):
                        w.setdefault(c, {}).setdefault(y, 0)
                        w[c][y] += f + 1
            self._main = {c: max(v, key=v.get) for c, v in w.items()}
        return self._main

    def default_reading(self, w, rs):
        """index of the reading the sheet opens with when the sentence does not decide (a pure function of the word)"""
        nums = [norm_num(p) for p, _ in rs]
        minor = lambda i: all(MINOR.search(g) for g in rs[i][1]) if rs[i][1] else True
        name = lambda i: rs[i][0][:1].isupper()
        want = [SINGLE.get(w), WORD_PY.get(w)]
        if len(w) == 1:
            want.append(self.main_reading().get(w))
        else:
            want.append(norm_num(self.hsk[w]) if w in self.hsk else None)
            if self.py and len(nums) > 1:
                s = self.score(w)
                want.append(' '.join(norm_num(y) for y in self.py(s[1] if s else w)))
        for x in want:
            if x and x in nums and not name(nums.index(x)):
                return nums.index(x)
        return sorted(range(len(rs)), key=lambda i: (name(i), minor(i), -len(rs[i][1]), not nums[i].endswith('5')))[0]

    def entry(self, w):
        """(score, lines [[marks, English]], numbered readings, parts) for a written word; parts: the CC-CEDICT words a
        jieba-only word is shown as (else None)"""
        r = self._entry.get(w)
        if r is None:
            s = self.score(w)
            q = s[0] if s else 0
            rs = self.readings(w) if (not s or s[2] == 'c') else []
            if rs:
                d = self.default_reading(w, rs)
                minor = lambda i: all(MINOR.search(g) for g in rs[i][1]) if rs[i][1] else True
                order = [d] + sorted((i for i in range(len(rs)) if i != d), key=lambda i: (rs[i][0][:1].isupper(), minor(i)))
                order = order[:SENSES]
                r = (q, [[marks(rs[i][0]), '; '.join(rs[i][1])] for i in order], [norm_num(rs[i][0]) for i in order], None)
            elif s and s[2] == 'j' and len(w) > 1:
                r = (q, [], [], self.parts(w))   # shown as its parts, each its own word
            else:
                r = (q, [], [], None)
            self._entry[w] = r
        return r

    def tappable(self, w):
        return bool(self.entry(w)[1])

    def shown(self, w):
        """a word of the cut -> the words the app shows for it (a jieba-only word: its parts)"""
        return self.entry(w)[3] or [w]

    # ---- the readings in context
    def read_words(self, words):
        """per word of one run: the line of its entry that fits the sentence, or None (its default, line 0)"""
        out = [None] * len(words)
        for j, w in enumerate(words):
            if len(w) != 1:
                continue
            e = self.entry(w)
            if not e[2]:
                continue
            if j >= 2 and words[j - 2] == w and words[j - 1] in ('一', '了', '不'):
                out[j] = out[j - 2]                # 數一數, 看了看: the second as the first
                continue
            got = rule(w, words[j - 1] if j else '', words[j + 1] if j + 1 < len(words) else '')
            if got and got != e[2][0] and got in e[2]:
                out[j] = e[2].index(got)
        return out


def model():
    global _M
    if _M is None:
        _M = Model()
    return _M


def available():
    return bool(model().ced)


def _b36(n):
    s = ''
    while True:
        n, r = divmod(n, 36)
        s = '0123456789abcdefghijklmnopqrstuvwxyz'[r] + s
        if not n:
            return s


def key(text):
    """the key of a text in the exceptions: FNV-1a (32 bits) over its code points, '.', its length (zhKey in the app)"""
    h, n = 0x811c9dc5, 0
    for c in text:
        h = ((h ^ ord(c)) * 0x01000193) & 0xffffffff
        n += 1
    return _b36(h) + '.' + _b36(n)


def analyse(text):
    """[str | [word, reading line or None]]: the build's cut (plain strings merged), each word with its reading here"""
    M = model()
    out = []
    def put(s):
        if out and isinstance(out[-1], str):
            out[-1] += s
        else:
            out.append(s)
    for i, part in enumerate(RUN.split(text or '')):
        if not part:
            continue
        if i % 2 == 0:
            put(part)
            continue
        ws = [y for w in M.cut_run(list(part)) for y in M.shown(w)]
        for w, r in zip(ws, M.read_words(ws)):
            if M.tappable(w):
                out.append([w, r])
            else:
                put(w)
    return out


def segment(text):
    """Mandarin text -> [str | [word]] (a list holds a tappable word)"""
    return [t if isinstance(t, str) else [t[0]] for t in analyse(text)]


class Lexicon:
    """the words a set of texts uses, and the readings that differ from a word's default"""
    def __init__(self):
        self.words, self.exc = set(), {}

    def add(self, text):
        M = model()
        for i, part in enumerate(RUN.split(text or '')):
            if i % 2 and part:
                for w in M.cut_run(list(part)):
                    if len(w) > 1 or M.score(w)[0] > 0 or M.tappable(w):   # its score or its entry matters to the browser
                        self.words.add(w)
                        for p in M.entry(w)[3] or []:   # a jieba-only word's parts: the app shows them
                            if M.tappable(p):
                                self.words.add(p)
        n, x = 0, []
        for t in analyse(text):
            if isinstance(t, list):
                if t[1]:
                    x.append(f'{_b36(n)}.{_b36(t[1])}')
                n += 1
        if x:
            k, v = key(text), ','.join(x)
            if self.exc.get(k, v) != v:
                raise SystemExit(f'zh_words: two texts share the key {k}')
            self.exc[k] = v
        return self

    def table(self, skip=()):
        """{word: "score|" + "pinyin<TAB>English" lines}; skip: words another table (the app's) already has"""
        out = {}
        for w in sorted(self.words):
            if w in skip:
                continue
            q, lines, _, ps = model().entry(w)
            out[w] = f'{q}|=' + ' '.join(ps) if ps else f'{q}|' + '\n'.join(p + '\t' + en for p, en in lines)
        return out

    def exceptions(self):
        return dict(sorted(self.exc.items()))


def browser(text, table, exc):
    """what the app shows for a text from a table and exceptions (zhCut/zhLine in the template), for check()"""
    M = model()
    def known(w):
        e = table.get(w)
        return int(e[:e.index('|')]) if e is not None else None
    out = []
    def put(s):
        if out and isinstance(out[-1], str):
            out[-1] += s
        else:
            out.append(s)
    for i, part in enumerate(RUN.split(text or '')):
        if not part:
            continue
        if i % 2 == 0:
            put(part)
            continue
        for w0 in M.cut_run(list(part), known):
            b = table.get(w0, '|').split('|', 1)[1]
            for w in (b[1:].split(' ') if b.startswith('=') else [w0]):
                b2 = table.get(w, '|').split('|', 1)[1]
                if b2 and not b2.startswith('='):
                    out.append([w, None])
                else:
                    put(w)
    x = dict(tuple(int(v, 36) for v in y.split('.')) for y in exc.get(key(text), '').split(',') if y)
    j = 0
    for t in out:
        if isinstance(t, list):
            t[1] = x.get(j)
            j += 1
    return out


def check(texts, table, exc):
    """number of texts the browser would cut or read differently from the build (should be 0)"""
    bad = 0
    for t in texts:
        if browser(t, table, exc) != analyse(t):
            bad += 1
            if bad <= 5:
                print('zh_words: the browser would show this text differently:', t[:60])
    return bad


def show(text):
    """one line for a person: words separated by /, each with the reading shown (* = chosen by the sentence;
    a jieba-only word as part+part)"""
    M, out = model(), []
    for t in analyse(text):
        if isinstance(t, str):
            out.append(t)
        else:
            py = M.entry(t[0])[1][t[1] or 0][0].replace(' ', '')
            out.append(f"{t[0]}({py}{'*' if t[1] else ''})")
    return '/'.join(out)


if __name__ == '__main__':   # python3 -I tools/zh_words.py 太過份了  -> the cut and the readings
    import sys
    for s in sys.argv[1:] or ['你把事情搞到這種地步才要我來善後，不會太過份了嗎？']:
        print(show(s))
