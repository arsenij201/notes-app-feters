import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import os
import re
import sys


class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Заметки - Notes App | Created by FETERS")
        self.root.geometry("1200x700")

        # Установка иконки (если есть файл icon.ico)
        try:
            if getattr(sys, 'frozen', False):
                # Если запущено как exe
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        # Переменные для перетаскивания окна
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Цветовая схема
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#007acc',
            'hover': '#005a9e',
            'list_bg': '#1e1e1e',
            'entry_bg': '#3c3c3c',
            'button_bg': '#0e639c'
        }

        self.setup_styles()

        # Определение пути для сохранения данных
        if getattr(sys, 'frozen', False):
            # Если запущено как exe, сохраняем в папку с программой
            self.notes_file = os.path.join(os.path.dirname(sys.executable), "notes.json")
        else:
            self.notes_file = "notes.json"

        self.notes = []
        self.current_note_id = None

        self.load_notes()
        self.create_widgets()
        self.refresh_notes_list()

        # Настраиваем перетаскивание
        self.setup_drag_drop()

    def setup_drag_drop(self):
        """Настройка перетаскивания окна"""
        if hasattr(self, 'header_frame'):
            self.header_frame.bind('<ButtonPress-1>', self.start_drag)
            self.header_frame.bind('<B1-Motion>', self.on_drag)

        if hasattr(self, 'status_bar'):
            self.status_bar.bind('<ButtonPress-1>', self.start_drag)
            self.status_bar.bind('<B1-Motion>', self.on_drag)

    def start_drag(self, event):
        """Запоминаем начальную позицию мыши"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        """Перемещаем окно"""
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка цветов для различных элементов
        self.root.configure(bg=self.colors['bg'])

        style.configure('Custom.TFrame', background=self.colors['bg'])
        style.configure('Left.TFrame', background=self.colors['bg'])
        style.configure('Right.TFrame', background=self.colors['bg'])

        style.configure('Custom.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['fg'],
                        font=('Segoe UI', 10))

        style.configure('Title.TLabel',
                        background=self.colors['bg'],
                        foreground=self.colors['accent'],
                        font=('Segoe UI', 12, 'bold'))

        style.configure('Accent.TButton',
                        background=self.colors['button_bg'],
                        foreground=self.colors['fg'],
                        borderwidth=0,
                        focuscolor='none',
                        font=('Segoe UI', 9))

        style.map('Accent.TButton',
                  background=[('active', self.colors['hover'])])

        style.configure('Custom.TEntry',
                        fieldbackground=self.colors['entry_bg'],
                        foreground=self.colors['fg'],
                        borderwidth=1,
                        font=('Segoe UI', 10))

    def create_widgets(self):
        # Создание главного контейнера
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Верхняя панель с заголовком
        self.header_frame = tk.Frame(main_container, bg=self.colors['accent'], height=60)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        self.header_frame.pack_propagate(False)

        title_label = tk.Label(self.header_frame,
                               text="📝 Менеджер заметок",
                               font=('Segoe UI', 18, 'bold'),
                               bg=self.colors['accent'],
                               fg=self.colors['fg'])
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Основной контейнер с двумя панелями
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Левая панель - список заметок
        left_panel = tk.Frame(content_frame, bg=self.colors['bg'], width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Поиск
        search_frame = tk.Frame(left_panel, bg=self.colors['bg'])
        search_frame.pack(fill=tk.X, pady=(0, 15))

        search_icon = tk.Label(search_frame, text="🔍",
                               bg=self.colors['bg'], fg=self.colors['fg'],
                               font=('Segoe UI', 12))
        search_icon.pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_notes())
        search_entry = tk.Entry(search_frame,
                                textvariable=self.search_var,
                                bg=self.colors['entry_bg'],
                                fg=self.colors['fg'],
                                font=('Segoe UI', 10),
                                relief=tk.FLAT,
                                insertbackground=self.colors['fg'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Заголовок списка заметок
        list_header = tk.Label(left_panel,
                               text="📋 Мои заметки",
                               font=('Segoe UI', 11, 'bold'),
                               bg=self.colors['bg'],
                               fg=self.colors['fg'])
        list_header.pack(anchor=tk.W, pady=(0, 5))

        # Список заметок с прокруткой
        list_container = tk.Frame(left_panel, bg=self.colors['list_bg'])
        list_container.pack(fill=tk.BOTH, expand=True)

        self.notes_listbox = tk.Listbox(list_container,
                                        bg=self.colors['list_bg'],
                                        fg=self.colors['fg'],
                                        selectbackground=self.colors['accent'],
                                        selectforeground=self.colors['fg'],
                                        font=('Segoe UI', 10),
                                        relief=tk.FLAT,
                                        highlightthickness=0,
                                        borderwidth=0)

        scrollbar = tk.Scrollbar(list_container,
                                 orient=tk.VERTICAL,
                                 command=self.notes_listbox.yview,
                                 bg=self.colors['bg'],
                                 troughcolor=self.colors['bg'])
        self.notes_listbox.configure(yscrollcommand=scrollbar.set)

        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)

        # Правая панель - редактирование
        right_panel = tk.Frame(content_frame, bg=self.colors['bg'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Поле заголовка
        title_frame = tk.Frame(right_panel, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_icon = tk.Label(title_frame, text="📌",
                              bg=self.colors['bg'], fg=self.colors['fg'],
                              font=('Segoe UI', 12))
        title_icon.pack(side=tk.LEFT, padx=(0, 5))

        title_label = tk.Label(title_frame, text="Заголовок:",
                               bg=self.colors['bg'], fg=self.colors['fg'],
                               font=('Segoe UI', 10, 'bold'))
        title_label.pack(side=tk.LEFT)

        self.title_entry = tk.Entry(title_frame,
                                    bg=self.colors['entry_bg'],
                                    fg=self.colors['fg'],
                                    font=('Segoe UI', 11),
                                    relief=tk.FLAT,
                                    insertbackground=self.colors['fg'])
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # Поле содержимого
        content_frame_right = tk.Frame(right_panel, bg=self.colors['bg'])
        content_frame_right.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        content_icon = tk.Label(content_frame_right, text="📄",
                                bg=self.colors['bg'], fg=self.colors['fg'],
                                font=('Segoe UI', 12))
        content_icon.pack(side=tk.LEFT, padx=(0, 5), anchor=tk.N)

        content_label = tk.Label(content_frame_right, text="Содержимое:",
                                 bg=self.colors['bg'], fg=self.colors['fg'],
                                 font=('Segoe UI', 10, 'bold'))
        content_label.pack(side=tk.LEFT, anchor=tk.N)

        text_container = tk.Frame(content_frame_right, bg=self.colors['entry_bg'])
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.content_text = tk.Text(text_container,
                                    bg=self.colors['entry_bg'],
                                    fg=self.colors['fg'],
                                    font=('Segoe UI', 10),
                                    relief=tk.FLAT,
                                    wrap=tk.WORD,
                                    insertbackground=self.colors['fg'])

        text_scrollbar = tk.Scrollbar(text_container,
                                      orient=tk.VERTICAL,
                                      command=self.content_text.yview,
                                      bg=self.colors['bg'],
                                      troughcolor=self.colors['bg'])
        self.content_text.configure(yscrollcommand=text_scrollbar.set)

        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Панель кнопок
        button_frame = tk.Frame(right_panel, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)

        button_style = {'bg': self.colors['button_bg'],
                        'fg': self.colors['fg'],
                        'font': ('Segoe UI', 9),
                        'relief': tk.FLAT,
                        'cursor': 'hand2',
                        'padx': 15,
                        'pady': 8}

        tk.Button(button_frame, text="➕ Новая", command=self.new_note, **button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="💾 Сохранить", command=self.save_note, **button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="🗑️ Удалить", command=self.delete_note, **button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="📤 Экспорт MD", command=self.export_to_md, **button_style).pack(side=tk.LEFT,
                                                                                                      padx=5)
        tk.Button(button_frame, text="📥 Импорт MD", command=self.import_from_md, **button_style).pack(side=tk.LEFT,
                                                                                                       padx=5)

        # Статус бар
        self.status_bar = tk.Frame(main_container, bg=self.colors['accent'], height=25)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        self.status_bar.pack_propagate(False)

        status_label = tk.Label(self.status_bar,
                                text="✨ Создатель: FETERS | Версия 2.0 | Все права защищены ✨",
                                bg=self.colors['accent'],
                                fg=self.colors['fg'],
                                font=('Segoe UI', 8))
        status_label.pack(pady=3)

        self.stats_label = tk.Label(self.status_bar,
                                    text="",
                                    bg=self.colors['accent'],
                                    fg=self.colors['fg'],
                                    font=('Segoe UI', 8))
        self.stats_label.pack(side=tk.RIGHT, padx=10, pady=3)

    def update_stats(self):
        """Обновление статистики заметок"""
        total = len(self.notes)
        self.stats_label.config(text=f"📊 Всего заметок: {total}")

    def load_notes(self):
        """Загрузка заметок из файла"""
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            else:
                self.notes = []
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить заметки: {str(e)}")
            self.notes = []

    def save_notes_to_file(self):
        """Сохранение заметок в файл"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
            self.update_stats()
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заметки: {str(e)}")
            return False

    def refresh_notes_list(self):
        """Обновление списка заметок"""
        self.notes_listbox.delete(0, tk.END)
        for note in self.notes:
            display_text = f"📝 {note['title']} [{note['date']}]"
            self.notes_listbox.insert(tk.END, display_text)
        self.update_stats()

    def filter_notes(self):
        """Фильтрация заметок по поисковому запросу"""
        search_text = self.search_var.get().lower()
        self.notes_listbox.delete(0, tk.END)

        for note in self.notes:
            if (search_text in note['title'].lower() or
                    search_text in note['content'].lower()):
                display_text = f"📝 {note['title']} [{note['date']}]"
                self.notes_listbox.insert(tk.END, display_text)

    def on_note_select(self, event):
        """Обработка выбора заметки из списка"""
        selection = self.notes_listbox.curselection()
        if selection:
            index = selection[0]
            search_text = self.search_var.get().lower()
            filtered_notes = []
            for note in self.notes:
                if (search_text in note['title'].lower() or
                        search_text in note['content'].lower()):
                    filtered_notes.append(note)

            if index < len(filtered_notes):
                note = filtered_notes[index]
                for original_note in self.notes:
                    if original_note['id'] == note['id']:
                        self.current_note_id = original_note['id']
                        self.title_entry.delete(0, tk.END)
                        self.title_entry.insert(0, original_note['title'])
                        self.content_text.delete(1.0, tk.END)
                        self.content_text.insert(1.0, original_note['content'])
                        break

    def new_note(self):
        """Создание новой заметки"""
        self.current_note_id = None
        self.title_entry.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)
        self.title_entry.focus()

    def save_note(self):
        """Сохранение текущей заметки"""
        title = self.title_entry.get().strip()
        content = self.content_text.get(1.0, tk.END).strip()

        if not title:
            messagebox.showwarning("Предупреждение", "Введите заголовок заметки")
            return

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        if self.current_note_id is None:
            new_id = max([note['id'] for note in self.notes], default=0) + 1
            new_note = {
                'id': new_id,
                'title': title,
                'content': content,
                'date': current_date
            }
            self.notes.append(new_note)
            self.current_note_id = new_id
        else:
            for note in self.notes:
                if note['id'] == self.current_note_id:
                    note['title'] = title
                    note['content'] = content
                    note['date'] = current_date
                    break

        if self.save_notes_to_file():
            self.refresh_notes_list()
            self.filter_notes()
            messagebox.showinfo("Успех", "Заметка сохранена")

    def delete_note(self):
        """Удаление текущей заметки"""
        if self.current_note_id is None:
            messagebox.showwarning("Предупреждение", "Выберите заметку для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту заметку?"):
            self.notes = [note for note in self.notes if note['id'] != self.current_note_id]
            if self.save_notes_to_file():
                self.current_note_id = None
                self.title_entry.delete(0, tk.END)
                self.content_text.delete(1.0, tk.END)
                self.refresh_notes_list()
                self.filter_notes()
                messagebox.showinfo("Успех", "Заметка удалена")

    def export_to_md(self):
        """Экспорт заметок в Markdown файлы"""
        if not self.notes:
            messagebox.showwarning("Предупреждение", "Нет заметок для экспорта")
            return

        folder = filedialog.askdirectory(title="Выберите папку для экспорта")
        if folder:
            try:
                exported_count = 0
                for note in self.notes:
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', note['title'])
                    filename = f"{safe_title}_{note['date'].replace(':', '-')}.md"
                    filepath = os.path.join(folder, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# {note['title']}\n\n")
                        f.write(f"*Дата: {note['date']}*\n\n")
                        f.write(f"---\n\n")
                        f.write(note['content'])
                        f.write(f"\n\n---\n*Экспортировано с помощью Notes App by FETERS*")

                    exported_count += 1

                messagebox.showinfo("Успех", f"✅ Экспортировано {exported_count} заметок в папку:\n{folder}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать заметки: {str(e)}")

    def import_from_md(self):
        """Импорт заметок из Markdown файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите Markdown файлы для импорта",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )

        if files:
            imported_count = 0
            errors = []

            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    lines = content.split('\n')
                    title = ""
                    note_content = ""
                    date = datetime.now().strftime("%Y-%m-%d %H:%M")

                    for i, line in enumerate(lines):
                        if line.startswith('# '):
                            title = line[2:].strip()
                            note_content = '\n'.join(lines[i + 1:])
                            break

                    if not title:
                        title = os.path.splitext(os.path.basename(filepath))[0]
                        note_content = content

                    note_lines = note_content.split('\n')
                    if note_lines and note_lines[0].startswith('*Дата:'):
                        note_content = '\n'.join(note_lines[1:]).strip()

                    note_content = re.sub(r'\n---\n\*Экспортировано с помощью Notes App by FETERS\*$', '', note_content)

                    new_id = max([note['id'] for note in self.notes], default=0) + 1
                    new_note = {
                        'id': new_id,
                        'title': title,
                        'content': note_content.strip(),
                        'date': date
                    }
                    self.notes.append(new_note)
                    imported_count += 1

                except Exception as e:
                    errors.append(f"{os.path.basename(filepath)}: {str(e)}")

            if self.save_notes_to_file():
                self.refresh_notes_list()
                self.filter_notes()

                if errors:
                    messagebox.showwarning("Частичный успех",
                                           f"✅ Импортировано {imported_count} заметок.\n\n❌ Ошибки:\n" + "\n".join(
                                               errors))
                else:
                    messagebox.showinfo("Успех", f"✅ Импортировано {imported_count} заметок")


def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()