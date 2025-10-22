"""
SAP Kanban Analyzer - Main Script
Hlavní skript pro analýzu materiálů a vyhodnocení Kanban kandidátů
"""

import yaml
import logging
from datetime import datetime, timedelta
from sap_connection import SAPConnection
from material_analyzer import MaterialAnalyzer
from kanban_evaluator import KanbanEvaluator

# Konfigurace loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file: str = "config.yaml") -> dict:
    """Načte konfiguraci ze souboru"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info("Konfigurace načtena")
        return config
    except Exception as e:
        logger.error(f"Chyba při načítání konfigurace: {e}")
        return {}


def main():
    """Hlavní funkce programu"""

    print("=" * 60)
    print("SAP KANBAN ANALYZER")
    print("Analýza materiálů pro vyhodnocení Kanban kandidátů")
    print("=" * 60)
    print()

    # 1. Načti konfiguraci
    config = load_config()
    if not config:
        logger.error("Nelze pokračovat bez konfigurace")
        return

    plant = config['analysis']['plant']
    material_types = config['analysis']['material_types']
    analysis_months = config['analysis']['analysis_period_months']

    print(f"Werk: {plant}")
    print(f"Typy materiálů: {', '.join(material_types)}")
    print(f"Období analýzy: {analysis_months} měsíců")
    print()

    # 2. Připoj se k SAP
    print("Připojování k SAP GUI...")
    sap = SAPConnection()

    if not sap.connect():
        print("\n⚠️  UPOZORNĚNÍ: Nepodařilo se připojit k SAP GUI.")
        print("Ujisti se, že:")
        print("  1. SAP GUI je spuštěná")
        print("  2. Jsi přihlášen do systému")
        print("  3. SAP GUI Scripting je povolený")
        print("\nPro povolení scriptingu:")
        print("  SAP GUI → Options → Accessibility & Scripting → Scripting")
        print("  ✓ Enable scripting")
        return

    print("✓ Připojeno k SAP")
    print()

    try:
        # 3. Inicializuj analyzer
        analyzer = MaterialAnalyzer(sap)

        # 4. Získej data zásob
        print("Získávám data zásob materiálů (MB52)...")
        print("  (To může trvat několik minut...)")

        stock_data = None
        for mat_type in material_types:
            print(f"  → Zpracovávám typ: {mat_type}")
            df = analyzer.get_materials_stock(plant, mat_type)
            if stock_data is None:
                stock_data = df
            else:
                stock_data = stock_data.append(df, ignore_index=True)

        if stock_data is not None and not stock_data.empty:
            print(f"✓ Získáno {len(stock_data)} materiálů")
        else:
            print("⚠️  Žádná data zásob")

        print()

        # 5. Získej pohyby materiálů
        print("Získávám pohyby materiálů (MB51)...")
        date_from = datetime.now() - timedelta(days=analysis_months * 30)
        date_to = datetime.now()

        movements_data = analyzer.get_material_movements(
            plant=plant,
            material="*",
            date_from=date_from,
            date_to=date_to
        )

        if movements_data is not None and not movements_data.empty:
            print(f"✓ Získáno {len(movements_data)} pohybů")
        else:
            print("⚠️  Žádná data pohybů")
            print("Nelze pokračovat bez dat pohybů")
            return

        print()

        # 6. Analyzuj spotřebu
        print("Analyzuji spotřebu materiálů...")
        consumption_analysis = analyzer.analyze_material_consumption(movements_data)

        if consumption_analysis.empty:
            print("⚠️  Analýza spotřeby selhala")
            return

        print(f"✓ Analyzováno {len(consumption_analysis)} materiálů")
        print()

        # 7. Vyhodnoť Kanban kandidáty
        print("Vyhodnocuji Kanban kandidáty...")
        evaluator = KanbanEvaluator(config['analysis']['kanban_criteria'])

        results = evaluator.evaluate_kanban_candidates(
            consumption_analysis,
            stock_data
        )

        if results.empty:
            print("⚠️  Vyhodnocení selhalo")
            return

        # 8. Vytvoř summary
        summary = evaluator.generate_summary_report(results)

        # 9. Zobraz výsledky
        print()
        print("=" * 60)
        print("VÝSLEDKY ANALÝZY")
        print("=" * 60)
        print()
        print(f"Celkem materiálů analyzováno: {summary['total_materials_analyzed']}")
        print(f"Doporučeno pro Kanban: {summary['total_kanban_candidates']} "
              f"({summary['recommendation_rate']})")
        print(f"Potenciální úspora vyskladnění: {summary['total_potential_savings_movements_per_year']} ročně")
        print(f"Průměrné skóre doporučených: {summary['average_kanban_score']}")
        print()

        # Top 10
        print("TOP 10 KANDIDÁTŮ PRO KANBAN:")
        print("-" * 60)
        for i, candidate in enumerate(summary['top_10_candidates'], 1):
            print(f"{i:2d}. Materiál: {candidate['Material']}")
            print(f"    Skóre: {candidate['Kanban_Score']:.2f}")
            print(f"    Vyskladnění/měsíc: {candidate['Movements_Per_Month']:.1f}")
            print(f"    Pravidelnost: {candidate['Consumption_Regularity']:.0%}")
            print(f"    Úspora: ~{candidate['Potential_Savings_Movements']} vyskladnění/rok")
            print()

        # 10. Export do Excel
        output_file = config['output']['excel_report']
        print(f"Exportuji výsledky do {output_file}...")
        evaluator.export_to_excel(results, summary, output_file)
        print(f"✓ Export dokončen")
        print()

        print("=" * 60)
        print("ANALÝZA DOKONČENA")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Chyba během provádění: {e}", exc_info=True)
        print(f"\n❌ Chyba: {e}")

    finally:
        # Odpoj se od SAP
        sap.disconnect()
        print("\nOdpojeno od SAP")


if __name__ == "__main__":
    main()
