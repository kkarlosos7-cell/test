"""
Material Data Analyzer Module
Modul pro získávání a analýzu dat o materiálech ze SAP
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sap_connection import SAPConnection
import time

logger = logging.getLogger(__name__)


class MaterialAnalyzer:
    """Třída pro analýzu materiálových dat ze SAP"""

    def __init__(self, sap_connection: SAPConnection):
        self.sap = sap_connection

    def get_materials_stock(self, plant: str, material_type: str = "ROH") -> pd.DataFrame:
        """
        Získá přehled zásob materiálů pomocí MB52

        Args:
            plant: Werk (např. "STD1")
            material_type: Typ materiálu (např. "ROH" pro raw materials)

        Returns:
            DataFrame s daty o zásobách
        """
        logger.info(f"Získávám data zásob pro werk {plant}, typ {material_type}")

        try:
            # Spusť transakci MB52
            if not self.sap.start_transaction("MB52"):
                raise Exception("Nelze spustit transakci MB52")

            # Vyplň selection screen
            # Werk
            self.sap.set_field("wnd[0]/usr/ctxtWERKS-LOW", plant)

            # Typ materiálu
            self.sap.set_field("wnd[0]/usr/ctxtMATART-LOW", material_type)

            # Layout - můžeš si nastavit vlastní layout
            # self.sap.set_field("wnd[0]/usr/ctxtPD_VT", "TVOJ_LAYOUT")

            # Spusť report (F8)
            self.sap.send_vkey(8)
            time.sleep(3)  # Počkej na načtení dat

            # Zkontroluj, zda jsou data
            try:
                status_bar = self.sap.get_field("wnd[0]/sbar")
                if "No data" in status_bar or "Žádná data" in status_bar:
                    logger.warning("Žádná data nalezena")
                    return pd.DataFrame()
            except:
                pass

            # Exportuj data do clipboardu pomocí Local File
            # Klikni na Export (Ctrl+Shift+F9) nebo přes menu
            try:
                # Zkus najít grid
                grid_id = "wnd[0]/usr/cntlGRID1/shellcont/shell"
                data = self._export_grid_to_dataframe(grid_id)

                # Ukončí transakci
                self.sap.send_vkey(3)  # F3 = Back
                self.sap.send_vkey(3)

                return data

            except Exception as e:
                logger.error(f"Chyba při exportu dat: {e}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Chyba při získávání zásob: {e}")
            return pd.DataFrame()

    def get_material_movements(self, plant: str, material: str = "*",
                                date_from: datetime = None,
                                date_to: datetime = None) -> pd.DataFrame:
        """
        Získá pohyby materiálu pomocí MB51

        Args:
            plant: Werk
            material: Číslo materiálu (* pro všechny)
            date_from: Datum od
            date_to: Datum do

        Returns:
            DataFrame s pohyby materiálu
        """
        if date_from is None:
            date_from = datetime.now() - timedelta(days=180)  # 6 měsíců
        if date_to is None:
            date_to = datetime.now()

        logger.info(f"Získávám pohyby pro werk {plant}, období {date_from.date()} - {date_to.date()}")

        try:
            # Spusť MB51
            if not self.sap.start_transaction("MB51"):
                raise Exception("Nelze spustit transakci MB51")

            # Vyplň selection screen
            self.sap.set_field("wnd[0]/usr/ctxtWERKS-LOW", plant)
            self.sap.set_field("wnd[0]/usr/ctxtMATNR-LOW", material)
            self.sap.set_field("wnd[0]/usr/ctxtBUDAT-LOW", date_from.strftime("%d.%m.%Y"))
            self.sap.set_field("wnd[0]/usr/ctxtBUDAT-HIGH", date_to.strftime("%d.%m.%Y"))

            # Můžeš filtrovat jen výdejky (movement type 261, 281, etc.)
            # self.sap.set_field("wnd[0]/usr/ctxtBWART-LOW", "261")

            # Spusť report
            self.sap.send_vkey(8)
            time.sleep(3)

            # Exportuj data
            try:
                grid_id = "wnd[0]/usr/cntlGRID1/shellcont/shell"
                data = self._export_grid_to_dataframe(grid_id)

                # Back
                self.sap.send_vkey(3)
                self.sap.send_vkey(3)

                return data

            except Exception as e:
                logger.error(f"Chyba při exportu pohybů: {e}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Chyba při získávání pohybů: {e}")
            return pd.DataFrame()

    def _export_grid_to_dataframe(self, grid_id: str) -> pd.DataFrame:
        """
        Exportuje data z SAP Grid do DataFrame

        Args:
            grid_id: ID grid controlu

        Returns:
            DataFrame s daty
        """
        try:
            grid = self.sap.session.findById(grid_id)
            row_count = grid.RowCount

            if row_count == 0:
                logger.warning("Grid neobsahuje žádná data")
                return pd.DataFrame()

            # Získej názvy sloupců
            col_order = grid.ColumnOrder
            columns = []
            for col_id in col_order:
                col_title = grid.GetColumnTitles(col_id)
                if isinstance(col_title, tuple):
                    col_title = col_title[0]
                columns.append(col_title if col_title else col_id)

            # Získej data řádek po řádku
            data = []
            for row in range(row_count):
                row_data = []
                for col_id in col_order:
                    try:
                        cell_value = grid.GetCellValue(row, col_id)
                        row_data.append(cell_value)
                    except:
                        row_data.append("")
                data.append(row_data)

            df = pd.DataFrame(data, columns=columns)
            logger.info(f"Exportováno {len(df)} řádků, {len(columns)} sloupců")

            return df

        except Exception as e:
            logger.error(f"Chyba při exportu gridu: {e}")
            # Fallback - zkus alternativní metodu přes clipboard
            return self._export_via_clipboard()

    def _export_via_clipboard(self) -> pd.DataFrame:
        """
        Alternativní metoda exportu přes clipboard

        Returns:
            DataFrame s daty
        """
        try:
            # Vyber všechna data (Ctrl+A)
            self.sap.session.findById("wnd[0]").sendVKey(16)  # Ctrl+Y = Select all

            # Kopíruj (Ctrl+C)
            self.sap.session.findById("wnd[0]").sendVKey(17)  # Ctrl+C

            time.sleep(1)

            # Načti z clipboardu
            import win32clipboard
            win32clipboard.OpenClipboard()
            clipboard_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            # Parsuj data
            from io import StringIO
            df = pd.read_csv(StringIO(clipboard_data), sep='\t')

            logger.info(f"Export přes clipboard úspěšný: {len(df)} řádků")
            return df

        except Exception as e:
            logger.error(f"Chyba při exportu přes clipboard: {e}")
            return pd.DataFrame()

    def analyze_material_consumption(self, movements_df: pd.DataFrame,
                                      material_column: str = "Material",
                                      quantity_column: str = "Quantity",
                                      date_column: str = "Posting Date",
                                      movement_type_column: str = "Movement Type") -> pd.DataFrame:
        """
        Analyzuje spotřebu materiálů z dat pohybů

        Args:
            movements_df: DataFrame s pohyby
            material_column: Název sloupce s materiálem
            quantity_column: Název sloupce s množstvím
            date_column: Název sloupce s datem
            movement_type_column: Název sloupce s typem pohybu

        Returns:
            DataFrame se statistikami spotřeby
        """
        if movements_df.empty:
            logger.warning("Prázdná data pohybů")
            return pd.DataFrame()

        try:
            # Filtruj jen výdejky (předpokládáme movement types 261, 281, etc.)
            # Tohle budeš muset upravit podle svých movement types
            issue_types = ['261', '281', '201', '221']  # Typické výdejky

            df = movements_df.copy()

            # Pokud máš sloupec movement type, filtruj
            if movement_type_column in df.columns:
                df = df[df[movement_type_column].astype(str).isin(issue_types)]

            if df.empty:
                logger.warning("Žádné výdejky po filtrování")
                return pd.DataFrame()

            # Převeď datum na datetime
            if date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

            # Převeď množství na číslo
            if quantity_column in df.columns:
                df[quantity_column] = pd.to_numeric(df[quantity_column], errors='coerce')

            # Agreguj podle materiálu
            analysis = df.groupby(material_column).agg({
                quantity_column: ['sum', 'count', 'mean', 'std'],
                date_column: ['min', 'max']
            }).reset_index()

            analysis.columns = [
                'Material',
                'Total_Quantity',
                'Movement_Count',
                'Avg_Quantity',
                'Std_Quantity',
                'First_Movement',
                'Last_Movement'
            ]

            # Vypočti další metriky
            analysis['Days_Active'] = (
                    analysis['Last_Movement'] - analysis['First_Movement']
            ).dt.days

            analysis['Movements_Per_Month'] = (
                    analysis['Movement_Count'] / (analysis['Days_Active'] / 30)
            )

            # Pravidelnost spotřeby (nižší std = pravidelnější)
            analysis['Consumption_Regularity'] = 1 - (
                    analysis['Std_Quantity'] / analysis['Avg_Quantity']
            ).clip(0, 1)

            logger.info(f"Analýza spotřeby hotova pro {len(analysis)} materiálů")

            return analysis

        except Exception as e:
            logger.error(f"Chyba při analýze spotřeby: {e}")
            return pd.DataFrame()
