import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import os
import io

# --- 頁面基本設定與全域 CSS ---
st.set_page_config(page_title="539 雙邏輯深度比對系統", layout="wide")

st.markdown("""
<style>
.custom-scrollbar {
    overflow-y: auto !important;
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
    margin-bottom: 20px;
}
.custom-scrollbar::-webkit-scrollbar {
    width: 12px !important;
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

# --- 3. 卦象與星數選擇 ---
st.header("2. 參數設定與進階比對")
params_col1, params_col2 = st.columns(2)
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

st.markdown("---")
st.write("**【進階交叉比對】鎖定特定出現次數進行相似度過濾 (精準省算力)**")
adv_col1, adv_col2 = st.columns(2)
with adv_col1:
    freq_a = st.number_input("落球順序 (區域A) 目標出現次數 (填0停用):", min_value=0, value=0, step=1)
    freq_b = st.number_input("大小順序 (區域B) 目標出現次數 (填0停用):", min_value=0, value=0, step=1)
with adv_col2:
    st.write("勾選要找出的相似度 (相差碼數):")
    diff_cols = st.columns(4)
    diff_0 = diff_cols[0].checkbox("相同(差0)", value=True)
    diff_1 = diff_cols[1].checkbox("差1號", value=True)
    diff_2 = diff_cols[2].checkbox("差2號", value=False)
    diff_3 = diff_cols[3].checkbox("差3號", value=False)
    diff_opts = [d for d, c in zip([0, 1, 2, 3], [diff_0, diff_1, diff_2, diff_3]) if c]

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
        blocks.append(block_data)

    n1_data, n2_data, n3_data, n4_data, n5_data = blocks
    group1_merged, group2_merged = [], []

    for b1, b2, b3 in zip(n1_data, n2_data, n3_data):
        merged = b1 + b2 + b3[:2] if exec_mode == "中卦" else b1 + b2 + b3[:3]
        group1_merged.append(list(dict.fromkeys(merged)) if is_strict_drop_order else sorted(list(set(merged))))

    for b3, b4, b5 in zip(n3_data, n4_data, n5_data):
        merged = b3[2:] + b4 + b5 if exec_mode == "中卦" else b3[3:] + b4 + b5
        group2_merged.append(list(dict.fromkeys(merged)) if is_strict_drop_order else sorted(list(set(merged))))

    return group1_merged + group2_merged

# ==========================================
# 報表產生器 (分拆為三部分返回)
# ==========================================
def generate_method_report(method_name, all_valid_rows, stars, win_nums):
    if not all_valid_rows:
        return "無有效行數產生。", "無有效行數產生。", "無有效行數產生。", {}

    win_set = set(win_nums) if win_nums else set()
    flat_nums = [n for row in all_valid_rows for n in row]
    total_nums = len(flat_nums)
    num_counts = Counter(flat_nums)
    
    # ------------------ Part 1: 單碼統計 ------------------
    p1 = []
    freq_to_nums = {}
    for i in range(1, 40):
        freq_to_nums.setdefault(num_counts.get(i, 0), []).append(i)

    p1.append(f"總計產出數字數量: {total_nums}\n")
    p1.append("[ 單碼出現次數排行 (由高至低) ]")
    p1.append("-" * 40)
    for freq in sorted(freq_to_nums.keys(), reverse=True):
        nums_str = " ".join([f"({n:02d})" for n in sorted(freq_to_nums[freq])])
        p1.append(f" {freq:>2} 次 | {nums_str}")
    
    p1.append("\n[ 01~39 各號碼詳細總數與佔比 ]")
    line_str = ""
    for i in range(1, 40):
        c = num_counts.get(i, 0)
        ratio = (c / total_nums * 100) if total_nums > 0 else 0
        line_str += f"({i:02d}) {c:>3}次({ratio:>5.2f}%) | "
        if i % 3 == 0: 
            p1.append(line_str)
            line_str = ""
    if line_str: p1.append(line_str)

    # ------------------ Part 2: 命中總表 ------------------
    p2 = []
    star_counters = {}
    for size in stars:
        counter = Counter()
        for row in all_valid_rows:
            if len(row) >= size:
                counter.update([tuple(sorted(c)) for c in itertools.combinations(row, size)])
        star_counters[size] = counter
        
        p2.append(f"\n--- [ {size} 星 命中與聽牌 ] ---")
        if not counter:
            p2.append("無數據。")
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
                    if match_count == size: hits_full.append(c)
                    elif match_count == size - 1: hits_miss_one.append(c)
            
            p2.append(f"▶ 出現 {count:>2} 次: 共有 {len(combos):>4} 組")
            if not win_set:
                p2.append("　(未輸入開獎號碼)")
            else:
                str_full = " ".join([f"({','.join([f'{x:02d}' for x in h])})" for h in hits_full])
                p2.append(f"　 １. [★全中 {len(hits_full):>2} 組]: {str_full}" if hits_full else "　 １. [★全中  0 組]")
                str_m1 = " ".join([f"({','.join([f'{x:02d}' for x in h])})" for h in hits_miss_one])
                p2.append(f"　 ２. [☆差一碼 {len(hits_miss_one):>2} 組]: {str_m1}" if hits_miss_one else "　 ２. [☆差一碼  0 組]")

    # ------------------ Part 3: 詳細名單 ------------------
    p3 = []
    for size in stars:
        p3.append(f"========== [ {size} 星 詳細列表 ] ==========")
        counter = star_counters[size]
        freq_dict = {}
        for combo, count in counter.items():
            freq_dict.setdefault(count, []).append(combo)
            
        for count in sorted(freq_dict.keys(), reverse=True):
            p3.append(f"出現 {count} 次:")
            line_str = ""
            for idx, combo in enumerate(sorted(freq_dict[count])):
                line_str += f"({','.join([f'{x:02d}' for x in combo])})  "
                if (idx + 1) % 4 == 0: 
                    p3.append(line_str)
                    line_str = ""
            if line_str: p3.append(line_str)
        p3.append("")

    return "\n".join(p1), "\n".join(p2), "\n".join(p3), star_counters

# ==========================================
# 差異與命中比對產生器 (加入進階過濾命中標記)
# ==========================================
def generate_comparison_reports(counters_strict, counters_sorted, stars, win_nums, f_a, f_b, d_opts):
    win_set = set(win_nums) if win_nums else set()
    c1, c2, c3 = [], [], []

    for size in stars:
        cA = counters_strict.get(size, Counter())
        cB = counters_sorted.get(size, Counter())

        # --- 比對 1: 基礎差異 ---
        c1.append(f"========== 🎯 {size} 星 基礎差異 ==========")
        all_freqs = sorted(list(set(cA.values()) | set(cB.values())), reverse=True)
        has_diff = False
        for freq in all_freqs:
            only_A = sorted(list({c for c, count in cA.items() if count == freq} - {c for c, count in cB.items() if count == freq}))
            only_B = sorted(list({c for c, count in cB.items() if count == freq} - {c for c, count in cA.items() if count == freq}))
            if only_A or only_B:
                has_diff = True
                c1.append(f"▶ 出現 {freq} 次的差異：")
                if only_A: c1.append(f"　[落球順序] 獨有 ({len(only_A)}組):\n　" + " ".join([f"({','.join([f'{x:02d}' for x in c])})" for c in only_A]))
                if only_B: c1.append(f"　[大小順序] 獨有 ({len(only_B)}組):\n　" + " ".join([f"({','.join([f'{x:02d}' for x in c])})" for c in only_B]))
        if not has_diff: c1.append("✅ 兩者在所有次數分佈上【完全無差異】。")
        c1.append("")

        # --- 比對 2: 命中與聽牌 ---
        c2.append(f"========== 🎯 {size} 星 命中與聽牌 ==========")
        if not win_set:
            c2.append("⚠️ 未輸入 T (開獎號碼)，無法比對命中。")
        else:
            all_hits = sorted(list({c for c in cA.keys() if len(set(c).intersection(win_set)) == size} | {c for c in cB.keys() if len(set(c).intersection(win_set)) == size}))
            all_m1 = sorted(list({c for c in cA.keys() if len(set(c).intersection(win_set)) == size - 1} | {c for c in cB.keys() if len(set(c).intersection(win_set)) == size - 1}))

            if not all_hits and not all_m1: c2.append("❌ 皆無任何全中或聽牌組合。")
            if all_hits:
                c2.append("[ ★ 全中組合比對 ]")
                for h in all_hits:
                    c2.append(f"★ ({','.join([f'{x:02d}' for x in h])}): [落球] {cA.get(h,0)} 次 vs [大小] {cB.get(h,0)} 次")
            if all_m1:
                c2.append("\n[ ☆ 差一碼(聽牌) 組合比對 ]")
                for m in all_m1:
                    c2.append(f"☆ ({','.join([f'{x:02d}' for x in m])}): [落球] {cA.get(m,0)} 次 vs [大小] {cB.get(m,0)} 次")
        c2.append("")

        # --- 比對 3: 進階過濾 (加入命中標記) ---
        if f_a > 0 and f_b > 0 and d_opts:
            c3.append(f"========== 🎯 {size} 星 進階過濾 ==========")
            c_A_tgt = [c for c, count in cA.items() if count == f_a]
            c_B_tgt = [c for c, count in cB.items() if count == f_b]
            if not c_A_tgt or not c_B_tgt:
                c3.append("❌ 此星數未找到符合目標次數的組合。")
            else:
                has_any_match = False
                for d in d_opts:
                    matches = []
                    for c_a in c_A_tgt:
                        set_a = set(c_a)
                        for c_b in c_B_tgt:
                            if size - len(set_a.intersection(c_b)) == d:
                                # 替 A 加上命中標記
                                str_a = f"({','.join([f'{x:02d}' for x in c_a])})"
                                if win_set:
                                    mc_a = len(set_a.intersection(win_set))
                                    if mc_a == size: str_a += " [★全中]"
                                    elif mc_a == size - 1: str_a += " [☆差一碼]"
                                
                                # 替 B 加上命中標記
                                str_b = f"({','.join([f'{x:02d}' for x in c_b])})"
                                if win_set:
                                    mc_b = len(set(c_b).intersection(win_set))
                                    if mc_b == size: str_b += " [★全中]"
                                    elif mc_b == size - 1: str_b += " [☆差一碼]"

                                matches.append(f"落球 {str_a} <-> 大小 {str_b}")
                    
                    if matches:
                        has_any_match = True
                        c3.append(f"[ 相差 {d} 號 ] 共 {len(matches)} 對:")
                        for m_str in matches: c3.append(f"　{m_str}")
                if not has_any_match:
                    c3.append("❌ 無符合所選差異碼數的組合。")
            c3.append("")

    if not (f_a > 0 and f_b > 0 and d_opts):
        c3.append("⚠️ 未啟用進階過濾參數 (或未設定目標次數)。")

    return "\n".join(c1), "\n".join(c2), "\n".join(c3)

# ==========================================
# Excel 匯出引擎 (保留所有排版)
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
            if col_idx != 0: row_idx += 1 
        row_idx += 1

def prepare_excel_data(all_valid_rows, counters, stars, win_
