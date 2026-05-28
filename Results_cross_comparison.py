import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import os
import io
from datetime import datetime

# --- 頁面基本設定與全域 CSS ---
st.set_page_config(page_title="539 雙引擎特徵掃描系統 (V5.6 雲端旗艦版)", layout="wide")

st.markdown("""
<style>
.custom-scrollbar {
    overflow-y: auto !important;
    overflow-x: auto !important;
    white-space: pre !important; 
    font-family: "Consolas", "Courier New", monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 15px;
    border: 1px solid rgba(128, 128, 128, 0.4);
    border-radius: 8px;
    background-color: rgba(128, 128, 128, 0.05);
    margin-bottom: 20px;
}
.custom-scrollbar::-webkit-scrollbar {
    width: 10px !important; height: 10px !important; display: block !important;
}
.custom-scrollbar::-webkit-scrollbar-track { background: rgba(128, 128, 128, 0.1); border-radius: 8px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.5); border-radius: 8px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: rgba(128, 128, 128, 0.8); }

.bg-hit { background-color: #E8F5E9; }  /* 淺綠底：命中區 */
.bg-miss { background-color: #FFEBEE; } /* 淺紅底：不出區 */
.bg-feat-tl { background-color: #FFF9C4; } /* 區10 命中標記 */
.bg-feat-bl { background-color: #F0F8FF; } /* 區10 命中全部 */
.bg-feat-tr { background-color: #FFCDD2; } /* 區10 不出標記 */
.bg-feat-br { background-color: #F5F5F5; } /* 區10 不出全部 */
</style>
""", unsafe_allow_html=True)

st.title("📱 539 雙引擎特徵掃描系統 (區5單碼 / 區10組合)")

# ==========================================
# 檔案讀取與快取處理
# ==========================================
def get_col_val(row, possible_names, default=None):
    for name in possible_names:
        if name in row.index and pd.notna(row[name]): return row[name]
    if default is not None: return default
    raise KeyError(f"Missing: {possible_names}")

@st.cache_data(show_spinner=False)
def load_main_db(filepath="539_2007.csv"):
    if not os.path.exists(filepath): return None, 1, "找不到主資料庫 539_2007.csv"
    try:
        try: df = pd.read_csv(filepath, sep=None, engine='python', encoding="utf-8-sig")
        except: df = pd.read_csv(filepath, sep=None, engine='python', encoding="cp950")
        is_headless = False
        try:
            [float(c) for c in df.columns]
            is_headless = True
        except ValueError: pass
        if is_headless:
            try: df = pd.read_csv(filepath, sep=None, engine='python', encoding="utf-8-sig", header=None)
            except: df = pd.read_csv(filepath, sep=None, engine='python', encoding="cp950", header=None)
            return df, 0, None
        return df, (1 if len(df.columns) >= 6 else 0), None
    except Exception as e: return None, 1, str(e)

@st.cache_data(show_spinner=False)
def load_features():
    combo_t = {}; combo_n = set()
    macro_t = {}; macro_n = set()

    def safe_load(filepath, target_dict_or_set, is_target):
        if not os.path.exists(filepath): return
        try:
            try: df = pd.read_csv(filepath, sep=None, engine='python', encoding="utf-8-sig")
            except: df = pd.read_csv(filepath, sep=None, engine='python', encoding="cp950")
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            for _, r in df.iterrows():
                try:
                    s = int(float(get_col_val(r, ['星數', '星', 'star'], default=1)))
                    x = int(float(get_col_val(r, ['落球次數(X)', '落球次數', 'X', 'x'])))
                    y = int(float(get_col_val(r, ['大小次數(Y)', '大小次數', 'Y', 'y'])))
                    if is_target:
                        tot = int(float(get_col_val(r, ['總出現次數', '歷史總遇見次數', '總次數'], 0)))
                        hit = int(float(get_col_val(r, ['命中次數', '實際開出次數', '命中'], 0)))
                        target_dict_or_set[(s, x, y)] = (tot, hit)
                    else: target_dict_or_set.add((s, x, y))
                except: continue
        except Exception as e: st.error(f"讀取 {filepath} 失敗: {e}")

    safe_load("target.csv", combo_t, True)
    safe_load("noway.csv", combo_n, False)
    safe_load("macro_target.csv", macro_t, True)
    safe_load("macro_noway.csv", macro_n, False)
    
    return combo_t, combo_n, macro_t, macro_n

