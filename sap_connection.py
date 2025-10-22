"""
SAP GUI Scripting Connection Module
Zajišťuje připojení k SAP GUI a základní operace
"""

import win32com.client
import time
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SAPConnection:
    """Třída pro správu připojení k SAP GUI"""

    def __init__(self):
        self.sap_gui_auto = None
        self.application = None
        self.connection = None
        self.session = None

    def connect(self, system_id: str = None, client: str = None,
                user: str = None, password: str = None, language: str = "CS") -> bool:
        """
        Připojí se k SAP GUI

        Args:
            system_id: ID SAP systému
            client: Mandant
            user: Uživatelské jméno
            password: Heslo
            language: Jazyk (default: CS)

        Returns:
            bool: True pokud úspěšné připojení
        """
        try:
            # Získání SAP GUI Scripting objektu
            self.sap_gui_auto = win32com.client.GetObject("SAPGUI")
            if not self.sap_gui_auto:
                raise Exception("SAP GUI není spuštěná")

            self.application = self.sap_gui_auto.GetScriptingEngine

            # Pokusíme se připojit k existující session
            if self.application.Connections.Count > 0:
                self.connection = self.application.Connections(0)
                if self.connection.Sessions.Count > 0:
                    self.session = self.connection.Sessions(0)
                    logger.info("Připojeno k existující SAP session")
                    return True

            logger.warning("Není nalezena existující session. Připoj se manuálně k SAP.")
            return False

        except Exception as e:
            logger.error(f"Chyba při připojování k SAP: {e}")
            return False

    def is_connected(self) -> bool:
        """Zkontroluje, zda je připojení aktivní"""
        try:
            if self.session:
                # Pokus o základní operaci
                _ = self.session.Info.SystemName
                return True
        except:
            return False
        return False

    def start_transaction(self, tcode: str) -> bool:
        """
        Spustí transakci v SAP

        Args:
            tcode: Transaction code

        Returns:
            bool: True pokud úspěšné
        """
        try:
            if not self.is_connected():
                logger.error("Nejsi připojen k SAP")
                return False

            self.session.StartTransaction(tcode)
            time.sleep(1)  # Počkej na načtení
            logger.info(f"Spuštěna transakce: {tcode}")
            return True

        except Exception as e:
            logger.error(f"Chyba při spouštění transakce {tcode}: {e}")
            return False

    def end_transaction(self) -> bool:
        """Ukončí aktuální transakci"""
        try:
            self.session.EndTransaction()
            return True
        except Exception as e:
            logger.error(f"Chyba při ukončování transakce: {e}")
            return False

    def send_vkey(self, key_code: int):
        """
        Pošle virtuální klíč (F-klávesy)

        Args:
            key_code: Kód klávesy (0=Enter, 3=F3, 8=F8, etc.)
        """
        try:
            self.session.findById("wnd[0]").sendVKey(key_code)
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Chyba při posílání vkey {key_code}: {e}")

    def set_field(self, field_id: str, value: Any):
        """
        Nastaví hodnotu pole v SAP

        Args:
            field_id: ID pole (např. "wnd[0]/usr/ctxtMATNR-LOW")
            value: Hodnota k nastavení
        """
        try:
            self.session.findById(field_id).text = str(value)
        except Exception as e:
            logger.error(f"Chyba při nastavování pole {field_id}: {e}")
            raise

    def get_field(self, field_id: str) -> str:
        """
        Získá hodnotu pole ze SAP

        Args:
            field_id: ID pole

        Returns:
            str: Hodnota pole
        """
        try:
            return self.session.findById(field_id).text
        except Exception as e:
            logger.error(f"Chyba při čtení pole {field_id}: {e}")
            return ""

    def press_button(self, button_id: str):
        """
        Stiskne tlačítko v SAP

        Args:
            button_id: ID tlačítka
        """
        try:
            self.session.findById(button_id).press()
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Chyba při stisknutí tlačítka {button_id}: {e}")

    def disconnect(self):
        """Odpojí se od SAP"""
        try:
            if self.session:
                self.session = None
            if self.connection:
                self.connection = None
            logger.info("Odpojeno od SAP")
        except Exception as e:
            logger.error(f"Chyba při odpojování: {e}")

    def get_grid_data(self, grid_id: str = "wnd[0]/usr/cntlGRID1/shellcont/shell") -> list:
        """
        Extrahuje data z grid controlu (ALV)

        Args:
            grid_id: ID grid controlu

        Returns:
            list: Seznam řádků jako dictionary
        """
        try:
            grid = self.session.findById(grid_id)
            row_count = grid.RowCount
            col_count = grid.ColumnCount

            # Získej názvy sloupců
            columns = []
            for col in range(col_count):
                col_name = grid.GetColumnNames(col)
                columns.append(col_name)

            # Získej data
            data = []
            for row in range(row_count):
                row_data = {}
                for col in range(col_count):
                    cell_value = grid.GetCellValue(row, columns[col])
                    row_data[columns[col]] = cell_value
                data.append(row_data)

            logger.info(f"Extrahováno {len(data)} řádků z gridu")
            return data

        except Exception as e:
            logger.error(f"Chyba při extrakci dat z gridu: {e}")
            return []
