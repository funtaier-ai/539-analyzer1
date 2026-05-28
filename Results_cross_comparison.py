import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import os
import io
from datetime import datetime
import numpy as np

# --- 頁面基本設定與全域 CSS ---
st.set_page_config(page_title="539 雙邏輯深度比對系統 (V3 雲端旗艦版)", layout="wide")

st.markdown("""
<style>
.custom-scrollbar {
    overflow-y: auto !important;
    overflow-x: auto !important;
    white-space: pre !important;  /* 強制不換行以保持表格對齊 */
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
    width: 10px !important;
    height: 10px !important;
    display: block !important;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: rgba(128, 128, 128, 0.1);
    border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(128, 128, 128, 0.5);
    border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: rgba(128, 128, 128, 0.8);
}
</style>
""", unsafe_allow_html=True)

st.title("📱 539 雙邏輯 (落球 vs 大小) 深度比對系統")

# --- 1. 資料庫載入區 ---
uploaded_file = st.file_uploader("上傳新的 CSV 資料庫 (自動偵測格式)", type=["csv"])
df = None
data_offset = 1

if uploaded_file is not None:
    try:
        try: temp_df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError: temp_df = pd.read_csv(uploaded_file, encoding="cp950")
        
        is_headless = False
        try:
            [float(c) for c in temp_df.columns]
            is_headless = True
        except ValueError:
            pass
            
        uploaded_file.seek(0) # 重置指標
        if is_headless:
            try: df = pd.read_csv(uploaded_file, encoding="utf-8", header=None)
            except: df = pd.read_csv(uploaded_file, encoding="cp950", header=None)
            data_offset = 0
        else:
            df = temp_df
            data_offset = 1 if len(df.columns) >= 6 else 0
            
        format_msg = "6欄(含日期)" if data_offset == 1 else "5欄(純號碼)"
        st.success(f"成功載入資料庫！(共 {len(df)} 筆, 格式: {format_msg})")
    except Exception as e:
        st.error(f"讀檔失敗: {e}")
else:
    st.info("請上傳 CSV 資料庫檔案。")

# --- 2. 輸入條件區 ---
st.header("1. 輸入條件區")
col_t, col_t1 = st.columns(2)

with col_t:
    st.write("**T (主輸入，5碼必填):**")
    t_cols = st.columns(5)
    t_inputs = [t_cols[i].text_input(f"T{i+1}", key=f"t{i}") for i in range(5)]

with col_t1:
    st.write("**T+1 (對答案，5碼選填):**")
    t1_cols = st.columns(5)
    t1_inputs = [t1_cols[i].text_input(f"T+1_{i+1}", key=f"t1_{i}") for i in range(5)]

st.write("**標記號碼 (6碼選填，報表中會加上【】外框):**")
m_cols = st.columns(6)
m_inputs = [m_cols[i].text_input(f"M{i+1}", key=f"m{i}") for i in range(6)]

