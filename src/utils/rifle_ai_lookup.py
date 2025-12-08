"""
AI-assisted Rifle Specification Lookup
Henter rifle-spesifikasjoner fra produsentens nettsider
"""

import logging
import re
from typing import Any, Dict, Optional

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
from HjemmeladingApp.utils.safe_logger import append_exception


class RifleAILookup:
    """AI-assistert rifle-søk"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Kjente rifle-produsenter og deres nettsider
        self.manufacturers = {
            "tikka": {
                "name": "Tikka",
                "urls": ["https://www.tikka.fi", "https://www.beretta.com/en-us/tikka"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                    "action": r"(bolt\s*action|semi-?auto)",
                },
            },
            "sako": {
                "name": "Sako",
                "urls": ["https://www.sako.fi", "https://www.beretta.com/en-us/sako"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "bergara": {
                "name": "Bergara",
                "urls": ["https://www.bergarausa.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "remington": {
                "name": "Remington",
                "urls": ["https://www.remarms.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "ruger": {
                "name": "Ruger",
                "urls": ["https://www.ruger.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "savage": {
                "name": "Savage Arms",
                "urls": ["https://www.savagearms.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "weatherby": {
                "name": "Weatherby",
                "urls": ["https://www.weatherby.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
            "browning": {
                "name": "Browning",
                "urls": ["https://www.browning.com"],
                "patterns": {
                    "barrel_length": r'barrel.*?(\d+\.?\d*)\s*(?:inch|")',
                    "twist_rate": r"twist.*?1[:\s](\d+)",
                },
            },
        }

    def lookup_rifle(
        self, rifle_name: str, manufacturer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Søker etter rifle-spesifikasjoner

        Args:
            rifle_name: Navn på rifle (f.eks. "Tikka T3X Hunter")
            manufacturer: Produsent (valgfritt, auto-detekteres hvis ikke oppgitt)

        Returns:
            Dictionary med rifle-data (kan være delvis fylt)
        """
        result: Dict[str, Any] = {
            "name": rifle_name,
            "manufacturer": manufacturer or "",
            "caliber": "",
            "barrel_length": None,
            "twist_rate": "",
            "action_type": "Bolt Action",  # Default
            "notes": "",
            "confidence": "low",
            "sources": [],
        }

        # Auto-detect manufacturer fra rifle-navn
        if not manufacturer:
            manufacturer = self._detect_manufacturer(rifle_name)
            if manufacturer:
                result["manufacturer"] = manufacturer

        # Hvis vi ikke finner produsent, bruk generisk søk
        if not manufacturer:
            return self._generic_search(rifle_name, result)

        # Søk på produsent-spesifikke nettsider
        mfg_key = manufacturer.lower()
        if mfg_key in self.manufacturers:
            return self._manufacturer_search(rifle_name, mfg_key, result)

        return result

    def _detect_manufacturer(self, rifle_name: str) -> Optional[str]:
        """Detekterer produsent fra rifle-navn"""
        rifle_lower = rifle_name.lower()

        for key, data in self.manufacturers.items():
            if key in rifle_lower or data["name"].lower() in rifle_lower:
                return data["name"]

        return None

    def _manufacturer_search(self, rifle_name: str, mfg_key: str, result: Dict) -> Dict:
        """Søker på produsent-spesifikke nettsider"""
        mfg_data = self.manufacturers[mfg_key]

        try:
            # Forsøk å finne produktside
            search_query = rifle_name.replace(mfg_data["name"], "").strip()

            # Gjett common URLs
            common_paths = [
                f"/products/{search_query.lower().replace(' ', '-')}",
                f"/rifles/{search_query.lower().replace(' ', '-')}",
                f"/firearms/{search_query.lower().replace(' ', '-')}",
            ]

            for base_url in mfg_data["urls"]:
                for path in common_paths:
                    try:
                        url = base_url + path
                        response = requests.get(url, headers=self.headers, timeout=5)

                        if response.status_code == 200:
                            result = self._parse_page(
                                response.text, mfg_data["patterns"], result
                            )
                            result["sources"].append(url)
                            result["confidence"] = "medium"
                            return result
                    except Exception as e:
                        logger.debug(
                            "AI lookup request failed for %s: %s", url, e, exc_info=True
                        )
                        try:
                            append_exception(f"AI lookup request failed for {url}", e)
                        except Exception:
                            pass
                        continue

        except Exception as e:
            result["notes"] += f"\nAI Lookup feilet: {str(e)}"

        # Hvis vi ikke fant noe, fyll ut defaults basert på rifle-navn
        result = self._extract_from_name(rifle_name, result)

        return result

    def _generic_search(self, rifle_name: str, result: Dict) -> Dict:
        """Generisk søk når produsent er ukjent"""

        # Ekstraher info fra navnet
        result = self._extract_from_name(rifle_name, result)

        result[
            "notes"
        ] += "\n🤖 AI kunne ikke finne spesifikk produktside. Data ekstrahert fra navn."
        result["confidence"] = "low"

        return result

    def _extract_from_name(self, rifle_name: str, result: Dict) -> Dict:
        """Ekstraherer info direkte fra rifle-navnet"""

        # Kaliber (common patterns)
        caliber_patterns = [
            r"\.(\d{3})",  # .308, .223, etc.
            r"(\d+mm)",  # 6.5mm, 7mm, etc.
            r"(6\.5\s*creedmoor)",
            r"(\.308\s*win)",
            r"(\.223\s*rem)",
            r"(\.30-06)",
            r"(\.300\s*win\s*mag)",
            r"(6\.5x55)",
            r"(7x64)",
        ]

        for pattern in caliber_patterns:
            match = re.search(pattern, rifle_name, re.IGNORECASE)
            if match:
                result["caliber"] = match.group(1)
                break

        # Barrel length (hvis nevnt i navnet)
        barrel_match = re.search(r'(\d+\.?\d*)\s*(?:inch|")', rifle_name, re.IGNORECASE)
        if barrel_match:
            result["barrel_length"] = float(barrel_match.group(1))

        # Action type
        if re.search(r"semi-?auto|ar-?15|ar-?10", rifle_name, re.IGNORECASE):
            result["action_type"] = "Semi-Auto"
        elif re.search(r"lever", rifle_name, re.IGNORECASE):
            result["action_type"] = "Lever Action"
        elif re.search(r"single\s*shot|break\s*action", rifle_name, re.IGNORECASE):
            result["action_type"] = "Single Shot"
        else:
            result["action_type"] = "Bolt Action"  # Most common

        return result

    def _parse_page(self, html: str, patterns: Dict, result: Dict) -> Dict:
        """Parser HTML-side for å finne spesifikasjoner"""
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().lower()

        # Barrel length
        if "barrel_length" in patterns:
            match = re.search(patterns["barrel_length"], text, re.IGNORECASE)
            if match:
                result["barrel_length"] = float(match.group(1))

        # Twist rate
        if "twist_rate" in patterns:
            match = re.search(patterns["twist_rate"], text, re.IGNORECASE)
            if match:
                result["twist_rate"] = f"1:{match.group(1)}"

        # Action type
        if "action" in patterns:
            match = re.search(patterns["action"], text, re.IGNORECASE)
            if match:
                action = match.group(1).strip()
                if "semi" in action:
                    result["action_type"] = "Semi-Auto"
                elif "bolt" in action:
                    result["action_type"] = "Bolt Action"

        return result

    def get_common_calibers(self) -> list:
        """Returnerer liste over vanlige kalibere"""
        return [
            ".223 Rem",
            ".308 Win",
            "6.5 Creedmoor",
            "6.5x55 SE",
            "7x64",
            ".30-06",
            ".300 Win Mag",
            "7mm Rem Mag",
            ".338 Lapua Mag",
            "6mm Creedmoor",
            "6.5 PRC",
            ".243 Win",
            ".270 Win",
            "7mm-08 Rem",
            ".300 PRC",
        ]

    def get_common_twist_rates(self, caliber: str) -> list:
        """Returnerer vanlige twist rates for en kaliber"""
        twist_map = {
            ".223": ["1:7", "1:8", "1:9", "1:12"],
            ".308": ["1:10", "1:11", "1:12"],
            "6.5": ["1:7", "1:8", "1:8.5"],
            "7mm": ["1:8", "1:9", "1:9.5"],
            ".30": ["1:10", "1:11"],
            ".338": ["1:9", "1:9.3", "1:10"],
        }

        for key, rates in twist_map.items():
            if key in caliber:
                return rates

        return ["1:8", "1:9", "1:10", "1:11", "1:12"]


def get_rifle_lookup_service() -> RifleAILookup:
    """Returnerer singleton instance"""
    return RifleAILookup()
