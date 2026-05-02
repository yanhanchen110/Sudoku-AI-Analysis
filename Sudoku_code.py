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
# 強制指定 TkAgg 後端以解決 GUI 衝突
matplotlib.use('TkAgg')

class SudokuGame:
    def __init__(self, master):
        self.master = master
        self.master.title("數獨挑戰-數據紀錄與分析版")
        
        # 遊戲統計變數
        self.mistakes = 0
        self.correct_count = 0  
        self.max_mistakes = 3
        self.start_time = None
        self.selected_cell = None
        self.highlight_num = None  
        self.pencil_mode = False 
        self.input_lock = False  
        
        self.cells = {}        
        self.cell_data = {}    
        self.solution = [] 
        
        self.create_widgets()
        self.new_game()
        self.update_timer()

    def save_stats(self, status="Finished"):
        """存檔至 CSV"""
        file_path = "sudoku_stats.csv"
        file_exists = os.path.isfile(file_path)
        
        end_time = time.time()
        elapsed_time = int(end_time - self.start_time)
        current_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_data = [current_now, status, self.correct_count, self.mistakes, elapsed_time]
        
        try:
            with open(file_path, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["時間點", "結果", "答對數", "答錯數", "花費秒數"])
                writer.writerow(log_data)
            self.add_to_history(f"系統：數據已紀錄至 {file_path}")
        except Exception as e:
            self.add_to_history(f"系統：存檔失敗 - {e}")

    def clear_all_history(self):
        """新增功能：清除右側 UI 紀錄與刪除 CSV 檔案"""
        confirm = messagebox.askyesno("確認清除", "是否要清除右側操作紀錄，並【永久刪除】統計數據檔案(CSV)？")
        if confirm:
            # 1. 清除 UI
            self.history_display.config(state=tk.NORMAL)
            self.history_display.delete('1.0', tk.END)
            self.history_display.config(state=tk.DISABLED)
            
            # 2. 刪除 CSV
            file_path = "sudoku_stats.csv"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    messagebox.showinfo("成功", "已清空紀錄與數據檔案！")
                except Exception as e:
                    messagebox.showerror("錯誤", f"無法刪除檔案：{e}")
            else:
                messagebox.showinfo("提示", "操作紀錄已清空（原本就沒有數據檔案）。")
            
            self.add_to_history("--- 紀錄已重設 ---")

    def show_analysis(self):
        """生成記憶力分析圖表"""
        file_path = "sudoku_stats.csv"
        if not os.path.exists(file_path):
            messagebox.showwarning("提示", "目前尚無數據，請先完成至少一局遊戲！")
            return

        try:
            df = pd.read_csv(file_path)
            if df.empty or len(df) < 1:
                messagebox.showinfo("提示", "數據不足，無法分析。")
                return

            df['效率指標'] = df['答對數'] / df['花費秒數'].replace(0, 1)

            plt.close('all')
            plt.figure(figsize=(10, 6))
            
            plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False

            plt.plot(df.index + 1, df['效率指標'], marker='o', linewidth=2, color='#1E88E5', label='記憶反應效率')
            plt.bar(df.index + 1, df['答錯數'] * 0.05, alpha=0.3, color='red', label='分心次數(量化)')

            plt.title("數獨練習：記憶力與專注度變化趨勢")
            plt.xlabel("練習次數 (Sessions)")
            plt.ylabel("表現得分")
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror("分析錯誤", f"讀取數據發生問題：{e}")

    def create_widgets(self):
        self.main_container = tk.Frame(self.master)
        self.main_container.pack(fill='both', expand=True)

        self.top_section = tk.Frame(self.main_container)
        self.top_section.pack(fill='both', expand=True, side=tk.TOP)

        self.game_area = tk.Frame(self.top_section, padx=10, pady=5)
        self.game_area.pack(side=tk.LEFT, fill='both', expand=True)

        self.record_area = tk.Frame(self.top_section, padx=10, pady=5)
        self.record_area.pack(side=tk.RIGHT, fill='y')

        # 1. 資訊列
        info_frame = tk.Frame(self.game_area)
        info_frame.pack(fill='x', pady=5)
        self.label_mistakes = tk.Label(info_frame, text="錯誤: 0/3", font=('Microsoft JhengHei', 12, 'bold'), fg="red")
        self.label_mistakes.pack(side=tk.LEFT, padx=10)
        self.label_timer = tk.Label(info_frame, text="時間: 00:00", font=('Microsoft JhengHei', 12))
        self.label_timer.pack(side=tk.RIGHT, padx=10)

        # 2. 數獨盤面
        self.board_frame = tk.Frame(self.game_area, bg="black", bd=2)
        self.board_frame.pack(pady=5)

        for r in range(9):
            for c in range(9):
                pdx = (3, 1) if c % 3 == 0 else (1, 1)
                pdy = (3, 1) if r % 3 == 0 else (1, 1)
                container = tk.Frame(self.board_frame, width=50, height=50, bg="white")
                container.grid(row=r, column=c, padx=(pdx[0], 1 if c%3!=2 else 3), pady=(pdy[0], 1 if r%3!=2 else 3))
                container.pack_propagate(False)

                val_l = tk.Label(container, text="", font=('Arial', 18, 'bold'), bg="white")
                val_l.place(relx=0.5, rely=0.5, anchor="center")
                
                note_l = tk.Label(container, text="", font=('Arial', 8), bg="white", fg="#888888")
                note_l.place(relx=0.5, rely=0.5, anchor="center")
                note_l.lower()

                self.cells[(r, c)] = {"frame": container, "val": val_l, "note": note_l}
                self.cell_data[(r, c)] = {"val": 0, "fixed": False, "notes": set()}

                for w in [container, val_l, note_l]:
                    w.bind("<Button-1>", lambda e, row=r, col=c: self.select_cell(row, col))

        # 3. 控制鈕
        ctrl_frame = tk.Frame(self.game_area)
        ctrl_frame.pack(pady=5)
        self.btn_pencil = tk.Button(ctrl_frame, text="鉛筆: OFF", width=10, command=self.toggle_pencil)
        self.btn_pencil.pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl_frame, text="橡皮擦", width=10, bg="#FFCDD2", command=self.clear_cell).pack(side=tk.LEFT, padx=5)
        
        # 分析與清除按鈕
        tk.Button(ctrl_frame, text="記憶力分析", width=12, bg="#C8E6C9", font=('Microsoft JhengHei', 9, 'bold'), 
                  command=self.show_analysis).pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl_frame, text="清除操作紀錄", width=12, bg="#EEEEEE", font=('Microsoft JhengHei', 9), 
                  command=self.clear_all_history).pack(side=tk.LEFT, padx=5)

        # 4. 數字按鈕區
        num_frame = tk.Frame(self.game_area)
        num_frame.pack(pady=5)
        for i in range(1, 10):
            btn = tk.Button(num_frame, text=str(i), width=4, font=('Arial', 12, 'bold'), bg="#FFF9C4",
                           command=lambda n=i: self.on_num_btn_click(n))
            btn.pack(side=tk.LEFT, padx=2)

        # 5. 右側歷史紀錄
        tk.Label(self.record_area, text="操作紀錄", font=('Microsoft JhengHei', 11, 'bold')).pack()
        self.history_display = scrolledtext.ScrolledText(self.record_area, width=28, height=30, font=('Consolas', 10), bg="#F8F9FA")
        self.history_display.pack(fill='both', expand=True)
        self.history_display.config(state=tk.DISABLED)

        self.master.bind("<Key>", self.handle_keypress)

    def select_cell(self, r, c):
        if self.selected_cell == (r, c):
            self.selected_cell, self.highlight_num = None, None
        else:
            self.selected_cell = (r, c)
            val = self.cell_data[(r, c)]["val"]
            self.highlight_num = val if val != 0 else None
        self.refresh_board_colors()

    def on_num_btn_click(self, num):
        if self.selected_cell:
            r, c = self.selected_cell
            if self.cell_data[(r, c)]["fixed"]: return 
            if self.pencil_mode:
                self.input_pencil_note(num)
            else:
                self.input_number(num)
            return
        self.highlight_num = None if self.highlight_num == num else num
        self.refresh_board_colors()

    def refresh_board_colors(self):
        for (r, c), cell in self.cells.items():
            val = self.cell_data[(r, c)]["val"]
            bg_color = "white"
            if self.highlight_num and val == self.highlight_num:
                bg_color = "#FFF176" 
            if self.selected_cell == (r, c):
                bg_color = "#BBDEFB" 
            cell["frame"].config(bg=bg_color)
            cell["val"].config(bg=bg_color)
            cell["note"].config(bg=bg_color)

    def input_number(self, num):
        r, c = self.selected_cell
        d, u = self.cell_data[(r, c)], self.cells[(r, c)]
        
        if num == self.solution[r][c]:
            d["val"] = num
            self.correct_count += 1
            u["val"].config(text=str(num), fg="blue")
            u["val"].lift()
            u["note"].config(text="")
            self.add_to_history(f"✓ ({r+1},{c+1}) 填入 {num}")
            self.highlight_num = num 
            self.check_win()
        else:
            self.mistakes += 1
            self.label_mistakes.config(text=f"錯誤: {self.mistakes}/3")
            self.add_to_history(f"❌ ({r+1},{c+1}) 錯誤: {num}")
            if self.mistakes >= 3:
                self.save_stats(status="Failed")
                messagebox.showerror("遊戲結束", "錯誤達 3 次，開新局！")
                self.new_game()
        self.refresh_board_colors()

    def input_pencil_note(self, num):
        r, c = self.selected_cell
        d = self.cell_data[(r, c)]
        if d["val"] != 0: return 
        if num in d["notes"]: d["notes"].remove(num)
        else: d["notes"].add(num)
        note_str = "".join(map(str, sorted(list(d["notes"]))))
        self.cells[(r, c)]["note"].config(text=note_str)
        self.cells[(r, c)]["note"].lift()

    def clear_cell(self):
        if self.selected_cell and not self.cell_data[self.selected_cell]["fixed"]:
            r, c = self.selected_cell
            self.cell_data[(r, c)].update({"val": 0, "notes": set()})
            self.cells[(r, c)]["val"].config(text="")
            self.cells[(r, c)]["note"].config(text="")
            self.refresh_board_colors()

    def add_to_history(self, msg):
        self.history_display.config(state=tk.NORMAL)
        t = time.strftime("%H:%M:%S")
        self.history_display.insert('1.0', f"[{t}] {msg}\n")
        self.history_display.config(state=tk.DISABLED)

    def toggle_pencil(self):
        self.pencil_mode = not self.pencil_mode
        self.btn_pencil.config(text=f"鉛筆: {'ON' if self.pencil_mode else 'OFF'}", 
                               bg="#B3E5FC" if self.pencil_mode else "SystemButtonFace")

    def handle_keypress(self, event):
        if self.input_lock: return
        if event.char.isdigit() and event.char != '0':
            self.input_lock = True
            self.on_num_btn_click(int(event.char))
            self.master.after(150, lambda: setattr(self, 'input_lock', False))
        elif event.keysym == "BackSpace":
            self.clear_cell()

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.label_timer.config(text=f"時間: {elapsed//60:02d}:{elapsed%60:02d}")
        self.master.after(1000, self.update_timer)

    def is_safe(self, b, r, c, n):
        for i in range(9):
            if b[r][i] == n or b[i][c] == n: return False
        sr, sc = 3*(r//3), 3*(c//3)
        for i in range(sr, sr+3):
            for j in range(sc, sc+3):
                if b[i][j] == n: return False
        return True

    def solve_board(self, b):
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    nums = list(range(1, 10)); random.shuffle(nums)
                    for n in nums:
                        if self.is_safe(b, r, c, n):
                            b[r][c] = n
                            if self.solve_board(b): return True
                            b[r][c] = 0
                    return False
        return True

    def new_game(self):
        self.mistakes, self.correct_count = 0, 0
        self.label_mistakes.config(text="錯誤: 0/3")
        self.start_time = time.time()
        self.selected_cell, self.highlight_num = None, None
        self.add_to_history("--- 新局開始 ---")
        
        self.solution = [[0]*9 for _ in range(9)]
        self.solve_board(self.solution)
        puzzle = [row[:] for row in self.solution]
        cells_list = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells_list)
        for i in range(40): puzzle[cells_list[i][0]][cells_list[i][1]] = 0
            
        for r in range(9):
            for c in range(9):
                d, u = self.cell_data[(r, c)], self.cells[(r, c)]
                d["notes"].clear(); u["note"].config(text="")
                if puzzle[r][c] != 0:
                    d.update({"val": puzzle[r][c], "fixed": True})
                    u["val"].config(text=str(puzzle[r][c]), fg="black")
                    u["val"].lift()
                else:
                    d.update({"val": 0, "fixed": False}); u["val"].config(text="")
        self.refresh_board_colors()

    def check_win(self):
        if all(self.cell_data[(r, c)]["val"] == self.solution[r][c] for r in range(9) for c in range(9)):
            self.save_stats(status="Win")
            messagebox.showinfo("恭喜", "完成挑戰！數據已存檔。")
            self.new_game()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("920x750")
    game = SudokuGame(root)
    root.mainloop()