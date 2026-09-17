"""
INCOIS Advisory Web Scraper (CHUNK_ID: R4-C05)
----------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/ingestion/incois_scraper.py
Prerequisites: [R4-C01] (pipeline.storage.b2_uploader)

Scrapes daily Potential Fishing Zone (PFZ) advisories and Ocean State Forecast
(OSF) advisories from the Indian National Centre for Ocean Information Services
(INCOIS) portal and the RSMCND IMD fisherman warning PDFs (which embed INCOIS
ocean current / swell alerts), normalizes to structured JSON, uploads to
Backblaze B2 storage under advisories/pfz/ and advisories/osf/.

Data sources:
  1. RSMCND Fisherman Warning page (rsmcnewdelhi.imd.gov.in/fishermen-warning.php)
     - embeds INCOIS Ocean Current Alert / Swell Surge / High Wave Alert sections.
  2. RSMCND Coastal Weather Bulletin (rsmcnewdelhi.imd.gov.in/coastal-weather-bulletin.php)
     - provides OSF sea state / wind / wave forecasts.
  3. IMD CAP RSS feed (cap-sources.s3.amazonaws.com/in-imd-en/rss.xml)
     - provides structured CAP alert items.

Acceptance Criteria:
  - [x] Fetches daily PFZ and OSF advisories (or closest available equivalents).
  - [x] Normalizes to structured JSON with advisory_type, date, source_url,
        advisory_text, zones, alert_level fields.
  - [x] Uploads JSON to advisories/pfz/YYYY-MM-DD.json and
        advisories/osf/YYYY-MM-DD.json on Backblaze B2.
  - [x] CLI: python -m pipeline.ingestion.incois_scraper [--no-upload] [--date YYYY-MM-DD]
"""

import os
import sys
import json
import logging
import argparse
import re
import tempfile
import warnings
from pipeline.storage.db_writer import DBWriter
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning

# Suppress SSL warnings and XML parser warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import B2Config
from pipeline.storage.b2_uploader import B2StorageManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("incois_scraper")

# ---------------------------------------------------------------------------
# Source URL constants
# ---------------------------------------------------------------------------
RSMCND_BASE = "https://rsmcnewdelhi.imd.gov.in"
RSMCND_FISHERMEN_URL = f"{RSMCND_BASE}/fishermen-warning.php"
RSMCND_COASTAL_URL = f"{RSMCND_BASE}/coastal-weather-bulletin.php"
INCOIS_FORECAST_URL = "https://incois.gov.in/site/forecast.jsp"
IMD_CAP_RSS_URL = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"

