import os, json, uuid
from datetime import datetime, timedelta
from io import BytesIO
from functools import lru_cache

import flask
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy import stats
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, value, PULP_CBC_CMD, LpStatusInfeasible, LpBinary, LpContinuous

app = flask.Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(16).hex())
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_PERMANENT=False,
)

DATA_FOLDER = "Dati_Dieta"
FILES = {
    'prices': os.path.join(DATA_FOLDER, 'food_prices.json'),
    'weights': os.path.join(DATA_FOLDER, 'wrecord.json'),
    'nvalues': os.path.join(DATA_FOLDER, 'nvalues.json'),
    'eaten': os.path.join(DATA_FOLDER, 'eaten_lists.json'),
    'calories': os.path.join(DATA_FOLDER, 'calories.json'),
    'pasti': os.path.join(DATA_FOLDER, 'pasti.json'),
    'plan': os.path.join(DATA_FOLDER, 'planner.json'),
    'constraints': os.path.join(DATA_FOLDER, 'constraints.json'),
    'porzioni': os.path.join(DATA_FOLDER, 'porzioni_piano.json'),
}
MEAL_CATEGORIES = ["Colazione", "Pranzo", "Cena", "Merenda"]

# --- Database setup (PostgreSQL on Render, JSON files locally) ---
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_DB = DATABASE_URL is not None

