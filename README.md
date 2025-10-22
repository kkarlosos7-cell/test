# SAP Kanban Analyzer

**Automatická analýza raw materiálů pro identifikaci Kanban kandidátů pomocí SAP GUI Scriptingu**

## 📋 Popis

Tato aplikace automaticky analyzuje data ze SAP systému a vyhodnocuje, které raw materiály jsou vhodné kandidáty pro Kanban systém. Analýza je založena na:

- ✅ Frekvenci vyskladnění (počet pohybů ze skladu)
- ✅ Pravidelnosti spotřeby
- ✅ Hodnotě materiálu
- ✅ Obrátkovosti zásob

**Výstup:** Prioritizovaný seznam materiálů s potenciální úsporou vyskladnění a doporučením pro zavedení Kanbanu.

## 🎯 Co aplikace dělá

1. Připojí se k SAP GUI (předpokládá aktivní session)
2. Získá data o zásobách materiálů (transakce **MB52**)
3. Získá historii pohybů materiálů (transakce **MB51**)
4. Analyzuje spotřebu a pravidelnost
5. Vyhodnotí Kanban kandidáty podle konfigurovatelných kritérií
6. Vygeneruje Excel report s výsledky a doporučeními

## 🚀 Rychlý start

### Předpoklady

- **Windows OS** (SAP GUI Scripting vyžaduje Windows)
- **SAP GUI** nainstalované a spuštěné
- **Python 3.8+**
- **Přihlášení do SAP** (aplikace používá aktivní session)

### Instalace

1. **Klonuj nebo stáhni tento projekt**

```bash
git clone <repository-url>
cd sap-kanban-analyzer
```

2. **Nainstaluj Python závislosti**

```bash
pip install -r requirements.txt
```

3. **Povolení SAP GUI Scriptingu**

V SAP GUI:
- Options → Accessibility & Scripting → Scripting
- ✅ Zaškrtni "Enable scripting"
- ✅ Zaškrtni "Open/Close connections"

### Konfigurace

1. **Uprav `config.yaml`** podle svého prostředí:

```yaml
analysis:
  plant: "STD1"              # ← Tvůj werk
  material_types:
    - "ROH"                  # ← Typy materiálů k analýze

  kanban_criteria:
    min_movements_per_month: 10     # Minimální vyskladnění/měsíc
    min_consumption_regularity: 0.7 # Pravidelnost (0-1)
    max_value_per_piece: 10000      # Max hodnota/kus
    min_stock_turns: 4              # Minimální obrátkovost

  analysis_period_months: 6  # Kolik měsíců zpět analyzovat
```

### Spuštění

**Varianta 1: Hlavní skript (automatický průběh)**

```bash
python main.py
```

**Varianta 2: Jupyter Notebook (interaktivní testování)**

```bash
jupyter notebook test_notebook.ipynb
```

## 📁 Struktura projektu

```
sap-kanban-analyzer/
│
├── main.py                  # Hlavní spustitelný skript
├── config.yaml              # Konfigurace aplikace
├── requirements.txt         # Python závislosti
├── README.md                # Tato dokumentace
│
├── sap_connection.py        # Modul pro SAP GUI připojení
├── material_analyzer.py     # Modul pro analýzu materiálových dat
├── kanban_evaluator.py      # Modul pro vyhodnocení Kanban kandidátů
│
└── test_notebook.ipynb      # Jupyter notebook pro testování
```

## 🔧 Moduly

### `sap_connection.py`

Zajišťuje připojení k SAP GUI a základní operace:

```python
from sap_connection import SAPConnection

sap = SAPConnection()
sap.connect()
sap.start_transaction("MB52")
sap.set_field("wnd[0]/usr/ctxtWERKS-LOW", "STD1")
sap.send_vkey(8)  # F8 = Execute
```

### `material_analyzer.py`

Získává a analyzuje data o materiálech:

```python
from material_analyzer import MaterialAnalyzer

analyzer = MaterialAnalyzer(sap)

# Získej zásoby
stock = analyzer.get_materials_stock("STD1", "ROH")

# Získej pohyby
movements = analyzer.get_material_movements("STD1", "*", date_from, date_to)

# Analyzuj spotřebu
analysis = analyzer.analyze_material_consumption(movements)
```

### `kanban_evaluator.py`

Vyhodnocuje Kanban kandidáty:

```python
from kanban_evaluator import KanbanEvaluator

evaluator = KanbanEvaluator(kanban_criteria)

# Vyhodnoť kandidáty
results = evaluator.evaluate_kanban_candidates(consumption_analysis, stock_data)

# Vytvoř summary
summary = evaluator.generate_summary_report(results)

# Export do Excel
evaluator.export_to_excel(results, summary, "report.xlsx")
```

## 📊 Výstup

Aplikace vytvoří Excel soubor s následujícími listy:

1. **All Materials** - Všechny analyzované materiály se skóre
2. **Recommended for Kanban** - Jen doporučené materiály
3. **Summary** - Souhrnná statistika
4. **Top 10 Candidates** - Top 10 kandidátů s největším potenciálem