# --- 3. 參數設定區 ---
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
    st.write("區域比對次數設定:")
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
        block_data = []
        matched_indices = target_df.index[target_df.iloc[:, col_idx] == n_val].tolist()
        
        for i in matched_indices:
            target_i = i + offset
            if 0 <= target_i < len(target_df):
                row_vals = target_df.iloc[target_i, offset_val : offset_val+5].tolist()
                if exec_mode == "中卦":
                    if n_val in row_vals: row_vals.remove(n_val) 
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
def build_reports(c_strict, c_sorted, stars, T, win_nums, markers, f_a, f_b, all_strict_rows, all_sorted_rows):
    win_set = set(win_nums) if win_nums else set()
    out = {f"A{k}": [] for k in range(1, 10)}
    
    t_text = f"T (主輸入): {', '.join(map(str, T))}"
    t1_text = f"T+1 (對答案): {', '.join(map(str, win_nums)) if win_nums else '無'}"
    m_text = f"標記號碼: {', '.join(map(str, markers)) if markers else '無'}"
    header_rows = [[t_text, t1_text, m_text], [""]]
    ex_data = {k: [row[:] for row in header_rows] for k in range(1, 10)}

    def fmt_combo(combo):
        s = f"({','.join([fmt_num(x, markers) for x in combo])})"
        if win_set:
            hit_count = len(set(combo).intersection(win_set))
            if hit_count == len(combo): s += "[★]"
            elif hit_count == len(combo) - 1: s += "[☆]"
        return s

    def build_combo_grid(title, combo_list, target_out, target_ex):
        target_out.append(title); target_ex.append([title])
        r_str = ""; e_row = []
        for i, c in enumerate(combo_list):
            cs = fmt_combo(c)
            r_str += f"{cs:<20}"
            e_row.append(cs)
            if (i+1)%6 == 0:
                target_out.append(r_str); target_ex.append(e_row)
                r_str = ""; e_row = []
        if e_row: target_out.append(r_str); target_ex.append(e_row)
        target_out.append(""); target_ex.append([""])

    for size in stars:
        s_dict = c_strict.get(size, Counter())
        o_dict = c_sorted.get(size, Counter())
        s_freq = {}; o_freq = {}
        for c, cnt in s_dict.items(): s_freq.setdefault(cnt, []).append(c)
        for c, cnt in o_dict.items(): o_freq.setdefault(cnt, []).append(c)

        # --- 區域1 & 區域2 ---
        out["A1"].append(f"========== 🎯 {size} 星 命中分析 =========="); out["A2"].append(f"========== 🎯 {size} 星 命中分析 ==========")
        ex_data[1].append([f"[{size}星 命中組合]"]); ex_data[2].append([f"[{size}星 差一碼組合]"])
        
        if not win_set:
            out["A1"].append("未提供 T+1 答案"); out["A2"].append("未提供 T+1 答案")
        else:
            s_hits = [c for c in s_dict if len(set(c).intersection(win_set)) == size]
            o_hits = [c for c in o_dict if len(set(c).intersection(win_set)) == size]
            s_m1 = [c for c in s_dict if len(set(c).intersection(win_set)) == size - 1]
            o_m1 = [c for c in o_dict if len(set(c).intersection(win_set)) == size - 1]
            
            out["A1"].append(f"【落球順序 ★全中】 共 {len(s_hits)} 組")
            for c in sorted(s_hits): out["A1"].append(f"出現 {s_dict[c]:>2} 次: {fmt_combo(c)}")
            ex_data[1].extend([[f"落球 出現 {s_dict[c]}次", fmt_combo(c)] for c in sorted(s_hits)])
            
            out["A2"].append(f"【大小順序 ★全中】 共 {len(o_hits)} 組")
            for c in sorted(o_hits): out["A2"].append(f"出現 {o_dict[c]:>2} 次: {fmt_combo(c)}")
            ex_data[1].extend([[f"大小 出現 {o_dict[c]}次", fmt_combo(c)] for c in sorted(o_hits)])

        out["A1"].append(""); out["A2"].append("")

        # --- 區域3 & 區域4 ---
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
                    target_out.append(row_str + "|"); target_ex.append(ex_row)
                    row_str = ""; ex_row = []; col_count = 0
            if col_count > 0: target_out.append(row_str + "|"); target_ex.append(ex_row)
            target_out.append(""); target_ex.append([""])

        build_freq_table(s_freq, out["A3"], ex_data[3])
        build_freq_table(o_freq, out["A4"], ex_data[4])

        # --- 區域6 & 7：比對 ---
        out["A6"].append(f"========== 🎯 {size} 星 選擇次數 相異 ==========")
        out["A7"].append(f"========== 🎯 {size} 星 選擇次數 相同 ==========")
        ex_data[6].append([f"[{size}星] 相異組合"]); ex_data[7].append([f"[{size}星] 相同組合"])

        if f_a > 0 and f_b > 0:
            s_tgt = set(s_freq.get(f_a, [])); o_tgt = set(o_freq.get(f_b, []))
            diff_A = sorted(list(s_tgt - o_tgt)); diff_B = sorted(list(o_tgt - s_tgt))
            same = sorted(list(s_tgt & o_tgt))
            out["A6"].append(f"► 落球獨有數量: {len(diff_A)} 組\n► 大小獨有數量: {len(diff_B)} 組\n")
            build_combo_grid(f"落球({f_a}次) 獨有:", diff_A, out["A6"], ex_data[6])
            build_combo_grid(f"大小({f_b}次) 獨有:", diff_B, out["A6"], ex_data[6])
            out["A7"].append(f"► 共同擁有數量: {len(same)} 組\n")
            build_combo_grid(f"兩者共同擁有:", same, out["A7"], ex_data[7])
        else:
            out["A6"].append("未設定比對次數\n"); out["A7"].append("未設定比對次數\n")

        # --- 區域8 & 9：所有清單 ---
        out["A8"].append(f"========== [ {size} 星 ] 落球順序 所有組合 ==========")
        out["A9"].append(f"========== [ {size} 星 ] 大小順序 所有組合 ==========")
        ex_data[8].append([f"[{size}星] 落球所有組合"]); ex_data[9].append([f"[{size}星] 大小所有組合"])
        for f in sorted(s_freq.keys(), reverse=True): build_combo_grid(f"出現 {f} 次:", sorted(s_freq[f]), out["A8"], ex_data[8])
        for f in sorted(o_freq.keys(), reverse=True): build_combo_grid(f"出現 {f} 次:", sorted(o_freq[f]), out["A9"], ex_data[9])

    # --- 區域5：1~39 總計與百分比 (帶 HTML Tag 格式) ---
    out["A5"].append([("========== 1~39 單碼總數量與百分比 ==========\n", "normal")])
    ex_data[5].append(["1~39 總計與百分比"])

    def build_num_stats(title, all_r, target_out, target_ex):
        target_out.append([(title + "\n", "normal")]); target_ex.append([title])
        flat = [n for r in all_r for n in r]
        tot = len(flat); cnt = Counter(flat)
        target_out.append([(f"總數量: {tot}\n", "normal")]); target_ex.append([f"總數量: {tot}"])
        
        e_row = []
        for i in range(1, 40):
            c = cnt.get(i, 0)
            pct = f"{(c/tot*100) if tot>0 else 0:.1f}%"
            num_s = fmt_num(i, markers)
            
            is_t1_hit = (i in win_set)
            tag = "t1_hit" if is_t1_hit else "normal"
            
            txt_part1 = f"{num_s:<6}"
            txt_part2 = f"{c:<5}{pct:<7}"
            
            target_out.append([(txt_part1, tag), (txt_part2, "normal")])
            e_row.extend([num_s, c, pct])
            
            if i % 6 == 0:
                target_out.append([("\n", "normal")]); target_ex.append(e_row)
                e_row = []
        if e_row: target_out.append([("\n", "normal")]); target_ex.append(e_row)
        target_out.append([("\n", "normal")])

    build_num_stats("【落球順序】", all_strict_rows, out["A5"], ex_data[5])
    build_num_stats("【大小順序】", all_sorted_rows, out["A5"], ex_data[5])

    return out, ex_data

