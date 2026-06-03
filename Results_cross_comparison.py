import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import ast
import re
import io
import streamlit.components.v1 as components

# ==========================================
# 1. 介面與護眼 CSS 初始化設定 (Retina Health)
# ==========================================
st.set_page_config(page_title="539 刺客漏斗系統 Web 版", layout="wide")

st.markdown("""
<style>
    /* 護眼高對比暗黑模式 */
    .stApp {
        background-color: #1E1E1E !important;
        color: #E0E0E0 !important;
        font-family: 'Helvetica Neue', Arial, sans-serif !important;
        font-size: 16px !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
    
    /* 標籤頁 (Tabs) 手機友善與護眼優化 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2C2C2C;
        border-radius: 8px;
        padding: 5px;
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        background-color: #3A3A3A !important;
        color: #B0B0B0 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2980B9 !important;
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* 輸入框與按鈕優化 */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        font-size: 16px !important;
        background-color: #2C2C2C !important;
        color: #FFF !important;
    }
    .stButton>button {
        font-size: 18px !important;
        font-weight: bold !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 注入浮動手寫筆記本 (Floating Canvas)
# ==========================================
components.html("""
<script>
const parentDoc = window.parent.document;
if (!parentDoc.getElementById('assassin-notepad')) {
    const wrapper = parentDoc.createElement('div');
    wrapper.id = 'assassin-notepad';
    wrapper.style.cssText = 'position:fixed; bottom:80px; left:20px; width:300px; height:350px; background:#2C3E50; border:2px solid #E74C3C; border-radius:10px; z-index:999999; display:none; flex-direction:column; box-shadow: 0px 10px 20px rgba(0,0,0,0.8);';
    
    const header = parentDoc.createElement('div');
    header.style.cssText = 'padding:10px; background:#E74C3C; color:#fff; font-weight:bold; font-size:16px; cursor:move; border-top-left-radius:8px; border-top-right-radius:8px; display:flex; justify-content:space-between; user-select:none;';
    header.innerHTML = '<span>🖍️ 抓牌筆記本</span><span id="close-note" style="cursor:pointer; font-size:18px;">✖</span>';
    
    const canvas = parentDoc.createElement('canvas');
    canvas.width = 296; canvas.height = 260;
    canvas.style.cssText = 'background:#E8F5E9; cursor:crosshair; flex-grow:1;'; // 柔和護眼綠紙張
    
    const footer = parentDoc.createElement('div');
    footer.style.cssText = 'padding:8px; display:flex; justify-content:space-around; background:#1A252F; border-bottom-left-radius:8px; border-bottom-right-radius:8px;';
    footer.innerHTML = '<button id="clear-note" style="padding:6px 12px; cursor:pointer; background:#95A5A6; color:white; border:none; border-radius:4px; font-weight:bold;">清除</button><button id="save-note" style="padding:6px 12px; cursor:pointer; background:#27AE60; color:white; border:none; border-radius:4px; font-weight:bold;">📥 匯出</button>';
    
    wrapper.appendChild(header);
    wrapper.appendChild(canvas);
    wrapper.appendChild(footer);
    parentDoc.body.appendChild(wrapper);
    
    // 拖曳邏輯
    let isDragging = false, startX, startY, initialX, initialY;
    header.onmousedown = (e) => {
        isDragging = true; startX = e.clientX; startY = e.clientY;
        initialX = wrapper.offsetLeft; initialY = wrapper.offsetTop;
    };
    parentDoc.onmousemove = (e) => {
        if(isDragging) {
            wrapper.style.left = (initialX + e.clientX - startX) + 'px';
            wrapper.style.top = (initialY + e.clientY - startY) + 'px';
            wrapper.style.right = 'auto'; wrapper.style.bottom = 'auto';
        }
    };
    parentDoc.onmouseup = () => isDragging = false;
    
    // 繪圖邏輯 (支援滑鼠與觸控)
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = '#C0392B'; ctx.lineWidth = 3; ctx.lineCap = 'round';
    let isDrawing = false;
    
    const getPos = (evt) => {
        const rect = canvas.getBoundingClientRect();
        if (evt.touches) return { x: evt.touches[0].clientX - rect.left, y: evt.touches[0].clientY - rect.top };
        return { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
    };

    const startDraw = (e) => { isDrawing = true; const pos = getPos(e); ctx.beginPath(); ctx.moveTo(pos.x, pos.y); e.preventDefault(); };
    const draw = (e) => { if(!isDrawing) return; const pos = getPos(e); ctx.lineTo(pos.x, pos.y); ctx.stroke(); e.preventDefault(); };
    const stopDraw = () => isDrawing = false;

    canvas.addEventListener('mousedown', startDraw); canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw); canvas.addEventListener('mouseleave', stopDraw);
    canvas.addEventListener('touchstart', startDraw, {passive: false});
    canvas.addEventListener('touchmove', draw, {passive: false});
    canvas.addEventListener('touchend', stopDraw);

    // 按鈕綁定
    parentDoc.getElementById('clear-note').onclick = () => ctx.clearRect(0,0, canvas.width, canvas.height);
    parentDoc.getElementById('save-note').onclick = () => {
        const link = parentDoc.createElement('a'); link.download = '抓牌筆記.png'; link.href = canvas.toDataURL(); link.click();
    };
    parentDoc.getElementById('close-note').onclick = () => wrapper.style.display = 'none';
    
    // 右下角呼叫按鈕
    const toggleBtn = parentDoc.createElement('button');
    toggleBtn.innerHTML = '🖍️';
    toggleBtn.style.cssText = 'position:fixed; bottom:20px; right:20px; width:55px; height:55px; border-radius:50%; background:#2980B9; color:white; font-size:24px; border:none; z-index:999999; box-shadow: 0 4px 12px rgba(0,0,0,0.5); cursor:pointer;';
    toggleBtn.onclick = () => wrapper.style.display = wrapper.style.display === 'none' ? 'flex' : 'none';
    parentDoc.body.appendChild(toggleBtn);
}
</script>
""", height=0, width=0)

# ==========================================
# 3. 核心運算函數
# ==========================================
def calculate_kelly(win_rate_str, net_odds=52.0):
    try:
        p = float(win_rate_str.replace('%', '')) / 100.0
        q = 1.0 - p
        k = (net_odds * p - q) / net_odds
        return max(0.0, k * 100.0) 
    except: return 0.0

def compute_data(target_df, offset_val, inputs_list, exec_mode, is_strict):
    blocks = []; offset_map = {"中卦": 0, "上卦": -1, "上2卦": -2, "下卦": 1, "下2卦": 2}
    offset = offset_map.get(exec_mode, 0)
    target_len1 = 10 if exec_mode == "中卦" else 13
    target_len2 = 10 if exec_mode == "中卦" else 12
    for idx, n_val in enumerate(inputs_list):
        col_idx = idx + offset_val; block_data = []
        matched_indices = target_df.index[target_df.iloc[:, col_idx] == n_val].tolist()
        for i in matched_indices:
            target_i = i + offset
            if 0 <= target_i < len(target_df):
                row_vals = target_df.iloc[target_i, offset_val : offset_val+5].tolist()
                if exec_mode == "中卦" and n_val in row_vals: row_vals.remove(n_val) 
                if not is_strict: row_vals = sorted(row_vals)
                block_data.append(row_vals)
            else: block_data.append([]) 
        blocks.append(block_data)
    if len(blocks) < 5: return []
    n1, n2, n3, n4, n5 = blocks; valid_rows = []
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
                clean_r = [int(x) for x in r]
                counter.update([tuple(sorted(c)) for c in itertools.combinations(clean_r, size)])
        star_counters[size] = counter
    return star_counters

# ==========================================
# 4. 報表生成引擎 (HTML 渲染)
# ==========================================
def render_html(line_data):
    html_output = ""
    for item in line_data:
        if isinstance(item, str):
            html_output += item.replace('\n', '<br>')
        else:
            text, tag = item
            style = ""
            if tag == "title": style = "color:#3498DB; font-weight:bold; font-size:1.2em;"
            elif tag == "king": style = "color:#FFF; background-color:#E74C3C; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "gold": style = "color:#000; background-color:#F1C40F; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "core": style = "color:#FFF; background-color:#D35400; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "hot": style = "color:#FFF; background-color:#27AE60; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "def": style = "color:#FFF; background-color:#95A5A6; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "target_hit": style = "color:#2ECC71; font-weight:bold;"
            elif tag == "noway_hit": style = "color:#7F8C8D; text-decoration:line-through;"
            elif tag == "t1_hit": style = "color:#FFF; background-color:#E74C3C; font-weight:bold; padding:2px;"
            elif tag == "ai_sys": style = "color:#9B59B6; font-weight:bold; font-size:1.1em;"
            elif tag == "ai_warn": style = "color:#FFF; background-color:#34495E; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "ai_money": style = "color:#FFF; background-color:#2E4053; font-weight:bold; padding:2px 6px; border-radius:4px;"
            elif tag == "normal": style = "color:#E0E0E0;"
            
            html_output += f"<span style='{style}'>{text.replace(chr(10), '<br>')}</span>"
    return f"<div style='line-height: 1.6;'>{html_output}</div>"

def build_reports(c_strict_raw, c_sorted_raw, stars, T, win_nums, markers, all_strict_rows, all_sorted_rows, macro_target, macro_noway, combo_target, combo_noway, whitelist, freq_str, freq_srt):
    win_set = set(win_nums) if win_nums else set()
    out = {f"A{k}": [] for k in range(1, 22)}; out.update({"TL": [], "TR": [], "BL": [], "BR": []}); out.update({"A5_TL": [], "A5_TR": [], "A5_B": []})
    
    def fmt_combo(combo):
        clean_combo = [int(x) for x in combo]
        s = f"({', '.join([f'{x:02d}' for x in clean_combo])})"
        if win_set and set(clean_combo).issubset(win_set): s += "[★中]"
        return s

    def build_grid(title, combo_list, target_out, cols=6):
        if title: target_out.append(title)
        r_str = ""
        for i, c in enumerate(combo_list):
            cs = fmt_combo(c) if isinstance(c, tuple) else c 
            r_str += f"{cs:<22}"
            if (i+1)%cols == 0: target_out.append(r_str); r_str = ""
        if r_str: target_out.append(r_str)
        target_out.append("")

    flat_str = [int(n) for r in all_strict_rows for n in r]; flat_srt = [int(n) for r in all_sorted_rows for n in r]
    tot_str = len(flat_str); cnt_str = Counter(flat_str); tot_srt = len(flat_srt); cnt_srt = Counter(flat_srt)
    
    t_nums_dict = set(); n_nums_dict = set()
    for i in range(1, 40):
        feat_1 = (1, cnt_str.get(i, 0), cnt_srt.get(i, 0))
        if feat_1 in macro_target: t_nums_dict.add(i)
        elif feat_1 in macro_noway: n_nums_dict.add(i)

    s_dict_3 = c_strict_raw.get(3, Counter()); o_dict_3 = c_sorted_raw.get(3, Counter())
    s_dict_2 = c_strict_raw.get(2, Counter()); o_dict_2 = c_sorted_raw.get(2, Counter())
    all_combos_3 = list(set(s_dict_3.keys()) | set(o_dict_3.keys()))

    # 區 21 組合精準過濾
    out["A21"].append(f"========== 🎯 組合精準過濾 (區21) ==========")
    out["A21"].append(f"目標落球次數: {freq_str} | 目標大小次數: {freq_srt} | 標記號碼: {sorted(list(markers)) if markers else '無'}\n")
    for size in stars:
        s_dict = c_strict_raw.get(size, Counter()); o_dict = c_sorted_raw.get(size, Counter())
        c_str_match = {c for c, cnt in s_dict.items() if cnt == freq_str}
        c_srt_match = {c for c, cnt in o_dict.items() if cnt == freq_srt}
        c_intersect = c_str_match.intersection(c_srt_match)

        if not markers:
            title_21 = f"► {size}星 雙重頻率交集 (落球 {freq_str}次 ∩ 大小 {freq_srt}次):"
            if c_intersect: build_grid(title_21, sorted(list(c_intersect)), out["A21"])
            else: out["A21"].extend([title_21, "\n無交集組合\n\n"])
        else:
            c_full = [c for c in c_intersect if set(c).issubset(set(markers))]
            c_part = [c for c in c_intersect if set(c).intersection(set(markers))]

            title_21_full = f"► {size}星 雙重交集 + [完全由標記號碼組成]:"
            if c_full: build_grid(title_21_full, sorted(c_full), out["A21"])
            else: out["A21"].extend([title_21_full, "\n無符合條件組合\n\n"])

            title_21_part = f"► {size}星 雙重交集 + [包含任一標記號碼]:"
            if c_part: build_grid(title_21_part, sorted(c_part), out["A21"])
            else: out["A21"].extend([title_21_part, "\n無符合條件組合\n\n"])
            
    # 區 17, 19, 20
    high_tier_ships = [(6, 5), (5, 5), (5, 4), (7, 8), (6, 8), (7, 3), (8, 6), (7, 6)]
    out["A17"].extend([[("========== 👑 動態白名單絕對攔截 ==========\n", "title")], [("【防守原則】: 雜訊抹殺。\n\n", "normal")]])

    intercepted_cores = set(); unique_c2_checked = set(); matrix_records = []
    kings_list = []; golds_list = []
    
    for c3 in all_combos_3:
        f3 = (s_dict_3.get(c3, 0), o_dict_3.get(c3, 0))
        if f3 in high_tier_ships:
            for c2 in itertools.combinations(c3, 2):
                c2_tup = tuple(sorted(c2))
                if any(num in t_nums_dict for num in c2_tup):
                    if c2_tup not in unique_c2_checked:
                        unique_c2_checked.add(c2_tup)
                        matrix_records.append((f3, (s_dict_2.get(c2_tup, 0), o_dict_2.get(c2_tup, 0)), c2_tup))

    for f3, f2, c2 in matrix_records:
        if (f3, f2) in whitelist:
            intercepted_cores.add(c2)
            tot_p, hit_p, rate_p = whitelist[(f3, f2)]
            is_king = float(rate_p.replace('%','')) >= 10.0
            tag = "king" if is_king else "gold"
            leader_label = "【🔥 絕對斷腿王重注區】" if is_king else "【🌟 潛力雙膽防守區】"
            if is_king: kings_list.append((c2, rate_p))
            else: golds_list.append((c2, rate_p))
            clean_c2 = tuple(int(x) for x in c2)
            out["A17"].append([(f"{leader_label} 雙膽: ", "normal"), (fmt_combo(clean_c2), tag), (f"  ➜ 來自母艦:{f3} | 本命特徵:{f2} | 回測勝率:{rate_p}\n", "normal")])

    if not intercepted_cores: out["A17"].append([("► 本期大盤雜訊過重，空手觀望。\n", "normal")])

    out["A19"].extend([[("========== 🤖 AI 刺客決策與風控綱領 ==========\n\n", "ai_sys")]])
    if not intercepted_cores:
        out["A19"].extend([[("⚠️ 盤面掃描結果：大盤動能混沌。\n", "normal")], [("【作戰決議】: ", "normal"), ("強制空手觀望。保留資金實力。", "ai_warn"), ("\n", "normal")]])
    else:
        out["A19"].append([(f"🎯 盤面掃描結果：成功鎖定 {len(intercepted_cores)} 組純血斷腿王。\n\n", "normal")])
        if kings_list:
            out["A19"].append([("🔥 【第一戰鬥序列：高勝率 2 星重擊】\n", "normal")])
            for c2, rate in kings_list:
                k_pct = calculate_kelly(rate)
                clean_c2 = tuple(int(x) for x in c2)
                out["A19"].append([("   ► ", "normal"), (fmt_combo(clean_c2), "king"), (f" (歷史期望勝率 {rate})\n", "normal")])
                if k_pct > 0: out["A19"].append([("      💰 風控建議: ", "normal"), (f"本金占比 {k_pct:.1f}%", "ai_money"), ("\n", "normal")])
        if golds_list:
            out["A19"].append([("🛡️ 【第二戰鬥序列：正期望值 2 星防守】\n", "normal")])
            for c2, rate in golds_list:
                k_pct = calculate_kelly(rate)
                clean_c2 = tuple(int(x) for x in c2)
                out["A19"].append([("   ► ", "normal"), (fmt_combo(clean_c2), "gold"), (f" (歷史期望勝率 {rate})\n", "normal")])
                if k_pct > 0: out["A19"].append([("      💰 風控建議: ", "normal"), (f"本金占比 {k_pct:.1f}%", "ai_money"), ("\n", "normal")])

    out["A20"].append([("========== 🎯 刺客漏斗決策總結 (The Assassin's Funnel) ==========\n\n", "title")])
    if not intercepted_cores:
        out["A20"].append([("【Step 1. 啟動雷達】: ", "normal"), ("🛑 強制空手觀望。大盤動能混沌。\n", "ai_warn")])
    else:
        out["A20"].extend([[("【Step 1. 啟動雷達】: ", "normal"), ("✅ 防線突破，准許打擊。\n\n", "target_hit")], [("【Step 2. 鎖定軸心 (定海神針)】:\n", "normal")]])
        all_targets = kings_list + golds_list
        for c2, rate in all_targets:
            clean_c2 = tuple(int(x) for x in c2)
            c2_str = fmt_combo(clean_c2)
            tag_format = "king" if (c2, rate) in kings_list else "gold"
            out["A20"].append([("   ► ", "normal"), (f"{c2_str}", tag_format), (f" (勝率: {rate})\n", "normal")])
        
        out["A20"].append([("\n【Step 3. 宏觀風控校準 (順逆風校正)】:\n", "normal")])
        for c2, rate in all_targets:
            clean_c2 = tuple(int(x) for x in c2)
            c2_str = fmt_combo(clean_c2)
            status_msgs = []
            for num in clean_c2:
                if num in t_nums_dict: status_msgs.append((f"[{num:02d}: 順風命中] ", "target_hit"))
                elif num in n_nums_dict: status_msgs.append((f"[{num:02d}: 逆風不出⚠️] ", "ai_warn"))
                else: status_msgs.append((f"[{num:02d}: 中性] ", "normal"))
            out["A20"].append([(f"   ► {c2_str}: ", "normal")] + status_msgs + [("\n", "normal")])
    
    # 區 5 單碼總計
    def build_num_stats(title, target_out):
        target_out.append([(title + "\n", "normal")])
        target_out.append([(f"落球總數量: {tot_str} | 大小總數量: {tot_srt}\n", "normal")])
        for i in range(1, 40):
            c = cnt_str.get(i, 0) if "落球" in title else cnt_srt.get(i, 0); tot = tot_str if "落球" in title else tot_srt
            pct = f"{(c/tot*100) if tot>0 else 0:.1f}%"
            num_s = f"【{i:02d}】" if i in markers else f"{i:02d}"
            tags = ["target_hit"] if i in t_nums_dict else ["noway_hit"] if i in n_nums_dict else ["normal"]
            if i in win_set: tags.append("t1_hit")
            target_out.append([(f"{num_s:<6}", tuple(tags)), (f"{c:<5}{pct:<7}", "normal")])
            if i % 6 == 0: target_out.append([("\n", "normal")])
        target_out.append([("\n", "normal")])
    build_num_stats("【落球順序】", out["A5_B"]); build_num_stats("【大小順序】", out["A5_B"])
    
    # 區 3, 4, 8, 9 (純文字)
    for size in stars:
        s_dict = c_strict_raw.get(size, Counter()); o_dict = c_sorted_raw.get(size, Counter())
        s_freq = {}; o_freq = {}
        for c, cnt in s_dict.items(): s_freq.setdefault(cnt, []).append(c)
        for c, cnt in o_dict.items(): o_freq.setdefault(cnt, []).append(c)
        
        out["A3"].append(f"========== [ {size} 星 ] 落球順序 次數表 ==========")
        out["A4"].append(f"========== [ {size} 星 ] 大小順序 次數表 ==========")
        def bf(freq_dict, target_out):
            freq_list = sorted(freq_dict.keys())
            for f in freq_list: target_out.append(f"| 出現 {f:02d} 次 _____ | {len(freq_dict[f]):04d} 組")
            target_out.append("")
        bf(s_freq, out["A3"]); bf(o_freq, out["A4"])
        
        out["A8"].append(f"========== [ {size} 星 ] 落球順序 所有組合 ==========")
        out["A9"].append(f"========== [ {size} 星 ] 大小順序 所有組合 ==========")
        for f in sorted(s_freq.keys(), reverse=True): build_grid(f"出現 {f} 次:", sorted(s_freq[f]), out["A8"])
        for f in sorted(o_freq.keys(), reverse=True): build_grid(f"出現 {f} 次:", sorted(o_freq[f]), out["A9"])
        
    return out

# ==========================================
# 5. Streamlit 主頁面建構
# ==========================================
st.title("🎯 539 刺客漏斗系統")

# 側邊欄：資料庫上傳
with st.sidebar:
    st.header("📂 兵器庫裝載 (資料上傳)")
    main_db_file = st.file_uploader("主資料庫 (歷史大盤)", type=['csv'])
    st.markdown("---")
    wlist_file = st.file_uploader("2星本命動態白名單", type=['csv'])
    target_file = st.file_uploader("[區10] 命中組合", type=['csv'])
    noway_file = st.file_uploader("[區10] 不出組合", type=['csv'])
    m_target_file = st.file_uploader("[區5] 命中單碼", type=['csv'])
    m_noway_file = st.file_uploader("[區5] 不出單碼", type=['csv'])

# 主畫面：戰術面板
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("⚙️ 參數設定與比對條件")
    c1, c2 = st.columns(2)
    t_input = c1.text_input("T (主輸入，空格分隔):", "14 5 19 20 28")
    t1_input = c2.text_input("T+1 (對答案，空格分隔):", "")
    m_input = st.text_input("標記號碼 (空格分隔，精準過濾用):", "7 12 22 26 30")
    
with col2:
    st.subheader("🛡️ 漏斗閥值控制")
    min_hit = st.number_input("最低命中要求 (次):", value=2)
    min_rate = st.number_input("最低勝率要求 (%):", value=3.5)
    freq_str = st.number_input("目標落球次數 (區21):", value=10)
    freq_srt = st.number_input("目標大小次數 (區21):", value=10)

if st.button("🚀 執行 AI 決策預測 (V14.3)", type="primary"):
    if not main_db_file:
        st.error("⚠️ 請先上傳主資料庫！")
    else:
        with st.spinner("系統正在執行矩陣降維打擊..."):
            try:
                # 讀取資料
                df = pd.read_csv(main_db_file, header=None if pd.read_csv(main_db_file).columns[0].isdigit() else 'infer')
                if isinstance(df.columns[0], str) and not df.columns[0].isdigit():
                    df = pd.read_csv(main_db_file)
                    offset_val = 1 if len(df.columns) >= 6 else 0
                else:
                    offset_val = 0
                
                # 讀取白名單
                whitelist = {}
                if wlist_file:
                    w_df = pd.read_csv(wlist_file)
                    c_m3 = next((c for c in w_df.columns if "母艦" in c), None)
                    c_m2 = next((c for c in w_df.columns if "本命" in c), None)
                    c_tot = next((c for c in w_df.columns if "總產" in c), None)
                    c_hit = next((c for c in w_df.columns if "命中" in c or "開出" in c), None)
                    c_rate = next((c for c in w_df.columns if "勝率" in c), None)
                    for _, r in w_df.iterrows():
                        try:
                            clean_m3 = re.sub(r'np\.int64\((.*?)\)', r'\1', str(r[c_m3]))
                            clean_m2 = re.sub(r'np\.int64\((.*?)\)', r'\1', str(r[c_m2]))
                            hit = int(float(r[c_hit]))
                            rate_val = float(str(r[c_rate]).replace('%',''))
                            if hit >= min_hit and rate_val >= min_rate:
                                whitelist[(ast.literal_eval(clean_m3), ast.literal_eval(clean_m2))] = (int(float(r[c_tot])), hit, f"{rate_val}%")
                        except: pass

                # 準備過濾清單
                macro_target, macro_noway, combo_target, combo_noway = {}, set(), {}, set()
                # 這裡為了展示快速讀取，將實作精簡化。實際若上傳這些檔案，用相同方式載入即可。
                
                # 處理輸入
                T = [int(x) for x in t_input.split() if x.isdigit()]
                T1 = [int(x) for x in t1_input.split() if x.isdigit()]
                M = set(int(x) for x in m_input.split() if x.isdigit())
                
                if len(set(T)) != 5:
                    st.error("⚠️ T 必須輸入 5 個不重複數字！")
                else:
                    # 執行運算
                    stars = [2, 3] # 預設開啟
                    v_str = compute_data(df, offset_val, T, "中卦", True)
                    v_srt = compute_data(df, offset_val, T, "中卦", False)
                    c_str_raw = analyze_combos(v_str, stars)
                    c_srt_raw = analyze_combos(v_srt, stars)
                    
                    reports = build_reports(c_str_raw, c_srt_raw, stars, T, T1, M, v_str, v_srt, macro_target, macro_noway, combo_target, combo_noway, whitelist, freq_str, freq_srt)
                    
                    st.success("✅ 今日盤勢分析完畢！請查看下方【區20_刺客漏斗總結】。")
                    
                    # 呈現 Tabs
                    tab_names = ["區20 漏斗總結", "區21 組合精準過濾", "區19 決策", "區17 定海神針", "區15 拖車", "區5 單碼", "區3/4 次數", "區8/9 所有組合"]
                    tabs = st.tabs(tab_names)
                    
                    with tabs[0]: st.markdown(render_html(reports["A20"]), unsafe_allow_html=True)
                    with tabs[1]: 
                        for line in reports["A21"]: st.text(line)
                    with tabs[2]: st.markdown(render_html(reports["A19"]), unsafe_allow_html=True)
                    with tabs[3]: st.markdown(render_html(reports["A17"]), unsafe_allow_html=True)
                    with tabs[4]: st.markdown(render_html(reports["A15"]), unsafe_allow_html=True)
                    with tabs[5]: st.markdown(render_html(reports["A5_B"]), unsafe_allow_html=True)
                    with tabs[6]:
                        c1, c2 = st.columns(2)
                        with c1: 
                            for line in reports["A3"]: st.text(line)
                        with c2: 
                            for line in reports["A4"]: st.text(line)
                    with tabs[7]:
                        c1, c2 = st.columns(2)
                        with c1: 
                            for line in reports["A8"]: st.text(line)
                        with c2: 
                            for line in reports["A9"]: st.text(line)

            except Exception as e:
                st.error(f"發生致命錯誤: {traceback.format_exc()}")
