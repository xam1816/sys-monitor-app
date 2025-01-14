import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import psutil
import tkinter as tk
from my_app import SysMonitorApp


class TestSysMonitorApp(unittest.TestCase):

    def setUp(self):
        """Создаём тестовое окружение."""
        self.root = tk.Tk()
        self.app = SysMonitorApp(self.root)
        self.app.conn = sqlite3.connect(":memory:")  # Временная база для тестов
        self.app.cursor = self.app.conn.cursor()
        self.app.cursor.execute('''CREATE TABLE monitor_data (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        timestamp TEXT,
                                        cpu REAL,
                                        ram_usage BIGINT,
                                        disk_usage BIGINT)''')

    def tearDown(self):
        """Закрываем приложение после тестов."""
        self.app.conn.close()
        self.root.destroy()

    @patch('psutil.cpu_percent', return_value=50.0)
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_update_info(self, mock_disk, mock_ram, mock_cpu):
        """Тест обновления информации о системе."""
        mock_ram.return_value = MagicMock(total=8 * 1024 ** 3, free=4 * 1024 ** 3)
        mock_disk.return_value = MagicMock(total=500 * 1024 ** 3, free=300 * 1024 ** 3)

        self.app.update_info()

        self.assertEqual(self.app.lbl_cpu.cget("text"), "ЦП: 50.0%")
        self.assertIn("GB", self.app.ram_lbl.cget("text"))
        self.assertIn("GB", self.app.disk_lbl.cget("text"))

    def test_write_data(self):
        """Тест записи данных в базу."""
        self.app.write_data(30.5, 4000000000, 3000000000)
        self.app.cursor.execute("SELECT * FROM monitor_data")
        rows = self.app.cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0][2], 30.5)

    def test_on_rec(self):
        """Тест функции записи данных."""
        self.app.on_rec()
        self.assertTrue(self.app.is_rec)
        self.assertEqual(self.app.btn_rec.cget("text"), "остановить\nзапись")
        self.app.on_rec()
        self.assertFalse(self.app.is_rec)
        self.assertEqual(self.app.btn_rec.cget("text"), "начать\nзапись")

    def test_view_history(self):
        """Тест открытия окна истории."""
        self.app.view_history()
        self.assertIsNotNone(self.app.history_window)
        self.assertTrue(self.app.history_window.winfo_exists())

    @patch('psutil.cpu_percent', return_value=10.0)
    def test_recording_data(self, mock_cpu):
        """Тест записи данных при активной записи."""
        self.app.is_rec = True
        self.app.update_info()
        self.app.cursor.execute("SELECT * FROM monitor_data")
        rows = self.app.cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0][2], 10.0)

    def test_timer_update(self):
        """Тест обновления таймера."""
        self.app.time_seconds = 5
        self.app.is_rec = True
        self.app.update_time()
        self.assertEqual(self.app.lbl_time_rec.cget("text"), "0:05")

    def test_close_app(self):
        """Тест закрытия приложения."""
        with patch.object(self.root, "destroy") as mock_destroy:
            self.app.on_close()
            mock_destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main()