if USE_DB:
    import psycopg2
    from psycopg2.extras import Json

    def get_db():
        return psycopg2.connect(DATABASE_URL)

    def init_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id TEXT PRIMARY KEY,
                data JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()

    def get_user_id():
        if 'user_id' not in flask.session:
            flask.session['user_id'] = uuid.uuid4().hex
        return flask.session['user_id']

    def load_user_data():
        uid = get_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT data FROM user_data WHERE user_id = %s', (uid,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
        return {}

    def save_user_data(data):
        uid = get_user_id()
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO user_data (user_id, data) VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET data = %s
        ''', (uid, Json(data), Json(data)))
        conn.commit()
        cur.close()
        conn.close()

    init_db()

def _path_to_key(path):
    """Convert a FILES path back to its key name, or return the path as-is."""
    for k, v in FILES.items():
        if v == path:
            return k
    return os.path.basename(path).replace('.json', '')

def look_for(path, default=None):
    if default is None:
        default = {}

    if USE_DB:
        key = _path_to_key(path)
        full = load_user_data()
        return full.get(key, default)

    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return default
    return default

def record(path, data):
    if USE_DB:
        key = _path_to_key(path)
        full = load_user_data()
        full[key] = data
        save_user_data(full)
        return

    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        flask.flash(f"Errore salvataggio: {e}", "error")

def load_data():
    data = {}
    data['weights'] = look_for(FILES['weights'], [])
    data['calories'] = look_for(FILES['calories'], [])
    data['nvalues'] = look_for(FILES['nvalues'], {})
    data['prices'] = look_for(FILES['prices'], {})
    data['constraints'] = look_for(FILES['constraints'], {})
    data['today_str'] = datetime.now().strftime("%Y-%m-%d")
    all_eaten = look_for(FILES['eaten'], {})
    data['today_eaten'] = all_eaten.get(data['today_str'], [])
    data['all_eaten'] = all_eaten
    return data

def save_food_data(today_str, today_eaten):
    all_data = look_for(FILES['eaten'], {})
    all_data[today_str] = today_eaten
    record(FILES['eaten'], all_data)

def _get_meal_ingredients(meal_data):
    if isinstance(meal_data, dict) and 'ingredients' in meal_data:
        return meal_data['ingredients']
    return meal_data if isinstance(meal_data, list) else []

def _get_meal_category(meal_data):
    if isinstance(meal_data, dict) and 'category' in meal_data:
        return meal_data['category']
    return ''

def _format_meal_name(val):
    if isinstance(val, dict):
        return val.get("nome", val.get("pasto", "-"))
    return val if val else "-"

def calcola_valori_pasto(nome_pasto, templates, nvalues):
    totali = {"kcal": 0.0, "proteine": 0.0, "carboidrati": 0.0, "grassi": 0.0}
    if nome_pasto == '-' or not nome_pasto:
        return totali
    ingredienti = _get_meal_ingredients(templates.get(nome_pasto, []))
    for food, qty in ingredienti:
        if food in nvalues:
            info = nvalues[food]
            totali["kcal"] += info.get("kcal", 0.0) * qty
            totali["proteine"] += info.get("proteine", 0.0) * qty
            totali["carboidrati"] += info.get("carboidrati", 0.0) * qty
            totali["grassi"] += info.get("grassi", 0.0) * qty
    return totali

def calcola_costo_pasto(nome_pasto, templates, prices):
    if nome_pasto == '-' or not nome_pasto:
        return 0.0
    ingredienti = _get_meal_ingredients(templates.get(nome_pasto, []))
    costo = 0.0
    for food, qty in ingredienti:
        p = prices.get(food, 0.0)
        if p <= 0.0:
            return None
        costo += p * qty
    return costo

# --- Routes ---

@app.route('/')
def main_screen():
    data = load_data()
    today_plan_data = look_for(FILES['plan'], {})
    today_plan = today_plan_data.get(data['today_str'], {c: '-' for c in MEAL_CATEGORIES})
    if today_plan is None:
        today_plan = {c: '-' for c in MEAL_CATEGORIES}

    stats_data = compute_stats(data)
    return flask.render_template('main.html', active='main', data=data,
                                 today_plan=today_plan, stats=stats_data)

@app.route('/record_weight', methods=['POST'])
def record_weight():
    val = flask.request.form.get('weight', '')
    try:
        val_float = float(val)
        weights = look_for(FILES['weights'], [])
        weights.append([datetime.now().isoformat(), val_float])
        record(FILES['weights'], weights)
        flask.flash("Peso registrato con successo!", "success")
    except ValueError:
        flask.flash("Inserisci un numero valido per il peso!", "error")
    return flask.redirect('/')

@app.route('/record_calories', methods=['POST'])
def record_calories():
    val = flask.request.form.get('calories', '')
    try:
        val_float = float(val)
        calories = look_for(FILES['calories'], [])
        calories.append([datetime.now().isoformat(), val_float])
        record(FILES['calories'], calories)
        flask.flash("Calorie registrate con successo!", "success")
    except ValueError:
        flask.flash("Inserisci un numero valido per le calorie!", "error")
    return flask.redirect('/')

@app.route('/plot')
def plot():
    data = load_data()
    weights = data['weights']
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=100, facecolor='#1a1a1e')
    ax.set_facecolor('#1a1a1e')

    dates, y_vals = [], []
    for item in weights:
        try:
            dates.append(datetime.fromisoformat(item[0]))
            y_vals.append(float(item[1]))
        except (ValueError, TypeError):
            continue

    if dates:
        sorted_pairs = sorted(zip(dates, y_vals))
        sorted_dates, sorted_y = zip(*sorted_pairs)
        ax.plot(sorted_dates, sorted_y, marker='o', color='#10b981', linewidth=2.5, markersize=5, label='Peso (kg)')
        ax.set_title("Andamento Peso Corporeo", color='white', fontsize=12, fontweight='bold', pad=12)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    for spine in ax.spines.values():
        spine.set_color('#252529')
    ax.tick_params(colors='white', which='both', labelsize=8)
    ax.grid(True, color='#252529', linestyle='--', alpha=0.6)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', facecolor='#1a1a1e')
    plt.close(fig)
    buf.seek(0)
    return flask.Response(buf.getvalue(), mimetype='image/png')

def compute_stats(data):
    weights = data['weights']
    calories = data['calories']
    result = {'trend': 'Stazionario', 'slope': 'Dati insufficienti', 'mean_cal': 'N/D', 'fabisogno': 'N/D'}

    if len(weights) > 1:
        y = np.array([float(w[1]) for w in weights])
        first_day = datetime.fromisoformat(weights[0][0])
        x = np.array([(datetime.fromisoformat(i[0]) - first_day).total_seconds()/86400 for i in weights])
        if len(x) > 1:
            slope, intercept, r, p_val, std_err = stats.linregress(x, y)
            trend_dir = "Dimagrimento" if slope < 0 else "Aumento"
            result['trend'] = trend_dir
            result['slope'] = f"{slope:.3f} kg/giorno (circa {slope*7700:.0f} kcal/giorno)"
            if calories:
                mean_cal = np.mean([float(i[1]) for i in calories])
                result['mean_cal'] = f"{int(mean_cal)} kcal/giorno"
                result['fabisogno'] = f"{mean_cal - slope*7700:.0f} kcal/giorno"
            else:
                result['mean_cal'] = "N/D"
                result['fabisogno'] = "Dati peso insufficienti"

    return result

# --- FOOD DIARY ---

@app.route('/food')
def food_screen():
    data = load_data()
    food_list = sorted(data['nvalues'].keys())
    return flask.render_template('food.html', active='food', data=data, food_list=food_list)

@app.route('/add_food_item', methods=['POST'])
def add_food_item():
    name = flask.request.form.get('name', '').strip()
    qty_str = flask.request.form.get('qty', '')
    if not name:
        flask.flash("Inserisci il nome di un alimento!", "error")
        return flask.redirect('/food')
    try:
        qty = float(qty_str)
    except ValueError:
        flask.flash("Inserisci una quantità numerica valida!", "error")
        return flask.redirect('/food')

    data = load_data()
    today_eaten = data['today_eaten']
    today_eaten.append([name, qty])
    save_food_data(data['today_str'], today_eaten)
    return flask.redirect('/food')

@app.route('/delete_food_item', methods=['POST'])
def delete_food_item():
    idx = flask.request.form.get('idx', '')
    try:
        idx = int(idx)
    except ValueError:
        return flask.redirect('/food')
    data = load_data()
    today_eaten = data['today_eaten']
    if 0 <= idx < len(today_eaten):
        today_eaten.pop(idx)
        save_food_data(data['today_str'], today_eaten)
    return flask.redirect('/food')

@app.route('/new_food_nutrition', methods=['POST'])
def new_food_nutrition():
    food_name = flask.request.form.get('food_name', '').strip()
    kcal_str = flask.request.form.get('kcal', '')
    if not food_name or not kcal_str:
        return flask.redirect('/food')
    try:
        kcal = float(kcal_str)
    except ValueError:
        flask.flash("Inserisci un valore numerico valido!", "error")
        return flask.redirect('/food')
    nvalues = look_for(FILES['nvalues'], {})
    nvalues[food_name] = {'kcal': kcal}
    record(FILES['nvalues'], nvalues)
    return flask.redirect('/food')

# --- HISTORY ---

@app.route('/history')
def history_screen():
    data = load_data()
    all_eaten = data['all_eaten']
    date_list = sorted(all_eaten.keys(), reverse=True)
    templates = look_for(FILES['pasti'], {})
    return flask.render_template('history.html', active='history', data=data,
                                 date_list=date_list, templates=templates)

@app.route('/save_meal_template', methods=['POST'])
def save_meal_template():
    nome_pasto = flask.request.form.get('nome_pasto', '').strip()
    ingredienti_json = flask.request.form.get('ingredienti', '[]')
    category = flask.request.form.get('category', '')

    if not nome_pasto:
        flask.flash("Inserisci un nome per il Pasto Rapido!", "error")
        return flask.redirect('/history')

    try:
        ingredienti = json.loads(ingredienti_json)
    except json.JSONDecodeError:
        ingredienti = []

    if not ingredienti:
        flask.flash("Aggiungi almeno un ingrediente!", "error")
        return flask.redirect('/history')

    templates = look_for(FILES['pasti'], {})
    if category:
        templates[nome_pasto] = {"ingredients": ingredienti, "category": category}
    else:
        templates[nome_pasto] = ingredienti
    record(FILES['pasti'], templates)
    flask.flash(f"Pasto '{nome_pasto}' salvato correttamente!", "success")
    return flask.redirect('/history')

# --- PLANNER ---

@app.route('/planner')
def planner_screen():
    data = load_data()
    plan_data = look_for(FILES['plan'], {})
    templates = look_for(FILES['pasti'], {})
    porzioni = look_for(FILES['porzioni'], {})
    constraints = look_for(FILES['constraints'], {})

    date_keys = []
    for i in range(5):
        date_obj = datetime.now() + timedelta(days=i)
        d_key = date_obj.strftime("%Y-%m-%d")
        d_display = date_obj.strftime("%a %d/%m")
        d_display = d_display.replace("Mon","Lun").replace("Tue","Mar").replace("Wed","Mer").replace("Thu","Gio").replace("Fri","Ven").replace("Sat","Sab").replace("Sun","Dom")
        date_keys.append({'key': d_key, 'display': d_display})

    # Compute active constraints
    labels_map = {"kcal":"Calorie","proteine":"Proteine","carboidrati":"Carboidrati","grassi":"Grassi"}
    active_parts = []
    for key, lbl in labels_map.items():
        cfg = constraints.get(key, {})
        if not cfg.get('enabled', False):
            continue
        lo, hi = cfg.get('min'), cfg.get('max')
        parts = []
        if lo is not None: parts.append(f"\u2265{lo:.0f}")
        if hi is not None: parts.append(f"\u2264{hi:.0f}")
        if parts: active_parts.append(f"{lbl}: {', '.join(parts)}")

    return flask.render_template('planner.html', active='planner', data=data,
                                 plan_data=plan_data, templates=templates,
                                 porzioni=porzioni, date_keys=date_keys,
                                 constraints=constraints, active_parts=active_parts,
                                 meal_categories=MEAL_CATEGORIES)

@app.route('/assign_meal', methods=['POST'])
def assign_meal():
    target_date = flask.request.form.get('date', '')
    category = flask.request.form.get('category', '')
    meal_name = flask.request.form.get('meal_name', '')

    plan_data = look_for(FILES['plan'], {})
    if target_date not in plan_data or plan_data[target_date] is None:
        plan_data[target_date] = {c: '-' for c in MEAL_CATEGORIES}

    if meal_name == "[ Svuota Cella ]":
        plan_data[target_date][category] = '-'
    else:
        plan_data[target_date][category] = meal_name

    record(FILES['plan'], plan_data)
    return flask.redirect('/planner')

@app.route('/swap_meals', methods=['POST'])
def swap_meals():
    src_date = flask.request.form.get('src_date', '')
    src_cat = flask.request.form.get('src_cat', '')
    dst_date = flask.request.form.get('dst_date', '')
    dst_cat = flask.request.form.get('dst_cat', '')

    plan_data = look_for(FILES['plan'], {})
    for d in [src_date, dst_date]:
        if d not in plan_data or plan_data[d] is None:
            plan_data[d] = {c: '-' for c in MEAL_CATEGORIES}

    src_val = plan_data[src_date].get(src_cat, '-')
    dst_val = plan_data[dst_date].get(dst_cat, '-')
    plan_data[src_date][src_cat] = dst_val
    plan_data[dst_date][dst_cat] = src_val
    record(FILES['plan'], plan_data)
    flask.flash("Pasti scambiati con successo!", "success")
    return flask.redirect('/planner')

@app.route('/ottimizza', methods=['POST'])
def ottimizza():
    try:
        ok = ottimizza_piano_func()
        if ok:
            flask.flash("Ottimizzazione completata con successo!", "success")
        else:
            flask.flash("Nessuna modifica apportata.", "info")
    except Exception as e:
        flask.flash(f"Errore durante l'ottimizzazione: {e}", "error")
    return flask.redirect('/planner')

def ottimizza_piano_func():
    templates = look_for(FILES['pasti'], {})
    if not templates:
        flask.flash("Non ci sono Pasti Rapidi salvati!", "warning")
        return False

    nvalues = look_for(FILES['nvalues'], {})
    prices = look_for(FILES['prices'], {})

    eligible_meals = []
    meal_base_costs = {}
    meal_base_nutrients = {}

    for nome in templates:
        costo = calcola_costo_pasto(nome, templates, prices)
        if costo is not None and costo > 0:
            eligible_meals.append(nome)
            meal_base_costs[nome] = costo
            meal_base_nutrients[nome] = calcola_valori_pasto(nome, templates, nvalues)

    if not eligible_meals:
        flask.flash("Nessun pasto ha prezzi validi nel database!", "error")
        return False

    plan_data = look_for(FILES['plan'], {})
    constraints = look_for(FILES['constraints'], {})

    # Exclude already assigned meals
    assigned_meals = set()
    for i in range(5):
        date_obj = datetime.now() + timedelta(days=i)
        d_key = date_obj.strftime("%Y-%m-%d")
        day_plan = plan_data.get(d_key, {})
        if day_plan:
            for cat in MEAL_CATEGORIES:
                meal = day_plan.get(cat, "-")
                if meal and meal != "-":
                    assigned_meals.add(meal)
    eligible_meals = [m for m in eligible_meals if m not in assigned_meals]
    if not eligible_meals:
        flask.flash("Tutti i pasti sono già assegnati manualmente.", "info")
        return False

    # Find empty slots (excluding Merenda)
    days_slots = {}
    for i in range(5):
        date_obj = datetime.now() + timedelta(days=i)
        d_key = date_obj.strftime("%Y-%m-%d")
        day_plan = plan_data.get(d_key, {c: '-' for c in MEAL_CATEGORIES})
        if day_plan is None:
            day_plan = {c: '-' for c in MEAL_CATEGORIES}
        for cat in MEAL_CATEGORIES:
            if cat == "Merenda":
                continue
            name = day_plan.get(cat, "-")
            if not name or name == "-":
                days_slots.setdefault(d_key, []).append(cat)

    if not days_slots:
        flask.flash("Tutti i giorni hanno già un piano completo.", "info")
        return False

    slots_to_fill = []
    for d_key in sorted(days_slots):
        for cat in days_slots[d_key]:
            slots_to_fill.append((d_key, cat))

    # Build PuLP model
    model = LpProblem("diet_dynamic_portions", LpMinimize)
    scelto, porzione = {}, {}

    for s_idx in range(len(slots_to_fill)):
        for nome in eligible_meals:
            safe = nome.replace(' ', '_').replace('/', '_')
            scelto[(s_idx, nome)] = LpVariable(f"scelto_{s_idx}_{safe}", cat=LpBinary)
            porzione[(s_idx, nome)] = LpVariable(f"porzione_{s_idx}_{safe}", lowBound=0.0, cat=LpContinuous)

    model += lpSum(porzione[(s_idx, nome)] * meal_base_costs[nome]
                   for s_idx in range(len(slots_to_fill)) for nome in eligible_meals)

    for s_idx in range(len(slots_to_fill)):
        model += lpSum(scelto[(s_idx, nome)] for nome in eligible_meals) == 1
        for nome in eligible_meals:
            model += porzione[(s_idx, nome)] >= 0.5 * scelto[(s_idx, nome)]
            model += porzione[(s_idx, nome)] <= 1.8 * scelto[(s_idx, nome)]

    for nome in eligible_meals:
        model += lpSum(scelto[(s_idx, nome)] for s_idx in range(len(slots_to_fill))) <= 1

    for s_idx in range(len(slots_to_fill)):
        d_key, cat = slots_to_fill[s_idx]
        for nome in eligible_meals:
            meal_data = templates.get(nome)
            if meal_data is not None:
                meal_cat = _get_meal_category(meal_data)
                if meal_cat and meal_cat != cat:
                    model += scelto[(s_idx, nome)] == 0

    for nutrient in ["kcal", "proteine", "carboidrati", "grassi"]:
        cfg = constraints.get(nutrient, {"min": None, "max": None})
        lo, hi = cfg.get("min"), cfg.get("max")
        if lo is None and hi is None:
            continue
        for d_key in sorted(days_slots):
            day_s_indices = [s_idx for s_idx, (dk, _) in enumerate(slots_to_fill) if dk == d_key]
            if not day_s_indices:
                continue
            nutrient_sum = lpSum(porzione[(s_idx, nome)] * meal_base_nutrients[nome].get(nutrient, 0.0)
                                 for s_idx in day_s_indices for nome in eligible_meals)
            fixed_day = plan_data.get(d_key, {})
            fixed_val = 0.0
            for cat in MEAL_CATEGORIES:
                nome_fissato = fixed_day.get(cat, "-")
                if nome_fissato and nome_fissato != "-":
                    fixed_val += calcola_valori_pasto(nome_fissato, templates, nvalues).get(nutrient, 0.0)
            if lo is not None:
                model += (nutrient_sum + fixed_val) >= lo
            if hi is not None:
                model += (nutrient_sum + fixed_val) <= hi

    status = model.solve(PULP_CBC_CMD(msg=False))
    if status == LpStatusInfeasible:
        flask.flash("Impossibile trovare una combinazione che soddisfi i vincoli!", "error")
        return False

    for s_idx, (d_key, cat) in enumerate(slots_to_fill):
        for nome in eligible_meals:
            if value(scelto[(s_idx, nome)]) == 1:
                if d_key not in plan_data or plan_data[d_key] is None:
                    plan_data[d_key] = {c: '-' for c in MEAL_CATEGORIES}
                plan_data[d_key][cat] = nome

    porzioni_data = look_for(FILES['porzioni'], {})
    for s_idx, (d_key, cat) in enumerate(slots_to_fill):
        for nome in eligible_meals:
            if value(scelto[(s_idx, nome)]) == 1:
                if d_key not in porzioni_data:
                    porzioni_data[d_key] = {}
                porzioni_data[d_key][cat] = round(float(value(porzione[(s_idx, nome)])), 2)
    record(FILES['porzioni'], porzioni_data)
    record(FILES['plan'], plan_data)
    return True

# --- DATABASE ---

@app.route('/database')
def database_screen():
    data = load_data()
    templates = look_for(FILES['pasti'], {})
    return flask.render_template('database.html', active='database', data=data, templates=templates)

@app.route('/add_food', methods=['POST'])
def add_food():
    nome = flask.request.form.get('nome', '').strip()
    if not nome:
        flask.flash("Inserisci il nome dell'alimento!", "error")
        return flask.redirect('/database')

    nvalues = look_for(FILES['nvalues'], {})
    if nome in nvalues:
        flask.flash(f"L'alimento '{nome}' esiste già!", "error")
        return flask.redirect('/database')

    try:
        kcal = float(flask.request.form.get('kcal', '0') or 0)
        prot = float(flask.request.form.get('proteine', '0') or 0)
        carb = float(flask.request.form.get('carboidrati', '0') or 0)
        grassi = float(flask.request.form.get('grassi', '0') or 0)
        prezzo = float(flask.request.form.get('prezzo', '0') or 0)
    except ValueError:
        flask.flash("Inserisci valori numerici validi!", "error")
        return flask.redirect('/database')

    nvalues[nome] = {"kcal": kcal, "proteine": prot, "carboidrati": carb, "grassi": grassi}
    record(FILES['nvalues'], nvalues)

    prices = look_for(FILES['prices'], {})
    prices[nome] = prezzo
    record(FILES['prices'], prices)

    flask.flash(f"Alimento '{nome}' aggiunto con successo!", "success")
    return flask.redirect('/database')

@app.route('/delete_food', methods=['POST'])
def delete_food():
    nome = flask.request.form.get('nome', '').strip()
    if not nome:
        return flask.redirect('/database')

    nvalues = look_for(FILES['nvalues'], {})
    if nome in nvalues:
        del nvalues[nome]
        record(FILES['nvalues'], nvalues)

    prices = look_for(FILES['prices'], {})
    if nome in prices:
        del prices[nome]
        record(FILES['prices'], prices)

    flask.flash(f"Alimento '{nome}' eliminato!", "success")
    return flask.redirect('/database')

@app.route('/update_food', methods=['POST'])
def update_food():
    old_name = flask.request.form.get('old_name', '').strip()
    field = flask.request.form.get('field', '')
    value_new = flask.request.form.get('value', '').strip()

    nvalues = look_for(FILES['nvalues'], {})
    prices = look_for(FILES['prices'], {})

    if field == 'nome':
        if not value_new or value_new in nvalues:
            return flask.redirect('/database')
        if old_name in nvalues:
            nvalues[value_new] = nvalues.pop(old_name)
            record(FILES['nvalues'], nvalues)
        if old_name in prices:
            prices[value_new] = prices.pop(old_name)
            record(FILES['prices'], prices)
        # Rename in templates
        templates = look_for(FILES['pasti'], {})
        updated = False
        for meal_name, meal_data in templates.items():
            ing_list = _get_meal_ingredients(meal_data)
            for ing_pair in ing_list:
                if ing_pair[0] == old_name:
                    ing_pair[0] = value_new
                    updated = True
        if updated:
            record(FILES['pasti'], templates)
    elif field == 'prezzo':
        try:
            prices[old_name] = float(value_new)
            record(FILES['prices'], prices)
        except ValueError:
            pass
    elif field in ('kcal', 'proteine', 'carboidrati', 'grassi'):
        if old_name in nvalues:
            try:
                nvalues[old_name][field] = float(value_new)
                record(FILES['nvalues'], nvalues)
            except ValueError:
                pass

    return flask.redirect('/database')

# --- CONSTRAINTS ---

@app.route('/constraints', methods=['GET', 'POST'])
def constraints_screen():
    if flask.request.method == 'POST':
        new_constraints = {}
        for key in ["kcal", "proteine", "carboidrati", "grassi"]:
            enabled = flask.request.form.get(f'enabled_{key}') == 'on'
            lo_str = flask.request.form.get(f'min_{key}', '').strip()
            hi_str = flask.request.form.get(f'max_{key}', '').strip()
            try:
                lo_val = float(lo_str) if lo_str else None
            except ValueError:
                flask.flash(f"Valore minimo non valido per {key}!", "error"); return flask.redirect('/constraints')
            try:
                hi_val = float(hi_str) if hi_str else None
            except ValueError:
                flask.flash(f"Valore massimo non valido per {key}!", "error"); return flask.redirect('/constraints')
            new_constraints[key] = {'enabled': enabled, 'min': lo_val, 'max': hi_val}
        record(FILES['constraints'], new_constraints)
        flask.flash("Vincoli salvati!", "success")
        return flask.redirect('/planner')

    constraints = look_for(FILES['constraints'], {})
    return flask.render_template('constraints.html', constraints=constraints)

app.jinja_env.globals.update(_format_meal_name=_format_meal_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
