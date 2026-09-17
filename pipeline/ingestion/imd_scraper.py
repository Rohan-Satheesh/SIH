"""
IMD Marine Warning Scraper (CHUNK_ID: R4-C06)
----------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/ingestion/imd_scraper.py
Prerequisites: [R4-C01] (pipeline.storage.b2_uploader)

Scrapes daily Indian Meteorological Department (IMD) coastal/marine warnings
from the Regional Specialised Meteorological Centre, New Delhi (RSMCND) website
and the IMD CAP RSS alert feed. Normalizes warnings to structured JSON and
uploads to Backblaze B2 storage under weather/imd/YYYY-MM-DD.json.

Data sources:
  1. RSMCND Sea Area Bulletin   (rsmcnewdelhi.imd.gov.in/sea-area-bulletin.php)
     - archive folder 47: Tropical Weather Outlook PDFs
  2. RSMCND Coastal Weather Bulletin (coastal-weather-bulletin.php)
     - archive folder 49: coastal weather bulletin PDFs
  3. RSMCND Port Warning          (port-warning.php)
     - archive folder 50: port warning PDFs
  4. RSMCND Fishermen Warning     (fishermen-warning.php)
     - archive folder 45: fishermen warning PDFs
  5. IMD CAP RSS feed             (cap-sources.s3.amazonaws.com/in-imd-en/rss.xml)
     - all current CAP alert items

Acceptance Criteria:
  - [x] Fetches daily IMD marine/coastal warnings from multiple live sources.
  - [x] Normalizes to structured JSON with warning_type, severity, date,
        source_url, warning_text, affected_areas, valid_until fields.
  - [x] Uploads JSON to weather/imd/YYYY-MM-DD.json on Backblaze B2.
  - [x] CLI: python -m pipeline.ingestion.imd_scraper [--no-upload] [--date YYYY-MM-DD]
"""

import os
import sys
import json
import logging
import argparse
import re
import tempfile
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings

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
logger = logging.getLogger("imd_scraper")

# ---------------------------------------------------------------------------
# Source URL constants
# ---------------------------------------------------------------------------
RSMCND_BASE = "https://rsmcnewdelhi.imd.gov.in"

# RSMCND bulletin pages with their known archive folder IDs
RSMCND_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "sea_area_bulletin",
        "label": "Sea Area Bulletin",
        "url": f"{RSMCND_BASE}/sea-area-bulletin.php",
        "archive_id": "47",
        "warning_type": "sea_area",
    },
    {
        "name": "coastal_weather_bulletin",
        "label": "Coastal Weather Bulletin",
        "url": f"{RSMCND_BASE}/coastal-weather-bulletin.php",
        "archive_id": "49",
        "warning_type": "coastal_weather",
    },
    {
        "name": "port_warning",
        "label": "Port Warning",
        "url": f"{RSMCND_BASE}/port-warning.php",
        "archive_id": "50",
        "warning_type": "port_warning",
    },
    {
        "name": "fishermen_warning",
        "label": "Fishermen Warning",
        "url": f"{RSMCND_BASE}/fishermen-warning.php",
        "archive_id": "45",
        "warning_type": "fishermen_warning",
    },
]

# IMD CAP RSS (live alert feed from S3)
IMD_CAP_RSS_URL = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"

DEFAULT_TIMEOUT = 25
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
                logger.info(f"Parsed {len(items)} CAP RSS items with '{parser}'")
                break
        except Exception:
            continue
    return items


