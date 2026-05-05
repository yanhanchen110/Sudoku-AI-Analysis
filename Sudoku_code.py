import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import time
import csv
import os
from datetime import datetime

# 數據分析相關庫
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

class AdvancedSudoku:
    def __init__(self, master):
        self.master = master
        self.master.title("數獨大腦實驗室-醫學觀察專用版")
        # 調整視窗初始大小，適配標準筆電螢幕
        self.master.geometry("1100x800") 

        self.reset_stats()
        self.is_hardcore = tk.BooleanVar(value=False) 

        self.cells = {}        
        self.cell_data = {}    
        self.solution = [] 
        self.input_lock = False
        self.selected_cell = None
        self.highlight_num = None
        self.pencil_mode = False

        self.create_widgets()
        self.new_game()
        self.update_timer()

    def reset_stats(self):
        self.mistakes = 0
        self.careless_errors = 0
        self.logic_errors = 0
        self.correct_count = 0
        self.max_mistakes = 3
        self.start_time = time.time()

    def save_stats(self, status="Finished"):
        file_path = "sudoku_medical_stats.csv"
        file_exists = os.path.isfile(file_path)
        elapsed_time = int(time.time() - self.start_time)
        current_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_data = [current_now, status, self.correct_count, self.careless_errors, self.logic_errors, elapsed_time, 1 if self.is_hardcore.get() else 0]
        
        try:
            with open(file_path, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["時間", "結果", "正確數", "粗心次數", "邏輯錯誤", "秒數", "極限模式"])
                writer.writerow(log_data)
            self.add_to_history(f"系統：大腦數據已同步至存檔")
        except Exception as e:
            self.add_to_history(f"系統：存檔失敗-{e}")

    def show_analysis(self):
        file_path = "sudoku_medical_stats.csv"
        if not os.path.exists(file_path):
            messagebox.showwarning("提示", "目前尚無歷史數據可供醫師觀察。")
            return

        try:
            df = pd.read_csv(file_path)
            if len(df) < 1: return
            
            # 轉換時間格式
            df['時間'] = pd.to_datetime(df['時間'])
            # --- 關鍵修改：只取「有玩的那一天」(最後一筆紀錄的日期) ---
            target_date = df['時間'].dt.date.iloc[-1]
            df = df[df['時間'].dt.date == target_date].copy()
            
            df['小時'] = df['時間'].dt.hour
            df['總錯誤'] = df['粗心次數'] + df['邏輯錯誤']
            df['產能'] = df['正確數'] / (df['秒數'] / 60) # 正確率/速率 (格/分)
            
            plt.close('all')
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 建立 2x2 的圖表佈局
            fig = plt.figure(figsize=(12, 8))
            fig.suptitle(f"大腦功能報告 - 統計日期: {target_date}", fontsize=16)
            gs = fig.add_gridspec(3, 2)

            # 1. 功能維度演變 (左上)
            ax1 = fig.add_subplot(gs[0, 0])
            indices = range(1, len(df) + 1)
            ax1.stackplot(indices, df['粗心次數'], df['邏輯錯誤'], 
                         labels=['粗心(注意力)', '邏輯(推理力)'], colors=['#FFAB91', '#81D4FA'], alpha=0.8)
            ax1.set_title("功能維度演變 (當日趨勢)")
            ax1.legend(loc='upper left')

            # 2. 正確率 (速率) 趨勢 (右上)
            ax2 = fig.add_subplot(gs[0, 1])
            ax2.plot(indices, df['產能'], color='#2E7D32', marker='o', linestyle='-', linewidth=2)
            ax2.set_title("正確率速率 (格/分)")
            ax2.set_ylabel("速度")

            # 3. 每小時錯誤分布 (左下)
            ax3 = fig.add_subplot(gs[1, 0])
            hourly_careless = df.groupby('小時')['粗心次數'].mean().reindex(range(24), fill_value=0)
            hourly_logic = df.groupby('小時')['邏輯錯誤'].mean().reindex(range(24), fill_value=0)
            ax3.bar(range(24), hourly_careless, label='平均粗心', color='#EF9A9A')
            ax3.bar(range(24), hourly_logic, bottom=hourly_careless, label='平均邏輯誤', color='#90CAF9')
            ax3.set_xticks([0, 6, 12, 18, 23])
            ax3.set_title("當日 24 小時錯誤分布")
            ax3.legend()

            # 4. 大腦穩定度 (右下)
            ax4 = fig.add_subplot(gs[1, 1])
            # 使用散佈圖觀察穩定度，極限模式會顯示不同顏色
            scatter = ax4.scatter(indices, df['產能'], c=df['極限模式'], cmap='coolwarm', s=100, edgecolors='gray')
            ax4.set_title("大腦穩定度 (散佈圖)")
            ax4.set_xlabel("當日局數")

            # 5. 臨床摘要 (底欄)
            ax5 = fig.add_subplot(gs[2, :])
            ax5.axis('off')
            avg_err = df['總錯誤'].mean()
            win_rate = (len(df[df['結果'] == 'Win']) / len(df)) * 100
            best_hour = df.groupby('小時')['產能'].mean().idxmax()
            risk_hour = df.groupby('小時')['總錯誤'].mean().idxmax()
            
            diagnosis_msg = (f"【醫師參考摘要 - 僅限今日】\n"
                            f"總挑戰次數：{len(df)} | 成功率：{win_rate:.1f}% | 平均錯誤：{avg_err:.2f}\n"
                            f"今日尖峰時段：{best_hour} 點 | 今日疲勞時段：{risk_hour} 點")
            ax5.text(0.5, 0.5, diagnosis_msg, ha='center', va='center', fontsize=12, 
                     bbox=dict(boxstyle="round", facecolor='#F5F5F5', edgecolor='#BDBDBD'))

            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("分析錯誤", f"報表生成失敗: {e}")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill='both', expand=True)

        # 左側：遊戲區
        self.game_area = tk.Frame(self.main_frame, padx=10)
        self.game_area.pack(side=tk.LEFT, fill='both', expand=True)

        info_f = tk.Frame(self.game_area)
        info_f.pack(fill='x', pady=5)
        self.label_mistakes = tk.Label(info_f, text="錯誤: 0/3", font=('Arial', 11, 'bold'), fg="red")
        self.label_mistakes.pack(side=tk.LEFT)
        self.label_timer = tk.Label(info_f, text="時間: 00:00", font=('Arial', 11))
        self.label_timer.pack(side=tk.RIGHT)

        self.board_frame = tk.Frame(self.game_area, bg="#333", bd=2)
        self.board_frame.pack()

        for r in range(9):
            for c in range(9):
                pdx = (3, 1) if c % 3 == 0 else (1, 1)
                pdy = (3, 1) if r % 3 == 0 else (1, 1)
                container = tk.Frame(self.board_frame, width=50, height=50, bg="white")
                container.grid(row=r, column=c, padx=(pdx[0], 1 if c%3!=2 else 3), pady=(pdy[0], 1 if r%3!=2 else 3))
                container.pack_propagate(False)
                v_l = tk.Label(container, text="", font=('Arial', 18, 'bold'), bg="white")
                v_l.place(relx=0.5, rely=0.5, anchor="center")
                n_l = tk.Label(container, text="", font=('Arial', 7), bg="white", fg="#888")
                n_l.place(relx=0.5, rely=0.5, anchor="center")
                self.cells[(r, c)] = {"f": container, "v": v_l, "n": n_l}
                self.cell_data[(r, c)] = {"val": 0, "fixed": False, "notes": set()}
                for w in [container, v_l, n_l]:
                    w.bind("<Button-1>", lambda e, r=r, c=c: self.select_cell(r, c))

        # --- 控制區：改用更緊湊的排列 ---
        ctrl_f = tk.Frame(self.game_area)
        ctrl_f.pack(pady=5)
        
        self.hc_check = tk.Checkbutton(ctrl_f, text="🔥極限模式", variable=self.is_hardcore, font=('Microsoft JhengHei', 9, 'bold'), fg="darkred")
        self.hc_check.grid(row=0, column=0, columnspan=2)

        self.btn_pencil = tk.Button(ctrl_f, text="鉛筆: OFF", width=8, command=self.toggle_pencil)
        self.btn_pencil.grid(row=0, column=2, padx=2)
        
        tk.Button(ctrl_f, text="橡皮擦", bg="#FFCDD2", width=8, command=self.clear_cell).grid(row=0, column=3, padx=2)
        tk.Button(ctrl_f, text="數據分析", bg="#C8E6C9", width=10, command=self.show_analysis).grid(row=1, column=0, columnspan=2, pady=5)
        tk.Button(ctrl_f, text="新遊戲", width=10, command=self.new_game).grid(row=1, column=2, columnspan=2, pady=5)

        # 數字鍵
        num_f = tk.Frame(self.game_area)
        num_f.pack()
        for i in range(1, 10):
            tk.Button(num_f, text=str(i), width=3, font=('Arial', 11, 'bold'), command=lambda n=i: self.on_num_click(n)).pack(side=tk.LEFT, padx=1)

        # 右側：紀錄區 (縮減寬度以免擠壓按鈕)
        self.rec_area = tk.Frame(self.main_frame, padx=5, bg="#F0F0F0")
        self.rec_area.pack(side=tk.RIGHT, fill='y')
        tk.Label(self.rec_area, text="診斷紀錄", bg="#F0F0F0", font=('Arial', 9, 'bold')).pack(pady=5)
        self.history = scrolledtext.ScrolledText(self.rec_area, width=22, state=tk.DISABLED, font=('Consolas', 8))
        self.history.pack(fill='both', expand=True)

        self.master.bind("<Key>", self.handle_key)

    def select_cell(self, r, c):
        self.selected_cell = (r, c)
        val = self.cell_data[(r, c)]["val"]
        self.highlight_num = val if val != 0 else None
        self.refresh_colors()

    def on_num_click(self, num):
        if not self.selected_cell or self.cell_data[self.selected_cell]["fixed"]: return
        if self.is_hardcore.get() or not self.pencil_mode: self.input_number(num)
        else: self.input_pencil(num)

    def input_number(self, num):
        r, c = self.selected_cell
        careless = any(self.cell_data[(r, i)]["val"] == num for i in range(9) if i != c) or any(self.cell_data[(i, c)]["val"] == num for i in range(9) if i != r)
        sr, sc = 3*(r//3), 3*(c//3)
        for i in range(sr, sr+3):
            for j in range(sc, sc+3):
                if self.cell_data[(i, j)]["val"] == num and (i, j) != (r, c): careless = True

        if num == self.solution[r][c]:
            self.cell_data[(r, c)]["val"] = num
            self.correct_count += 1
            self.cells[(r, c)]["v"].config(text=str(num), fg="gray" if self.is_hardcore.get() else "blue")
            self.cells[(r, c)]["v"].lift()
            self.add_to_history(f"✓ ({r+1},{c+1})={num}")
            self.check_win()
        else:
            self.mistakes += 1
            if careless: self.careless_errors += 1; self.add_to_history(f"⚠ ({r+1},{c+1}) 粗心!")
            else: self.logic_errors += 1; self.add_to_history(f"✘ ({r+1},{c+1}) 邏輯誤!")
            self.label_mistakes.config(text=f"錯誤: {self.mistakes}/3")
            if self.mistakes >= 3:
                self.save_stats("Failed"); messagebox.showerror("失敗", "錯滿3次，數據已記錄。"); self.new_game()
        self.refresh_colors()

    def input_pencil(self, num):
        r, c = self.selected_cell
        d = self.cell_data[(r, c)]
        if d["val"] != 0: return
        if num in d["notes"]: d["notes"].remove(num)
        else: d["notes"].add(num)
        self.cells[(r, c)]["n"].config(text="".join(map(str, sorted(list(d["notes"])))))
        self.cells[(r, c)]["n"].lift()

    def refresh_colors(self):
        for (r, c), cell in self.cells.items():
            bg = "#BBDEFB" if self.selected_cell == (r, c) else ("#FFF176" if self.highlight_num and self.cell_data[(r, c)]["val"] == self.highlight_num else "white")
            cell["f"].config(bg=bg); cell["v"].config(bg=bg); cell["n"].config(bg=bg)

    def add_to_history(self, msg):
        self.history.config(state=tk.NORMAL)
        self.history.insert('1.0', f"[{time.strftime('%M:%S')}] {msg}\n")
        self.history.config(state=tk.DISABLED)

    def toggle_pencil(self):
        if self.is_hardcore.get(): return
        self.pencil_mode = not self.pencil_mode
        self.btn_pencil.config(bg="#B3E5FC" if self.pencil_mode else "SystemButtonFace", text=f"鉛筆: {'ON' if self.pencil_mode else 'OFF'}")

    def clear_cell(self):
        if self.selected_cell and not self.cell_data[self.selected_cell]["fixed"]:
            r, c = self.selected_cell
            self.cell_data[(r, c)].update({"val": 0, "notes": set()})
            self.cells[(r, c)]["v"].config(text=""); self.cells[(r, c)]["n"].config(text="")
            self.refresh_colors()

    def handle_key(self, e):
        if self.input_lock: return
        if e.char.isdigit() and e.char != '0':
            self.input_lock = True; self.on_num_click(int(e.char))
            self.master.after(100, lambda: setattr(self, 'input_lock', False))
        elif e.keysym == "BackSpace": self.clear_cell()

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        self.label_timer.config(text=f"時間: {elapsed//60:02d}:{elapsed%60:02d}")
        self.master.after(1000, self.update_timer)

    def solve(self, b):
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    nums = list(range(1,10)); random.shuffle(nums)
                    for n in nums:
                        if all(b[r][i]!=n for i in range(9)) and all(b[i][c]!=n for i in range(9)) and not any(b[i][j]==n for i in range(3*(r//3), 3*(r//3)+3) for j in range(3*(c//3), 3*(c//3)+3)):
                            b[r][c] = n
                            if self.solve(b): return True
                            b[r][c] = 0
                    return False
        return True

    def new_game(self):
        self.reset_stats(); self.label_mistakes.config(text="錯誤: 0/3")
        self.solution = [[0]*9 for _ in range(9)]; self.solve(self.solution)
        p = [row[:] for row in self.solution]
        for r, c in random.sample([(i, j) for i in range(9) for j in range(9)], 40): p[r][c] = 0
        for r in range(9):
            for c in range(9):
                d, u = self.cell_data[(r, c)], self.cells[(r, c)]
                d["notes"].clear(); u["n"].config(text="")
                d.update({"val": p[r][c], "fixed": (p[r][c] != 0)})
                u["v"].config(text=str(p[r][c]) if p[r][c] != 0 else "", fg="black")
                u["v"].lift()
        self.add_to_history("---新實驗場次開始---"); self.refresh_colors()

    def check_win(self):
        if all(self.cell_data[(r, c)]["val"] == self.solution[r][c] for r in range(9) for c in range(9)):
            self.save_stats("Win"); messagebox.showinfo("成功", "挑戰完成！"); self.new_game()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedSudoku(root)
    root.mainloop()