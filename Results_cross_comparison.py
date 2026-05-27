import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import os
import io

# --- 頁面基本設定與全域 CSS ---
st.set_page_config(page_title="539 雙邏輯比對系統", layout="wide")

st.markdown("""
<style>
.custom-scroll-box {
    height: 650px;
    overflow-y: scroll !important;
    overflow-x: hidden;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: "Consolas", "Courier New", monospace !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 15px;
    border: 1px solid rgba(128, 128, 128, 0.4);
    border-radius: 8px;
    background-color: rgba(128, 128, 128, 0.05);
}

.custom-scroll-box::-webkit-scrollbar {
    width: 14px !important;
    display: block !important;
}
.custom-scroll-box::-webkit-scrollbar-track {
    background: rgba(128, 128, 128, 0.1);
    border-left: 1px solid rgba(128, 128, 128, 0.3);
}
.custom-scroll-box::-webkit-scrollbar-thumb {
    background: rgba(128, 128, 128, 0.5);
    border-radius: 10px;
    border: 3px solid transparent;
    background-clip: content-box;
}
.custom-scroll-box::-webkit-scrollbar-thumb:hover {
    background-color: rgba(128, 128, 128, 0.8);
}
</style>
""", unsafe_allow_html=True)

st.title("📱 539 雙邏輯 (落球 vs 大小) 深度比對系統")

# --- 1. 資料庫載入區 ---
uploaded_file = st.file_uploader("上傳新的 CSV 資料庫 (若不選則尋找預設檔案 539_2007.csv)", type=["csv"])
df = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="cp950")
    st.success(f"成功載入上傳的資料庫！(共 {len(df)} 筆)")