### Klíčové metriky ve výstupu:

- `Kanban_Score` (0-1): Celkové skóre vhodnosti pro Kanban
- `Movements_Per_Month`: Průměrný počet vyskladnění za měsíc
- `Consumption_Regularity` (0-1): Pravidelnost spotřeby (1 = maximálně pravidelná)
- `Potential_Savings_Movements`: Odhad ročních úspor vyskladnění
- `Recommendation_Reasons`: Textové zdůvodnění doporučení

## 🧪 Testování v Jupyter Notebooku

Jupyter notebook (`test_notebook.ipynb`) umožňuje:

- ✅ Interaktivní testování jednotlivých modulů
- ✅ Vizualizaci výsledků (grafy, scatter ploty)
- ✅ Prozkoumání dat krok po kroku
- ✅ Ladění a úpravu kritérií
- ✅ Vlastní ad-hoc analýzy

**Spuštění:**

```bash
jupyter notebook test_notebook.ipynb
```

## ⚙️ Kritéria pro vyhodnocení Kanban

Materiál je doporučen pro Kanban, pokud **Kanban_Score > 0.6**.

Skóre se počítá z těchto faktorů:

1. **Frekvence vyskladnění (30%)** - Čím častější pohyby, tím vhodnější
2. **Pravidelnost spotřeby (30%)** - Stabilní spotřeba = lepší pro Kanban
3. **Hodnota materiálu (20%)** - Levnější materiály preferovány
4. **Obrátkovost (20%)** - Vysoká obrátkovost = vhodné pro Kanban

Každý faktor je normalizován na škálu 0-1.

## 🎨 Přizpůsobení

### Změna kritérií

Uprav `config.yaml`:

```yaml
kanban_criteria:
  min_movements_per_month: 15      # Zvýšení prahu
  min_consumption_regularity: 0.8  # Přísnější pravidelnost
  max_value_per_piece: 5000        # Nižší maximální hodnota
  min_stock_turns: 6               # Vyšší obrátkovost
```

### Změna vah ve skóre

Uprav `kanban_evaluator.py` → metoda `evaluate_kanban_candidates()`:

```python
df['Kanban_Score'] = (
    freq_score * 0.4 +        # ← Změň váhy
    regularity_score * 0.3 +
    value_score * 0.2 +
    turnover_score * 0.1
)
```

### Přidání vlastního movement type filtru

Uprav `material_analyzer.py` → metoda `analyze_material_consumption()`:

```python
# Filtruj specifické movement types
issue_types = ['261', '281', '201', '221', 'Z99']  # ← Přidej vlastní
```

## 🐛 Troubleshooting

### ❌ "SAP GUI není spuštěná"

- Ujisti se, že SAP GUI je otevřená a jsi přihlášen
- Zkontroluj, že máš aktivní session

### ❌ "Scripting není povolený"

- SAP GUI → Options → Accessibility & Scripting → Scripting
- Zaškrtni "Enable scripting"

### ❌ "Chyba při extrakci dat z gridu"

- Data mohou mít jiné názvy sloupců než očekávané
- Zkontroluj `movements_data.columns` a uprav názvy v kódu
- Použij Jupyter notebook pro debugging

### ❌ "Žádná data nalezena"

- Zkontroluj, že werk a typ materiálu v `config.yaml` jsou správné
- Zkontroluj, že máš oprávnění k transakcím MB51 a MB52
- Zkus manuálně spustit MB52 s tvými parametry a zkontroluj data

### ❌ "Název sloupce nenalezen"

SAP může vracet data s různými názvy sloupců v různých systémech.

**Řešení:**

1. Spusť Jupyter notebook
2. Získej data pomocí `get_material_movements()`
3. Zobraz sloupce: `print(movements_data.columns)`
4. Uprav názvy sloupců v `analyze_material_consumption()` podle toho

## 📝 Poznámky

- **Performance:** Analýza může trvat několik minut v závislosti na množství dat
- **SAP verze:** Testováno na SAP ECC 6.0, mělo by fungovat i na S/4HANA
- **Transakce:** Vyžaduje přístup k MB51, MB52
- **Bezpečnost:** Aplikace NEČTE ani NEUKLÁDÁ přihlašovací údaje - používá aktivní session

## 🤝 Příspěvky a úpravy

Tento kód je poskytnutý jako základ. Můžeš ho upravit podle svých potřeb:

- Přidat další transakce (MM03 pro master data, MMBE pro stock/requirements)
- Přidat analýzu ABC klasifikace
- Integrovat s jinými systémy (email report, database export)
- Přidat grafické UI (tkinter, PyQt)

## 📄 Licence

Tento projekt je poskytnutý "jak je" bez jakýchkoli záruk.

## 🆘 Podpora

Pro otázky nebo problémy:

1. Zkontroluj sekci **Troubleshooting** výše
2. Použij Jupyter notebook pro debugging
3. Zkontroluj SAP GUI Scripting dokumentaci

---

**Happy Kanban Analysis! 🎯**