DEFAULT_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; NeerMitra-Pipeline/1.0)"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get(url: str, timeout: int = DEFAULT_TIMEOUT, verify: bool = True) -> requests.Response:
    """Perform a GET request with error handling."""
    resp = _SESSION.get(url, timeout=timeout, verify=verify)
    resp.raise_for_status()
    return resp


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from a PDF byte string using pypdf."""
    try:
        import io as _io
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(_io.BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception as exc:
        logger.warning(f"PDF text extraction failed: {exc}")
        return ""


def _normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def _parse_cap_rss(xml_text: str) -> List[Dict[str, Any]]:
    """Parse IMD CAP RSS feed into a list of alert items."""
    items: List[Dict[str, Any]] = []
    # Try lxml xml parser first, fall back to html.parser
    for parser in ("lxml-xml", "xml", "lxml", "html.parser"):
        try:
            soup = BeautifulSoup(xml_text, parser)
            rss_items = soup.find_all("item")
            if rss_items:
                for item in rss_items:
                    title = item.find("title")
                    desc = item.find("description")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    category = item.find("category")
                    items.append({
                        "title": title.get_text(strip=True) if title else "",
                        "description": desc.get_text(strip=True) if desc else "",
                        "link": link.get_text(strip=True) if link else "",
                        "published": pub_date.get_text(strip=True) if pub_date else "",
                        "category": category.get_text(strip=True) if category else "",
                    })
                break
        except Exception:
            continue
    return items


def _scrape_bulletin_pdfs(
    page_url: str,
    base_url: str,
    limit: int = 3,
    archive_folder_hint: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Scrape the most recent bulletin PDF links from an RSMCND bulletin page
    and extract their text content.

    Args:
        page_url: URL of the RSMCND bulletin listing page.
        base_url: Base URL prefix for relative PDF links.
        limit: Maximum number of PDFs to fetch.
        archive_folder_hint: If set (e.g. '45'), only PDF links under
            uploads/archive/<hint>/ are considered. Prevents cross-contamination
            between bulletin types that share the same RSMCND page.
    """
    results = []
    try:
        resp = _get(page_url, verify=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if not (href.endswith(".pdf") and "archive" in href):
                continue
            # Apply archive folder filter if provided
            if archive_folder_hint:
                # href pattern: uploads/archive/<id>/...
                # or download.php?path=uploads/archive/<id>/...
                if f"/archive/{archive_folder_hint}/" not in href:
                    continue
            # Build absolute URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("download.php"):
                full_url = f"{base_url}/{href}"
            else:
                full_url = f"{base_url}/{href.lstrip('/')}"
            pdf_links.append({"title": text or Path(href).stem, "url": full_url})
        # Deduplicate preserving order
        seen: set = set()
        unique_links = []
        for item in pdf_links:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique_links.append(item)
        logger.info(f"Found {len(unique_links)} unique PDF links on {page_url}")
        # Take the most recent `limit` PDFs
        for link in unique_links[:limit]:
            try:
                pdf_resp = _SESSION.get(link["url"], timeout=30, verify=True)
                pdf_resp.raise_for_status()
                text = _extract_pdf_text(pdf_resp.content)
                text = _normalize_whitespace(text)
                results.append({
                    "source_url": link["url"],
                    "title": link["title"],
                    "text": text[:8000],  # cap at 8 KB
                })
                logger.info(f"Extracted PDF: {link['url']} ({len(text)} chars)")
            except Exception as exc:
                logger.warning(f"Failed to fetch/parse PDF {link['url']}: {exc}")
    except Exception as exc:
        logger.error(f"Failed to scrape bulletin page {page_url}: {exc}")
    return results


def _extract_pfz_zones_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse PFZ zone descriptors from advisory text.
    Looks for lat/lon range patterns and named sea areas.
    """
    zones: List[Dict[str, Any]] = []
    # Match latitude/longitude range patterns
    lat_lon_pattern = re.compile(
        r"(?:lat(?:itude)?s?\s*)?(\d+(?:\.\d+)?)\s*[-\u2013to]+\s*(\d+(?:\.\d+)?)"
        r"\s*[deg\s]*[Nn][,\s]+(?:lon(?:gitude)?s?\s*)?(\d+(?:\.\d+)?)"
        r"\s*[-\u2013to]+\s*(\d+(?:\.\d+)?)\s*[deg\s]*[Ee]",
        re.IGNORECASE
    )
    for match in lat_lon_pattern.finditer(text):
        lat_min, lat_max, lon_min, lon_max = match.groups()
        zones.append({
            "lat_min": float(lat_min),
            "lat_max": float(lat_max),
            "lon_min": float(lon_min),
            "lon_max": float(lon_max),
            "description": match.group(0).strip(),
        })

    # Match named sea areas
    sea_pattern = re.compile(
        r"(?:Bay of Bengal|Arabian Sea|Andaman Sea|Lakshadweep Sea|Indian Ocean"
        r"|Gulf of Mannar|Gulf of Kutch|Palk Strait)[^\n.]{0,100}",
        re.IGNORECASE
    )
    for match in sea_pattern.finditer(text):
        zones.append({
            "lat_min": None,
            "lat_max": None,
            "lon_min": None,
            "lon_max": None,
            "description": match.group(0).strip(),
        })

    return zones


def _extract_alert_level(text: str) -> str:
    """
    Infer alert level from warning text keywords.
    Returns one of: 'red', 'orange', 'yellow', 'green', 'none'.
    """
    text_lower = text.lower()
    if any(k in text_lower for k in ["very high wave", "extremely heavy", "cyclone", "storm surge", "do not venture"]):
        return "red"
    if any(k in text_lower for k in ["high wave", "heavy swell", "squall", "gale force", "wind speed 45", "wind speed 50"]):
        return "orange"
    if any(k in text_lower for k in ["rough sea", "moderate swell", "wind speed 40", "caution"]):
        return "yellow"
    if any(k in text_lower for k in ["calm", "fair", "normal"]):
        return "green"
    return "none"


# ---------------------------------------------------------------------------
# Main scraper class
# ---------------------------------------------------------------------------

class IncoisScraper:
    """
    Scrapes INCOIS PFZ (Potential Fishing Zone) and OSF (Ocean State Forecast)
    advisories and uploads structured JSON to Backblaze B2 storage.
    """

    def __init__(
        self,
        b2_manager: Optional[B2StorageManager] = None,
        staging_dir: Optional[Path] = None,
        mock_mode: bool = False,
        timeout_seconds: int = DEFAULT_TIMEOUT,
        db_writer: Optional[DBWriter] = None,
    ):
        """
        Initialize the INCOIS Advisory Scraper.

        Args:
            b2_manager: B2StorageManager instance. Created automatically if None.
            staging_dir: Local temp directory for intermediate files.
            mock_mode: If True, skip real B2 uploads (local storage only).
            timeout_seconds: HTTP request timeout.
        """
        self.timeout = timeout_seconds
        self.mock_mode = mock_mode
        self.db_writer = db_writer or DBWriter()
        self.staging_dir = staging_dir or Path(tempfile.mkdtemp(prefix="incois_"))
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        if b2_manager is not None:
            self.b2 = b2_manager
        else:
            self.b2 = B2StorageManager(mock_mode=mock_mode)

        logger.info(
            f"IncoisScraper initialized | mock={mock_mode} | staging={self.staging_dir}"
        )

    # ------------------------------------------------------------------
    # PFZ Advisory scraping
    # ------------------------------------------------------------------

    def fetch_pfz_advisory(self, target_date: date) -> Dict[str, Any]:
        """
        Fetch the daily Potential Fishing Zone (PFZ) advisory.

        Strategy:
          1. Scrape the latest fisherman warning PDFs from RSMCND (which embed
             INCOIS Ocean Current Alert / High Wave / Swell Surge data).
          2. Pull IMD CAP RSS for any relevant marine alerts.
          3. Synthesize a structured PFZ advisory record.

        Args:
            target_date: The date for which to fetch the advisory.

        Returns:
            Structured PFZ advisory dict.
        """
        date_str = target_date.isoformat()
        logger.info(f"Fetching PFZ advisory for {date_str}")

        advisory: Dict[str, Any] = {
            "advisory_type": "pfz",
            "date": date_str,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "INCOIS via RSMCND Fisherman Warning / IMD CAP RSS",
            "source_urls": [],
            "alert_level": "none",
            "advisory_text": "",
            "zones": [],
            "ocean_current_alerts": [],
            "swell_surge_alerts": [],
            "high_wave_alerts": [],
            "cap_alerts": [],
            "raw_bulletins": [],
        }

        # Step 1: Scrape RSMCND fisherman warning PDFs
        logger.info("Scraping RSMCND fisherman warning PDFs...")
        advisory["source_urls"].append(RSMCND_FISHERMEN_URL)
        # archive folder 45 = fishermen warnings on RSMCND
        bulletins = _scrape_bulletin_pdfs(RSMCND_FISHERMEN_URL, RSMCND_BASE, limit=2, archive_folder_hint="45")
        advisory["raw_bulletins"] = bulletins

        combined_text = ""
        for bulletin in bulletins:
            combined_text += bulletin.get("text", "") + "\n"

        if combined_text.strip():
            advisory["advisory_text"] = combined_text[:3000]
            advisory["alert_level"] = _extract_alert_level(combined_text)
            advisory["zones"] = _extract_pfz_zones_from_text(combined_text)

            # Extract INCOIS-specific alert paragraphs
            for line in combined_text.splitlines():
                line_upper = line.upper()
                if "OCEAN CURRENT ALERT" in line_upper:
                    advisory["ocean_current_alerts"].append(line.strip())
                elif "SWELL SURGE ALERT" in line_upper:
                    advisory["swell_surge_alerts"].append(line.strip())
                elif "HIGH WAVE ALERT" in line_upper:
                    advisory["high_wave_alerts"].append(line.strip())

        # Step 2: IMD CAP RSS feed for additional marine alerts
        try:
            logger.info("Fetching IMD CAP RSS feed...")
            advisory["source_urls"].append(IMD_CAP_RSS_URL)
            rss_resp = _get(IMD_CAP_RSS_URL)
            cap_items = _parse_cap_rss(rss_resp.text)
            marine_keywords = [
                "marine", "coastal", "fisher", "wave", "swell", "cyclone",
                "storm", "sea", "ocean", "bay", "arabian", "andaman"
            ]
            advisory["cap_alerts"] = [
                item for item in cap_items
                if any(
                    k in (item.get("title", "") + item.get("description", "")).lower()
                    for k in marine_keywords
                )
            ]
            logger.info(f"Found {len(advisory['cap_alerts'])} marine CAP alerts")
        except Exception as exc:
            logger.warning(f"CAP RSS fetch failed: {exc}")

        # Escalate alert level if INCOIS-specific alerts are present
        if advisory["ocean_current_alerts"] or advisory["swell_surge_alerts"] or advisory["high_wave_alerts"]:
            if advisory["alert_level"] in ("none", "green"):
                advisory["alert_level"] = "yellow"

        logger.info(
            f"PFZ advisory built | zones={len(advisory['zones'])} "
            f"alert_level={advisory['alert_level']}"
        )
        return advisory

    # ------------------------------------------------------------------
    # OSF Advisory scraping
    # ------------------------------------------------------------------

    def fetch_osf_advisory(self, target_date: date) -> Dict[str, Any]:
        """
        Fetch the daily Ocean State Forecast (OSF) advisory.

        Strategy:
          1. Scrape the RSMCND Coastal Weather Bulletin PDFs.
          2. Parse wave height, wind speed, sea state from text.
          3. Synthesize structured OSF advisory record.

        Args:
            target_date: The date for which to fetch the advisory.

        Returns:
            Structured OSF advisory dict.
        """
        date_str = target_date.isoformat()
        logger.info(f"Fetching OSF advisory for {date_str}")

        advisory: Dict[str, Any] = {
            "advisory_type": "osf",
            "date": date_str,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "RSMCND INCOIS Sea Area / Coastal Weather Bulletin",
            "source_urls": [RSMCND_COASTAL_URL],
            "alert_level": "none",
            "advisory_text": "",
            "sea_state": [],
            "wind_forecast": [],
            "wave_forecast": [],
            "zones": [],
            "raw_bulletins": [],
        }

        # Coastal Weather Bulletin PDFs
        logger.info("Scraping RSMCND coastal weather bulletin PDFs...")
        # archive folder 49 = coastal weather bulletins on RSMCND
        bulletins = _scrape_bulletin_pdfs(RSMCND_COASTAL_URL, RSMCND_BASE, limit=2, archive_folder_hint="49")
        advisory["raw_bulletins"] = bulletins

        combined_text = ""
        for bulletin in bulletins:
            combined_text += bulletin.get("text", "") + "\n"

        if combined_text.strip():
            advisory["advisory_text"] = combined_text[:3000]
            advisory["alert_level"] = _extract_alert_level(combined_text)
            advisory["zones"] = _extract_pfz_zones_from_text(combined_text)

            # Parse wind speed mentions
            wind_pattern = re.compile(
                r"wind speed\s+\d+(?:\s*to\s*\d+)?\s*(?:knots?|kts?|kmph|km/h)?[^\n.]{0,150}",
                re.IGNORECASE
            )
            advisory["wind_forecast"] = [
                m.group(0).strip() for m in wind_pattern.finditer(combined_text)
            ]

            # Parse wave/swell mentions
            wave_pattern = re.compile(
                r"(?:wave|swell|sea height)[^\n.]{0,150}",
                re.IGNORECASE
            )
            advisory["wave_forecast"] = [
                m.group(0).strip() for m in wave_pattern.finditer(combined_text)
            ]

            # Parse sea state descriptors
            sea_state_pattern = re.compile(
                r"(?:rough|moderate|slight|high|very high|calm)[^\n.]{0,100}sea[^\n.]{0,100}",
                re.IGNORECASE
            )
            advisory["sea_state"] = [
                m.group(0).strip() for m in sea_state_pattern.finditer(combined_text)
            ]

        logger.info(
            f"OSF advisory built | zones={len(advisory['zones'])} "
            f"alert_level={advisory['alert_level']} "
            f"wind_items={len(advisory['wind_forecast'])}"
        )
        return advisory

    # ------------------------------------------------------------------
    # Upload to B2
    # ------------------------------------------------------------------

    def _upload_advisory(self, advisory: Dict[str, Any], b2_key: str) -> Dict[str, Any]:
        """Serialize advisory to JSON and upload to B2."""
        filename = Path(b2_key).name
        local_path = self.staging_dir / filename

        json_bytes = json.dumps(advisory, indent=2, ensure_ascii=False).encode("utf-8")
        local_path.write_bytes(json_bytes)
        logger.info(f"Wrote {len(json_bytes)} bytes to {local_path}")

        result = self.b2.upload_file(
            str(local_path),
            b2_key,
            content_type="application/json"
        )
        logger.info(f"Uploaded to B2: {b2_key}")
        return result

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------

    def run(self, target_date: Optional[date] = None, upload: bool = True) -> Dict[str, Any]:
        """
        Execute the full INCOIS advisory scrape and upload pipeline.

        Args:
            target_date: Date to fetch advisories for (defaults to today UTC).
            upload: If False, skip B2 upload (safe test mode).

        Returns:
            Summary dict with pfz and osf advisory results.
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        date_str = target_date.isoformat()
        logger.info(f"=== INCOIS Scraper run for {date_str} ===")

        pfz_advisory = self.fetch_pfz_advisory(target_date)
        osf_advisory = self.fetch_osf_advisory(target_date)

        upload_results: Dict[str, Any] = {"pfz": None, "osf": None}

        if upload:
            pfz_key = f"advisories/pfz/{date_str}.json"
            try:
                upload_results["pfz"] = self._upload_advisory(pfz_advisory, pfz_key)
                logger.info(f"PFZ advisory uploaded: {pfz_key}")
                self.db_writer.record_success(
                    dataset_name="incois_pfz",
                    record_count=len(pfz_advisory.get("zones", [])),
                    file_size_bytes=(
                        upload_results["pfz"].get("size_bytes", 0)
                        if upload_results["pfz"]
                        else 0
                    ),
                    source_info={
                        "source": "INCOIS PFZ Advisory / IMD RSMC bulletins",
                        "target_date": date_str,
                        "b2_remote_key": pfz_key,
                    },
                    extra_metadata={
                        "alert_level": pfz_advisory.get("alert_level"),
                        "ocean_current_alerts": len(
                            pfz_advisory.get("ocean_current_alerts", [])
                        ),
                        "swell_alerts": len(
                            pfz_advisory.get("swell_surge_alerts", [])
                        ),
                        "high_wave_alerts": len(
                            pfz_advisory.get("high_wave_alerts", [])
                        ),
                        "cap_alerts": len(
                            pfz_advisory.get("cap_alerts", [])
                        ),
                        "bulletins_scraped": len(
                            pfz_advisory.get("raw_bulletins", [])
                        ),
                    },
                )
            except Exception as exc:
                logger.error(f"PFZ upload failed: {exc}")
                upload_results["pfz"] = {"status": "error", "error": str(exc)}

            osf_key = f"advisories/osf/{date_str}.json"
            try:
                upload_results["osf"] = self._upload_advisory(osf_advisory, osf_key)
                logger.info(f"OSF advisory uploaded: {osf_key}")
                self.db_writer.record_success(
                    dataset_name="incois_osf",
                    record_count=len(osf_advisory.get("zones", [])),
                    file_size_bytes=(
                        upload_results["osf"].get("size_bytes", 0)
                        if upload_results["osf"]
                        else 0
                    ),
                    source_info={
                        "source": "INCOIS OSF Advisory / IMD RSMC bulletins",
                        "target_date": date_str,
                        "b2_remote_key": osf_key,
                    },
                    extra_metadata={
                        "alert_level": osf_advisory.get("alert_level"),
                        "wind_items": len(
                            osf_advisory.get("wind_forecast", [])
                        ),
                        "wave_items": len(
                            osf_advisory.get("wave_forecast", [])
                        ),
                        "bulletins_scraped": len(
                            osf_advisory.get("raw_bulletins", [])
                        ),
                    },
                )
            except Exception as exc:
                logger.error(f"OSF upload failed: {exc}")
                upload_results["osf"] = {"status": "error", "error": str(exc)}
        else:
            logger.info("Upload skipped (--no-upload flag set)")
            pfz_path = self.staging_dir / f"pfz_{date_str}.json"
            osf_path = self.staging_dir / f"osf_{date_str}.json"
            pfz_path.write_bytes(json.dumps(pfz_advisory, indent=2, ensure_ascii=False).encode())
            osf_path.write_bytes(json.dumps(osf_advisory, indent=2, ensure_ascii=False).encode())
            logger.info(f"PFZ saved locally: {pfz_path}")
            logger.info(f"OSF saved locally: {osf_path}")

        summary = {
            "date": date_str,
            "pfz": {
                "alert_level": pfz_advisory.get("alert_level"),
                "zones_found": len(pfz_advisory.get("zones", [])),
                "ocean_current_alerts": len(pfz_advisory.get("ocean_current_alerts", [])),
                "swell_alerts": len(pfz_advisory.get("swell_surge_alerts", [])),
                "high_wave_alerts": len(pfz_advisory.get("high_wave_alerts", [])),
                "cap_alerts": len(pfz_advisory.get("cap_alerts", [])),
                "bulletins_scraped": len(pfz_advisory.get("raw_bulletins", [])),
                "upload": upload_results["pfz"],
            },
            "osf": {
                "alert_level": osf_advisory.get("alert_level"),
                "zones_found": len(osf_advisory.get("zones", [])),
                "wind_items": len(osf_advisory.get("wind_forecast", [])),
                "wave_items": len(osf_advisory.get("wave_forecast", [])),
                "bulletins_scraped": len(osf_advisory.get("raw_bulletins", [])),
                "upload": upload_results["osf"],
            },
        }

        logger.info(f"INCOIS scraper summary: {json.dumps(summary, indent=2)}")
        return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="INCOIS Advisory Web Scraper (CHUNK_ID: R4-C05)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date in YYYY-MM-DD format (defaults to today UTC)",
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        default=False,
        help="Skip B2 upload; save JSON locally for inspection",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Use mock B2 storage (local simulation)",
    )
    parser.add_argument(
        "--staging-dir",
        type=str,
        default=None,
        help="Local staging directory for intermediate files",
    )
    args = parser.parse_args()

    target_date: Optional[date] = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"ERROR: Invalid date format: {args.date}. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)

    staging_dir = Path(args.staging_dir) if args.staging_dir else None

    scraper = IncoisScraper(
        staging_dir=staging_dir,
        mock_mode=args.mock,
    )

    summary = scraper.run(
        target_date=target_date,
        upload=not args.no_upload,
    )

    print("\n=== INCOIS Scraper Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
