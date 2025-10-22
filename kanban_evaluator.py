"""
Kanban Evaluator Module
Vyhodnocuje, které materiály jsou vhodné kandidáty pro Kanban systém
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class KanbanEvaluator:
    """Třída pro vyhodnocení Kanban kandidátů"""

    def __init__(self, criteria: Dict = None):
        """
        Inicializace evaluátoru

        Args:
            criteria: Dictionary s kritérii pro vyhodnocení
                - min_movements_per_month: Minimální počet vyskladnění za měsíc
                - min_consumption_regularity: Minimální pravidelnost (0-1)
                - max_value_per_piece: Maximální hodnota za kus
                - min_stock_turns: Minimální obrátkovost zásob
        """
        self.criteria = criteria or {
            'min_movements_per_month': 10,
            'min_consumption_regularity': 0.7,
            'max_value_per_piece': 10000,
            'min_stock_turns': 4
        }

    def evaluate_kanban_candidates(self,
                                     consumption_analysis: pd.DataFrame,
                                     stock_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Vyhodnotí Kanban kandidáty na základě spotřeby a zásob

        Args:
            consumption_analysis: DataFrame s analýzou spotřeby
            stock_data: DataFrame se zásobami (optional)

        Returns:
            DataFrame s vyhodnocením a skóre
        """
        if consumption_analysis.empty:
            logger.warning("Prázdná data pro vyhodnocení")
            return pd.DataFrame()

        df = consumption_analysis.copy()

        # Inicializuj skóre
        df['Kanban_Score'] = 0.0
        df['Kanban_Recommended'] = False
        df['Recommendation_Reasons'] = ''
        df['Potential_Savings_Movements'] = 0

        try:
            # 1. Vyhodnoť četnost vyskladnění
            freq_score = self._evaluate_frequency(df)
            df['Frequency_Score'] = freq_score

            # 2. Vyhodnoť pravidelnost
            regularity_score = self._evaluate_regularity(df)
            df['Regularity_Score'] = regularity_score

            # 3. Pokud máme data zásob, vyhodnoť hodnotu a obrátkovost
            if stock_data is not None and not stock_data.empty:
                value_score = self._evaluate_value(df, stock_data)
                turnover_score = self._evaluate_turnover(df, stock_data)
                df['Value_Score'] = value_score
                df['Turnover_Score'] = turnover_score

                # Celkové skóre s váhami
                df['Kanban_Score'] = (
                        freq_score * 0.3 +
                        regularity_score * 0.3 +
                        value_score * 0.2 +
                        turnover_score * 0.2
                )
            else:
                # Pouze frekvence a pravidelnost
                df['Kanban_Score'] = (
                        freq_score * 0.5 +
                        regularity_score * 0.5
                )

            # 4. Urči doporučení (skóre > 0.6)
            df['Kanban_Recommended'] = df['Kanban_Score'] > 0.6

            # 5. Vypočti potenciální úspory
            df['Potential_Savings_Movements'] = self._calculate_savings(df)

            # 6. Generuj důvody doporučení
            df['Recommendation_Reasons'] = df.apply(
                lambda row: self._generate_reasons(row), axis=1
            )

            # Seřaď podle skóre
            df = df.sort_values('Kanban_Score', ascending=False)

            logger.info(
                f"Vyhodnoceno {len(df)} materiálů, "
                f"{df['Kanban_Recommended'].sum()} doporučeno pro Kanban"
            )

            return df

        except Exception as e:
            logger.error(f"Chyba při vyhodnocování: {e}")
            return df

    def _evaluate_frequency(self, df: pd.DataFrame) -> pd.Series:
        """
        Vyhodnotí četnost vyskladnění

        Returns:
            Series se skóre 0-1
        """
        try:
            movements = df['Movements_Per_Month'].fillna(0)
            min_threshold = self.criteria['min_movements_per_month']

            # Normalizuj skóre (sigmoid funkce)
            score = 1 / (1 + np.exp(-(movements - min_threshold) / 5))

            return score

        except Exception as e:
            logger.error(f"Chyba při vyhodnocování frekvence: {e}")
            return pd.Series(0, index=df.index)

    def _evaluate_regularity(self, df: pd.DataFrame) -> pd.Series:
        """
        Vyhodnotí pravidelnost spotřeby

        Returns:
            Series se skóre 0-1
        """
        try:
            regularity = df['Consumption_Regularity'].fillna(0)
            min_threshold = self.criteria['min_consumption_regularity']

            # Skóre podle dosažení prahu
            score = (regularity / min_threshold).clip(0, 1)

            return score

        except Exception as e:
            logger.error(f"Chyba při vyhodnocování pravidelnosti: {e}")
            return pd.Series(0, index=df.index)

    def _evaluate_value(self, df: pd.DataFrame, stock_data: pd.DataFrame) -> pd.Series:
        """
        Vyhodnotí hodnotu materiálu (levnější = lepší pro Kanban)

        Returns:
            Series se skóre 0-1
        """
        try:
            # Merge s data zásob
            merged = df.merge(
                stock_data[['Material', 'Value per Unit']],
                on='Material',
                how='left'
            )

            value = merged['Value per Unit'].fillna(0)
            max_threshold = self.criteria['max_value_per_piece']

            # Inverze - levnější materiály = vyšší skóre
            score = 1 - (value / max_threshold).clip(0, 1)

            return score

        except Exception as e:
            logger.error(f"Chyba při vyhodnocování hodnoty: {e}")
            return pd.Series(0.5, index=df.index)

    def _evaluate_turnover(self, df: pd.DataFrame, stock_data: pd.DataFrame) -> pd.Series:
        """
        Vyhodnotí obrátkovost zásob

        Returns:
            Series se skóre 0-1
        """
        try:
            # Obrátkovost = roční spotřeba / průměrná zásoba
            # To by vyžadovalo propojení dat, zatím zjednodušená verze

            # Vysoká frekvence pohybů = vysoká obrátkovost
            movements = df['Movements_Per_Month'].fillna(0)
            min_threshold = self.criteria['min_stock_turns']

            # Odhadni obrátkovost z frekvence
            estimated_turns = movements * 12 / 52  # Přibližný odhad

            score = (estimated_turns / min_threshold).clip(0, 1)

            return score

        except Exception as e:
            logger.error(f"Chyba při vyhodnocování obrátkovosti: {e}")
            return pd.Series(0.5, index=df.index)

    def _calculate_savings(self, df: pd.DataFrame) -> pd.Series:
        """
        Vypočítá potenciální úspory vyskladnění

        Args:
            df: DataFrame s materiály

        Returns:
            Series s odhady úspor
        """
        try:
            # Kanban typicky redukuje vyskladnění o 60-80%
            # protože probíhá doplňování automaticky
            reduction_factor = 0.7

            monthly_movements = df['Movements_Per_Month'].fillna(0)
            yearly_movements = monthly_movements * 12

            # Pokud je materiál vhodný pro Kanban
            is_recommended = df['Kanban_Score'] > 0.6

            savings = yearly_movements * reduction_factor * is_recommended

            return savings.round(0).astype(int)

        except Exception as e:
            logger.error(f"Chyba při výpočtu úspor: {e}")
            return pd.Series(0, index=df.index)

    def _generate_reasons(self, row: pd.Series) -> str:
        """
        Generuje textové důvody pro doporučení

        Args:
            row: Řádek DataFrame s materiálem

        Returns:
            String s důvody
        """
        reasons = []

        try:
            if row['Kanban_Score'] <= 0.6:
                return "Nevhodný pro Kanban"

            # Vysoká frekvence
            if row.get('Frequency_Score', 0) > 0.7:
                movements = row.get('Movements_Per_Month', 0)
                reasons.append(f"Vysoká frekvence vyskladnění ({movements:.1f}/měsíc)")

            # Pravidelná spotřeba
            if row.get('Regularity_Score', 0) > 0.7:
                regularity = row.get('Consumption_Regularity', 0)
                reasons.append(f"Pravidelná spotřeba ({regularity:.0%})")

            # Nízká hodnota
            if row.get('Value_Score', 0) > 0.7:
                reasons.append("Nízká hodnota - vhodné pro Kanban")

            # Vysoká obrátkovost
            if row.get('Turnover_Score', 0) > 0.7:
                reasons.append("Vysoká obrátkovost")

            # Úspory
            savings = row.get('Potential_Savings_Movements', 0)
            if savings > 0:
                reasons.append(f"Ušetří ~{savings} vyskladnění ročně")

            return " | ".join(reasons) if reasons else "Splňuje základní kritéria"

        except Exception as e:
            logger.error(f"Chyba při generování důvodů: {e}")
            return ""

    def generate_summary_report(self, results: pd.DataFrame) -> Dict:
        """
        Vytvoří souhrnný report z výsledků

        Args:
            results: DataFrame s vyhodnocením

        Returns:
            Dictionary se statistikami
        """
        if results.empty:
            return {}

        try:
            total_materials = len(results)
            recommended = results[results['Kanban_Recommended'] == True]
            total_recommended = len(recommended)

            total_savings = recommended['Potential_Savings_Movements'].sum()
            avg_score = recommended['Kanban_Score'].mean()

            # Top 10 kandidátů
            top_10 = recommended.nlargest(10, 'Kanban_Score')[[
                'Material', 'Kanban_Score', 'Movements_Per_Month',
                'Consumption_Regularity', 'Potential_Savings_Movements'
            ]]

            summary = {
                'total_materials_analyzed': total_materials,
                'total_kanban_candidates': total_recommended,
                'recommendation_rate': f"{total_recommended / total_materials * 100:.1f}%",
                'total_potential_savings_movements_per_year': int(total_savings),
                'average_kanban_score': f"{avg_score:.2f}",
                'top_10_candidates': top_10.to_dict('records')
            }

            logger.info(f"Summary report generován: {total_recommended} kandidátů")

            return summary

        except Exception as e:
            logger.error(f"Chyba při generování summary: {e}")
            return {}

    def export_to_excel(self, results: pd.DataFrame, summary: Dict,
                        filename: str = "kanban_analysis.xlsx"):
        """
        Exportuje výsledky do Excel souboru

        Args:
            results: DataFrame s výsledky
            summary: Dictionary se summary
            filename: Název výstupního souboru
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Sheet 1: Všechny výsledky
                results.to_excel(writer, sheet_name='All Materials', index=False)

                # Sheet 2: Jen doporučené
                recommended = results[results['Kanban_Recommended'] == True]
                recommended.to_excel(writer, sheet_name='Recommended for Kanban', index=False)

                # Sheet 3: Summary
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Sheet 4: Top candidates
                if 'top_10_candidates' in summary:
                    top_df = pd.DataFrame(summary['top_10_candidates'])
                    top_df.to_excel(writer, sheet_name='Top 10 Candidates', index=False)

            logger.info(f"Export do {filename} dokončen")

        except Exception as e:
            logger.error(f"Chyba při exportu do Excel: {e}")