# ==========================================
# 執行區與 UI 渲染
# ==========================================
if st.button("🚀 執行單筆運算比對", type="primary"):
    if df is None:
        st.warning("請先載入資料庫！")
        st.stop()
        
    T = get_valid_ints(t_inputs)
    T1 = get_valid_ints(t1_inputs)
    M = set(get_valid_ints(m_inputs))
    
    if len(set(T)) != 5:
        st.error("T 必須輸入5個不重複數字！")
        st.stop()
    if len(T1) > 0 and len(set(T1)) != 5:
        st.error("T+1 如果有輸入，必須是5個不重複數字！")
        st.stop()
    if not selected_stars:
        st.error("請至少選擇一種星數！")
        st.stop()

    # 計算邏輯
    v_str = compute_data(df, data_offset, T, mode, True)
    v_srt = compute_data(df, data_offset, T, mode, False)
    c_str = analyze_combos(v_str, selected_stars)
    c_srt = analyze_combos(v_srt, selected_stars)
    
    txt_out, ex_data = build_reports(c_str, c_srt, selected_stars, T, T1, M, freq_a, freq_b, v_str, v_srt)
    
    # --- 記憶體打包 Excel 準備下載 ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i in range(1, 10):
            ws = writer.book.add_worksheet(f'區域{i}')
            for row_idx, row_data in enumerate(ex_data[i]):
                for col_idx, cell_data in enumerate(row_data):
                    ws.write(row_idx, col_idx, cell_data)
    excel_data = output.getvalue()
    
    current_time = datetime.now().strftime("%Y%m%d")
    ts_str = datetime.now().strftime("%H%M%S")
    dynamic_filename = f"{current_time}_539_predict_{ts_str}.xlsx"

    st.download_button(
        label=f"📥 點擊下載完整分析報表 (將儲存為 {dynamic_filename})",
        data=excel_data,
        file_name=dynamic_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("運算完成！請查閱下方報表。")

    # --- UI 渲染輔助 ---
    def render_area(data_lines):
        return "\n".join(data_lines)

    def render_html_area(data_tuples_list):
        html_str = ""
        for line in data_tuples_list:
            for text, tag in line:
                if tag == "t1_hit":
                    html_str += f'<span style="color:#D32F2F; font-weight:bold; text-decoration:underline;">{text}</span>'
                else:
                    html_str += text
        return html_str

    # --- 5個分頁顯示 ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["命中與聽牌 (區1,2)", "出現次數統計 (區3,4)", "單碼機率總計 (區5)", "組合交叉比對 (區6,7)", "詳細組合清單 (區8,9)"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1: st.markdown(f'<div class="custom-scrollbar">【區域1 落球順序】\n{render_area(txt_out["A1"])}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="custom-scrollbar">【區域2 大小順序】\n{render_area(txt_out["A2"])}</div>', unsafe_allow_html=True)

    with tab2:
        c3, c4 = st.columns(2)
        with c3: st.markdown(f'<div class="custom-scrollbar">【區域3 落球次數】\n{render_area(txt_out["A3"])}</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="custom-scrollbar">【區域4 大小次數】\n{render_area(txt_out["A4"])}</div>', unsafe_allow_html=True)

    with tab3:
        # 區域 5 使用自製 HTML 來渲染顏色標記
        st.markdown(f'<div class="custom-scrollbar">【區域5 單碼總計】\n{render_html_area(txt_out["A5"])}</div>', unsafe_allow_html=True)

    with tab4:
        c6, c7 = st.columns(2)
        with c6: st.markdown(f'<div class="custom-scrollbar">【區域6 相異比對】\n{render_area(txt_out["A6"])}</div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="custom-scrollbar">【區域7 相同比對】\n{render_area(txt_out["A7"])}</div>', unsafe_allow_html=True)

    with tab5:
        c8, c9 = st.columns(2)
        with c8: st.markdown(f'<div class="custom-scrollbar">【區域8 落球詳細】\n{render_area(txt_out["A8"])}</div>', unsafe_allow_html=True)
        with c9: st.markdown(f'<div class="custom-scrollbar">【區域9 大小詳細】\n{render_area(txt_out["A9"])}</div>', unsafe_allow_html=True)