# 載入資料
df, data_offset, db_err = load_main_db()
if st.button("🔄 重新載入雲端特徵與資料庫 (清除快取)"):
    st.cache_data.clear()
    st.rerun()

combo_target, combo_noway, macro_target, macro_noway = load_features()

# --- UI 狀態顯示 ---
st.header("1. 系統狀態與條件輸入")
col_st1, col_st2 = st.columns(2)
with col_st1:
    if df is not None: st.success(f"✅ 主資料庫載入成功 (共 {len(df)} 筆)")
    else: st.error(f"❌ 主資料庫載入失敗: {db_err}")
with col_st2:
    st.info(f"🔍 雙引擎載入狀態: \n[區10 組合] 命:{len(combo_target)} / 不:{len(combo_noway)} \n[區 5 單碼] 命:{len(macro_target)} / 不:{len(macro_noway)}")

col_t, col_t1 = st.columns(2)
with col_t:
    st.write("**T (主輸入，5碼必填):**")
    t_cols = st.columns(5)
    t_inputs = [t_cols[i].text_input(f"T{i+1}", key=f"t{i}") for i in range(5)]
with col_t1:
    st.write("**T+1 (對答案，5碼選填):**")
    t1_cols = st.columns(5)
    t1_inputs = [t1_cols[i].text_input(f"T+1_{i+1}", key=f"t1_{i}") for i in range(5)]

st.write("**標記號碼 (擴充至9碼選填，報表中會加上【】外框):**")
m_cols = st.columns(9)
m_inputs = [m_cols[i].text_input(f"M{i+1}", key=f"m{i}") for i in range(9)]

st.header("2. 參數設定與比對條件")
params_col1, params_col2 = st.columns(2)
with params_col1:
    mode = st.selectbox("篩選模式:", ["中卦", "上卦", "上2卦", "下卦", "下2卦"])
    st.write("選擇星數:")
    s_cols = st.columns(4)
    s2 = s_cols[0].checkbox("2星", value=True)
    s3 = s_cols[1].checkbox("3星", value=True)
    s4 = s_cols[2].checkbox("4星", value=True)
    s5 = s_cols[3].checkbox("5星", value=True)
    selected_stars = [s for s, chk in zip([2, 3, 4, 5], [s2, s3, s4, s5]) if chk]
with params_col2:
    st.write("區域比對次數設定 (選填):")
    freq_a = st.number_input("落球順序 目標次數 (填0停用):", min_value=0, value=0, step=1)
    freq_b = st.number_input("大小順序 目標次數 (填0停用):", min_value=0, value=0, step=1)

st.markdown("---")

# ==========================================
# 核心邏輯引擎
# ==========================================
def get_valid_ints(str_list):
    return [int(x.strip()) for x in str_list if x.strip().isdigit()]

def fmt_num(num, markers):
    return f"【{num:02d}】" if num in markers else f"{num:02d}"

def compute_data(target_df, offset_val, inputs_list, exec_mode, is_strict):
    blocks = [] 
    offset_map = {"中卦": 0, "上卦": -1, "上2卦": -2, "下卦": 1, "下2卦": 2}
    offset = offset_map[exec_mode]
    target_len1 = 10 if exec_mode == "中卦" else 13
    target_len2 = 10 if exec_mode == "中卦" else 12

    for idx, n_val in enumerate(inputs_list):
        col_idx = idx + offset_val 
        matched_indices = target_df.index[target_df.iloc[:, col_idx] == n_val].tolist()
        block_data = []
        for i in matched_indices:
            target_i = i + offset
            if 0 <= target_i < len(target_df):
                row_vals = target_df.iloc[target_i, offset_val : offset_val+5].tolist()
                if exec_mode == "中卦" and n_val in row_vals: row_vals.remove(n_val) 
                if not is_strict: row_vals = sorted(row_vals)
                block_data.append(row_vals)
            else: block_data.append([]) 
        blocks.append(block_data)

    n1, n2, n3, n4, n5 = blocks
    valid_rows = []

    for b1, b2, b3, b4, b5 in zip(n1, n2, n3, n4, n5):
        if not (b1 and b2 and b3 and b4 and b5): continue 
        m1 = b1 + b2 + b3[:2] if exec_mode == "中卦" else b1 + b2 + b3[:3]
        m2 = b3[2:] + b4 + b5 if exec_mode == "中卦" else b3[3:] + b4 + b5
        g1 = list(dict.fromkeys(m1)) if is_strict else sorted(list(set(m1)))
        g2 = list(dict.fromkeys(m2)) if is_strict else sorted(list(set(m2)))
        if len(g1) == target_len1: valid_rows.append(g1)
        if len(g2) == target_len2: valid_rows.append(g2)
    return valid_rows

