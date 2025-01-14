import tkinter as tk
from tkinter import ttk
import psutil
import sqlite3


class SysMonitorApp:
    def __init__(self, root:tk.Tk):
        # настраиваем параметры основного окна
        self.root = root
        # self.root.geometry('400x400')
        self.root.config(bg='black')
        self.root.title('Системный монитор')

        self.lbl_title = tk.Label(text='Уровень загруженности:', font=("Courier", 16, 'bold'), fg='lightgreen', bg='black')
        self.lbl_title.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        # лейблы для вывода информации на экран
        self.lbl_cpu = tk.Label(text='ЦП: ', font=("Courier", 14, 'bold'), fg='lightgreen', bg='black')
        self.lbl_cpu.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.ram_lbl = tk.Label(text='ОЗУ: ',font=("Courier", 14,'bold'), fg='lightgreen',bg='black')
        self.ram_lbl.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.disk_lbl = tk.Label(text='ПЗУ: ',font=("Courier", 14,'bold'), fg='lightgreen',bg='black')
        self.disk_lbl.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        # кнопка для записи
        self.btn_rec = tk.Button(text='начать\nзапись',font=("Courier", 12,'bold'), fg='lightgreen',bg='black',
                                 command=self.on_rec, width=10)
        self.btn_rec.grid(row=5, column=0, padx=10, pady=5, sticky="w")

        # кнопка просмотра записи
        self.btn_view_history = tk.Button(text='просмотр\nзаписей',font=("Courier", 12,'bold'), fg='lightgreen',bg='black',
                                          command=self.view_history, width=10)
        self.btn_view_history.grid(row=7, column=0, padx=10, pady=5,sticky="w")

        # лейбл таймера записи
        self.lbl_time_rec =tk.Label(text='', font=("Courier", 12,'bold'), fg='lightgreen',bg='black', width=10)
        self.lbl_time_rec.grid(row=6, column=0, padx=10, pady=5,sticky="w")

        # создаем таблицу в базе данных для записи
        self.conn = sqlite3.connect("system_monitor.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS monitor_data (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
                                        cpu REAL,
                                        ram_usage BIGINT,
                                        disk_usage BIGINT)''')
        self.conn.commit()

        # флаг состояния записи
        self.is_rec = False

        # окно для просмотра записей изначально None, чтобы отслеживать открыто или нет
        self.history_window = None

        # Начальное состояние таймера записи
        self.time_seconds = 0

        self.update_info()

    # записать в бд
    def write_data(self, cpu, ram, disk):
        self.cursor.execute("INSERT INTO monitor_data (cpu, ram_usage, disk_usage) VALUES (?, ?, ?)",
                            (cpu, ram, disk))
        self.conn.commit()

    # обновление информации
    def update_info(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        self.lbl_cpu.config(text=f'ЦП: {cpu}%')
        self.ram_lbl.config(text=f'ОЗУ: {ram.free / (1024 ** 3):.2f} GB /{ram.total / (1024 ** 3):.2f} GB')
        self.disk_lbl.config(text=f'ПЗУ: {disk.free / (1024 ** 3):.2f} GB / {disk.total / (1024 ** 3):.2f} GB')
        if self.is_rec:
            self.write_data(cpu, ram.used, disk.used)
        self.root.after(1000, self.update_info)

    # выполнить при нажатии на кнопку записи
    def on_rec(self):
        # если запись меняем флаг записи и текст кнопки
        self.is_rec = not self.is_rec
        self.btn_rec.config(text='остановить\nзапись' if self.is_rec else 'начать\nзапись')
        # если запись показать таймер иначе скрыть
        self.update_time()
        if not self.is_rec:
            self.time_seconds = 0
            self.lbl_time_rec.config(text='')

    # выполнить при нажатии на кнопку просмотр записей
    def view_history(self):
        if self.history_window and self.history_window.winfo_exists():
            return
        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("History Data")
        self.history_window.geometry("500x400")

        table = ttk.Treeview(self.history_window, columns=("ID", "Timestamp", "CPU Usage", "RAM Usage", "Disk Usage"),
                             show="headings")
        table.heading("ID", text="ID")
        table.heading("Timestamp", text="Timestamp")
        table.heading("CPU Usage", text="CPU Usage")
        table.heading("RAM Usage", text="RAM Usage")
        table.heading("Disk Usage", text="Disk Usage")

        table.pack(fill="both", expand=True)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM monitor_data")
        rows = cursor.fetchall()

        for row in rows:
            table.insert("", "end", values=row)

        close_button = tk.Button(self.history_window, text="Close", command=self.history_window.destroy)
        close_button.pack(pady=5)

    # обновить время таймера
    def update_time(self):
        if self.is_rec:
            minutes = self.time_seconds // 60
            seconds = self.time_seconds % 60
            time_str = f"{minutes}:{seconds:02d}"
            self.lbl_time_rec.config(text=time_str)
            self.time_seconds += 1
            self.root.after(1000, self.update_time)

    # выполнить при завершении программы
    def on_close(self):
        self.conn.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SysMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == '__main__':
    main()