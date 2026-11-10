import flet as ft
import sqlite3
import os
import datetime

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS classes (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, class_name TEXT, title TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, filename TEXT)''')
    
    classes = ["5-б", "5-в", "6-а", "6-б", "6-в", "7-а", "7-б", "7-в", "8-а", "8-б", "9-а", "9-б", "10-а", "10-б", "10-в", "11-а", "11-б"]
    for cls in classes:
        try:
            c.execute("INSERT INTO classes (name) VALUES (?)", (cls,))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def get_classes():
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("SELECT name FROM classes")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_notes(class_name):
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("SELECT id, title, content FROM notes WHERE class_name=?", (class_name,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_note(class_name, title, content):
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("INSERT INTO notes (class_name, title, content) VALUES (?, ?, ?)", (class_name, title, content))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()

def get_books():
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("SELECT id, filename FROM books")
    rows = c.fetchall()
    conn.close()
    return rows

def add_book(filename):
    conn = sqlite3.connect("teacher_pro.db")
    c = conn.cursor()
    c.execute("INSERT INTO books (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()

# --- ИНТЕРФЕЙС ---
def main(page: ft.Page):
    page.title = "Учитель Про"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    init_db()

    # Экраны
    def show_home():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Учитель Про"), bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
        
        page.add(
            ft.Container(height=20),
            ft.ElevatedButton("🚀 Начать урок", on_click=lambda _: show_classes(), width=300, height=50),
            ft.ElevatedButton("📚 Книги", on_click=lambda _: show_books(), width=300, height=50),
            ft.Container(height=20),
            ft.Text(f"Сегодня: {datetime.date.today().strftime('%d.%m.%Y')}", size=16, color=ft.colors.GREY_700),
            ft.Container(height=10),
            ft.Text("Календарь (расписание):", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("Пока не настроен. Скоро добавим!", color=ft.colors.GREY_500)
        )
        page.update()

    def show_classes():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Выберите класс"), bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: show_home()))
        
        classes = get_classes()
        grid = ft.GridView(expand=True, max_extent=120, child_aspect_ratio=1.5, spacing=10, run_spacing=10)
        for cls in classes:
            grid.controls.append(
                ft.ElevatedButton(
                    cls, 
                    on_click=lambda e, c=cls: show_class_notes(c), 
                    style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_100)
                )
            )
        page.add(grid)
        page.update()

    def show_class_notes(class_name):
        page.clean()
        page.appbar = ft.AppBar(
            title=ft.Text(f"Класс {class_name}"), 
            bgcolor=ft.colors.BLUE_700, 
            color=ft.colors.WHITE, 
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: show_classes()),
            actions=[ft.IconButton(ft.icons.ADD, on_click=lambda _: add_note_dialog(class_name))]
        )
        
        notes = get_notes(class_name)
        if not notes:
            page.add(ft.Text("Конспектов пока нет. Нажмите + чтобы добавить.", color=ft.colors.GREY_500))
        else:
            col = ft.Column(scroll=ft.ScrollMode.ALWAYS)
            for idx, (nid, title, content) in enumerate(notes):
                col.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            leading=ft.CircleAvatar(content=ft.Text(str(idx+1))),
                            title=ft.Text(f"Урок {idx+1}: {title}"),
                            subtitle=ft.Text(content[:50] + "..." if len(content) > 50 else content),
                            trailing=ft.IconButton(ft.icons.DELETE, on_click=lambda e, id=nid: delete_note_and_refresh(id, class_name)),
                        ),
                        margin=ft.margin.only(bottom=10)
                    )
                )
            page.add(col)
        page.update()

    def delete_note_and_refresh(note_id, class_name):
        delete_note(note_id)
        show_class_notes(class_name)

    def add_note_dialog(class_name):
        title_input = ft.TextField(label="Тема урока", hint_text="Например: Имя существительное")
        content_input = ft.TextField(label="Текст конспекта", multiline=True, min_lines=5, max_lines=10)

        def save(e):
            if title_input.value and content_input.value:
                add_note(class_name, title_input.value, content_input.value)
                page.dialog.open = False
                page.update()
                show_class_notes(class_name)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Заполните все поля!"), bgcolor=ft.colors.RED)
                page.snack_bar.open = True
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Новый конспект ({class_name})"),
            content=ft.Column([title_input, content_input], tight=True),
            actions=[
                ft.TextButton("Отмена", on_click=lambda _: close_dialog(dialog)),
                ft.ElevatedButton("Сохранить", on_click=save)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def close_dialog(dialog):
        dialog.open = False
        page.update()

    def show_books():
        page.clean()
        page.appbar = ft.AppBar(
            title=ft.Text("Книги"), 
            bgcolor=ft.colors.BLUE_700, 
            color=ft.colors.WHITE, 
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: show_home())
        )
        
        books = get_books()
        if not books:
            page.add(ft.Text("Книг пока нет. Добавьте названия книг (без загрузки файлов)."))
        else:
            col = ft.Column()
            for bid, fname in books:
                col.controls.append(ft.ListTile(title=ft.Text(fname), leading=ft.Icon(ft.icons.BOOK)))
            page.add(col)
        
        # Форма добавления
        book_input = ft.TextField(label="Название книги или путь к файлу")
        def add_b(e):
            if book_input.value:
                add_book(book_input.value)
                show_books()
        
        page.add(
            ft.Divider(),
            ft.Text("Добавить книгу:"),
            book_input,
            ft.ElevatedButton("Добавить", on_click=add_b)
        )
        page.update()

    show_home()

ft.app(target=main)
