import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import traceback


class YchotAvto:
    def __init__(s, root):
        s.root = root
        s.root.title("Учет автомобилей. Регистрация продажи.")
        s.root.geometry("750x750")

        s.conn = sqlite3.connect("databd.db")
        s.cursor = s.conn.cursor()

        s.create_tables()
        s.create_widgets()
        s.load_data()

    def create_tables(s):
        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Discount (
                id_discount INTEGER PRIMARY KEY,
                title TEXT,
                size INTEGER
            )"""
        )

        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Stamps (
                id_stamp INTEGER PRIMARY KEY,
                name_stamp TEXT
            )"""
        )

        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Cars (
                id_car INTEGER PRIMARY KEY,
                id_stamp INTEGER,
                year_release INTEGER,
                model TEXT,
                price TEXT,
                FOREIGN KEY (id_stamp) REFERENCES Stamps (id_stamp)
            )"""
        )

        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Clients (
                id_client INTEGER PRIMARY KEY,
                fio TEXT NOT NULL,
                date_of_birth TEXT,
                passport TEXT,
                phone TEXT,
                id_sale INTEGER,
                FOREIGN KEY (id_sale) REFERENCES Discount (id_discount)
            )"""
        )

        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Sellers (
                id_seller INTEGER PRIMARY KEY,
                fio TEXT NOT NULL,
                phone TEXT
            )"""
        )

        s.cursor.execute(
            """CREATE TABLE IF NOT EXISTS Buys (
                id_buy INTEGER PRIMARY KEY,
                id_client INTEGER,
                id_seller INTEGER,
                id_car INTEGER,
                date_buy TEXT,
                FOREIGN KEY (id_car) REFERENCES Cars (id_car),
                FOREIGN KEY (id_client) REFERENCES Clients (id_client),
                FOREIGN KEY (id_seller) REFERENCES Sellers (id_seller)
            )"""
        )
        s.conn.commit()

    def create_widgets(s):
        # Создаем вкладки
        s.notebook = ttk.Notebook()
        s.notebook.pack(fill="both", expand=True)

        # Создаем фреймы
        s.Clients_frame = ttk.Frame(s.notebook)
        s.Sellers_frame = ttk.Frame(s.notebook)
        s.Discount_frame = ttk.Frame(s.notebook)
        s.Stamps_frame = ttk.Frame(s.notebook)
        s.Cars_frame = ttk.Frame(s.notebook)
        s.Buys_frame = ttk.Frame(s.notebook)
        s.Search_frame = ttk.Frame(s.notebook)

        s.notebook.add(s.Clients_frame, text="Клиенты")
        s.notebook.add(s.Sellers_frame, text="Консультанты")
        s.notebook.add(s.Discount_frame, text="Скидки")
        s.notebook.add(s.Stamps_frame, text="Марки")
        s.notebook.add(s.Cars_frame, text="Машины")
        s.notebook.add(s.Buys_frame, text="Покупки")
        s.notebook.add(s.Search_frame, text="Поиск")

        s.create_Clients_table()
        s.create_Sellers_table()
        s.create_Discount_table()
        s.create_Stamps_table()
        s.create_Cars_table()
        s.create_Buys_table()
        s.create_Search_table()

        control_frame = tk.Frame(s.root)
        control_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(control_frame, text="Обновить данные", command=s.load_data).pack(
            side="left", padx=7
        )
        tk.Button(control_frame, text="Добавить запись", command=s.add_record).pack(
            side="left", padx=7
        )
        tk.Button(
            control_frame, text="Редактировать запись", command=s.edit_record
        ).pack(side="left", padx=7)
        tk.Button(control_frame, text="Удалить запись", command=s.delete_record).pack(
            side="left", padx=7
        )

        tk.Button(control_frame, text="Отчет", command=s.generate_html_report).pack(
            side="left", padx=7
        )

        # Добавленная кнопка для показа непроданных машин
        tk.Button(
            control_frame, text="Непроданные машины", command=s.show_unsold_cars
        ).pack(side="left", padx=7)

        tk.Button(
            control_frame, text="Проданные машины", command=s.show_sold_cars
        ).pack(side="left", padx=7)

        tk.Button(control_frame, text="Выход", command=s.root.quit).pack(
            side="left", padx=7
        )

    def show_sold_cars(s):
        # Создаем новое окно для отображения проданных машин
        sold_window = tk.Toplevel(s.root)
        sold_window.title("Проданные автомобили")
        sold_window.geometry("1000x600")

        # Получаем список проданных машин с дополнительной информацией
        s.cursor.execute(
            """
            SELECT 
                st.name_stamp, 
                c.model, 
                c.year_release, 
                c.price,
                cl.fio AS buyer,
                sl.fio AS seller,
                b.date_buy
            FROM Cars c
            JOIN Stamps st ON c.id_stamp = st.id_stamp
            JOIN Buys b ON c.id_car = b.id_car
            JOIN Clients cl ON b.id_client = cl.id_client
            JOIN Sellers sl ON b.id_seller = sl.id_seller
            ORDER BY b.date_buy DESC
        """
        )
        sold_cars = s.cursor.fetchall()

        # Создаем Treeview для отображения данных
        columns = (
            "Марка",
            "Модель",
            "Год выпуска",
            "Цена",
            "Покупатель",
            "Продавец",
            "Дата продажи",
        )
        tree = ttk.Treeview(sold_window, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(
                col, width=120 if col not in ["Покупатель", "Продавец"] else 150
            )

        for car in sold_cars:
            tree.insert("", tk.END, values=car)

        tree.pack(fill="both", expand=True)

        # Добавляем кнопку закрытия
        tk.Button(sold_window, text="Закрыть", command=sold_window.destroy).pack(
            pady=10
        )

    def show_unsold_cars(s):
        # Создаем новое окно для отображения непроданных машин
        unsold_window = tk.Toplevel(s.root)
        unsold_window.title("Непроданные автомобили")
        unsold_window.geometry("800x400")

        # Получаем список непроданных машин
        s.cursor.execute(
            """
            SELECT c.id_car, st.name_stamp, c.model, c.year_release, c.price 
            FROM Cars c
            JOIN Stamps st ON c.id_stamp = st.id_stamp
            WHERE c.id_car NOT IN (SELECT id_car FROM Buys)
        """
        )
        unsold_cars = s.cursor.fetchall()

        # Создаем Treeview для отображения данных
        columns = ("ID", "Марка", "Модель", "Год выпуска", "Цена")
        tree = ttk.Treeview(unsold_window, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        for car in unsold_cars:
            tree.insert("", tk.END, values=car)

        tree.pack(fill="both", expand=True)

        # Добавляем кнопку закрытия
        tk.Button(unsold_window, text="Закрыть", command=unsold_window.destroy).pack(
            pady=10
        )
        # Привязываем обновление комбобоксов при переключении на вкладку поиска
        s.notebook.bind("<<NotebookTabChanged>>", s.on_tab_changed)

    def edit_record(s):
        current_tab = s.notebook.index(s.notebook.select())

        if current_tab == 0:  # Клиенты
            selected_item = s.Clients_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            # Получаем данные выбранной записи
            values = s.Clients_tree.item(selected_item[0])["values"]
            fio = values[0]

            # Находим ID клиента
            s.cursor.execute("SELECT id_client FROM Clients WHERE fio = ?", (fio,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            # Открываем окно редактирования
            s.edit_Client(result[0], values)

        elif current_tab == 1:  # Консультанты
            selected_item = s.Sellers_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            values = s.Sellers_tree.item(selected_item[0])["values"]
            fio = values[0]

            s.cursor.execute("SELECT id_seller FROM Sellers WHERE fio = ?", (fio,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            s.edit_Seller(result[0], values)

        elif current_tab == 2:  # Скидки
            selected_item = s.Discount_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            values = s.Discount_tree.item(selected_item[0])["values"]
            title = values[0]

            s.cursor.execute(
                "SELECT id_discount FROM Discount WHERE title = ?", (title,)
            )
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            s.edit_Discount(result[0], values)

        elif current_tab == 3:  # Марки
            selected_item = s.Stamps_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            values = s.Stamps_tree.item(selected_item[0])["values"]
            name_stamp = values[0]

            s.cursor.execute(
                "SELECT id_stamp FROM Stamps WHERE name_stamp = ?", (name_stamp,)
            )
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            s.edit_Stamp(result[0], values)

        elif current_tab == 4:  # Машины
            selected_item = s.Cars_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            values = s.Cars_tree.item(selected_item[0])["values"]
            model = values[2]  # Модель как уникальный идентификатор

            s.cursor.execute("SELECT id_car FROM Cars WHERE model = ?", (model,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            s.edit_Car(result[0], values)

        elif current_tab == 5:  # Покупки
            selected_item = s.Buys_tree.selection()
            if not selected_item:
                messagebox.showwarning(
                    "Предупреждение", "Выберите запись для редактирования"
                )
                return

            values = s.Buys_tree.item(selected_item[0])["values"]
            date_buy = values[3]  # Дата покупки как часть идентификатора

            # Здесь нужно более точное определение записи, так как дата может повторяться
            # Используем комбинацию клиента, консультанта, авто и даты
            s.cursor.execute(
                """
                SELECT id_buy FROM Buys 
                JOIN Clients ON Buys.id_client = Clients.id_client
                JOIN Sellers ON Buys.id_seller = Sellers.id_seller
                JOIN Cars ON Buys.id_car = Cars.id_car
                WHERE Clients.fio = ? AND Sellers.fio = ? AND Cars.model = ? AND Buys.date_buy = ?
            """,
                (values[0], values[1], values[2], date_buy),
            )

            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror(
                    "Ошибка", "Не удалось найти запись для редактирования"
                )
                return

            s.edit_Buy(result[0], values)

        else:
            messagebox.showwarning(
                "Предупреждение", "Редактирование недоступно для этой вкладки"
            )

    def edit_Client(s, client_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать клиента")
        edit_window.geometry("400x400")

        # Получаем доступные скидки
        s.cursor.execute("SELECT id_discount, title FROM Discount")
        Discount = s.cursor.fetchall()
        dis_options = [r[1] for r in Discount]
        dis_dict = {r[1]: r[0] for r in Discount}

        # Поля для редактирования
        tk.Label(edit_window, text="ФИО:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        fio_entry = tk.Entry(edit_window)
        fio_entry.grid(row=0, column=1, padx=5, pady=5)
        fio_entry.insert(0, current_values[0])

        tk.Label(edit_window, text="Дата Рождения:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        date_of_birth_entry = tk.Entry(edit_window)
        date_of_birth_entry.grid(row=1, column=1, padx=5, pady=5)
        date_of_birth_entry.insert(0, current_values[1])

        tk.Label(edit_window, text="Паспорт:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        passport_entry = tk.Entry(edit_window)
        passport_entry.grid(row=2, column=1, padx=5, pady=5)
        passport_entry.insert(0, current_values[2])

        tk.Label(edit_window, text="Телефон:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        phone_entry = tk.Entry(edit_window)
        phone_entry.grid(row=3, column=1, padx=5, pady=5)
        phone_entry.insert(0, current_values[3])

        tk.Label(edit_window, text="Скидка:").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        sale_combobox = ttk.Combobox(edit_window, values=dis_options)
        sale_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        # Устанавливаем текущее значение скидки
        current_discount = current_values[4] if len(current_values) > 4 else ""
        sale_combobox.set(current_discount)

        def save():
            try:
                id_sale = dis_dict.get(sale_combobox.get(), None)

                s.cursor.execute(
                    """
                    UPDATE Clients 
                    SET fio = ?, date_of_birth = ?, passport = ?, phone = ?, id_sale = ?
                    WHERE id_client = ?
                """,
                    (
                        fio_entry.get(),
                        date_of_birth_entry.get(),
                        passport_entry.get(),
                        phone_entry.get(),
                        id_sale,
                        client_id,
                    ),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=6, columnspan=2, pady=10
        )

    def edit_Seller(s, seller_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать консультанта")

        tk.Label(edit_window, text="ФИО:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        fio_entry = tk.Entry(edit_window)
        fio_entry.grid(row=0, column=1, padx=5, pady=5)
        fio_entry.insert(0, current_values[0])

        tk.Label(edit_window, text="Телефон:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        phone_entry = tk.Entry(edit_window)
        phone_entry.grid(row=1, column=1, padx=5, pady=5)
        phone_entry.insert(0, current_values[1])

        def save():
            try:
                s.cursor.execute(
                    """
                    UPDATE Sellers 
                    SET fio = ?, phone = ?
                    WHERE id_seller = ?
                """,
                    (fio_entry.get(), phone_entry.get(), seller_id),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=2, columnspan=2, pady=10
        )

    def edit_Discount(s, discount_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать скидку")

        tk.Label(edit_window, text="Наименование:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        title_entry = tk.Entry(edit_window)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        title_entry.insert(0, current_values[0])

        tk.Label(edit_window, text="Процент:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        size_entry = tk.Entry(edit_window)
        size_entry.grid(row=1, column=1, padx=5, pady=5)
        size_entry.insert(0, current_values[1])

        def save():
            try:
                s.cursor.execute(
                    """
                    UPDATE Discount 
                    SET title = ?, size = ?
                    WHERE id_discount = ?
                """,
                    (title_entry.get(), size_entry.get(), discount_id),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=2, columnspan=2, pady=10
        )

    def edit_Stamp(s, stamp_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать марку")

        tk.Label(edit_window, text="Марка:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        name_stamp_entry = tk.Entry(edit_window)
        name_stamp_entry.grid(row=0, column=1, padx=5, pady=5)
        name_stamp_entry.insert(0, current_values[0])

        def save():
            try:
                s.cursor.execute(
                    """
                    UPDATE Stamps 
                    SET name_stamp = ?
                    WHERE id_stamp = ?
                """,
                    (name_stamp_entry.get(), stamp_id),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=1, columnspan=2, pady=10
        )

    def edit_Car(s, car_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать машину")
        edit_window.geometry("400x400")

        # Получаем доступные марки
        s.cursor.execute("SELECT id_stamp, name_stamp FROM Stamps")
        Stamps = s.cursor.fetchall()
        st_options = [r[1] for r in Stamps]
        st_dict = {r[1]: r[0] for r in Stamps}

        # Поля для редактирования
        tk.Label(edit_window, text="Марка:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        stamp_combobox = ttk.Combobox(edit_window, values=st_options)
        stamp_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        stamp_combobox.set(current_values[0])  # Устанавливаем текущую марку

        tk.Label(edit_window, text="Год реализации:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        year_release_entry = tk.Entry(edit_window)
        year_release_entry.grid(row=1, column=1, padx=5, pady=5)
        year_release_entry.insert(0, current_values[1])

        tk.Label(edit_window, text="Модель:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        model_entry = tk.Entry(edit_window)
        model_entry.grid(row=2, column=1, padx=5, pady=5)
        model_entry.insert(0, current_values[2])

        tk.Label(edit_window, text="Цена:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        price_entry = tk.Entry(edit_window)
        price_entry.grid(row=3, column=1, padx=5, pady=5)
        price_entry.insert(0, current_values[3])

        def save():
            try:
                id_stamp = st_dict[stamp_combobox.get()]

                s.cursor.execute(
                    """
                    UPDATE Cars 
                    SET id_stamp = ?, year_release = ?, model = ?, price = ?
                    WHERE id_car = ?
                """,
                    (
                        id_stamp,
                        year_release_entry.get(),
                        model_entry.get(),
                        price_entry.get(),
                        car_id,
                    ),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=4, columnspan=2, pady=10
        )

    def edit_Buy(s, buy_id, current_values):
        edit_window = tk.Toplevel(s.root)
        edit_window.title("Редактировать покупку")
        edit_window.geometry("400x400")

        # Получаем данные для комбобоксов
        s.cursor.execute("SELECT id_client, fio FROM Clients")
        Clients = s.cursor.fetchall()
        cl_options = [r[1] for r in Clients]
        cl_dict = {r[1]: r[0] for r in Clients}

        s.cursor.execute("SELECT id_seller, fio FROM Sellers")
        Sellers = s.cursor.fetchall()
        sl_options = [r[1] for r in Sellers]
        sl_dict = {r[1]: r[0] for r in Sellers}

        s.cursor.execute("SELECT id_car, model FROM Cars")
        Cars = s.cursor.fetchall()
        cr_options = [r[1] for r in Cars]
        cr_dict = {r[1]: r[0] for r in Cars}

        # Поля для редактирования
        tk.Label(edit_window, text="Покупатель:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        client_combobox = ttk.Combobox(edit_window, values=cl_options)
        client_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        client_combobox.set(current_values[0])

        tk.Label(edit_window, text="Консультант:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        seller_combobox = ttk.Combobox(edit_window, values=sl_options)
        seller_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        seller_combobox.set(current_values[1])

        tk.Label(edit_window, text="Автомобиль:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        car_combobox = ttk.Combobox(edit_window, values=cr_options)
        car_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        car_combobox.set(current_values[2])

        tk.Label(edit_window, text="Дата покупки:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        date_buy_entry = tk.Entry(edit_window)
        date_buy_entry.grid(row=3, column=1, padx=5, pady=5)
        date_buy_entry.insert(0, current_values[3])

        def save():
            try:
                id_client = cl_dict[client_combobox.get()]
                id_seller = sl_dict[seller_combobox.get()]
                id_car = cr_dict[car_combobox.get()]

                s.cursor.execute(
                    """
                    UPDATE Buys 
                    SET id_client = ?, id_seller = ?, id_car = ?, date_buy = ?
                    WHERE id_buy = ?
                """,
                    (id_client, id_seller, id_car, date_buy_entry.get(), buy_id),
                )
                s.conn.commit()
                s.load_data()
                edit_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить запись: {str(e)}")

        tk.Button(edit_window, text="Сохранить", command=save).grid(
            row=4, columnspan=2, pady=10
        )

    def on_tab_changed(s, event):
        # Обновляем комбобоксы при переключении на вкладку поиска
        if s.notebook.index(s.notebook.select()) == 6:  # 6 - индекс вкладки поиска
            s.update_search_comboboxes()

    def create_Clients_table(s):
        s.Clients_tree = ttk.Treeview(
            s.Clients_frame,
            columns=(
                "fio",
                "date_of_birth",
                "passport",
                "phone",
                "id_sale",
            ),
            show="headings",
        )

        s.Clients_tree.heading(
            "fio",
            text="Фамилия Имя Отчество",
            command=lambda: s.sort_treeview(s.Clients_tree, "fio", False),
        )
        s.Clients_tree.heading(
            "date_of_birth",
            text="Дата рождения",
            command=lambda: s.sort_treeview(s.Clients_tree, "date_of_birth", False),
        )
        s.Clients_tree.heading(
            "passport",
            text="Паспортные данные",
            command=lambda: s.sort_treeview(s.Clients_tree, "passport", False),
        )
        s.Clients_tree.heading(
            "phone",
            text="Телефон",
            command=lambda: s.sort_treeview(s.Clients_tree, "phone", False),
        )
        s.Clients_tree.heading(
            "id_sale",
            text="Скидка",
            command=lambda: s.sort_treeview(s.Clients_tree, "id_sale", False),
        )

        s.Clients_tree.column("fio", width=150)
        s.Clients_tree.column("date_of_birth", width=100)
        s.Clients_tree.column("passport", width=100)
        s.Clients_tree.column("phone", width=100)
        s.Clients_tree.column("id_sale", width=50)

        s.Clients_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            s.Clients_frame, orient="vertical", command=s.Clients_tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        s.Clients_tree.configure(yscrollcommand=scrollbar.set)

    def create_Sellers_table(s):
        s.Sellers_tree = ttk.Treeview(
            s.Sellers_frame,
            columns=("fio", "phone"),
            show="headings",
        )

        s.Sellers_tree.heading(
            "fio",
            text="Фамилия Имя Отчество",
            command=lambda: s.sort_treeview(s.Sellers_tree, "fio", False),
        )
        s.Sellers_tree.heading(
            "phone",
            text="Телефон",
            command=lambda: s.sort_treeview(s.Sellers_tree, "phone", False),
        )

        s.Sellers_tree.column("fio", width=150)
        s.Sellers_tree.column("phone", width=100)

        s.Sellers_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            s.Sellers_frame, orient="vertical", command=s.Sellers_tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        s.Sellers_tree.configure(yscrollcommand=scrollbar.set)

    def create_Discount_table(s):
        s.Discount_tree = ttk.Treeview(
            s.Discount_frame,
            columns=("title", "size"),
            show="headings",
        )

        s.Discount_tree.heading(
            "title",
            text="Наименование",
            command=lambda: s.sort_treeview(s.Discount_tree, "title", False),
        )
        s.Discount_tree.heading(
            "size",
            text="Процент скидки",
            command=lambda: s.sort_treeview(s.Discount_tree, "size", False),
        )

        s.Discount_tree.column("title", width=150)
        s.Discount_tree.column("size", width=100)

        s.Discount_tree.pack(fill="both", expand=True)

    def create_Stamps_table(s):
        s.Stamps_tree = ttk.Treeview(
            s.Stamps_frame,
            columns=("name_stamp"),
            show="headings",
        )

        s.Stamps_tree.heading(
            "name_stamp",
            text="Марка",
            command=lambda: s.sort_treeview(s.Stamps_tree, "name_stamp", False),
        )

        s.Stamps_tree.column("name_stamp", width=150)

        s.Stamps_tree.pack(fill="both", expand=True)

    def create_Cars_table(s):
        s.Cars_tree = ttk.Treeview(
            s.Cars_frame,
            columns=("id_stamp", "year_release", "model", "price"),
            show="headings",
        )

        s.Cars_tree.heading(
            "id_stamp",
            text="Марка",
            command=lambda: s.sort_treeview(s.Cars_tree, "id_stamp", False),
        )
        s.Cars_tree.heading(
            "year_release",
            text="Год выпуска",
            command=lambda: s.sort_treeview(s.Cars_tree, "year_release", False),
        )
        s.Cars_tree.heading(
            "model",
            text="Наименование",
            command=lambda: s.sort_treeview(s.Cars_tree, "model", False),
        )
        s.Cars_tree.heading(
            "price",
            text="Цена",
            command=lambda: s.sort_treeview(s.Cars_tree, "price", False),
        )

        s.Cars_tree.column("id_stamp", width=100)
        s.Cars_tree.column("year_release", width=100)
        s.Cars_tree.column("model", width=150)
        s.Cars_tree.column("price", width=100)

        s.Cars_tree.pack(fill="both", expand=True)

    def create_Buys_table(s):
        s.Buys_tree = ttk.Treeview(
            s.Buys_frame,
            columns=("id_client", "id_seller", "id_car", "date_buy"),
            show="headings",
        )

        s.Buys_tree.heading(
            "id_client",
            text="Клиент",
            command=lambda: s.sort_treeview(s.Buys_tree, "id_client", False),
        )
        s.Buys_tree.heading(
            "id_seller",
            text="Консультант",
            command=lambda: s.sort_treeview(s.Buys_tree, "id_seller", False),
        )
        s.Buys_tree.heading(
            "id_car",
            text="Авто",
            command=lambda: s.sort_treeview(s.Buys_tree, "id_car", False),
        )
        s.Buys_tree.heading(
            "date_buy",
            text="Дата покупки",
            command=lambda: s.sort_treeview(s.Buys_tree, "date_buy", False),
        )

        s.Buys_tree.column("id_client", width=100)
        s.Buys_tree.column("id_seller", width=100)
        s.Buys_tree.column("id_car", width=100)
        s.Buys_tree.column("date_buy", width=100)

        s.Buys_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            s.Buys_frame, orient="vertical", command=s.Buys_tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        s.Buys_tree.configure(yscrollcommand=scrollbar.set)

    def sort_treeview(s, tree, col, reverse):
        # Получаем все элементы из Treeview
        l = [(tree.set(k, col), k) for k in tree.get_children("")]

        # Пробуем отсортировать как числа, если не получается - как строки
        try:
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        # Перемещаем элементы в отсортированном порядке
        for index, (val, k) in enumerate(l):
            tree.move(k, "", index)

        # Меняем направление сортировки для следующего клика
        tree.heading(col, command=lambda: s.sort_treeview(tree, col, not reverse))

    def create_Search_table(s):
        # Создание интерфейса для поиска
        main_frame = ttk.Frame(s.Search_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        search_frame = ttk.LabelFrame(main_frame, text="Параметры поиска")
        search_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(search_frame, text="Покупатель:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        s.Buyer_combobox = ttk.Combobox(search_frame)
        s.Buyer_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(search_frame, text="Консультант:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        s.Seller_combobox = ttk.Combobox(search_frame)
        s.Seller_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(search_frame, text="Авто:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        s.Avt_combobox = ttk.Combobox(search_frame)
        s.Avt_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        ttk.Label(search_frame, text="Дата покупки:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        s.date_entry = ttk.Entry(search_frame)
        s.date_entry.grid(row=3, column=1, padx=5, pady=5, sticky="we")
        s.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # обновляем списки
        s.update_search_comboboxes()

        results_frame = ttk.LabelFrame(main_frame, text="Результаты поиска")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # отображение результатов поиска
        s.search_tree = ttk.Treeview(
            results_frame,
            columns=("client", "seller", "car", "date"),
            show="headings",
        )

        s.search_tree.heading(
            "client",
            text="Покупатель",
            command=lambda: s.sort_treeview(s.search_tree, "client", False),
        )
        s.search_tree.heading(
            "seller",
            text="Консультант",
            command=lambda: s.sort_treeview(s.search_tree, "seller", False),
        )
        s.search_tree.heading(
            "car",
            text="Авто",
            command=lambda: s.sort_treeview(s.search_tree, "car", False),
        )
        s.search_tree.heading(
            "date",
            text="Дата покупки",
            command=lambda: s.sort_treeview(s.search_tree, "date", False),
        )

        s.search_tree.column("client", width=150)
        s.search_tree.column("seller", width=150)
        s.search_tree.column("car", width=150)
        s.search_tree.column("date", width=100)

        s.search_tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=s.search_tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        s.search_tree.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=4, column=0, columnspan=6, pady=10)

        ttk.Button(button_frame, text="Поиск", command=s.perform_search).pack(
            side="left", padx=5
        )

    def update_search_comboboxes(s):
        # Populate comboboxes with data from the database
        s.Buyer_combobox["values"] = [
            client[1]
            for client in s.cursor.execute(
                "SELECT id_client, fio FROM Clients"
            ).fetchall()
        ]
        s.Seller_combobox["values"] = [
            seller[1]
            for seller in s.cursor.execute(
                "SELECT id_seller, fio FROM Sellers"
            ).fetchall()
        ]
        s.Avt_combobox["values"] = [
            f"{car[2]} ({car[1]})"  # Формат: "Модель (Марка)"
            for car in s.cursor.execute(
                """SELECT Cars.id_car, Stamps.name_stamp, Cars.model 
                   FROM Cars JOIN Stamps ON Cars.id_stamp = Stamps.id_stamp"""
            ).fetchall()
        ]

    def perform_search(s):
        # Очищаем предыдущие результаты
        for item in s.search_tree.get_children():
            s.search_tree.delete(item)

        # Получаем параметры поиска
        client_name = s.Buyer_combobox.get()
        seller_name = s.Seller_combobox.get()
        car_info = s.Avt_combobox.get()
        date_buy = s.date_entry.get()

        # Формируем базовый запрос
        query = """
            SELECT 
                Clients.fio AS client_name,
                Sellers.fio AS seller_name,
                Stamps.name_stamp || ' ' || Cars.model AS car_info,
                Buys.date_buy
            FROM Buys
            JOIN Clients ON Buys.id_client = Clients.id_client
            JOIN Sellers ON Buys.id_seller = Sellers.id_seller
            JOIN Cars ON Buys.id_car = Cars.id_car
            JOIN Stamps ON Cars.id_stamp = Stamps.id_stamp
            WHERE 1=1
        """

        params = []

        # Добавляем условия в запрос в зависимости от введенных параметров
        if client_name:
            query += " AND Clients.fio = ?"
            params.append(client_name)
        if seller_name:
            query += " AND Sellers.fio = ?"
            params.append(seller_name)
        if car_info:
            # Разбираем информацию об авто (формат: "Модель (Марка)")
            model = car_info.split(" (")[0]
            query += " AND Cars.model = ?"
            params.append(model)
        if date_buy:
            query += " AND Buys.date_buy = ?"
            params.append(date_buy)

        try:
            # Выполняем запрос
            results = s.cursor.execute(query, params).fetchall()

            # Если результатов нет, показываем сообщение
            if not results:
                messagebox.showinfo("Информация", "По вашему запросу ничего не найдено")
                return

            # Добавляем результаты в Treeview
            for result in results:
                s.search_tree.insert("", "end", values=result)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при выполнении поиска: {str(e)}")

    def load_data(s):
        # Очищаем все таблицы перед загрузкой новых данных
        for tree in [
            s.Clients_tree,
            s.Sellers_tree,
            s.Discount_tree,
            s.Stamps_tree,
            s.Cars_tree,
            s.Buys_tree,
            s.search_tree,
        ]:
            if tree:
                for item in tree.get_children():
                    tree.delete(item)

        # Загрузка данных из бд
        s.cursor.execute("SELECT * FROM Sellers")
        Sellers = s.cursor.fetchall()
        for sel in Sellers:
            s.Sellers_tree.insert("", "end", values=sel[1:])

        s.cursor.execute("SELECT * FROM Discount")
        Discount = s.cursor.fetchall()
        for dis in Discount:
            s.Discount_tree.insert("", "end", values=dis[1:])

        s.cursor.execute("SELECT * FROM Buys")
        Buys = s.cursor.fetchall()
        for bab in Buys:
            s.Buys_tree.insert("", "end", values=bab[1:])

        s.cursor.execute(
            """
            SELECT 
                Clients.fio, 
                Clients.date_of_birth, 
                Clients.passport, 
                Clients.phone, 
                COALESCE(Discount.title, '')  -- Заменяем NULL на пустую строку
            FROM Clients
            LEFT JOIN Discount ON Clients.id_sale = Discount.id_discount
            """
        )
        Clients = s.cursor.fetchall()
        for cl in Clients:
            s.Clients_tree.insert("", "end", values=cl)

        s.cursor.execute("SELECT * FROM Stamps")
        Stamps = s.cursor.fetchall()
        for st in Stamps:
            s.Stamps_tree.insert("", "end", values=st[1:])

        s.cursor.execute(
            """
            SELECT 
                Stamps.name_stamp,
                Cars.year_release,
                Cars.model,
                Cars.price
            FROM Cars
            JOIN Stamps ON Cars.id_stamp = Stamps.id_stamp
        """
        )
        Cars = s.cursor.fetchall()
        for cr in Cars:
            s.Cars_tree.insert("", "end", values=cr)

        s.update_search_comboboxes()

    def add_record(s):
        # добавление новой записи
        current_tab = s.notebook.index(s.notebook.select())

        if current_tab == 5:
            s.add_Buys()
        elif current_tab == 0:
            s.add_Clients()
        elif current_tab == 3:
            s.add_Stamps()
        elif current_tab == 4:
            s.add_Cars()
        elif current_tab == 2:
            s.add_Discount()
        elif current_tab == 1:
            s.add_Sellers()

    def add_Stamps(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить Марку")

        tk.Label(add_window, text="Марка:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        name_stamp = tk.Entry(add_window)
        name_stamp.grid(row=0, column=1, padx=5, pady=5)

        def save():
            if not name_stamp.get():
                messagebox.showwarning(
                    "Предупреждение", "Поле 'Марка' не может быть пустым."
                )
                return
            try:
                s.cursor.execute(
                    "INSERT INTO Stamps (name_stamp) VALUES (?)",
                    (name_stamp.get(),),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror("Ошибка", f"Не удалось добавить Марку: {str(e)}")

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=2, columnspan=2, pady=10
        )

    def add_Sellers(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить Консультанта")

        tk.Label(add_window, text="ФИО:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        fio = tk.Entry(add_window)
        fio.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Телефон:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        phone = tk.Entry(add_window)
        phone.grid(row=1, column=1, padx=5, pady=5)

        def save():
            if not fio.get() or not phone.get():
                messagebox.showwarning(
                    "Предупреждение", "Пожалуйста, заполните все поля."
                )
                return

            try:
                s.cursor.execute(
                    "INSERT INTO Sellers (fio, phone) VALUES (?, ?)",
                    (fio.get(), phone.get()),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно добавлена")
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror(
                    "Ошибка", f"Не удалось добавить Консультанта: {str(e)}"
                )

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=5, columnspan=2, pady=10
        )

    def add_Discount(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить Скидочку")

        tk.Label(add_window, text="Наименование:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        title = tk.Entry(add_window)
        title.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Процент:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        size = tk.Entry(add_window)
        size.grid(row=1, column=1, padx=5, pady=5)

        def save():
            if not title.get() or not size.get():
                messagebox.showwarning(
                    "Предупреждение", "Пожалуйста, заполните все поля."
                )
                return

            try:
                s.cursor.execute(
                    "INSERT INTO Discount (title, size) VALUES (?, ?)",
                    (title.get(), size.get()),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно добавлена")
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror("Ошибка", f"Не удалось добавить скидку: {str(e)}")

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=5, columnspan=2, pady=10
        )

    def add_Clients(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить клиента")
        add_window.geometry("400x400")

        s.cursor.execute("SELECT id_discount, title FROM Discount")
        Discount = s.cursor.fetchall()
        dis_options = [r[1] for r in Discount]
        dis_dict = {r[1]: r[0] for r in Discount}

        tk.Label(add_window, text="ФИО:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        fio = tk.Entry(add_window)
        fio.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Дата Рождения:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        date_of_birth = tk.Entry(add_window)
        date_of_birth.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Паспорт:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        passport = tk.Entry(add_window)
        passport.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Телефон:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        phone = tk.Entry(add_window)
        phone.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Скидка:").grid(
            row=4, column=0, padx=5, pady=5, sticky="e"
        )
        sale = ttk.Combobox(add_window, values=dis_options)
        sale.grid(row=4, column=1, padx=5, pady=5, sticky="we")

        def save():
            if (
                not fio.get()
                or not date_of_birth.get()
                or not passport.get()
                or not phone.get()
            ):
                messagebox.showwarning(
                    "Предупреждение", "Пожалуйста, заполните все поля."
                )
                return

            try:
                id_sale = dis_dict.get(
                    sale.get(), None
                )  # Если скидка не выбрана, будет None

                s.cursor.execute(
                    "INSERT INTO Clients (fio, date_of_birth, passport, phone, id_sale) VALUES (?, ?, ?, ?, ?)",
                    (
                        fio.get(),
                        date_of_birth.get(),
                        passport.get(),
                        phone.get(),
                        id_sale,
                    ),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно добавлена")
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror("Ошибка", f"Не удалось добавить клиента: {str(e)}")

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=6, columnspan=2, pady=10
        )

    def add_Cars(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить машину")
        add_window.geometry("400x400")

        s.cursor.execute("SELECT id_stamp, name_stamp FROM Stamps")
        Stamps = s.cursor.fetchall()
        st_options = [r[1] for r in Stamps]
        st_dict = {r[1]: r[0] for r in Stamps}

        tk.Label(add_window, text="Марка:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        st = ttk.Combobox(add_window, values=st_options)
        st.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        tk.Label(add_window, text="Год реализации:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        year_release = tk.Entry(add_window)
        year_release.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Модель:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        model = tk.Entry(add_window)
        model.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(add_window, text="Цена:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        price = tk.Entry(add_window)
        price.grid(row=3, column=1, padx=5, pady=5)

        def save():
            if (
                not st.get()
                or not year_release.get()
                or not model.get()
                or not price.get()
            ):
                messagebox.showwarning(
                    "Предупреждение", "Пожалуйста, заполните все поля."
                )
                return

            try:
                id_stamp = st_dict[st.get()]

                s.cursor.execute(
                    "INSERT INTO Cars (id_stamp, year_release, model, price) VALUES (?, ?, ?, ?)",
                    (id_stamp, year_release.get(), model.get(), price.get()),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно добавлена")
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror("Ошибка", f"Не удалось добавить машину: {str(e)}")

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=6, columnspan=2, pady=10
        )

    def add_Buys(s):
        add_window = tk.Toplevel(s.root)
        add_window.title("Добавить покупочку")
        add_window.geometry("400x400")

        s.cursor.execute("SELECT id_car, model FROM Cars")
        Cars = s.cursor.fetchall()
        cr_options = [r[1] for r in Cars]
        cr_dict = {r[1]: r[0] for r in Cars}

        tk.Label(add_window, text="Машина:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        cr = ttk.Combobox(add_window, values=cr_options)
        cr.grid(row=2, column=1, padx=5, pady=5, sticky="we")

        s.cursor.execute("SELECT id_client, fio FROM Clients")
        Clients = s.cursor.fetchall()
        cl_options = [r[1] for r in Clients]
        cl_dict = {r[1]: r[0] for r in Clients}

        tk.Label(add_window, text="Покупатель:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        cl = ttk.Combobox(add_window, values=cl_options)
        cl.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        s.cursor.execute("SELECT id_seller, fio FROM Sellers")
        Sellers = s.cursor.fetchall()
        sl_options = [r[1] for r in Sellers]
        sl_dict = {r[1]: r[0] for r in Sellers}

        tk.Label(add_window, text="Консультант:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        sl = ttk.Combobox(add_window, values=sl_options)
        sl.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        tk.Label(add_window, text="Дата покупочки:").grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )
        date_buy = tk.Entry(add_window)
        date_buy.grid(row=3, column=1, padx=5, pady=5)

        def save():
            if not cl.get() or not sl.get() or not cr.get() or not date_buy.get():
                messagebox.showwarning(
                    "Предупреждение", "Пожалуйста, заполните все поля."
                )
                return

            try:
                id_client = cl_dict[cl.get()]
                id_seller = sl_dict[sl.get()]
                id_car = cr_dict[cr.get()]

                s.cursor.execute(
                    "INSERT INTO Buys (id_client, id_seller, id_car, date_buy) VALUES (?, ?, ?, ?)",
                    (id_client, id_seller, id_car, date_buy.get()),
                )
                s.conn.commit()
                s.load_data()
                add_window.destroy()
                messagebox.showinfo("Успех", "Запись успешно добавлена")
            except Exception as e:
                print(e)  # Вывод ошибки в консоль
                messagebox.showerror("Ошибка", f"Не удалось добавить покупку: {str(e)}")

        tk.Button(add_window, text="Сохранить", command=save).grid(
            row=6, columnspan=2, pady=10
        )

    def __del__(s):
        # Закрытие соединения с БД
        s.conn.close()

    def delete_record(s):
        current_tab = s.notebook.index(s.notebook.select())

        if current_tab == 0:
            tree = s.Clients_tree
            table = "Clients"
            id_col = "id_client"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return

            fio = tree.item(selected_item[0])["values"][0]
            s.cursor.execute("SELECT id_client FROM Clients WHERE fio = ?", (fio,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        elif current_tab == 1:
            tree = s.Sellers_tree
            table = "Sellers"
            id_col = "id_seller"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            fio = tree.item(selected_item[0])["values"][0]
            s.cursor.execute("SELECT id_seller FROM Sellers WHERE fio = ?", (fio,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        elif current_tab == 2:
            tree = s.Discount_tree
            table = "Discount"
            id_col = "id_discount"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            title = tree.item(selected_item[0])["values"][0]
            s.cursor.execute(
                "SELECT id_discount FROM Discount WHERE title = ?", (title,)
            )
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        elif current_tab == 3:
            tree = s.Stamps_tree
            table = "Stamps"
            id_col = "id_stamp"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            name_stamp = tree.item(selected_item[0])["values"][0]
            s.cursor.execute(
                "SELECT id_stamp FROM Stamps WHERE name_stamp = ?", (name_stamp,)
            )
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        elif current_tab == 4:
            tree = s.Cars_tree
            table = "Cars"
            id_col = "id_car"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            model = tree.item(selected_item[0])["values"][0]
            s.cursor.execute("SELECT id_car FROM Cars WHERE model = ?", (model,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        elif current_tab == 5:
            tree = s.Buys_tree
            table = "Buys"
            id_col = "id_buy"

            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            date_buy = tree.item(selected_item[0])["values"][0]
            s.cursor.execute("SELECT id_buy FROM Buys WHERE date_buy = ?", (date_buy,))
            result = s.cursor.fetchone()
            if not result:
                messagebox.showerror("Ошибка", "Не удалось найти запись для удаления")
                return
            item_id = result[0]

        else:
            messagebox.showwarning(
                "Предупреждение", "Нельзя удалять записи из результатов поиска"
            )
            return

        if messagebox.askyesno(
            "Подтверждение", "Вы уверены, что хотите удалить эту запись?"
        ):
            try:
                # Удаление записи
                s.cursor.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (item_id,))
                s.conn.commit()
                s.load_data()
                messagebox.showinfo("Успех", "Запись успешно удалена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить запись: {str(e)}")

    def generate_html_report(s):
        try:
            # Get sold cars data
            s.cursor.execute(
                """
                SELECT 
                    st.name_stamp, 
                    c.model, 
                    c.year_release, 
                    c.price,
                    cl.fio AS buyer,
                    sl.fio AS seller,
                    b.date_buy
                FROM Cars c
                JOIN Stamps st ON c.id_stamp = st.id_stamp
                JOIN Buys b ON c.id_car = b.id_car
                JOIN Clients cl ON b.id_client = cl.id_client
                JOIN Sellers sl ON b.id_seller = sl.id_seller
                ORDER BY b.date_buy DESC
            """
            )
            sold_cars = s.cursor.fetchall()

            # Get sales statistics
            s.cursor.execute("SELECT COUNT(*) FROM Buys")
            total_sold = s.cursor.fetchone()[0]

            s.cursor.execute(
                """
                SELECT Stamps.name_stamp, COUNT(*) 
                FROM Buys
                JOIN Cars ON Buys.id_car = Cars.id_car
                JOIN Stamps ON Cars.id_stamp = Stamps.id_stamp
                GROUP BY Stamps.name_stamp
                ORDER BY COUNT(*) DESC
            """
            )
            sales_by_brand = s.cursor.fetchall()

            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Отчет по проданным автомобилям</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; text-align: center; }}
                    h2 {{ color: #3498db; border-bottom: 1px solid #3498db; padding-bottom: 5px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .stats {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .stat-item {{ margin-bottom: 10px; }}
                </style>
            </head>
            <body>
                <h1>Отчет по проданным автомобилям</h1>
                <p>Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="stats">
                    <h2>Статистика продаж</h2>
                    <div class="stat-item"><strong>Всего продано автомобилей:</strong> {total_sold}</div>
                    
                    <h3>Продажи по маркам:</h3>
                    <ul>
            """

            for brand, count in sales_by_brand:
                html_content += f"<li><strong>{brand}:</strong> {count} авто</li>"

            html_content += """
                    </ul>
                </div>
                
                <h2>Детализация продаж</h2>
                <table>
                    <tr>
                        <th>Марка</th>
                        <th>Модель</th>
                        <th>Год выпуска</th>
                        <th>Цена</th>
                        <th>Покупатель</th>
                        <th>Продавец</th>
                        <th>Дата продажи</th>
                    </tr>
            """

            for car in sold_cars:
                html_content += f"""
                    <tr>
                        <td>{car[0]}</td>
                        <td>{car[1]}</td>
                        <td>{car[2]}</td>
                        <td>{car[3]}</td>
                        <td>{car[4]}</td>
                        <td>{car[5]}</td>
                        <td>{car[6]}</td>
                    </tr>
                """

            html_content += """
                </table>
            </body>
            </html>
            """

            # Save HTML file
            report_filename = (
                f"sold_cars_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Open in default browser
            #  webbrowser.open_new_tab("file://" + os.path.abspath(report_filename))

            messagebox.showinfo(
                "Успех", f"HTML отчет сохранен в файл: {report_filename}"
            )

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось сформировать HTML отчет: {str(e)}"
            )
            print(traceback.format_exc())


if __name__ == "__main__":
    root = tk.Tk()
    app = YchotAvto(root)
    root.mainloop()
