import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, END
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy import stats

class DietApp:
    def __init__(self, root):
        #root deve essere un oggetto Tk()
        self.root = root
        self.root.title("Programma Dieta")
        self.root.geometry("900x680")
        
        # Applica tema scuro alla finestra principale
        self.root.configure(bg="#121214")

       # Definiamo il nome della cartella dei dati
        self.data_folder = "Dati_Dieta"
        
        # Se la cartella non esiste, la crea automaticamente
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        # Percorsi file aggiornati dentro la sottocartella
        self.files = {
            'prices': os.path.join(self.data_folder, 'food_prices.json'),
            'weights': os.path.join(self.data_folder, 'wrecord.json'),
            'nvalues': os.path.join(self.data_folder, 'nvalues.json'),
            'eaten': os.path.join(self.data_folder, 'eaten_lists.json'),
            'calories': os.path.join(self.data_folder, 'calories.json'),
            'pasti': os.path.join(self.data_folder, 'pasti.json'),
            'plan': os.path.join(self.data_folder, 'planner.json'),
            'constraints': os.path.join(self.data_folder, 'constraints.json'),
            'porzioni': os.path.join(self.data_folder, 'porzioni_piano.json')
        }
        # Inizializzazione dati
        self.load_data()

        # Configurazione Stile TTK (per Treeview e altri widget avanzati)
        self.setup_styles()

        # Navigation Bar (persistente in alto)
        self.nav_frame = tk.Frame(self.root, bg="#121214")
        self.nav_frame.pack(fill="x", side="top", padx=20, pady=(15, 0))
        
        self.tabs = {}
        schede = [
            ("Scheda principale", self.show_main_screen),
            ("Diario Alimentare", self.show_food_screen),
            ("Storico Pasti", self.show_history_screen),
            ("Piano Settimanale", self.show_planner_screen),
            ("Database Alimenti", self.show_database_screen)]
        for tab_name, command in schede :
            btn = tk.Button(
                self.nav_frame, text=tab_name, command=command,
                bg="#1a1a1e", fg="#a0a0a5", activebackground="#252529", activeforeground="white",
                relief="flat", font=("Segoe UI", 10, "bold"), bd=0, padx=18, pady=10, cursor="hand2"
            )
            btn.pack(side="left", padx=3)
            self.tabs[tab_name] = btn

        # Separatore sottile sotto la nav bar
        sep = tk.Frame(self.root, height=1, bg="#252529")
        sep.pack(fill="x", padx=20, pady=(5, 15))

        # Container principale (per le varie schermate)
        self.main_frame = tk.Frame(self.root, bg="#121214")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Mostra la prima scheda
        self.show_main_screen()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        
        # Configurazione Treeview (Piano Settimanale)
        style.configure("Treeview", 
                        background="#1a1a1e", 
                        foreground="white", 
                        rowheight=28, 
                        fieldbackground="#1a1a1e",
                        bordercolor="#252529",
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.map('Treeview', 
                  background=[('selected', '#3b82f6')], 
                  foreground=[('selected', 'white')])
        
        style.configure("Treeview.Heading", 
                        background="#252529", 
                        foreground="white", 
                        font=('Segoe UI', 10, 'bold'),
                        bordercolor="#121214",
                        borderwidth=1)

    def set_active_tab(self, active_name):
        #serve a mostrare con colore diverso la scheda in uso
        for name, btn in self.tabs.items():
            if name == active_name:
                btn.config(bg="#3b82f6", fg="white")
            else:
                btn.config(bg="#1a1a1e", fg="#a0a0a5")

    def look_for(self, path, default=None):
        if default is None:
            default = {}
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = default
        else:
            data = default
        return data

    def record(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare i dati: {e}")

    def load_data(self):
        self.weights = self.look_for(self.files['weights'], [])
        self.calories = self.look_for(self.files['calories'], [])
        self.nvalues = self.look_for(self.files['nvalues'], {})
        self.prices = self.look_for(self.files['prices'], {})
        self.constraints = self.look_for(self.files['constraints'], {})

        # Carica pasti del giorno
        all_eaten = self.look_for(self.files['eaten'], {})
        self.today_str = datetime.now().strftime("%Y-%m-%d")
        self.today_eaten = all_eaten.get(self.today_str, [])

    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_screen(self, tab_name, render_func):
        self.clear_screen()
        self.set_active_tab(tab_name)
        # Configura grid del container principale per espansione
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)
        render_func()

    # --- WIDGET CREATION HELPERS ---
    def create_label(self, parent, text, font=("Segoe UI", 10), fg="white", bg="#1a1a1e"):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg)

    def create_hint(self, parent, text, bg="#121214"):
        return self.create_label(parent, text, font=("Segoe UI", 9, "italic"), fg="#6b7280", bg=bg)

    def create_entry(self, parent, font=("Segoe UI", 11)):
        return tk.Entry(
            parent, bg="#252529", fg="white", insertbackground="white",
            relief="flat", highlightthickness=1, highlightbackground="#3f3f46",
            highlightcolor="#3b82f6", font=font
        )

    def create_button(self, parent, text, command, bg="#3b82f6", fg="white", cursor="hand2"):
        active_map = {
            "#3b82f6": "#2563eb",
            "#10b981": "#059669",
            "#ef4444": "#dc2626",
            "#7c3aed": "#6d28d9",
            "#0e7490": "#0c6680",
        }
        return tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=active_map.get(bg, "#27272a"),
            activeforeground="white", font=("Segoe UI", 10, "bold"), 
            relief="flat", bd=0, padx=12, pady=6, cursor=cursor
        )

    def create_listbox(self, parent, width=50, height=10):
        return tk.Listbox(
            parent, bg="#252529", fg="white", selectbackground="#3b82f6", selectforeground="white",
            relief="flat", highlightthickness=1, highlightbackground="#3f3f46",
            highlightcolor="#3b82f6", font=("Segoe UI", 10), width=width, height=height
        )

    # --- MAIN SCREEN (SCHEDA PRINCIPALE) ---
    def show_main_screen(self):
        self.load_data()
        self.show_screen("Scheda principale", self._render_main_screen)

    def _render_main_screen(self):
        # Card Input (in alto a sinistra)
        input_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=20, pady=20)
        input_card.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        input_card.grid_columnconfigure(1, weight=1)
        input_card.grid_columnconfigure(4, weight=1)

        # Sezione Peso
        self.create_label(input_card, "Registra Peso (kg):", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        w_entry = self.create_entry(input_card)
        w_entry.grid(row=0, column=1, padx=(0, 15), sticky="ew")
        
        btn_w = self.create_button(input_card, "Registra", command=lambda: self.record_weight(w_entry.get()), bg="#10b981")
        btn_w.grid(row=0, column=2, padx=(0, 30))

        # Sezione Calorie
        self.create_label(input_card, "Registra Calorie (kcal):", font=("Segoe UI", 11, "bold")).grid(row=0, column=3, sticky="w", padx=(0, 10))
        c_entry = self.create_entry(input_card)
        c_entry.grid(row=0, column=4, padx=(0, 15), sticky="ew")
        
        btn_c = self.create_button(input_card, "Registra", command=lambda: self.record_calories(c_entry.get()), bg="#3b82f6")
        btn_c.grid(row=0, column=5)

        # Suggerimenti iniziali
        hint_frame = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=8)
        hint_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.create_hint(hint_frame,
            "Per iniziare registra giorno per giorno la massa corporea e le calorie ingerite. "
            "Puoi pianificare i pasti nella scheda Piano Settimanale. "
            "Puoi aiutarti nel calcolare le calorie mangiate giorno per giorno con gli strumenti presenti nella scheda Diario Alimentare.",
            bg="#1a1a1e"
        ).pack()

        # Grafico (in mezzo, espandibile)
        self.render_plot()

        # Pasti pianificati per oggi (a destra del grafico)
        self.render_today_plan()

        # Statistiche (in basso)
        if len(self.weights) > 1:
            self.render_stats()
        else:
            stats_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
            stats_card.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(15, 0))
            self.create_label(stats_card, "Fornisci almeno due record di peso per sbloccare le statistiche del trend.", 
                              font=("Segoe UI", 10, "italic"), fg="#a0a0a5").pack()

    def render_plot(self):
        if not self.weights:
            empty_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529")
            empty_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=15)
            empty_card.grid_columnconfigure(0, weight=1)
            empty_card.grid_rowconfigure(0, weight=1)
            self.create_label(empty_card, "Nessun dato di peso registrato disponibile per il grafico.", 
                              font=("Segoe UI", 11, "italic"), fg="#a0a0a5").grid(row=0, column=0, pady=60)
            return

        fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=100, facecolor='#1a1a1e')
        ax.set_facecolor('#1a1a1e')

        # Caricamento e ordinamento dei dati per data
        dates = []
        y_vals = []
        for item in self.weights:
            try:
                dates.append(datetime.fromisoformat(item[0]))
                y_vals.append(float(item[1]))
            except (ValueError, TypeError):
                continue

        if not dates:
            empty_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529")
            empty_card.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=15)
            self.create_label(empty_card, "Nessun dato di peso valido disponibile.", 
                              font=("Segoe UI", 11, "italic"), fg="#ef4444").pack(pady=60)
            return

        sorted_pairs = sorted(zip(dates, y_vals))
        sorted_dates, sorted_y = zip(*sorted_pairs)

        # Plot Customization
        ax.plot(sorted_dates, sorted_y, marker='o', color='#10b981', linewidth=2.5, markersize=5, label='Peso (kg)')
        ax.set_title("Andamento Peso Corporeo", color='white', fontsize=12, fontweight='bold', pad=12)
        
        for spine in ax.spines.values():
            spine.set_color('#252529')
        
        ax.tick_params(colors='white', which='both', labelsize=8)
        ax.grid(True, color='#252529', linestyle='--', alpha=0.6)
        
        # Formattazione data dell'asse X
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        canvas.draw()
        
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.config(bg='#1a1a1e', highlightthickness=1, highlightbackground='#252529')
        canvas_widget.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")

    def render_today_plan(self):
        plan_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        plan_card.grid(row=2, column=2, sticky="nsew", pady=10, padx=(10, 0))
        plan_card.grid_columnconfigure(0, weight=1)

        self.create_label(plan_card, "Pasti Pianificati Oggi", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # Legge il piano per oggi
        plan_data = self.look_for(self.files['plan'], {})
        today_plan = plan_data.get(self.today_str, {"Colazione": '-', "Pranzo": '-', "Cena": '-'})
        if today_plan is None:
            today_plan = {"Colazione": '-', "Pranzo": '-', "Cena": '-'}

        meals = [
            ("Colazione", self._format_meal_name(today_plan.get("Colazione", "-"))),
            ("Pranzo", self._format_meal_name(today_plan.get("Pranzo", "-"))),
            ("Cena", self._format_meal_name(today_plan.get("Cena", "-")))
        ]

        row = 1
        for meal_type, meal_name in meals:
            # Container per ogni riga pasto
            meal_row = tk.Frame(plan_card, bg="#1a1a1e")
            meal_row.grid(row=row, column=0, sticky="ew", pady=5)
            meal_row.grid_columnconfigure(1, weight=1)

            # Etichetta del tipo di pasto (Colazione, Pranzo, Cena)
            lbl_type = self.create_label(meal_row, f"{meal_type}:", font=("Segoe UI", 10, "bold"), fg="#a0a0a5")
            lbl_type.grid(row=0, column=0, sticky="w")

            # Nome del pasto
            lbl_name = self.create_label(meal_row, meal_name, font=("Segoe UI", 10))
            lbl_name.grid(row=0, column=1, sticky="w", padx=10)

            row += 1

    def render_stats(self):
        # Calcolo del trend lineare sul peso
        y = np.array([float(w[1]) for w in self.weights])
        first_day = datetime.fromisoformat(self.weights[0][0])
        x = np.array([(datetime.fromisoformat(i[0]) - first_day).total_seconds()/86400 for i in self.weights])
        
        if len(x) > 1:
            slope, intercept, r, p, std_err = stats.linregress(x, y)
            trend_dir = "Dimagrimento" if slope < 0 else "Aumento"
            slope_str = f"{slope:.3f} kg/giorno (circa {slope*7700:.0f} kcal/giorno)"
        else:
            slope = 0.0
            trend_dir = "Stazionario"
            slope_str = "Dati insufficienti"

        # Controllo calorie per evitare crash se la lista è vuota
        if self.calories:
            mean_calories = np.mean([float(i[1]) for i in self.calories])
            mean_cal_str = f"{int(mean_calories)} kcal/giorno"
            if len(x) > 1:
                fabisogno_str = f"{mean_calories - slope*7700:.0f} kcal/giorno"
            else:
                fabisogno_str = "Dati peso insufficienti"
        else:
            mean_cal_str = "N/D"
            fabisogno_str = "N/D"

        stats_card = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        stats_card.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        stats_card.grid_columnconfigure(0, weight=1)
        stats_card.grid_columnconfigure(1, weight=1)
        stats_card.grid_columnconfigure(2, weight=1)

        self.create_label(stats_card, f"Trend Rilevato\n{trend_dir}", font=("Segoe UI", 10, "bold"), fg="#10b981" if slope < 0 else "#3b82f6").grid(row=0, column=0)
        self.create_label(stats_card, f"Variazione Peso\n{slope_str}", font=("Segoe UI", 10, "bold")).grid(row=0, column=1)
        self.create_label(stats_card, f"Calorie Medie (Introito)\n{mean_cal_str}\n\nFabbisogno Giornaliero Stimato\n{fabisogno_str}", font=("Segoe UI", 10, "bold")).grid(row=0, column=2)

    def record_weight(self, val):
        try:
            val_float = float(val)
            self.weights.append([datetime.now().isoformat(), val_float])
            self.record(self.files['weights'], self.weights)
            messagebox.showinfo("Successo", "Peso registrato con successo!")
            self.show_main_screen()
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido per il peso!")

    def record_calories(self, val):
        try:
            val_float = float(val)
            self.calories.append([datetime.now().isoformat(), val_float])
            self.record(self.files['calories'], self.calories)
            messagebox.showinfo("Successo", "Calorie registrate con successo!")
            self.show_main_screen()
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido per le calorie!")

    # --- FOOD SCREEN (DIARIO ALIMENTARE) ---
    def show_food_screen(self):
        self.show_screen("Diario Alimentare", self._render_food_screen)

    def _render_food_screen(self):
        food_list = sorted(list(self.nvalues.keys()))

        # Layout a due colonne: Sinistra (Aggiunta pasto), Destra (Riepilogo Oggi)
        col_sinistra = tk.Frame(self.main_frame, bg="#121214")
        col_sinistra.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10)
        col_sinistra.grid_columnconfigure(1, weight=1)

        col_destra = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        col_destra.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        col_destra.grid_columnconfigure(0, weight=1)
        col_destra.grid_rowconfigure(1, weight=1)

        # Configurazione colonna sinistra
        self.create_label(col_sinistra, "Aggiungi un alimento al diario di oggi", font=("Segoe UI", 12, "bold"), bg="#121214").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 5))
        self.create_hint(col_sinistra,
            "Seleziona un alimento dalla lista qui sotto o digita il nome manualmente, "
            "poi inserisci la quantità in ettogrammi (hg) e clicca Aggiungi al Diario.",
            bg="#121214"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.create_label(col_sinistra, "Alimento:", bg="#121214").grid(row=2, column=0, sticky="w", pady=5)
        food_entry = self.create_entry(col_sinistra)
        food_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        self.create_label(col_sinistra, "Quantità (hg):", bg="#121214").grid(row=3, column=0, sticky="w", pady=5)
        qty_entry = self.create_entry(col_sinistra)
        qty_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        # Etichetta calorie veloci
        self.preview_label = self.create_label(col_sinistra, "Calorie previste: --", font=("Segoe UI", 10, "italic"), fg="#a0a0a5", bg="#121214")
        self.preview_label.grid(row=3, column=2, sticky="w", padx=5)

        # Autocompletamento Listbox degli alimenti salvati
        self.create_label(col_sinistra, "Alimenti salvati nel database:", font=("Segoe UI", 10, "bold"), bg="#121214").grid(row=4, column=0, columnspan=3, sticky="w", pady=(15, 5))
        self.options = self.create_listbox(col_sinistra, height=8)
        self.options.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=5)

        # Popola listbox alimenti salvati
        for item in food_list:
            self.options.insert(tk.END, item)

        # Associa filtri
        def check(e):
            calcola_veloce(e)
            typed = food_entry.get()
            self.options.delete(0, tk.END)
            if typed == '':
                for item in food_list:
                    self.options.insert(tk.END, item)
            else:
                for item in food_list:
                    if typed.lower() in item.lower():
                        self.options.insert(tk.END, item)

        def fillout(e):
            if self.options.curselection():
                food_entry.delete(0, tk.END)
                food_entry.insert(0, self.options.get(self.options.curselection()[0]))
                calcola_veloce(e)

        food_entry.bind('<KeyRelease>', check)
        self.options.bind('<<ListboxSelect>>', fillout)

        def calcola_veloce(event):
            nome = food_entry.get()
            try:
                kcal_unita = self.nvalues.get(nome, {}).get('kcal', 0)
                q = float(qty_entry.get())
                risultato = kcal_unita * q
                self.preview_label.config(text=f"Calorie previste: {risultato:.1f} kcal", fg="#10b981")
            except ValueError:
                self.preview_label.config(text="Calorie previste: --", fg="#a0a0a5")

        qty_entry.bind("<KeyRelease>", calcola_veloce)

        def add_item():
            name = food_entry.get().strip()
            if not name:
                messagebox.showwarning("Errore", "Inserisci il nome di un alimento!")
                return
            try:
                qty = float(qty_entry.get())
                self.today_eaten.append([name, qty])
                self.save_food_data()
                self.update_food_list()
                food_entry.delete(0, tk.END)
                qty_entry.delete(0, tk.END)
                self.preview_label.config(text="Calorie previste: --", fg="#a0a0a5")
            except ValueError:
                messagebox.showwarning("Errore", "Inserisci una quantità numerica valida!")

        btn_add = self.create_button(col_sinistra, "Aggiungi al Diario", command=add_item, bg="#3b82f6")
        btn_add.grid(row=6, column=0, columnspan=3, pady=15, sticky="ew")

        # Configurazione colonna destra (Riepilogo pasti del giorno)
        self.create_label(col_destra, "Diario Alimentare di Oggi", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.create_hint(col_destra,
            "Se l'alimento non è nella lista, aggiungilo comunque: si aprirà una finestra "
            "in cui inserirai le calorie per ettogrammo.",
            bg="#1a1a1e"
        ).pack(anchor="w", pady=(0, 10))
        self.food_listbox = self.create_listbox(col_destra, height=15)
        self.food_listbox.pack(fill="both", expand=True, pady=5)
        
        # Bottone cancella alimento selezionato oggi
        def delete_selected_today():
            sel = self.food_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            # Salta separatori o righe di totale
            if idx < len(self.today_eaten):
                self.today_eaten.pop(idx)
                self.save_food_data()
                self.update_food_list()

        btn_del = self.create_button(col_destra, "Elimina Pasto Selezionato", command=delete_selected_today, bg="#ef4444")
        btn_del.pack(fill="x", pady=(10, 0))

        # Mostra la lista iniziale
        self.update_food_list()

    def update_food_list(self):
        self.food_listbox.delete(0, tk.END)
        total_kcal = 0

        for food, qty in self.today_eaten:
            if food in self.nvalues:
                kcal_per_hg = self.nvalues[food].get('kcal', 0)
                kcal_totali = kcal_per_hg * qty
                total_kcal += kcal_totali
                self.food_listbox.insert(tk.END, f"{food} - {qty} hg (~{kcal_totali:.0f} kcal)")
            else:
                self.open_new_food_window(food)
                return

        self.food_listbox.insert(tk.END, "------------------------------------------")
        self.food_listbox.insert(tk.END, f"TOTALE DI OGGI: {total_kcal:.1f} kcal")

    def open_new_food_window(self, food_name):
        self.top = tk.Toplevel(self.root)
        self.top.title(f"Dati mancanti: {food_name}")
        self.top.geometry("350x200")
        self.top.configure(bg="#1a1a1e")
        self.top.wait_visibility()
        self.top.grab_set() # Modale

        # Centra la finestra modale
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'+{x}+{y}')

        self.create_label(self.top, f"Inserisci le kcal per 1 hg di:\n{food_name}", 
                          font=("Segoe UI", 11, "bold")).pack(pady=(15, 10))
        
        add_entry = self.create_entry(self.top)
        add_entry.pack(pady=5, padx=20, fill="x")

        def save_and_resume():
            try:
                valore = float(add_entry.get())
                self.nvalues[food_name] = {'kcal': valore}
                self.record(self.files['nvalues'], self.nvalues)
                self.top.destroy()
                self.update_food_list()
            except ValueError:
                messagebox.showerror("Errore", "Inserisci un valore numerico valido!")

        def on_cancel():
            # Rimuove il cibo non censito per evitare loop di richieste
            self.today_eaten = [x for x in self.today_eaten if x[0] != food_name]
            self.save_food_data()
            self.top.destroy()
            self.update_food_list()

        # Intercetta chiusura per gestire il cancel
        self.top.protocol("WM_DELETE_WINDOW", on_cancel)

        btn_save = self.create_button(self.top, "Salva e Calcola", command=save_and_resume, bg="#10b981")
        btn_save.pack(pady=15)

    def save_food_data(self):
        all_data = self.look_for(self.files['eaten'], {})
        all_data[self.today_str] = self.today_eaten
        self.record(self.files['eaten'], all_data)

    # --- HISTORY SCREEN (STORICO PASTI) ---
    def show_history_screen(self):
        self.show_screen("Storico Pasti", self.render_history_screen)

    def render_history_screen(self):
        self.elementi_pasto = []
        all_eaten = self.look_for(self.files['eaten'], {})
        date_list = sorted(list(all_eaten.keys()), reverse=True) # Ordina dalle più recenti

        # Layout a tre colonne
        # 1. Date
        col1 = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        col1.grid_rowconfigure(1, weight=1)

        # 2. Cibi in quella data
        col2 = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        col2.grid(row=0, column=1, sticky="nsew", padx=5)
        col2.grid_rowconfigure(1, weight=1)

        # 3. Composizione pasto rapido
        col3 = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        col3.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        col3.grid_rowconfigure(1, weight=1)

        # Colonna 1: Lista Date
        self.create_label(col1, "Seleziona Data:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))
        self.date_listbox = self.create_listbox(col1, width=18)
        self.date_listbox.pack(fill="both", expand=True, pady=5)
        
        for data_str in date_list:
            self.date_listbox.insert(tk.END, data_str)

        # Colonna 2: Alimenti Consumati
        lbl_history_pasti = self.create_label(col2, "Pasti Consumati:", font=("Segoe UI", 11, "bold"))
        lbl_history_pasti.pack(anchor="w", pady=(0, 5))
        
        self.history_food_listbox = self.create_listbox(col2, width=32)
        self.history_food_listbox.pack(fill="both", expand=True, pady=5)

        self.current_selected_date = None

        def on_date_select(event):
            if not self.date_listbox.curselection():
                return
            
            self.current_selected_date = self.date_listbox.get(self.date_listbox.curselection()[0])
            lbl_history_pasti.config(text=f"Consumati il {self.current_selected_date}:")
            
            pasti = all_eaten.get(self.current_selected_date, [])
            self.history_food_listbox.delete(0, tk.END)
            for food, qty in pasti:
                self.history_food_listbox.insert(tk.END, f"{food} - {qty} hg")

        self.date_listbox.bind('<<ListboxSelect>>', on_date_select)

        # Colonna 3: Composizione Pasto Rapido
        self.create_label(col3, "Crea Pasto Rapido", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 2))
        self.create_hint(col3,
            "Fai doppio click sui cibi al centro per aggiungerli, "
            "poi dai un nome al pasto e salvalo come Pasto Rapido.",
            bg="#1a1a1e"
        ).pack(anchor="w", pady=(0, 10))
        
        self.pasti_listbox = self.create_listbox(col3, width=30, height=8)
        self.pasti_listbox.pack(fill="both", expand=True, pady=5)
        self.pasti_listbox.insert(tk.END, "Seleziona elementi con doppio click")

        self.create_label(col3, "Nome del Pasto Rapido:").pack(anchor="w", pady=(10, 2))
        meal_name_entry = self.create_entry(col3)
        meal_name_entry.pack(fill="x", pady=5)

        def reset_quick_meal_list(e):
            # Cancella il placeholder al primo inserimento nel campo nome pasto
            if self.pasti_listbox.get(0) == "Seleziona elementi con doppio click":
                self.pasti_listbox.delete(0, tk.END)
                self.elementi_pasto = []

        meal_name_entry.bind('<FocusIn>', reset_quick_meal_list)

        def add_from_history(event):
            if not self.history_food_listbox.curselection() or not self.current_selected_date:
                return

            index = self.history_food_listbox.curselection()[0]
            pasti = all_eaten.get(self.current_selected_date, [])
            food_name, qty = pasti[index]

            if self.pasti_listbox.get(0) == "Seleziona elementi con doppio click":
                self.pasti_listbox.delete(0, tk.END)

            self.pasti_listbox.insert(tk.END, f"{food_name} ({qty} hg)")
            self.elementi_pasto.append([food_name, float(qty)])

        self.history_food_listbox.bind('<Double-Button-1>', add_from_history)

        def save_meal_template():
            nome_pasto = meal_name_entry.get().strip()
            if not nome_pasto:
                messagebox.showwarning("Errore", "Inserisci un nome per il Pasto Rapido!")
                return
            if not self.elementi_pasto:
                messagebox.showwarning("Errore", "Aggiungi almeno un ingrediente allo storico prima di salvare!")
                return

            templates = self.look_for(self.files['pasti'], {})
            templates[nome_pasto] = self.elementi_pasto
            self.record(self.files['pasti'], templates)
            
            messagebox.showinfo("Successo", f"Pasto '{nome_pasto}' salvato correttamente!")
            meal_name_entry.delete(0, tk.END)
            self.pasti_listbox.delete(0, tk.END)
            self.pasti_listbox.insert(tk.END, "Seleziona elementi con doppio click")
            self.elementi_pasto = []

        btn_save = self.create_button(col3, "Salva come Pasto Rapido", command=save_meal_template, bg="#10b981")
        btn_save.pack(fill="x", pady=10)

    # --- DATABASE SCREEN (DATABASE ALIMENTI) ---
    def show_database_screen(self):
        self.show_screen("Database Alimenti", self._render_database_screen)

    def _render_database_screen(self):
        # Form di inserimento in alto
        form_frame = tk.Frame(self.main_frame, bg="#1a1a1e", highlightthickness=1, highlightbackground="#252529", padx=15, pady=15)
        form_frame.pack(fill="x", pady=(0, 10))
        
        # Grid per form
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        form_frame.grid_columnconfigure(5, weight=1)
        form_frame.grid_columnconfigure(7, weight=1)
        form_frame.grid_columnconfigure(9, weight=1)
        form_frame.grid_columnconfigure(11, weight=1)

        self.create_label(form_frame, "Nome:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.db_name_entry = self.create_entry(form_frame)
        self.db_name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.create_label(form_frame, "kcal/hg:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.db_kcal_entry = self.create_entry(form_frame)
        self.db_kcal_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        self.create_label(form_frame, "Pro/hg (g):").grid(row=0, column=4, sticky="w", padx=(0, 5))
        self.db_pro_entry = self.create_entry(form_frame)
        self.db_pro_entry.grid(row=0, column=5, sticky="ew", padx=(0, 10))

        self.create_label(form_frame, "Carb/hg (g):").grid(row=0, column=6, sticky="w", padx=(0, 5))
        self.db_carb_entry = self.create_entry(form_frame)
        self.db_carb_entry.grid(row=0, column=7, sticky="ew", padx=(0, 10))

        self.create_label(form_frame, "Grassi/hg (g):").grid(row=0, column=8, sticky="w", padx=(0, 5))
        self.db_fat_entry = self.create_entry(form_frame)
        self.db_fat_entry.grid(row=0, column=9, sticky="ew", padx=(0, 10))

        self.create_label(form_frame, "Costo/hg (€):").grid(row=0, column=10, sticky="w", padx=(0, 5))
        self.db_price_entry = self.create_entry(form_frame)
        self.db_price_entry.grid(row=0, column=11, sticky="ew", padx=(0, 10))

        btn_add = self.create_button(form_frame, "Aggiungi", command=self.add_food_to_db, bg="#10b981")
        btn_add.grid(row=0, column=12, padx=(5, 0))

        # Hint database
        self.create_hint(self.main_frame,
            "Compila tutti i campi per ogni alimento. Prezzo e valori nutrizionali sono essenziali "
            "per l'ottimizzatore del piano settimanale.",
            bg="#121214"
        ).pack(anchor="w", pady=(0, 5))

        # Container per la tabella e scrollbar
        table_container = tk.Frame(self.main_frame, bg="#121214")
        table_container.pack(fill="both", expand=True, pady=5)

        colonne = ("Alimento", "kcal", "Proteine", "Carboidrati", "Grassi", "Prezzo")
        self.db_tree = ttk.Treeview(table_container, columns=colonne, show='headings', selectmode='browse')
        
        self.db_tree.heading("Alimento", text="Alimento")
        self.db_tree.heading("kcal", text="kcal/hg")
        self.db_tree.heading("Proteine", text="Proteine/hg (g)")
        self.db_tree.heading("Carboidrati", text="Carboidrati/hg (g)")
        self.db_tree.heading("Grassi", text="Grassi/hg (g)")
        self.db_tree.heading("Prezzo", text="Prezzo/hg (€)")

        self.db_tree.column("Alimento", width=200, anchor="w")
        self.db_tree.column("kcal", width=100, anchor="center")
        self.db_tree.column("Proteine", width=120, anchor="center")
        self.db_tree.column("Carboidrati", width=120, anchor="center")
        self.db_tree.column("Grassi", width=120, anchor="center")
        self.db_tree.column("Prezzo", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.db_tree.yview)
        self.db_tree.configure(yscrollcommand=scrollbar.set)
        
        self.db_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bottone Elimina sotto la tabella
        btn_delete = self.create_button(self.main_frame, "Elimina Alimento Selezionato", command=self.delete_food_from_db, bg="#ef4444")
        btn_delete.pack(anchor="w", pady=(10, 0))

        self.db_tree.bind("<Double-Button-1>", self.on_database_cell_double_click)

        self.db_tree.tag_configure('needs_price', foreground='#f59e0b')
        self.db_tree.tag_configure('needs_nutrition', foreground='#f97316')
        self.db_tree.tag_configure('needs_both', foreground='#ef4444')

        self._refresh_database_table()

    def _refresh_database_table(self):
        # Svuota tabella
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)

        # Determina quali alimenti sono usati nei pasti rapidi e cosa manca
        templates = self.look_for(self.files['pasti'], {})
        constrained_nutrients = set()
        for nutrient, cfg in self.constraints.items():
            if cfg.get('min') is not None or cfg.get('max') is not None:
                constrained_nutrients.add(nutrient)

        foods_in_meals = set()
        for meal_name, ingredients in templates.items():
            for food, qty in ingredients:
                foods_in_meals.add(food)

        # Inserisci alimenti in ordine alfabetico
        for food_name in sorted(self.nvalues.keys()):
            val = self.nvalues[food_name]
            kcal = val.get("kcal", 0.0)
            prot = val.get("proteine", 0.0)
            carb = val.get("carboidrati", 0.0)
            grassi = val.get("grassi", 0.0)
            prezzo = self.prices.get(food_name, 0.0)

            tags = ()
            if food_name in foods_in_meals:
                missing_price = prezzo <= 0.0
                missing_nutrients = any(
                    val.get(n, 0.0) <= 0.0 for n in constrained_nutrients
                )
                if missing_price and missing_nutrients:
                    tags = ('needs_both',)
                elif missing_price:
                    tags = ('needs_price',)
                elif missing_nutrients:
                    tags = ('needs_nutrition',)

            self.db_tree.insert("", tk.END, values=(food_name, f"{kcal:.1f}", f"{prot:.1f}", f"{carb:.1f}", f"{grassi:.1f}", f"{prezzo:.2f}"), tags=tags)

    def add_food_to_db(self):
        nome = self.db_name_entry.get().strip()
        if not nome:
            messagebox.showwarning("Errore", "Inserisci il nome dell'alimento!")
            return
        
        if nome in self.nvalues:
            messagebox.showwarning("Errore", f"L'alimento '{nome}' esiste già nel database!")
            return

        try:
            kcal = float(self.db_kcal_entry.get().strip() or 0.0)
            prot = float(self.db_pro_entry.get().strip() or 0.0)
            carb = float(self.db_carb_entry.get().strip() or 0.0)
            grassi = float(self.db_fat_entry.get().strip() or 0.0)
            prezzo = float(self.db_price_entry.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror("Errore", "Inserisci valori numerici validi per i nutrienti e il prezzo!")
            return

        self.nvalues[nome] = {
            "kcal": kcal,
            "proteine": prot,
            "carboidrati": carb,
            "grassi": grassi
        }
        self.prices[nome] = prezzo
        self.record(self.files['nvalues'], self.nvalues)
        self.record(self.files['prices'], self.prices)
        
        # Pulisci i campi
        self.db_name_entry.delete(0, tk.END)
        self.db_kcal_entry.delete(0, tk.END)
        self.db_pro_entry.delete(0, tk.END)
        self.db_carb_entry.delete(0, tk.END)
        self.db_fat_entry.delete(0, tk.END)
        self.db_price_entry.delete(0, tk.END)

        self._refresh_database_table()
        messagebox.showinfo("Successo", f"Alimento '{nome}' aggiunto con successo!")

    def delete_food_from_db(self):
        selected = self.db_tree.selection()
        if not selected:
            messagebox.showwarning("Errore", "Seleziona un alimento da eliminare!")
            return
        
        item = self.db_tree.item(selected[0])
        food_name = str(item['values'][0])

        if messagebox.askyesno("Conferma", f"Sei sicuro di voler eliminare '{food_name}' dal database?"):
            if food_name in self.nvalues:
                del self.nvalues[food_name]
                self.record(self.files['nvalues'], self.nvalues)
            if food_name in self.prices:
                del self.prices[food_name]
                self.record(self.files['prices'], self.prices)
            self._refresh_database_table()

    def on_database_cell_double_click(self, event):
        region = self.db_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.db_tree.identify_column(event.x) # es. "#1", "#2"
        row_id = self.db_tree.identify_row(event.y)

        col_idx = int(column.replace('#', '')) - 1
        if col_idx < 0:
            return

        bbox = self.db_tree.bbox(row_id, column)
        if not bbox:
            return

        x, y, w, h = bbox

        # Recupera valori correnti della riga
        values = self.db_tree.item(row_id)['values']
        curr_val = values[col_idx]
        food_name = str(values[0])

        # Crea widget di Entry temporaneo sopra la cella
        entry = tk.Entry(self.db_tree, relief="flat", font=("Segoe UI", 10))
        entry.insert(0, str(curr_val))
        entry.select_range(0, tk.END)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        # Flag per evitare chiamate multiple (sia Return che FocusOut)
        state = {"saved": False}

        def save_edit(event_obj=None):
            if state["saved"]:
                return
            state["saved"] = True

            new_text = entry.get().strip()
            entry.destroy()

            if not new_text:
                return

            if col_idx == 0:
                # Modifica del nome dell'alimento
                if new_text == food_name:
                    return
                if new_text in self.nvalues:
                    messagebox.showwarning("Errore", f"L'alimento '{new_text}' esiste già nel database!")
                    self._refresh_database_table()
                    return

                # Rinomina la chiave nel dizionario nutrienti
                self.nvalues[new_text] = self.nvalues.pop(food_name)
                self.record(self.files['nvalues'], self.nvalues)

                # Rinomina la chiave nel dizionario prezzi
                if food_name in self.prices:
                    self.prices[new_text] = self.prices.pop(food_name)
                    self.record(self.files['prices'], self.prices)

                # Rinomina l'ingrediente nei pasti (pasti.json)
                templates = self.look_for(self.files['pasti'], {})
                updated_templates = False
                for meal_name, ingredients in templates.items():
                    for idx_ing, ing_pair in enumerate(ingredients):
                        if ing_pair[0] == food_name:
                            ing_pair[0] = new_text
                            updated_templates = True
                if updated_templates:
                    self.record(self.files['pasti'], templates)
            else:
                # Modifica di kcal, proteine, carboidrati, grassi, o prezzo
                try:
                    val_float = float(new_text)
                except ValueError:
                    messagebox.showerror("Errore", "Inserisci un valore numerico valido!")
                    self._refresh_database_table()
                    return

                if col_idx == 5:
                    # Modifica del prezzo
                    self.prices[food_name] = val_float
                    self.record(self.files['prices'], self.prices)
                else:
                    # Chiave corrispondente alla colonna
                    keys = [None, "kcal", "proteine", "carboidrati", "grassi"]
                    key = keys[col_idx]

                    # Aggiorna il valore
                    if food_name in self.nvalues:
                        self.nvalues[food_name][key] = val_float
                        self.record(self.files['nvalues'], self.nvalues)

            self._refresh_database_table()

        def cancel_edit(event_obj=None):
            if state["saved"]:
                return
            state["saved"] = True
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", cancel_edit)

    # --- HELPERS ---
    def _format_meal_name(self, val):
        """Ritorna il nome leggibile del pasto (stringa o dict con 'pasto')."""
        if isinstance(val, dict):
            return val.get("nome", val.get("pasto", "-"))
        return val if val else "-"

    def calcola_valori_pasto(self, nome_pasto, templates):
        """Calcola i nutrienti totali di un singolo pasto rapido."""
        totali = {"kcal": 0.0, "proteine": 0.0, "carboidrati": 0.0, "grassi": 0.0}
        if nome_pasto == '-' or not nome_pasto:
            return totali
        ingredienti = templates.get(nome_pasto, [])
        for food, qty in ingredienti:
            if food in self.nvalues:
                info = self.nvalues[food]
                totali["kcal"] += info.get("kcal", 0.0) * qty
                totali["proteine"] += info.get("proteine", 0.0) * qty
                totali["carboidrati"] += info.get("carboidrati", 0.0) * qty
                totali["grassi"] += info.get("grassi", 0.0) * qty
        return totali

    def calcola_costo_pasto(self, nome_pasto, templates):
        """Calcola il costo totale di un pasto rapido.
        Ritorna None se qualsiasi ingrediente manca di prezzo (prezzo <= 0)."""
        if nome_pasto == '-' or not nome_pasto:
            return 0.0
        ingredienti = templates.get(nome_pasto, [])
        costo = 0.0
        for food, qty in ingredienti:
            p = self.prices.get(food, 0.0)
            if p <= 0.0:
                return None  # prezzo mancante: pasto non eleggibile
            costo += p * qty
        return costo

    def ottimizza_piano(self):
        """Usa PuLP per riempire gli slot vuoti ottimizzando dinamicamente le porzioni (moltiplicatori)
        dei pasti scelti, minimizzando i costi e rispettando rigidamente i vincoli nutrizionali."""
        from pulp import LpProblem, LpVariable, LpMinimize, lpSum, value, PULP_CBC_CMD, LpStatusInfeasible, LpBinary, LpContinuous
        from datetime import timedelta

        templates = self.look_for(self.files['pasti'], {})
        if not templates:
            messagebox.showwarning("Attenzione", "Non ci sono Pasti Rapidi salvati nello storico!")
            return False

        # Calcoliamo i costi e i nutrienti di RIFERIMENTO (base 1.0) per ogni pasto rapido
        eligible_meals = []
        meal_base_costs = {}
        meal_base_nutrients = {}

        for nome in templates:
            costo = self.calcola_costo_pasto(nome, templates)
            if costo is not None and costo > 0:
                eligible_meals.append(nome)
                meal_base_costs[nome] = costo
                meal_base_nutrients[nome] = self.calcola_valori_pasto(nome, templates)

        if not eligible_meals:
            messagebox.showerror("Errore", "Nessun pasto ha ingredienti con prezzi validi nel database!")
            return False

        plan_data = self.look_for(self.files['plan'], {})
        constraints = self.look_for(self.files['constraints'], {})

        # Trova gli slot vuoti nei prossimi 5 giorni
        days_slots = {}
        for i in range(5):
            date_obj = datetime.now() + timedelta(days=i)
            d_key = date_obj.strftime("%Y-%m-%d")
            day_plan = plan_data.get(d_key, {"Colazione": "-", "Pranzo": "-", "Cena": "-"})
            if day_plan is None:
                day_plan = {"Colazione": "-", "Pranzo": "-", "Cena": "-"}

            for cat in ["Colazione", "Pranzo", "Cena"]:
                name = day_plan.get(cat, "-")
                if not name or name == "-":
                    days_slots.setdefault(d_key, []).append(cat)

        if not days_slots:
            messagebox.showinfo("Piano completo", "Tutti i giorni futuri hanno già un piano assegnato.")
            return False

        slots_to_fill = []
        for d_key in sorted(days_slots):
            for cat in days_slots[d_key]:
                slots_to_fill.append((d_key, cat))

        # Modello di Ottimizzazione
        model = LpProblem("diet_dynamic_portions", LpMinimize)

        # VARIABILI DI DECISIONE:
        # 1. 'scelto' (Binaria): definisce SE quel determinato pasto è assegnato a quel preciso slot (0 o 1)
        # 2. 'porzione' (Continua): definisce QUANTO di quel pasto mangiare (es. 0.5 per mezza porzione, 1.2 per più abbondante)
        scelto = {}
        porzione = {}

        for s_idx in range(len(slots_to_fill)):
            for nome in eligible_meals:
                safe = nome.replace(' ', '_').replace('/', '_')
                scelto[(s_idx, nome)] = LpVariable(f"scelto_{s_idx}_{safe}", cat=LpBinary)
                # La porzione può oscillare tra il 50% (0.5) e il 180% (1.8) della ricetta base
                porzione[(s_idx, nome)] = LpVariable(f"porzione_{s_idx}_{safe}", lowBound=0.0, cat=LpContinuous)

        # FUNZIONE OBIETTIVO: Minimizzare il costo complessivo (costo_base * porzione)
        model += lpSum(
            porzione[(s_idx, nome)] * meal_base_costs[nome]
            for s_idx in range(len(slots_to_fill))
            for nome in eligible_meals
        )

        # VINCOLI DI STRUTTURA ED ESCURSIONE PORZIONI
        for s_idx in range(len(slots_to_fill)):
            # Per ogni slot, un solo pasto può essere scelto (la somma delle variabili binarie deve fare 1)
            model += lpSum(scelto[(s_idx, nome)] for nome in eligible_meals) == 1

            for nome in eligible_meals:
                # Se il pasto NON è scelto (scelto=0), la porzione DEVE essere costretta a 0.
                # Se il pasto È scelto (scelto=1), la porzione può variare entro i limiti antropometrici (es. 0.5 - 1.8)
                model += porzione[(s_idx, nome)] >= 0.5 * scelto[(s_idx, nome)]
                model += porzione[(s_idx, nome)] <= 1.8 * scelto[(s_idx, nome)]

        # VINCOLO DI UNICITÀ: Un pasto rapido può comparire al massimo una volta sola nell'intero piano
        for nome in eligible_meals:
            model += lpSum(scelto[(s_idx, nome)] for s_idx in range(len(slots_to_fill))) <= 1

        # VINCOLI NUTRIZIONALI GIORNALIERI (Versione sicura senza crash)
        for nutrient in ["kcal", "proteine", "carboidrati", "grassi"]:
            cfg = constraints.get(nutrient, {"min": None, "max": None})
            lo = cfg.get("min")
            hi = cfg.get("max")

            # Se per questo nutriente non hai impostato nessun limite, passa avanti
            if lo is None and hi is None:
                continue

            for d_key in sorted(days_slots):
                day_s_indices = [s_idx for s_idx, (dk, _) in enumerate(slots_to_fill) if dk == d_key]
                if not day_s_indices:
                    continue

                # 1. Somma dei nutrienti degli slot che stiamo ottimizzando
                nutrient_sum = lpSum(
                    porzione[(s_idx, nome)] * meal_base_nutrients[nome].get(nutrient, 0.0)
                    for s_idx in day_s_indices
                    for nome in eligible_meals
                )

                # 2. Somma dei nutrienti dei pasti già fissati manualmente in questo giorno
                fixed_day = plan_data.get(d_key, {})
                fixed_val = 0.0
                for cat in ["Colazione", "Pranzo", "Cena"]:
                    nome_fissato = fixed_day.get(cat, "-")
                    if nome_fissato and nome_fissato != "-":
                        # Calcola i valori nutrizionali reali del pasto fisso
                        valori_fissi = self.calcola_valori_pasto(nome_fissato, templates)
                        fixed_val += valori_fissi.get(nutrient, 0.0)

                # 3. Applica i limiti minimi e massimi a PuLP
                if lo is not None:
                    model += (nutrient_sum + fixed_val) >= lo
                if hi is not None:
                    model += (nutrient_sum + fixed_val) <= hi

        # Risoluzione
        status = model.solve(PULP_CBC_CMD(msg=False))

        if status == LpStatusInfeasible:
            messagebox.showerror("Errore", "Impossibile trovare una combinazione o porzionatura di pasti che soddisfi i tuoi vincoli senza ripetere i pasti!")
            return False

        # Salvataggio dei risultati nel dizionario plan_data
        for s_idx, (d_key, cat) in enumerate(slots_to_fill):
            for nome in eligible_meals:
                # Se la variabile binaria 'scelto' è pari a 1, significa che il pasto è stato selezionato per questo slot
                if value(scelto[(s_idx, nome)]) == 1:

                    if d_key not in plan_data:
                        plan_data[d_key] = {"Colazione": "-", "Pranzo": "-", "Cena": "-"}

                    # Salviamo solo la stringa con il nome pulito del pasto
                    plan_data[d_key][cat] = nome

        porzioni_data = self.look_for(self.files['porzioni'], {})
        for s_idx, (d_key, cat) in enumerate(slots_to_fill):
            for nome in eligible_meals:
                if value(scelto[(s_idx, nome)]) == 1:
                    if d_key not in porzioni_data:
                        porzioni_data[d_key] = {}
                    porzioni_data[d_key][cat] = round(float(value(porzione[(s_idx, nome)])), 2)
        self.record(self.files['porzioni'], porzioni_data)

        self.record(self.files['plan'], plan_data)
        messagebox.showinfo("Successo", "Ottimizzazione completata! Controlla il terminale per vedere le porzioni consigliate.")
        return True

    def show_constraints_dialog(self):
        """Finestra modale per impostare i vincoli nutrizionali giornalieri usati dall'ottimizzatore."""
        constraints = self.look_for(self.files['constraints'], {})

        top = tk.Toplevel(self.root)
        top.title("Vincoli Nutrizionali Giornalieri")
        top.geometry("520x380")
        top.configure(bg="#1a1a1e")
        top.resizable(False, False)
        top.wait_visibility()
        top.grab_set()
        top.update_idletasks()
        w = top.winfo_width()
        h = top.winfo_height()
        x = (top.winfo_screenwidth() // 2) - (w // 2)
        y = (top.winfo_screenheight() // 2) - (h // 2)
        top.geometry(f'+{x}+{y}')

        # Nutrienti configurabili e label leggibili
        nutrienti = [
            ("kcal",        "Calorie (kcal)"),
            ("proteine",    "Proteine (g)"),
            ("carboidrati", "Carboidrati (g)"),
            ("grassi",      "Grassi (g)"),
        ]

        self.create_label(top, "Vincoli Nutrizionali Giornalieri",
                          font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=5,
                          sticky="w", padx=20, pady=(18, 6))
        self.create_label(top, "Attivo", font=("Segoe UI", 9, "bold"), fg="#a0a0a5"
                         ).grid(row=1, column=0, padx=(20, 6))
        self.create_label(top, "Nutriente", font=("Segoe UI", 9, "bold"), fg="#a0a0a5"
                         ).grid(row=1, column=1, sticky="w", padx=6)
        self.create_label(top, "Min", font=("Segoe UI", 9, "bold"), fg="#a0a0a5"
                         ).grid(row=1, column=2, padx=6)
        self.create_label(top, "Max", font=("Segoe UI", 9, "bold"), fg="#a0a0a5"
                         ).grid(row=1, column=3, padx=6)

        # Separator
        sep = tk.Frame(top, height=1, bg="#252529")
        sep.grid(row=2, column=0, columnspan=5, sticky="ew", padx=20, pady=4)

        rows_vars = {}  # key -> (enabled_var, min_entry, max_entry)
        for r_idx, (key, label) in enumerate(nutrienti):
            cfg = constraints.get(key, {})
            row_num = r_idx + 3

            enabled_var = tk.BooleanVar(value=cfg.get('enabled', False))
            chk = tk.Checkbutton(top, variable=enabled_var, bg="#1a1a1e",
                                 activebackground="#1a1a1e", selectcolor="#3b82f6",
                                 relief="flat", bd=0)
            chk.grid(row=row_num, column=0, padx=(20, 6), pady=8)

            self.create_label(top, label, font=("Segoe UI", 10)).grid(
                row=row_num, column=1, sticky="w", padx=6, pady=8)

            min_entry = self.create_entry(top, font=("Segoe UI", 10))
            min_entry.config(width=8)
            lo = cfg.get('min', '')
            if lo is not None and lo != '':
                min_entry.insert(0, str(lo))
            min_entry.grid(row=row_num, column=2, padx=6, pady=8)

            max_entry = self.create_entry(top, font=("Segoe UI", 10))
            max_entry.config(width=8)
            hi = cfg.get('max', '')
            if hi is not None and hi != '':
                max_entry.insert(0, str(hi))
            max_entry.grid(row=row_num, column=3, padx=6, pady=8)

            rows_vars[key] = (enabled_var, min_entry, max_entry)

        # Nota informativa
        nota = tk.Label(top,
            text="Lascia Min o Max vuoto per non imporre quel limite.\n"
                 "I vincoli sono applicati per ogni giorno ottimizzato.",
            font=("Segoe UI", 9, "italic"), fg="#a0a0a5", bg="#1a1a1e", justify="left")
        nota.grid(row=row_num + 1, column=0, columnspan=5, sticky="w", padx=20, pady=(8, 4))

        def salva():
            new_constraints = {}
            for key, (enabled_var, min_entry, max_entry) in rows_vars.items():
                lo_str = min_entry.get().strip()
                hi_str = max_entry.get().strip()
                try:
                    lo_val = float(lo_str) if lo_str else None
                except ValueError:
                    messagebox.showerror("Errore", f"Valore minimo non valido per {key}!")
                    return
                try:
                    hi_val = float(hi_str) if hi_str else None
                except ValueError:
                    messagebox.showerror("Errore", f"Valore massimo non valido per {key}!")
                    return
                new_constraints[key] = {
                    'enabled': enabled_var.get(),
                    'min': lo_val,
                    'max': hi_val
                }
            self.record(self.files['constraints'], new_constraints)
            self.constraints = new_constraints
            top.destroy()
            self.show_planner_screen()

        btn_salva = self.create_button(top, "Salva Vincoli", command=salva, bg="#10b981")
        btn_salva.grid(row=row_num + 2, column=0, columnspan=5, pady=18)

    # --- PLANNER SCREEN (PIANO SETTIMANALE) ---
    def show_planner_screen(self):
        self.show_screen("Piano Settimanale", self._render_planner_screen)

    def _render_planner_screen(self):
        from datetime import timedelta

        self.create_label(self.main_frame, "Piano Alimentare dei prossimi 5 giorni", 
                          font=("Segoe UI", 12, "bold"), bg="#121214").pack(anchor="w", pady=(0, 10))

        colonne = ("Pasto", "Giorno1", "Giorno2", "Giorno3", "Giorno4", "Giorno5")
        
        # Grid Treeview
        self.tree = ttk.Treeview(self.main_frame, columns=colonne, show='headings', height=5)
        self.tree.heading("Pasto", text="Orario")
        self.tree.column("Pasto", width=120, anchor="center")
        self.ingredients_label = tk.Label(self.main_frame, text='Click su un pasto programmato per visualizzare gli ingredienti', font=("Segoe UI", 9, "italic"), fg="#a0a0a5", bg="#1a1a1e")
        self.ingredients_label.pack(expand=True, pady=5)

        date_keys = []
        plan_data = self.look_for(self.files['plan'], {})
        meals = self.look_for(self.files['pasti'], {})
        new_plan = {}

        # Genera le intestazioni per i prossimi 5 giorni
        for i in range(5):
            date_obj = datetime.now() + timedelta(days=i)
            d_key = date_obj.strftime("%Y-%m-%d")
            # Visualizzazione giorno in italiano
            d_display = date_obj.strftime("%a %d/%m").replace("Mon", "Lun").replace("Tue", "Mar").replace("Wed", "Mer").replace("Thu", "Gio").replace("Fri", "Ven").replace("Sat", "Sab").replace("Sun", "Dom")
            date_keys.append(d_key)

            self.tree.heading(f"Giorno{i+1}", text=d_display)
            self.tree.column(f"Giorno{i+1}", width=150, anchor="center")
            new_plan[d_key] = plan_data.get(d_key)

        self.tree.pack(fill="both", expand=True, pady=10)

        # Carica righe
        for cat in ["Colazione", "Pranzo", "Cena"]:
            valori = [cat]
            for d_key in date_keys:
                pasti = plan_data.get(d_key)
                if pasti is None:
                    valori.append('-')
                else:
                    valori.append(self._format_meal_name(pasti.get(cat, '-')))
            self.tree.insert("", tk.END, values=valori)

        # Gestione Doppio Click per inserire Pasto Rapido nel piano
        def on_double_click(event):
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                column = self.tree.identify_column(event.x) # es. "#2"
                row_id = self.tree.identify_row(event.y)

                col_idx = int(column.replace('#', '')) - 2 # Sottrae per ottenere l'indice di date_keys
                if col_idx < 0:
                    return # Cliccato su intestazione "Orario"

                selected_date = date_keys[col_idx]
                selected_cat = self.tree.item(row_id)['values'][0]

                self.show_template_popup(selected_date, selected_cat)

        def on_click(event):
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                column = self.tree.identify_column(event.x)
                row_id = self.tree.identify_row(event.y)

                col_idx = int(column.replace('#', '')) - 2
                if col_idx < 0:
                    return

                selected_date = date_keys[col_idx]
                selected_cat = self.tree.item(row_id)['values'][0]

                raw_meal = plan_data.get(selected_date, {}).get(selected_cat, '-')
                # Estrae il nome in modo sicuro se per caso fosse rimasto un vecchio dizionario
                meal_name = raw_meal.get("nome", "-") if isinstance(raw_meal, dict) else raw_meal

                if meal_name == '-':
                    self.ingredients_label.config(text="Click su un pasto programmato per visualizzare gli ingredienti")
                    return

                if meal_name in meals:
                    porzioni = self.look_for(self.files['porzioni'], {})
                    porzione = porzioni.get(selected_date, {}).get(selected_cat, 1)
                    str_ingredients = ''
                    for i in meals[meal_name]:
                        str_ingredients += f"{i[1]*porzione:.2f} hg di {i[0]}, "
                    # Rimuove l'ultima virgola
                    str_ingredients = str_ingredients.strip(", ")
                    self.ingredients_label.config(text=f"{meal_name} fatto con: {str_ingredients}")
                else:
                    self.ingredients_label.config(text=f"{meal_name} (Nessun dettaglio ingredienti nel database)")

        self.tree.bind("<Double-Button-1>", on_double_click)
        self.tree.bind("<Button-1>", on_click)


        # --- Bottoni azione ---
        btn_frame = tk.Frame(self.main_frame, bg="#121214")
        btn_frame.pack(fill="x", pady=(0, 5))

        def run_ottimizza():
            ok = self.ottimizza_piano()
            if ok:
                self.show_planner_screen()

        btn_opt = self.create_button(
            btn_frame, "✨ Ottimizza Piano",
            command=run_ottimizza, bg="#7c3aed"
        )
        btn_opt.pack(side="left", padx=(0, 10))

        btn_cns = self.create_button(
            btn_frame, "⚙ Imposta Vincoli",
            command=self.show_constraints_dialog, bg="#0e7490"
        )
        btn_cns.pack(side="left", padx=(0, 15))

        self.create_label(
            btn_frame,
            "Riempi i giorni vuoti minimizzando il costo e rispettando i vincoli nutrizionali.",
            font=("Segoe UI", 9, "italic"), fg="#a0a0a5", bg="#121214"
        ).pack(side="left", anchor="w")

        # --- Riepilogo vincoli attivi ---
        constraints = self.look_for(self.files['constraints'], {})
        labels_map = {
            "kcal":        "Calorie",
            "proteine":    "Proteine",
            "carboidrati": "Carboidrati",
            "grassi":      "Grassi",
        }
        active_parts = []
        for key, lbl in labels_map.items():
            cfg = constraints.get(key, {})
            if not cfg.get('enabled', False):
                continue
            lo = cfg.get('min')
            hi = cfg.get('max')
            parts = []
            if lo is not None:
                parts.append(f"≥{lo:.0f}")
            if hi is not None:
                parts.append(f"≤{hi:.0f}")
            if parts:
                active_parts.append(f"{lbl}: {', '.join(parts)}")

        cns_frame = tk.Frame(self.main_frame, bg="#121214")
        cns_frame.pack(fill="x", pady=(0, 4))

        if active_parts:
            cns_icon = self.create_label(cns_frame, "📋 Vincoli attivi:",
                font=("Segoe UI", 9, "bold"), fg="#10b981", bg="#121214")
            cns_icon.pack(side="left", padx=(0, 6))
            self.create_label(cns_frame, "   |   ".join(active_parts),
                font=("Segoe UI", 9), fg="#d1d5db", bg="#121214"
            ).pack(side="left")
        else:
            self.create_label(cns_frame,
                "📋 Nessun vincolo nutrizionale attivo — usa ⚙ Imposta Vincoli per aggiungerne.",
                font=("Segoe UI", 9, "italic"), fg="#6b7280", bg="#121214"
            ).pack(side="left")

    def show_template_popup(self, target_date, category):
        top = tk.Toplevel(self.root)
        top.title(f"Pianifica: {category} ({target_date})")
        top.geometry("380x280")
        top.configure(bg="#1a1a1e")
        top.wait_visibility()
        top.grab_set()

        # Centra
        top.update_idletasks()
        width = top.winfo_width()
        height = top.winfo_height()
        x = (top.winfo_screenwidth() // 2) - (width // 2)
        y = (top.winfo_screenheight() // 2) - (height // 2)
        top.geometry(f'+{x}+{y}')

        self.create_label(top, f"Associa un Pasto Rapido a {category}:", font=("Segoe UI", 11, "bold")).pack(pady=(15, 5))

        templates = self.look_for(self.files['pasti'], {})
        lb_tmpl = self.create_listbox(top, width=40, height=6)
        lb_tmpl.pack(padx=20, pady=5)
        
        # Aggiunge opzione svuota cella
        lb_tmpl.insert(tk.END, "[ Svuota Cella ]")
        for t in sorted(templates.keys()): 
            lb_tmpl.insert(tk.END, t)

        def conferma():
            if not lb_tmpl.curselection():
                return
            nome_pasto = lb_tmpl.get(lb_tmpl.curselection()[0])

            # Operiamo su planner.json
            plan_data = self.look_for(self.files['plan'], {})

            if plan_data.get(target_date) is None:
                plan_data[target_date] = {"Colazione": '-', "Pranzo": '-', "Cena": '-'}

            if nome_pasto == "[ Svuota Cella ]":
                plan_data[target_date][category] = '-'
            else:
                plan_data[target_date][category] = nome_pasto

            self.record(self.files['plan'], plan_data)
            top.destroy()
            self.show_planner_screen() # Rinfresca la tabella principale
            
        btn_plan = self.create_button(top, "Inserisci nel Piano", command=conferma, bg="#27ae60")
        btn_plan.pack(pady=15)

if __name__ == "__main__":
    root = tk.Tk()
    app = DietApp(root)

    def on_closing():
        plt.close('all') # Chiude tutti i processi grafici di Matplotlib
        root.destroy()   # Chiude la finestra di Tkinter

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