def analyze_combos(rows, stars):
    star_counters = {}
    for size in stars:
        counter = Counter()
        for r in rows:
            if len(r) >= size:
                counter.update([tuple(sorted(c)) for c in itertools.combinations(r, size)])
        star_counters[size] = counter
    return star_counters

# ==========================================
# 報表生成與 Excel 數據準備
# ==========================================
def build_reports(c_strict_raw, c_sorted_raw, stars, T, win_nums, markers, f_a, f_b, all_strict_rows, all_sorted_rows):
    win_set = set(win_nums) if win_nums else set()
    out = {f"A{k}": [] for k in range(1, 10)}
    out.update({"TL": [], "TR": [], "BL": [], "BR": []})
    out.update({"A5_TL": [], "A5_TR": [], "A5_B": []})
    
    t_text = f"T (主輸入): {', '.join(map(str, T))}"
    t1_text = f"T+1 (對答案): {', '.join(map(str, win_nums)) if win_nums else '無'}"
    m_text = f"標記號碼: {', '.join(map(str, markers)) if markers else '無'}"
    header_rows = [[t_text, t1_text, m_text], [""]]
    ex_data = {k: [row[:] for row in header_rows] for k in range(1, 11)}

    def fmt_combo(combo):
        s = f"({','.join([fmt_num(x, markers) for x in combo])})"
        if win_set:
            hit_count = len(set(combo).intersection(win_set))
            if hit_count == len(combo): s += "[★]"
            elif hit_count == len(combo) - 1: s += "[☆]"
        return s

    def build_combo_grid(title, combo_list, target_out, target_ex, cols=6):
        target_out.append(title); target_ex.append([title])
        r_str = ""; e_row = []
        for i, c in enumerate(combo_list):
            cs = fmt_combo(c) if isinstance(c, tuple) else c 
            r_str += f"{cs:<22}"
            e_row.append(cs)
            if (i+1)%cols == 0:
                target_out.append(r_str); target_ex.append(e_row)
                r_str = ""; e_row = []
        if e_row: target_out.append(r_str); target_ex.append(e_row)
        target_out.append(""); target_ex.append([""])

    # ★ 區域10: 組合特徵掃描 (使用 combo_target/noway)
    ex_data[10].append(["【組合特徵過濾】(左側命中，右側不出)"]); ex_data[10].append([""])
    for size in stars:
        s_dict = c_strict_raw.get(size, Counter()); o_dict = c_sorted_raw.get(size, Counter())
        all_combos = list(set(s_dict.keys()) | set(o_dict.keys()))
        
        target_marked = []; target_all = []; noway_marked = []; noway_all = []
        for c in all_combos:
            x = s_dict.get(c, 0); y = o_dict.get(c, 0)
            feat = (size, x, y)
            is_subset_m = set(c).issubset(markers) and len(markers) > 0
            
            if feat in combo_noway:
                noway_all.append(c)
                if is_subset_m: noway_marked.append(c)
            elif feat in combo_target:
                tot_occ, hit_occ = combo_target[feat]
                info_str = f"{fmt_combo(c)} | 星:{size} 落:{x} 大:{y} 總:{tot_occ} 命:{hit_occ}"
                target_all.append(c)
                if is_subset_m: target_marked.append(info_str)

        if target_marked:
            out["TL"].append(f"► {size}星 命中特徵 + 全為標記號碼:")
            ex_data[10].append([f"► {size}星 命中特徵 + 全為標記號碼:"])
            for txt in target_marked: 
                out["TL"].append(txt); ex_data[10].append([txt])
            out["TL"].append(""); ex_data[10].append([""])
        else:
            msg = f"► {size}星 無符合命中特徵之標記號碼"
            out["TL"].append(msg); out["TL"].append(""); ex_data[10].append([msg]); ex_data[10].append([""])

        if target_all: build_combo_grid(f"► {size}星 所有命中特徵組合:", target_all, out["BL"], ex_data[10], cols=6)
        else:
            msg = f"► {size}星 本次計算無符合之命中特徵組合"
            out["BL"].append(msg); out["BL"].append(""); ex_data[10].append([msg]); ex_data[10].append([""])
        
        if noway_marked:
            out["TR"].append(f"► {size}星 不出特徵 + 全為標記號碼:")
            ex_data[10].append([f"► {size}星 不出特徵 + 全為標記號碼:"])
            build_combo_grid("歷史尚未有出現經驗:", noway_marked, out["TR"], ex_data[10], cols=3)
        else:
            msg = f"► {size}星 無符合不出特徵之標記號碼"
            out["TR"].append(msg); out["TR"].append(""); ex_data[10].append([msg]); ex_data[10].append([""])

        if noway_all: build_combo_grid(f"► {size}星 所有不出特徵組合:", noway_all, out["BR"], ex_data[10], cols=6)
        else:
            msg = f"► {size}星 本次計算無符合之不出特徵組合"
            out["BR"].append(msg); out["BR"].append(""); ex_data[10].append([msg]); ex_data[10].append([""])

    # ★ 區域 5: 單碼特徵掃描 (使用 macro_target/noway)
    flat_str = [n for r in all_strict_rows for n in r]; flat_srt = [n for r in all_sorted_rows for n in r]
    tot_str = len(flat_str); cnt_str = Counter(flat_str)
    tot_srt = len(flat_srt); cnt_srt = Counter(flat_srt)

    t_nums = []; n_nums = []
    t_nums_dict = set(); n_nums_dict = set()
    
    for i in range(1, 40):
        x = cnt_str.get(i, 0); y = cnt_srt.get(i, 0)
        if (1, x, y) in macro_target:
            tot, hit = macro_target[(1, x, y)]
            t_nums.append((i, x, y, tot, hit))
            t_nums_dict.add(i)
        elif (1, x, y) in macro_noway:
            n_nums.append((i, x, y))
            n_nums_dict.add(i)

    out["A5_TL"].append("========== 🎯 命中特徵單碼 ==========")
    if t_nums:
        for num, x, y, tot, hit in t_nums: out["A5_TL"].append(f"【{num:02d}】 落:{x:<2} 大:{y:<2} | 總:{tot} 命:{hit}")
    else: out["A5_TL"].append("無符合之命中特徵單碼")

    out["A5_TR"].append("========== ❌ 不出特徵單碼 ==========")
    if n_nums:
        for num, x, y in n_nums: out["A5_TR"].append(f"【{num:02d}】 落:{x:<2} 大:{y:<2}")
    else: out["A5_TR"].append("無符合之不出特徵單碼")

    ex_data[5].append(["【🎯 命中特徵單碼】", "", "", "【❌ 不出特徵單碼】"])
    max_len = max(len(t_nums), len(n_nums))
    if max_len == 0: ex_data[5].append(["無", "", "", "無"])
    else:
        for i in range(max_len):
            r_t = f"【{t_nums[i][0]:02d}】 落:{t_nums[i][1]} 大:{t_nums[i][2]} | 總:{t_nums[i][3]} 命:{t_nums[i][4]}" if i < len(t_nums) else ""
            r_n = f"【{n_nums[i][0]:02d}】 落:{n_nums[i][1]} 大:{n_nums[i][2]}" if i < len(n_nums) else ""
            ex_data[5].append([r_t, "", "", r_n])
    ex_data[5].append([""])
    
    # 區域 5 下半部
    out["A5_B"].append([("========== 1~39 單碼總數量與百分比 ==========\n", "normal")])
    ex_data[5].append(["1~39 總計與百分比"])

    def build_num_stats(title, target_out, target_ex):
        target_out.append([(title + "\n", "normal")]); target_ex.append([title])
        target_out.append([(f"落球總數量: {tot_str} | 大小總數量: {tot_srt}\n", "normal")]); target_ex.append([f"落球總數量: {tot_str} | 大小總數量: {tot_srt}"])
        
        e_row = []
        for i in range(1, 40):
            c = cnt_str.get(i, 0) if "落球" in title else cnt_srt.get(i, 0)
            tot = tot_str if "落球" in title else tot_srt
            pct = f"{(c/tot*100) if tot>0 else 0:.1f}%"
            num_s = fmt_num(i, markers)
            
            tags = []
            if i in t_nums_dict: tags.append("target_hit")
            elif i in n_nums_dict: tags.append("noway_hit")
            if i in win_set: tags.append("t1_hit")
            if not tags: tags.append("normal")
            
            txt_part1 = f"{num_s:<6}"
            txt_part2 = f"{c:<5}{pct:<7}"
            
            target_out.append([(txt_part1, tuple(tags)), (txt_part2, "normal")])
            e_row.extend([num_s, c, pct])
            if i % 6 == 0:
                target_out.append([("\n", "normal")]); target_ex.append(e_row); e_row = []
        if e_row: target_out.append([("\n", "normal")]); target_ex.append(e_row)
        target_out.append([("\n", "normal")])

    build_num_stats("【落球順序】", out["A5_B"], ex_data[5])
    build_num_stats("【大小順序】", out["A5_B"], ex_data[5])

    # ★ 常規 Area 1~4, 6~9 (100%保留)
    for size in stars:
        s_dict = c_strict_raw.get(size, Counter()); o_dict = c_sorted_raw.get(size, Counter())
        s_freq = {}; o_freq = {}
        for c, cnt in s_dict.items(): s_freq.setdefault(cnt, []).append(c)
        for c, cnt in o_dict.items(): o_freq.setdefault(cnt, []).append(c)

        out["A1"].append(f"========== 🎯 {size} 星 命中分析 =========="); out["A2"].append(f"========== 🎯 {size} 星 命中分析 ==========")
        ex_data[1].append([f"[{size}星 命中組合]"]); ex_data[2].append([f"[{size}星 差一碼組合]"])
        
        if not win_set:
            out["A1"].append("未提供 T+1 答案"); out["A2"].append("未提供 T+1 答案")
            ex_data[1].append(["未提供 T+1 答案"]); ex_data[2].append(["未提供 T+1 答案"])
        else:
            s_hits = [c for c in s_dict if len(set(c).intersection(win_set)) == size]
            o_hits = [c for c in o_dict if len(set(c).intersection(win_set)) == size]
            out["A1"].append(f"【落球順序 ★全中】 共 {len(s_hits)} 組")
            for c in sorted(s_hits): out["A1"].append(f"出現 {s_dict[c]:>2} 次: {fmt_combo(c)}")
            ex_data[1].extend([[f"落球 出現 {s_dict[c]}次", fmt_combo(c)] for c in sorted(s_hits)])
            out["A2"].append(f"【大小順序 ★全中】 共 {len(o_hits)} 組")
            for c in sorted(o_hits): out["A2"].append(f"出現 {o_dict[c]:>2} 次: {fmt_combo(c)}")
            ex_data[1].extend([[f"大小 出現 {o_dict[c]}次", fmt_combo(c)] for c in sorted(o_hits)])

        out["A1"].append(""); out["A2"].append(""); ex_data[1].append([""]); ex_data[2].append([""])

        out["A3"].append(f"========== [ {size} 星 ] 落球順序 次數表 ==========")
        out["A4"].append(f"========== [ {size} 星 ] 大小順序 次數表 ==========")
        ex_data[3].append([f"[{size}星] 落球次數表"]); ex_data[4].append([f"[{size}星] 大小次數表"])

        def build_freq_table(freq_dict, target_out, target_ex):
            freq_list = sorted(freq_dict.keys())
            row_str = ""; ex_row = []; col_count = 0
            for f in freq_list:
                c_str = f"| 出現 {f:02d} 次 _____"
                v_str = f"| {len(freq_dict[f]):04d} 組 _____"
                row_str += f"{c_str:<18} {v_str:<16} "
                ex_row.extend([f"出現 {f} 次", f"{len(freq_dict[f])} 組"])
                col_count += 1
                if col_count == 3: 
                    target_out.append(row_str + "|"); target_ex.append(ex_row); row_str = ""; ex_row = []; col_count = 0
            if col_count > 0: target_out.append(row_str + "|"); target_ex.append(ex_row)
            target_out.append(""); target_ex.append([""])

        build_freq_table(s_freq, out["A3"], ex_data[3]); build_freq_table(o_freq, out["A4"], ex_data[4])

        out["A6"].append(f"========== 🎯 {size} 星 選擇次數 相異 ==========")
        out["A7"].append(f"========== 🎯 {size} 星 選擇次數 相同 ==========")
        ex_data[6].append([f"[{size}星] 相異組合"]); ex_data[7].append([f"[{size}星] 相同組合"])

        if f_a > 0 and f_b > 0:
            s_tgt = set(s_freq.get(f_a, [])); o_tgt = set(o_freq.get(f_b, []))
            diff_A = sorted(list(s_tgt - o_tgt)); diff_B = sorted(list(o_tgt - s_tgt)); same = sorted(list(s_tgt & o_tgt))
            out["A6"].append(f"► 落球獨有數量: {len(diff_A)} 組\n► 大小獨有數量: {len(diff_B)} 組\n")
            build_combo_grid(f"落球({f_a}次) 獨有:", diff_A, out["A6"], ex_data[6])
            build_combo_grid(f"大小({f_b}次) 獨有:", diff_B, out["A6"], ex_data[6])
            out["A7"].append(f"► 共同擁有數量: {len(same)} 組\n")
            build_combo_grid(f"兩者共同擁有:", same, out["A7"], ex_data[7])
        else:
            out["A6"].append("未設定比對次數\n"); out["A7"].append("未設定比對次數\n")
            ex_data[6].append(["未設定比對次數"]); ex_data[7].append(["未設定比對次數"])

        out["A8"].append(f"========== [ {size} 星 ] 落球順序 所有組合 ==========")
        out["A9"].append(f"========== [ {size} 星 ] 大小順序 所有組合 ==========")
        ex_data[8].append([f"[{size}星] 落球所有組合"]); ex_data[9].append([f"[{size}星] 大小所有組合"])
        for f in sorted(s_freq.keys(), reverse=True): build_combo_grid(f"出現 {f} 次:", sorted(s_freq[f]), out["A8"], ex_data[8])
        for f in sorted(o_freq.keys(), reverse=True): build_combo_grid(f"出現 {f} 次:", sorted(o_freq[f]), out["A9"], ex_data[9])

    return out, ex_data