else:
    default_file = "539_2007.csv"
    if os.path.exists(default_file):
        try:
            df = pd.read_csv(default_file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(default_file, encoding="cp950")
        st.info(f"已自動載入預設檔案：{default_file} (共 {len(df)} 筆)")
    else:
        st.error("找不到資料庫！請上傳 CSV 檔案。")

# --- 2. 號碼輸入區 ---
st.header("1. 輸入篩選條件")
st.write("**T-1: 輸入5個不重複數字 (1~39) - 必填**")
cols = st.columns(5)
n_inputs = []
labels = ["n1 (B欄)", "n2 (C欄)", "n3 (D欄)", "n4 (E欄)", "n5 (F欄)"]
for i in range(5):
    val = cols[i].number_input(labels[i], min_value=1, max_value=39, step=1, value=None, key=f"n{i}")
    n_inputs.append(val)

st.write("**T: 開獎號碼 (用於比對對獎) - 選填**")
win_cols = st.columns(5)
win_inputs = []
for i in range(5):
    w_val = win_cols[i].number_input(f"開獎 {i+1}", min_value=1, max_value=39, step=1, value=None, key=f"w{i}")
    win_inputs.append(w_val)

# --- 3. 參數設定區 (新增相似度配對選項) ---
params_col1, params_col2, params_col3 = st.columns(3)
with params_col1:
    mode = st.selectbox("選擇篩選模式:", ["中卦", "上卦", "上2卦", "下卦", "下2卦"])
with params_col2:
    st.write("選擇星數:")
    s_cols = st.columns(4)
    s2 = s_cols[0].checkbox("2星", value=True)
    s3 = s_cols[1].checkbox("3星", value=True)
    s4 = s_cols[2].checkbox("4星", value=True)
    s5 = s_cols[3].checkbox("5星", value=True)
    selected_stars = [s for s, chk in zip([2, 3, 4, 5], [s2, s3, s4, s5]) if chk]
with params_col3:
    st.write("跨邏輯相似度配對 (A vs B):")
    d_cols = st.columns(4)
    d0 = d_cols[0].checkbox("相同", value=False)
    d1 = d_cols[1].checkbox("差1碼", value=False)
    d2 = d_cols[2].checkbox("差2碼", value=False)
    d3 = d_cols[3].checkbox("差3碼", value=False)
    selected_diffs = [i for i, chk in enumerate([d0, d1, d2, d3]) if chk]

# ==========================================
# 核心邏輯引擎
# ==========================================
def compute_data(df_data, inputs_list, exec_mode, is_strict_drop_order):
    blocks = [] 
    offset_map = {"中卦": 0, "上卦": -1, "上2卦": -2, "下卦": 1, "下2卦": 2}
    offset = offset_map[exec_mode]

    for idx, n_val in enumerate(inputs_list):
        col_idx = idx + 1 
        block_data = []
        matched_indices = df_data.index[df_data.iloc[:, col_idx] == n_val].tolist()
        
        for i in matched_indices:
            target_i = i + offset
            if 0 <= target_i < len(df_data):
                row_vals = df_data.iloc[target_i, 1:6].tolist()
                
                if exec_mode == "中卦":
                    if n_val in row_vals:
                        row_vals.remove(n_val) 
                    if not is_strict_drop_order:
                        row_vals = sorted(row_vals)
                    block_data.append(row_vals)
                else:
                    if not is_strict_drop_order:
                        row_vals = sorted(row_vals)
                    block_data.append(row_vals)
        blocks.append(block_data)

    n1_data, n2_data, n3_data, n4_data, n5_data = blocks

    group1_merged = []
    for b1, b2, b3 in zip(n1_data, n2_data, n3_data):
        merged = b1 + b2 + b3[:2] if exec_mode == "中卦" else b1 + b2 + b3[:3]
        if is_strict_drop_order:
            group1_merged.append(list(dict.fromkeys(merged)))
        else:
            group1_merged.append(sorted(list(set(merged))))

    group2_merged = []
    for b3, b4, b5 in zip(n3_data, n4_data, n5_data):
        merged = b3[2:] + b4 + b5 if exec_mode == "中卦" else b3[3:] + b4 + b5
        if is_strict_drop_order:
            group2_merged.append(list(dict.fromkeys(merged)))
        else:
            group2_merged.append(sorted(list(set(merged))))

    return group1_merged + group2_merged

# ==========================================
# 報表產生器 (UI 顯示)
# ==========================================
def generate_method_report(method_name, all_valid_rows, stars, win_nums):
    if not all_valid_rows:
        return f"【 {method_name} 】\n此條件下無有效行數產生。", {}

    win_set = set(win_nums) if win_nums else set()
    flat_nums = [n for row in all_valid_rows for n in row]
    total_nums_count = len(flat_nums)
    num_counts = Counter(flat_nums)
    
    freq_to_nums = {}
    for i in range(1, 40):
        freq = num_counts.get(i, 0)
        freq_to_nums.setdefault(freq, []).append(i)

    out = []
    out.append(f"【 {method_name}：1星(單碼) 數據總表 】")
    out.append(f"總計產出數字數量: {total_nums_count}\n")
    
    out.append("[ 表格一：單碼出現次數排行 (由高至低) ]")
    out.append("次數 | 號碼名單")
    out.append("-" * 55)
    for freq in sorted(freq_to_nums.keys(), reverse=True):
        nums = freq_to_nums[freq]
        nums_str = " ".join([f"({n:02d})" for n in sorted(nums)])
        out.append(f" {freq:>2} | {nums_str}")
    
    out.append("\n[ 表格二：01~39 各號碼詳細總數與佔比 ]")
    line_str = ""
    for i in range(1, 40):
        c = num_counts.get(i, 0)
        ratio = (c / total_nums_count * 100) if total_nums_count > 0 else 0
        line_str += f"({i:02d}) {c:>3}次({ratio:>5.2f}%) | "
        if i % 3 == 0: 
            out.append(line_str)
            line_str = ""
    if line_str: out.append(line_str)

    out.append("="*55)
    out.append(f"【 {method_name}：命中與次數總表 】")
    star_counters = {}
    
    for size in stars:
        counter = Counter()
        for row in all_valid_rows:
            if len(row) >= size:
                combos = list(itertools.combinations(row, size))
                normalized_combos = [tuple(sorted(c)) for c in combos]
                counter.update(normalized_combos)
        star_counters[size] = counter
        
        out.append(f"\n--- [ {size} 星組合 ] ---")
        if not counter:
            out.append("無數據。")
            continue
            
        freq_dict = {}
        for combo, count in counter.items():
            freq_dict.setdefault(count, []).append(combo)
            
        for count in sorted(freq_dict.keys(), reverse=True):
            combos = freq_dict[count]
            hits_full, hits_miss_one = [], []
            
            if win_set:
                for c in combos:
                    match_count = len(set(c).intersection(win_set))
                    if match_count == size:
                        hits_full.append(c)
                    elif match_count == size - 1:
                        hits_miss_one.append(c)
            
            out.append(f"▶ 出現 {count:>2} 次: 共有 {len(combos):>4} 組")
            if not win_set:
                out.append("　 １. (未輸入開獎號碼，無法對獎)")
            else:
                str_full = " ".join([f"({','.join([f'{x:02d}' for x in h])})" for h in hits_full]) if hits_full else ""
                out.append(f"　 １. [★全中 {len(hits_full):>2} 組]: {str_full}" if hits_full else "　 １. [★全中  0 組]")
                
                str_m1 = " ".join([f"({','.join([f'{x:02d}' for x in h])})" for h in hits_miss_one]) if hits_miss_one else ""
                out.append(f"　 ２. [☆差一碼 {len(hits_miss_one):>2} 組]: {str_m1}" if hits_miss_one else "　 ２. [☆差一碼  0 組]")

    out.append("="*55)
    out.append(f"【 {method_name}：以下為詳細組合名單 】\n")
    
    for size in stars:
        out.append(f"[{size}星 詳細列表]")
        counter = star_counters[size]
        freq_dict = {}
        for combo, count in counter.items():
            freq_dict.setdefault(count, []).append(combo)
            
        for count in sorted(freq_dict.keys(), reverse=True):
            combo_list = sorted(freq_dict[count])
            out.append(f"出現 {count} 次:")
            
            line_str = ""
            for idx, combo in enumerate(combo_list):
                formatted = f"({','.join([f'{x:02d}' for x in combo])})"
                line_str += f"　{formatted} "
                if (idx + 1) % 4 == 0: 
                    out.append(line_str)
                    line_str = ""
            if line_str: out.append(line_str)
        out.append("-" * 40)

    return "\n".join(out), star_counters

# ==========================================
# 差異與命中比對產生器 (加入同次數相似度比對)
# ==========================================
def generate_comparison_report(counters_strict, counters_sorted, stars, win_nums, selected_diffs):
    win_set = set(win_nums) if win_nums else set()
    out = []
    out.append("【 雙邏輯深度比對分析 】\n")

    for size in stars:
        out.append(f"========== 🎯 {size} 星 比對 ==========")
        cA = counters_strict.get(size, Counter())
        cB = counters_sorted.get(size, Counter())

        # 1. 獨有組合
        out.append("【 １. 每個出現次數的差異組合 (各自獨有) 】")
        all_freqs = sorted(list(set(cA.values()) | set(cB.values())), reverse=True)
        has_diff = False
        
        for freq in all_freqs:
            combos_A = {c for c, count in cA.items() if count == freq}
            combos_B = {c for c, count in cB.items() if count == freq}

            only_A = sorted(list(combos_A - combos_B))
            only_B = sorted(list(combos_B - combos_A))

            if only_A or only_B:
                has_diff = True
                out.append(f"▶ 出現 {freq} 次的差異：")
                if only_A:
                    s = " ".join([f"({','.join([f'{x:02d}' for x in c])})" for c in only_A])
                    out.append(f"　[落球順序] 獨有 ({len(only_A)}組):\n　{s}")
                if only_B:
                    s = " ".join([f"({','.join([f'{x:02d}' for x in c])})" for c in only_B])
                    out.append(f"　[大小順序] 獨有 ({len(only_B)}組):\n　{s}")
                    
        if not has_diff:
            out.append("✅ 兩者在所有次數分佈上【完全無差異】。")

        # 2. 跨邏輯相似度配對
        if selected_diffs:
            out.append("\n【 ２. 同次數組合 相似度配對 (A ➜ B) 】")
            for freq in all_freqs:
                combos_A = [c for c, count in cA.items() if count == freq]
                combos_B = [c for c, count in cB.items() if count == freq]
                
                if not combos_A or not combos_B:
                    continue
                
                freq_has_output = False
                for diff_target in selected_diffs:
                    if diff_target > size: continue
                    
                    pairs = []
                    for ca in sorted(combos_A):
                        set_ca = set(ca)
                        matches = []
                        for cb in sorted(combos_B):
                            if size - len(set_ca.intersection(cb)) == diff_target:
                                matches.append(cb)
                        if matches:
                            pairs.append((ca, matches))
                    
                    if pairs:
                        if not freq_has_output:
                            out.append(f"--- [ 出現 {freq} 次 ] ---")
                            freq_has_output = True
                        
                        out.append(f"▶ 相差 {diff_target} 碼配對:")
                        for ca, cbs in pairs:
                            ca_str = f"({','.join([f'{x:02d}' for x in ca])})"
                            cb_strs = " ".join([f"({','.join([f'{x:02d}' for x in cb])})" for cb in cbs])
                            out.append(f"　[落球] {ca_str} ➜ [大小] {cb_strs}")

        # 3. 命中與聽牌
        out.append("\n【 ３. 命中與聽牌(差一碼)組合 比對 】")
        if not win_set:
            out.append("⚠️ 未輸入 T (開獎號碼)，無法比對命中。")
        else:
            hits_A = {c for c in cA.keys() if len(set(c).intersection(win_set)) == size}
            hits_B = {c for c in cB.keys() if len(set(c).intersection(win_set)) == size}
            all_hits = sorted(list(hits_A | hits_B))
            
            m1_A = {c for c in cA.keys() if len(set(c).intersection(win_set)) == size - 1}
            m1_B = {c for c in cB.keys() if len(set(c).intersection(win_set)) == size - 1}
            all_m1 = sorted(list(m1_A | m1_B))

            if not all_hits and not all_m1:
                out.append("❌ 皆無任何全中或聽牌組合。")
            
            if all_hits:
                out.append("[ ★ 全中組合比對 ]")
                for h in all_hits:
                    h_str = f"({','.join([f'{x:02d}' for x in h])})"
                    freq_A = cA.get(h, 0)
                    freq_B = cB.get(h, 0)
                    out.append(f"★ {h_str}: [落球] {freq_A} 次 vs [大小] {freq_B} 次")
            
            if all_m1:
                out.append("\n[ ☆ 差一碼(聽牌) 組合比對 ]")
                for m in all_m1:
                    m_str = f"({','.join([f'{x:02d}' for x in m])})"
                    freq_A = cA.get(m, 0)
                    freq_B = cB.get(m, 0)
                    out.append(f"☆ {m_str}: [落球] {freq_A} 次 vs [大小] {freq_B} 次")
        out.append("\n")
        
    return "\n".join(out)

# ==========================================
# Excel 匯出處理引擎
# ==========================================
def format_excel_sheet(worksheet, data_list):
    row_idx = 1
    for group in data_list:
        if group["header"]:
            worksheet.write(row_idx, 0, group["header"])
            row_idx += 1
        
        combos = group.get("combos", [])
        if combos:
            col_idx = 0
            for combo in combos:
                worksheet.write(row_idx, col_idx, combo)
                col_idx += 1
                if col_idx == 6:
                    col_idx = 0
                    row_idx += 1
            if col_idx != 0:
                row_idx += 1 
        row_idx += 1

def prepare_excel_data(all_valid_rows, counters, stars, win_nums):
    sheet_data = []
    win_set = set(win_nums) if win_nums else set()

    if not all_valid_rows:
        sheet_data.append({"header": "此條件下無有效行數產生", "combos": []})
        return sheet_data

    flat_nums = [n for row in all_valid_rows for n in row]
    total_nums = len(flat_nums)
    num_counts = Counter(flat_nums)
    
    freq_to_nums = {}
    for i in range(1, 40):
        freq = num_counts.get(i, 0)
        freq_to_nums.setdefault(freq, []).append(i)

    sheet_data.append({"header": "【 1星(單碼) 數據總表 】", "combos": []})
    sheet_data.append({"header": f"總計產出數字數量: {total_nums}", "combos": []})
    
    sheet_data.append({"header": "[ 單碼出現次數排行 (由高至低) ]", "combos": []})
    for freq in sorted(freq_to_nums.keys(), reverse=True):
        nums_str = " ".join([f"({n:02d})" for n in sorted(freq_to_nums[freq])])
        sheet_data.append({"header": f"出現 {freq} 次:", "combos": [nums_str]})
        
    sheet_data.append({"header": "[ 01~39 各號碼詳細總數與佔比 ]", "combos": []})
    ratio_list = []
    for i in range(1, 40):
        c = num_counts.get(i, 0)
        ratio = (c / total_nums * 100) if total_nums > 0 else 0
        ratio_list.append(f"({i:02d}) {c}次({ratio:.2f}%)")
    sheet_data.append({"header": "", "combos": ratio_list})

    for size in stars:
        sheet_data.append({"header": f"========== [{size}星 詳細列表] ==========", "combos": []})
        counter = counters.get(size, Counter())
        
        freq_dict = {}
        for combo, count in counter.items():
            freq_dict.setdefault(count, []).append(combo)
            
        for count in sorted(freq_dict.keys(), reverse=True):
            combo_list = sorted(freq_dict[count])
            
            formatted_combos = []
            for c in combo_list:
                c_str = f"({','.join([f'{x:02d}' for x in c])})"
                if win_set:
                    match_count = len(set(c).intersection(win_set))
                    if match_count == size:
                        c_str += " [★全中]"
                    elif match_count == size - 1:
                        c_str += " [☆差一碼]"
                formatted_combos.append(c_str)
                
            sheet_data.append({
                "header": f"出現 {count} 次:",
                "combos": formatted_combos
            })
            
    return sheet_data

def prepare_comparison_excel_data(counters_strict, counters_sorted, stars, win_nums, selected_diffs):
    sheet_data = []
    win_set = set(win_nums) if win_nums else set()

    for size in stars:
        sheet_data.append({"header": f"========== 🎯 {size} 星 比對 ==========", "combos": []})
        cA = counters_strict.get(size, Counter())
        cB = counters_sorted.get(size, Counter())
        all_freqs = sorted(list(set(cA.values()) | set(cB.values())), reverse=True)

        # 1. 差異比較
        sheet_data.append({"header": "【 １. 每個出現次數的差異組合 (各自獨有) 】", "combos": []})
        has_diff = False
        for freq in all_freqs:
            combos_A = {c for c, count in cA.items() if count == freq}
            combos_B = {c for c, count in cB.items() if count == freq}
            only_A = sorted(list(combos_A - combos_B))
            only_B = sorted(list(combos_B - combos_A))

            if only_A or only_B:
                has_diff = True
                sheet_data.append({"header": f"▶ 出現 {freq} 次的差異：", "combos": []})
                if only_A:
                    formatted = [f"({','.join([f'{x:02d}' for x in c])})" for c in only_A]
                    sheet_data.append({"header": f"　[落球順序] 獨有 ({len(only_A)}組):", "combos": formatted})
                if only_B:
                    formatted = [f"({','.join([f'{x:02d}' for x in c])})" for c in only_B]
                    sheet_data.append({"header": f"　[大小順序] 獨有 ({len(only_B)}組):", "combos": formatted})
        if not has_diff:
            sheet_data.append({"header": "✅ 兩者完全無差異", "combos": []})

        # 2. 相似度配對
        if selected_diffs:
            sheet_data.append({"header": "【 ２. 同次數組合 相似度配對 (A ➜ B) 】", "combos": []})
            for freq in all_freqs:
                combos_A = [c for c, count in cA.items() if count == freq]
                combos_B = [c for c, count in cB.items() if count == freq]
                
                if not combos_A or not combos_B: continue
                
                freq_has_output = False
                for diff_target in selected_diffs:
                    if diff_target > size: continue
                    pairs = []
                    for ca in sorted(combos_A):
                        set_ca = set(ca)
                        matches = []
                        for cb in sorted(combos_B):
                            if size - len(set_ca.intersection(cb)) == diff_target:
                                matches.append(cb)
                        if matches:
                            pairs.append((ca, matches))
                    
                    if pairs:
                        if not freq_has_output:
                            sheet_data.append({"header": f"--- [ 出現 {freq} 次 ] ---", "combos": []})
                            freq_has_output = True
                        
                        sheet_data.append({"header": f"▶ 相差 {diff_target} 碼配對:", "combos": []})
                        for ca, cbs in pairs:
                            ca_str = f"({','.join([f'{x:02d}' for x in ca])})"
                            cb_strs = [f"({','.join([f'{x:02d}' for x in cb])})" for cb in cbs]
                            sheet_data.append({"header": f"　[落球] {ca_str} ➜ [大小]:", "combos": cb_strs})

        # 3. 命中與聽牌
        sheet_data.append({"header": "【 ３. 命中與聽牌(差一碼) 比對 】", "combos": []})
        if not win_set:
            sheet_data.append({"header": "⚠️ 未輸入 T (開獎號碼)，無法比對命中。", "combos": []})
        else:
            hits_A = {c for c in cA.keys() if len(set(c).intersection(win_set)) == size}
            hits_B = {c for c in cB.keys() if len(set(c).intersection(win_set)) == size}
            all_hits = sorted(list(hits_A | hits_B))
            
            m1_A = {c for c in cA.keys() if len(set(c).intersection(win_set)) == size - 1}
            m1_B = {c for c in cB.keys() if len(set(c).intersection(win_set)) == size - 1}
            all_m1 = sorted(list(m1_A | m1_B))

            if not all_hits and not all_m1:
                sheet_data.append({"header": "❌ 皆無任何全中或聽牌組合。", "combos": []})
            
            if all_hits:
                sheet_data.append({"header": "[ ★ 全中組合比對 ]", "combos": []})
                for h in all_hits:
                    h_str = f"({','.join([f'{x:02d}' for x in h])})"
                    freq_A = cA.get(h, 0)
                    freq_B = cB.get(h, 0)
                    sheet_data.append({"header": f"★ {h_str}: [落球] {freq_A} 次 vs [大小] {freq_B} 次", "combos": []})
            
            if all_m1:
                sheet_data.append({"header": "[ ☆ 差一碼(聽牌) 比對 ]", "combos": []})
                for m in all_m1:
                    m_str = f"({','.join([f'{x:02d}' for x in m])})"
                    freq_A = cA.get(m, 0)
                    freq_B = cB.get(m, 0)
                    sheet_data.append({"header": f"☆ {m_str}: [落球] {freq_A} 次 vs [大小] {freq_B} 次", "combos": []})
        sheet_data.append({"header": "", "combos": []})
        
    return sheet_data

# --- 專用渲染組件 ---
def render_wrapped_text(text):
    st.markdown(f'<div class="custom-scroll-box">{text}</div>', unsafe_allow_html=True)

# --- 4. 執行與運算區 ---
if st.button("🚀 執行雙邏輯運算與比對", type="primary"):
    if df is None:
        st.warning("請先確認資料庫已載入！")
        st.stop()
        
    if None in n_inputs:
        st.error("T-1 篩選號碼 (n1~n5) 必須全部填寫！")
        st.stop()
        
    inputs = [int(x) for x in n_inputs]
    if len(set(inputs)) != 5:
        st.error("T-1 篩選的5個數字不能有重複！")
        st.stop()

    win_nums = []
    empty_win_count = win_inputs.count(None)
    if empty_win_count == 0:
        win_nums = [int(x) for x in win_inputs]
        if len(set(win_nums)) != 5:
            st.error("T 開獎號碼不能有重複！")
            st.stop()
    elif empty_win_count < 5:
        st.error("T 開獎號碼請麼全填，要麼全不填 (留空)。")
        st.stop()

    if not selected_stars:
        st.error("請至少勾選一種星數！")
        st.stop()

    valid_strict = compute_data(df, inputs, mode, is_strict_drop_order=True)
    valid_sorted = compute_data(df, inputs, mode, is_strict_drop_order=False)

    report_strict, counters_strict = generate_method_report("嚴格落球順序", valid_strict, selected_stars, win_nums)
    report_sorted, counters_sorted = generate_method_report("強制大小排序", valid_sorted, selected_stars, win_nums)
    report_diff = generate_comparison_report(counters_strict, counters_sorted, selected_stars, win_nums, selected_diffs)

    st.header("📊 雙邏輯運算結果與比對區")

    # 產出 Excel 檔案
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        ws_strict = workbook.add_worksheet('落球順序')
        strict_data = prepare_excel_data(valid_strict, counters_strict, selected_stars, win_nums)
        format_excel_sheet(ws_strict, strict_data)
        
        ws_sorted = workbook.add_worksheet('大小順序')
        sorted_data = prepare_excel_data(valid_sorted, counters_sorted, selected_stars, win_nums)
        format_excel_sheet(ws_sorted, sorted_data)
        
        ws_diff = workbook.add_worksheet('邏輯比對')
        diff_data = prepare_comparison_excel_data(counters_strict, counters_sorted, selected_stars, win_nums, selected_diffs)
        format_excel_sheet(ws_diff, diff_data)

    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 點擊下載完整分析報表 (Excel / .xlsx)",
        data=excel_data,
        file_name="539_analysis_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

    col_view1, col_view2 = st.columns(2)
    
    with col_view1:
        st.subheader("1️⃣ 落球順序 (原汁原味)")
        render_wrapped_text(report_strict)

    with col_view2:
        st.subheader("2️⃣ 大小順序 (打亂排序)")
        render_wrapped_text(report_sorted)

    st.subheader("3️⃣ 邏輯深度比對 (差異與命中)")
    render_wrapped_text(report_diff)
        
    st.success("運算比對完成！")
