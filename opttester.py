import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

df = pd.read_excel('Optimiserdata.xlsx', sheet_name='Sheet2')

# Category definitions: prefix -> (Name col, Price col, CO2 col)
CATEGORIES = {
    'WM':  ('WMN',  'WMP',  'WMC'),
    'DW':  ('DWN',  'DWP',  'DWC'),
    'DS':  ('DSN',  'DSP',  'DSC'),
    'WFP': ('WFPN', 'WFPP', 'WFPC'),
    'KR':  ('KRN',  'KRP',  'KRC'),
    'TR':  ('TRN',  'TRP',  'TRC'),
    'BB':  ('BBN',  'BBP',  'BBC'),
    'TP':  ('TPN',  'TPP',  'TPC'),
    'HS':  ('HSN',  'HSP',  'HSC'),
    'DEO': ('DEON', 'DEOP', 'DEOC'),
    'SHA': ('SHAN', 'SHAP', 'SHAC'),
    'BW':  ('BWN',  'BWP',  'BWC'),
    'CON': ('CONN', 'CONP', 'CONC'),
    'DF':  ('DFN',  'DFP',  'DFC'),
    'CF':  ('CFN',  'CFP',  'CFC'),
}

def get_category_products(category_key):
    """Return list of {id, name, price, co2} dicts for all products in a category."""
    name_col, price_col, co2_col = CATEGORIES[category_key]
    products = []
    for _, row in df.iterrows():
        name = row[name_col]
        price = row[price_col]
        co2 = row[co2_col]
        if pd.notna(name) and pd.notna(price) and pd.notna(co2):
            products.append({
                'id': str(name),
                'name': str(name),
                'price': round(float(price), 2),
                'co2': round(float(co2), 2),
            })
    return products

def identify_category(item_id):
    """Identify which category an item belongs to by matching its ID prefix.
    Longest prefix is checked first to handle e.g. 'WFP' before 'W'."""
    for key in sorted(CATEGORIES.keys(), key=len, reverse=True):
        if item_id.upper().startswith(key):
            return key
    return None

def get_item_details(item_id):
    """Look up full product details from the dataframe by product ID."""
    for cat_key, (name_col, price_col, co2_col) in CATEGORIES.items():
        for _, row in df.iterrows():
            if str(row[name_col]).upper() == item_id.upper():
                return {
                    'id': str(row[name_col]),
                    'name': str(row[name_col]),
                    'price': round(float(row[price_col]), 2),
                    'co2': round(float(row[co2_col]), 2),
                    'category': cat_key,
                }
    return None

def optimise_basket(basket):
    """
    Given a basket of items, return a new basket with:
    - Exactly the same categories as the original (no additions, no removals)
    - One item per category
    - Total CO2 minimised
    - Total cost <= original basket total cost

    Uses dynamic programming over a discretised budget (integer pence) to
    guarantee the global optimum for any basket size up to all 15 categories.
    A 1-pence tolerance is added to absorb floating-point accumulation errors.
    """
    # --- Resolve items and collect categories ---
    original_categories = []
    original_total_cost = 0.0

    for item in basket:
        item_id = item.get('id', '')
        details = get_item_details(item_id)
        if details is None:
            cat_key = identify_category(item_id)
            if cat_key is None:
                # Skip unrecognised items
                continue
            details = {
                'id': item_id,
                'name': item.get('name', item_id),
                'price': float(item.get('price', 0)),
                'co2': float(item.get('co2', 0)),
                'img': item.get('img', f"{item_id}.png"),
                'category': cat_key,
            }
        original_categories.append(details['category'])
        original_total_cost += details['price']

    # Deduplicate categories while preserving order
    seen = set()
    unique_categories = []
    for c in original_categories:
        if c not in seen:
            seen.add(c)
            unique_categories.append(c)

    category_options = {cat: get_category_products(cat) for cat in unique_categories}

    # --- Dynamic programming over discretised budget ---
    # Work in integer pence to avoid floating-point drift.
    # Add 1p tolerance to absorb any accumulated rounding error across categories.
    SCALE = 100
    TOLERANCE_PENCE = 1
    max_budget = int(round(original_total_cost * SCALE )) + TOLERANCE_PENCE

    # dp maps budget_spent (int pence) -> (total_co2, [chosen product dicts])
    # Only the lowest-CO2 state is kept for each budget level.
    dp = {0: (0.0, [])}

    for cat in unique_categories:
        new_dp = {}
        options = category_options[cat]

        for spent, (co2_so_far, chosen) in dp.items():
            for prod in options:
                new_spent = spent + int(round(prod['price'] * SCALE))
                if new_spent > max_budget:
                    continue
                new_co2 = co2_so_far + prod['co2']
                if new_spent not in new_dp or new_co2 < new_dp[new_spent][0]:
                    new_dp[new_spent] = (new_co2, chosen + [prod])

        dp = new_dp

    if not dp:
        raise ValueError(
            "No valid combination found within budget. "
            "The budget may be too tight for the selected categories."
        )

    # Return the complete basket with the lowest total CO2
    _, new_basket = min(dp.values(), key=lambda x: x[0])
    return new_basket


@app.route('/optimise', methods=['POST'])
def optimise():
    basket = request.get_json()
    print("Received basket for optimisation:", basket)

    try:
        new_basket = optimise_basket(basket)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    print("Optimised basket:", new_basket)
    return jsonify(new_basket)


if __name__ == '__main__':
    app.run(debug=True)