# ==========================================
# 執行區與 UI 渲染
# ==========================================
if st.button("🚀 執行單筆運算與特徵比對", type="primary"):
    if df is None:
        st.warning("請等待或手動載入資料庫！")
        st.stop()
        
    T = get_valid_ints(t_inputs)
    T1 = get_valid_ints(t1_inputs)
    M = set(get_valid_ints(m_inputs))
    
    if len(set(T)) != 5: st.error("T 必須輸入 5 個不重複數字！"); st.stop()
    if len(T1) > 0 and len(set(T1)) != 5: st.error("T+1 如果有輸入，必須是 5 個不重複數字！"); st.stop()
    if not selected_stars: st.error("請至少選擇一種星數！"); st.stop()

    v_str = compute_data(df, data_offset, T, mode, True)
    v_srt = compute_data(df, data_offset, T, mode, False)
    c_str_raw = analyze_combos(v_str, selected_stars)
    c_srt_raw = analyze_combos(v_srt, selected_stars)
    
    txt_out, ex_data = build_reports(c_str_raw, c_srt_raw, selected_stars, T, T1, M, freq_a, freq_b, v_str, v_srt)
    
    # 打包 Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i in range(1, 11):
            ws_name = f'區域{i}' if i < 10 else '區域10_特徵過濾'
            ws = writer.book.add_worksheet(ws_name)
            for row_idx, row_data in enumerate(ex_data[i]):
                for col_idx, cell_data in enumerate(row_data):
                    ws.write(row_idx, col_idx, cell_data)
    excel_data = output.getvalue()
    
    dl_filename = f"{datetime.now().strftime('%Y%m%d')}_539_predict_{datetime.now().strftime('%H%M%S')}.xlsx"
    st.download_button(
        label=f"📥 點擊下載完整分析報表 (檔案: {dl_filename})",
        data=excel_data,
        file_name=dl_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    st.success("🎯 運算完成！雙引擎特徵提取完畢，請查閱下方報表。")

    # --- UI 渲染輔助 ---
    def render_area(data_lines): return "\n".join(data_lines)

    def render_html_area(data_tuples_list):
        html_str = ""
        for line in data_tuples_list:
            for text, tags in line:
                if isinstance(tags, str): tags = [tags]
                style = ""
                # UI 顏色優先順序
                if "target_hit" in tags: style += "color:#2E7D32; font-weight:bold; "
                elif "noway_hit" in tags: style += "color:#9E9E9E; text-decoration:line-through; "
                if "t1_hit" in tags: style += "color:#D32F2F; font-weight:bold; text-decoration:underline; "
                
                if style: html_str += f'<span style="{style}">{text}</span>'
                else: html_str += text
        return html_str

    # --- 分頁顯示 ---
    t1, t2, t3, t4, t5, t6 = st.tabs(["特徵過濾 (區10)", "單碼機率總計 (區5)", "命中與聽牌 (區1,2)", "出現次數統計 (區3,4)", "組合交叉比對 (區6,7)", "詳細組合清單 (區8,9)"])

    with t1: # 區10
        c10_1, c10_2 = st.columns(2)
        with c10_1:
            st.markdown(f'<div class="custom-scrollbar bg-feat-tl">【命中特徵 + 標記】\n{render_area(txt_out["TL"])}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="custom-scrollbar bg-feat-bl">【所有命中特徵】\n{render_area(txt_out["BL"])}</div>', unsafe_allow_html=True)
        with c10_2:
            st.markdown(f'<div class="custom-scrollbar bg-feat-tr">【不出特徵 + 標記】\n{render_area(txt_out["TR"])}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="custom-scrollbar bg-feat-br">【所有不出特徵】\n{render_area(txt_out["BR"])}</div>', unsafe_allow_html=True)

    with t2: # 區5
        c5_1, c5_2 = st.columns(2)
        with c5_1: st.markdown(f'<div class="custom-scrollbar bg-hit">{render_area(txt_out["A5_TL"])}</div>', unsafe_allow_html=True)
        with c5_2: st.markdown(f'<div class="custom-scrollbar bg-miss">{render_area(txt_out["A5_TR"])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="custom-scrollbar">【總表】綠色(命中) | 灰刪除線(不出) | 紅底線(T+1命中)\n{render_html_area(txt_out["A5_B"])}</div>', unsafe_allow_html=True)

    with t3: # 區1, 2
        c1, c2 = st.columns(2)
        with c1: st.markdown(f'<div class="custom-scrollbar">【區域1 落球順序】\n{render_area(txt_out["A1"])}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="custom-scrollbar">【區域2 大小順序】\n{render_area(txt_out["A2"])}</div>', unsafe_allow_html=True)

    with t4: # 區3, 4
        c3, c4 = st.columns(2)
        with c3: st.markdown(f'<div class="custom-scrollbar">【區域3 落球次數】\n{render_area(txt_out["A3"])}</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="custom-scrollbar">【區域4 大小次數】\n{render_area(txt_out["A4"])}</div>', unsafe_allow_html=True)

    with t5: # 區6, 7
        c6, c7 = st.columns(2)
        with c6: st.markdown(f'<div class="custom-scrollbar">【區域6 相異比對】\n{render_area(txt_out["A6"])}</div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="custom-scrollbar">【區域7 相同比對】\n{render_area(txt_out["A7"])}</div>', unsafe_allow_html=True)

    with t6: # 區8, 9
        c8, c9 = st.columns(2)
        with c8: st.markdown(f'<div class="custom-scrollbar">【區域8 落球詳細】\n{render_area(txt_out["A8"])}</div>', unsafe_allow_html=True)
        with c9: st.markdown(f'<div class="custom-scrollbar">【區域9 大小詳細】\n{render_area(txt_out["A9"])}</div>', unsafe_allow_html=True)