def _scrape_rsmcnd_pdfs(
    page_url: str,
    archive_id: str,
    limit: int = 2,
) -> List[Dict[str, Any]]:
    """
    Scrape recent bulletin PDFs from an RSMCND page filtered by archive folder ID.

    RSMCND pages list PDFs in links like:
      uploads/archive/45/45_abc123_fishermen.pdf
    or via download.php?path=uploads/archive/45/...

    Args:
        page_url: RSMCND bulletin listing page URL.
        archive_id: Numeric archive folder (e.g. '45' for fishermen warnings).
        limit: Max number of PDFs to fetch and parse.

    Returns:
        List of dicts with {source_url, title, text} for each fetched PDF.
    """
    results = []
    try:
        resp = _get(page_url)
        soup = BeautifulSoup(resp.text, "html.parser")

        pdf_links: List[Dict[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)
            if not href.endswith(".pdf"):
                continue
            if f"/archive/{archive_id}/" not in href:
                continue
            # Build absolute URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("download.php"):
                full_url = f"{RSMCND_BASE}/{href}"
            else:
                full_url = f"{RSMCND_BASE}/{href.lstrip('/')}"
            pdf_links.append({"title": title or Path(href).stem, "url": full_url})

        # Deduplicate preserving order
        seen: set = set()
        unique: List[Dict[str, str]] = []
        for item in pdf_links:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique.append(item)

        logger.info(f"Found {len(unique)} PDFs in archive/{archive_id} on {page_url}")

        for link in unique[:limit]:
            try:
                pdf_resp = _SESSION.get(link["url"], timeout=30)
                pdf_resp.raise_for_status()
                text = _normalize_whitespace(_extract_pdf_text(pdf_resp.content))
                results.append({
                    "source_url": link["url"],
                    "title": link["title"],
                    "text": text[:8000],
                })
                logger.info(f"  Extracted: {link['url']} ({len(text)} chars)")
            except Exception as exc:
                logger.warning(f"  Failed to fetch PDF {link['url']}: {exc}")

    except Exception as exc:
        logger.error(f"Failed to scrape {page_url}: {exc}")

    return results


# ---------------------------------------------------------------------------
# Text analysis helpers
# ---------------------------------------------------------------------------

def _classify_severity(text: str) -> str:
    """
    Classify warning severity from text content.
    Returns one of: 'extreme', 'severe', 'moderate', 'minor', 'none'.
    """
    t = text.lower()
    if any(k in t for k in ["do not venture", "extremely severe", "super cyclonic", "very severe cyclonic"]):
        return "extreme"
    if any(k in t for k in ["severe cyclonic", "cyclone", "storm surge", "gale force", "wind speed 64", "wind speed 50"]):
        return "severe"
    if any(k in t for k in ["squall", "rough sea", "wind speed 45", "wind speed 40", "high wave"]):
        return "moderate"
    if any(k in t for k in ["caution", "wind speed 30", "wind speed 25", "moderate swell"]):
        return "minor"
    return "none"


def _extract_affected_areas(text: str) -> List[str]:
    """Extract named coastal/sea areas from warning text."""
    areas: List[str] = []
    patterns = [
        r"Bay of Bengal[^\n.]{0,100}",
        r"Arabian Sea[^\n.]{0,100}",
        r"Andaman Sea[^\n.]{0,100}",
        r"Lakshadweep Sea[^\n.]{0,100}",
        r"Gulf of Mannar[^\n.]{0,100}",
        r"Gulf of Kutch[^\n.]{0,100}",
        r"North(?:ern|east|west)?\s+(?:Bay|Arabian|Indian)[^\n.]{0,80}",
        r"South(?:ern|east|west)?\s+(?:Bay|Arabian|Indian)[^\n.]{0,80}",
        r"(?:Tamil Nadu|Maharashtra|Karnataka|Kerala|Andhra|Odisha|West Bengal|Gujarat|Goa)\s+coast[^\n.]{0,80}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            area = match.group(0).strip()
            if area not in areas:
                areas.append(area)
    return areas[:20]  # cap at 20 distinct areas


def _extract_valid_until(text: str) -> Optional[str]:
    """Try to extract a validity period from the warning text."""
    # Pattern: "valid till HH:MM IST of DD/MM/YYYY" or similar
    patterns = [
        r"valid (?:till|until|upto)[^\n.]{0,60}",
        r"till \d{2}[/-]\d{2}[/-]\d{4}",
        r"till \d{2}:\d{2}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


# ---------------------------------------------------------------------------
# Main scraper class
# ---------------------------------------------------------------------------

class ImdScraper:
    """
    Scrapes IMD coastal/marine warnings from RSMCND bulletin pages and the
    IMD CAP RSS feed. Normalizes to structured JSON and uploads to B2.
    """

    def __init__(
        self,
        b2_manager: Optional[B2StorageManager] = None,
        staging_dir: Optional[Path] = None,
        mock_mode: bool = False,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the IMD Marine Warning Scraper.

        Args:
            b2_manager: B2StorageManager instance. Created automatically if None.
            staging_dir: Local directory for intermediate JSON files.
            mock_mode: If True, skip real B2 uploads.
            timeout_seconds: HTTP request timeout.
        """
        self.timeout = timeout_seconds
        self.mock_mode = mock_mode
        self.staging_dir = staging_dir or Path(tempfile.mkdtemp(prefix="imd_"))
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        if b2_manager is not None:
            self.b2 = b2_manager
        else:
            self.b2 = B2StorageManager(mock_mode=mock_mode)

        logger.info(
            f"ImdScraper initialized | mock={mock_mode} | staging={self.staging_dir}"
        )

    # ------------------------------------------------------------------
    # RSMCND bulletin scraping
    # ------------------------------------------------------------------

    def _scrape_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape a single RSMCND bulletin source.

        Args:
            source: Dict from RSMCND_SOURCES with name, label, url, archive_id,
                    warning_type.

        Returns:
            Structured warning dict for this source.
        """
        name = source["name"]
        warning_type = source["warning_type"]
        page_url = source["url"]
        archive_id = source["archive_id"]
        label = source["label"]

        logger.info(f"Scraping {label} (archive/{archive_id})...")

        record: Dict[str, Any] = {
            "name": name,
            "warning_type": warning_type,
            "label": label,
            "source_url": page_url,
            "bulletins": [],
            "combined_text_preview": "",
            "severity": "none",
            "affected_areas": [],
            "valid_until": None,
        }

        bulletins = _scrape_rsmcnd_pdfs(page_url, archive_id, limit=2)
        record["bulletins"] = bulletins

        combined_text = "\n".join(b.get("text", "") for b in bulletins)
        if combined_text.strip():
            record["combined_text_preview"] = combined_text[:2000]
            record["severity"] = _classify_severity(combined_text)
            record["affected_areas"] = _extract_affected_areas(combined_text)
            record["valid_until"] = _extract_valid_until(combined_text)

        logger.info(
            f"  {label}: severity={record['severity']} "
            f"areas={len(record['affected_areas'])} "
            f"bulletins={len(bulletins)}"
        )
        return record

    # ------------------------------------------------------------------
    # CAP RSS
    # ------------------------------------------------------------------

    def _fetch_cap_alerts(self) -> List[Dict[str, Any]]:
        """Fetch and return all current IMD CAP alert items."""
        try:
            resp = _get(IMD_CAP_RSS_URL)
            items = _parse_cap_rss(resp.text)
            logger.info(f"Fetched {len(items)} CAP alerts from IMD RSS feed")
            return items
        except Exception as exc:
            logger.warning(f"CAP RSS fetch failed: {exc}")
            return []

    # ------------------------------------------------------------------
    # Upload to B2
    # ------------------------------------------------------------------

    def _upload_payload(self, payload: Dict[str, Any], b2_key: str) -> Dict[str, Any]:
        """Serialize payload to JSON and upload to B2."""
        filename = Path(b2_key).name
        local_path = self.staging_dir / filename

        json_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
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
        Execute the full IMD Marine Warning scrape and upload pipeline.

        Args:
            target_date: Date to fetch warnings for (defaults to today UTC).
            upload: If False, skip B2 upload (safe test mode).

        Returns:
            Summary dict with per-source results.
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        date_str = target_date.isoformat()
        logger.info(f"=== IMD Scraper run for {date_str} ===")

        # Scrape all RSMCND bulletin sources
        scraped_sources: List[Dict[str, Any]] = []
        for source in RSMCND_SOURCES:
            try:
                record = self._scrape_source(source)
                scraped_sources.append(record)
            except Exception as exc:
                logger.error(f"Failed to scrape {source['name']}: {exc}")
                scraped_sources.append({
                    "name": source["name"],
                    "warning_type": source["warning_type"],
                    "error": str(exc),
                })

        # Determine overall severity
        severity_order = ["none", "minor", "moderate", "severe", "extreme"]
        overall_severity = "none"
        for record in scraped_sources:
            sev = record.get("severity", "none")
            if severity_order.index(sev) > severity_order.index(overall_severity):
                overall_severity = sev

        # Fetch CAP alerts
        cap_alerts = self._fetch_cap_alerts()

        # Build payload
        payload: Dict[str, Any] = {
            "date": date_str,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "IMD RSMCND Marine Bulletins + CAP RSS",
            "overall_severity": overall_severity,
            "warnings": scraped_sources,
            "cap_alerts": cap_alerts,
            "cap_alert_count": len(cap_alerts),
        }

        upload_result = None
        if upload:
            b2_key = f"weather/imd/{date_str}.json"
            try:
                upload_result = self._upload_payload(payload, b2_key)
                logger.info(f"IMD warnings uploaded: {b2_key}")
            except Exception as exc:
                logger.error(f"IMD upload failed: {exc}")
                upload_result = {"status": "error", "error": str(exc)}
        else:
            logger.info("Upload skipped (--no-upload flag set)")
            local_path = self.staging_dir / f"imd_{date_str}.json"
            local_path.write_bytes(json.dumps(payload, indent=2, ensure_ascii=False).encode())
            logger.info(f"IMD warnings saved locally: {local_path}")

        summary = {
            "date": date_str,
            "overall_severity": overall_severity,
            "sources_scraped": len(scraped_sources),
            "cap_alerts_total": len(cap_alerts),
            "per_source": [
                {
                    "name": r.get("name"),
                    "severity": r.get("severity", "none"),
                    "areas": len(r.get("affected_areas", [])),
                    "bulletins": len(r.get("bulletins", [])),
                }
                for r in scraped_sources
            ],
            "upload": upload_result,
        }

        logger.info(f"IMD scraper summary: {json.dumps(summary, indent=2)}")
        return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="IMD Marine Warning Scraper (CHUNK_ID: R4-C06)"
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

    scraper = ImdScraper(
        staging_dir=staging_dir,
        mock_mode=args.mock,
    )

    summary = scraper.run(
        target_date=target_date,
        upload=not args.no_upload,
    )

    print("\n=== IMD Scraper Summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
