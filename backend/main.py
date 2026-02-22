from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Query
from typing import Optional
try:
    from .app.scanner import scan_market, scan_analysis
except ImportError:
    from app.scanner import scan_market, scan_analysis
try:
    from .config import INDEXES
except ImportError:
    from config import INDEXES
import json

import asyncio
import concurrent.futures
import threading
from datetime import datetime, timezone

# Simple in-memory cache/manager for scan results and status
SCAN_CACHE = {}
CACHE_LOCK = threading.Lock()

# Validate INDEXES on startup
if not INDEXES:
    print("WARNING: INDEXES is empty or not loaded correctly from config.py")
else:
    print(f"Loaded {len(INDEXES)} indexes: {list(INDEXES.keys())}")

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    html_content = """
    <html>
    <head>
        <title>NSE Quant Tool API</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f9; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 15px; margin-top: 0; }
            ul { list-style: none; padding: 0; }
            li { background: #fff; border-bottom: 1px solid #f0f0f0; padding: 15px 0; }
            li:last-child { border-bottom: none; }
            a { font-weight: 600; color: #3498db; text-decoration: none; font-size: 1.1em; }
            a:hover { color: #2980b9; text-decoration: underline; }
            .meta { font-size: 0.85em; color: #95a5a6; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
            .desc { color: #555; margin-top: 5px; line-height: 1.5; }
            .header-links { margin-bottom: 20px; color: #666; }
            .header-links a { font-size: 1em; color: #2c3e50; text-decoration: underline; }
            .search-box { margin-bottom: 20px; }
            .search-box input { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            .tag-group { margin-bottom: 20px; }
            .tag-title { background-color: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 10px; color: #495057; font-size: 1.2em; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
            .tag-title:hover { background-color: #dee2e6; }
            .tag-title::after { content: '▼'; font-size: 0.8em; transition: transform 0.3s; }
            .tag-group.collapsed .tag-title::after { transform: rotate(-90deg); }
            .tag-group.collapsed ul { display: none; }
            .endpoint-row { display: flex; align-items: center; }
            .copy-btn { margin-left: 10px; background: #fff; border: 1px solid #ccc; border-radius: 3px; cursor: pointer; font-size: 0.75em; padding: 2px 6px; color: #555; transition: all 0.2s; }
            .copy-btn:hover { background-color: #eee; border-color: #bbb; color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>NSE Quant Tool API</h1>
            <div class="header-links">
                See also: <a href="/docs" target="_blank">Swagger UI</a> | <a href="/redoc" target="_blank">ReDoc</a>
            </div>
            <div class="search-box">
                <input type="text" id="endpointSearch" placeholder="Search endpoints..." onkeyup="filterEndpoints()">
            </div>
            <div id="endpointList">
    """
    routes_by_tag = {}
    for route in request.app.routes:
        if hasattr(route, "methods") and "GET" in route.methods:
            tags = getattr(route, "tags", [])
            if not tags:
                tags = ["General"]
            for tag in tags:
                if tag not in routes_by_tag:
                    routes_by_tag[tag] = []
                routes_by_tag[tag].append(route)

    for tag in sorted(routes_by_tag.keys()):
        html_content += f"""
        <div class="tag-group">
            <h3 class="tag-title">{tag}</h3>
            <ul>
        """
        for route in routes_by_tag[tag]:
            desc = getattr(route, "description", None) or "No description available."
            path = getattr(route, "path", "")
            html_content += f"""
            <li>
                <div class="meta">{getattr(route, "name", "Unnamed")}</div>
                <div class="endpoint-row">
                    <a href="{path}" target="_blank">{path}</a>
                    <button class="copy-btn" onclick="copyToClipboard(this, '{path}')">Copy URL</button>
                </div>
                <div class="desc">{desc}</div>
            </li>"""
        html_content += "</ul></div>"

    html_content += """
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const titles = document.querySelectorAll('.tag-title');
                titles.forEach(title => {
                    title.addEventListener('click', () => {
                        title.parentElement.classList.toggle('collapsed');
                    });
                });
            });

            function copyToClipboard(btn, path) {
                const fullUrl = window.location.origin + path;
                navigator.clipboard.writeText(fullUrl).then(() => {
                    const originalText = btn.textContent;
                    btn.textContent = 'Copied!';
                    setTimeout(() => { btn.textContent = originalText; }, 1500);
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            }

            function filterEndpoints() {
                var input, filter, container, groups, i, j, ul, li, a, meta, txtValue, groupVisible;
                input = document.getElementById('endpointSearch');
                filter = input.value.toUpperCase();
                container = document.getElementById("endpointList");
                groups = container.getElementsByClassName('tag-group');

                for (i = 0; i < groups.length; i++) {
                    ul = groups[i].getElementsByTagName('ul')[0];
                    li = ul.getElementsByTagName('li');
                    groupVisible = false;

                    for (j = 0; j < li.length; j++) {
                        a = li[j].getElementsByTagName("a")[0];
                        meta = li[j].getElementsByClassName("meta")[0];
                        txtValue = (a.textContent || a.innerText) + " " + (meta.textContent || meta.innerText);
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            li[j].style.display = "";
                            groupVisible = true;
                        } else {
                            li[j].style.display = "none";
                        }
                    }
                    groups[i].style.display = groupVisible ? "" : "none";
                    if (filter && groupVisible) {
                        groups[i].classList.remove('collapsed');
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


def _render_scan_page(default_live=False):
    # Render interactive page; fetch INDEXES via API to ensure latest data
    default_live_js = 'true' if default_live else 'false'
    html = """
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>NSE Scan Results</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f4f4f9; color: #333; }
                h2 { color: #2c3e50; margin-top: 0; margin-bottom: 20px; }
                .controls { margin-bottom: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
                select, button { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
                select { min-width: 200px; }
                button { background-color: #3498db; color: white; border: none; cursor: pointer; transition: background 0.2s; }
                button:hover { background-color: #2980b9; }
                table { border-collapse: collapse; width: 100%; max-width: 1200px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
                th, td { border-bottom: 1px solid #eee; padding: 12px 15px; text-align: left; }
                th { background: #f8f9fa; font-weight: 600; color: #2c3e50; cursor: pointer; user-select: none; }
                th:hover { background: #e9ecef; }
                tr:last-child td { border-bottom: none; }
                tr:hover { background-color: #f1f1f1; }
                .sort-indicator { margin-left: 6px; font-size: 0.8em; color: #999; }
                #progressInfo { color: #666; font-style: italic; margin-left: auto; }
                .positive { color: #27ae60; font-weight: 500; }
                .negative { color: #c0392b; font-weight: 500; }
                .spinner {
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #3498db;
                    border-radius: 50%;
                    width: 16px;
                    height: 16px;
                    animation: spin 1s linear infinite;
                    display: none;
                    vertical-align: middle;
                    margin-left: 10px;
                }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <h2>NSE Scan</h2>
            <div class="controls">
                <label>Index: <select id="indexSelect"><option value="" disabled selected>Loading...</option></select></label>
                <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                    <input type="checkbox" id="liveCheck"> Live (intraday)
                </label>
                <label>Min Return %: <input type="number" id="minReturnInput" placeholder="0" style="width: 60px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px;"></label>
                <button id="refreshBtn">Refresh</button>
                <button id="exportBtn">Export CSV</button>
                <div id="loadingSpinner" class="spinner"></div>
                <span id="progressInfo"></span>
            </div>
            <table id="resultsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('resultsTable', 0)">Index<span class="sort-indicator"></span></th>
                        <th onclick="sortTable('resultsTable', 1)">Symbol<span class="sort-indicator"></span></th>
                        <th onclick="sortTable('resultsTable', 2)">Last Price (INR)<span class="sort-indicator"></span></th>
                        <th onclick="sortTable('resultsTable', 3)">Momentum Return (%)<span class="sort-indicator"></span></th>
                        <th onclick="sortTable('resultsTable', 4)">Mean Reversion Return (%)<span class="sort-indicator"></span></th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            </table>

            <script>window.DEFAULT_LIVE = __DEFAULT_LIVE_PLACEHOLDER__;</script>
            <script>
                (async function() {
                    let INDEXES = {};
                    let loadingCount = 0;
                    const spinner = document.getElementById('loadingSpinner');

                    function updateSpinner() {
                        spinner.style.display = loadingCount > 0 ? 'inline-block' : 'none';
                    }

                    async function fetchIndexes() {
                        loadingCount++;
                        updateSpinner();
                        try {
                            const response = await fetch('/api/indexes');
                            if (!response.ok) throw new Error('Failed to fetch indexes');
                            INDEXES = await response.json();
                            populateDropdown();
                        } catch (error) {
                            console.error('Error fetching indexes:', error);
                            document.getElementById('progressInfo').textContent = 'Error loading indexes. Please check console.';
                        } finally {
                            loadingCount--;
                            updateSpinner();
                        }
                    }

                    function populateDropdown() {
                        const indexSelect = document.getElementById('indexSelect');
                        indexSelect.innerHTML = ''; // Clear loading option
                        
                        const keys = Object.keys(INDEXES).sort();
                        
                        // Add "All Indexes" option
                        const totalCount = keys.reduce((acc, key) => acc + (INDEXES[key] ? INDEXES[key].length : 0), 0);
                        const allOpt = document.createElement('option');
                        allOpt.value = 'ALL';
                        allOpt.textContent = `All Indexes (${totalCount})`;
                        indexSelect.appendChild(allOpt);

                        if (keys.length === 0) {
                            const opt = document.createElement('option');
                            opt.textContent = "No indexes found";
                            indexSelect.appendChild(opt);
                            return;
                        }

                        keys.forEach(name => {
                            const opt = document.createElement('option');
                            opt.value = name;
                            const count = INDEXES[name] ? INDEXES[name].length : 0;
                            opt.textContent = `${name} (${count})`;
                            indexSelect.appendChild(opt);
                        });

                        // Select the first real index by default if available
                        if (keys.length > 0) {
                            indexSelect.value = keys[0];
                            loadScanResults(document.getElementById('liveCheck').checked);
                        }
                    }

                    function getColorClass(v) {
                        if (v === null || isNaN(v)) return '';
                        return v >= 0 ? 'positive' : 'negative';
                    }

                    function renderTable(data) {
                        const tbody = document.getElementById('resultsTable').tBodies[0];
                        tbody.innerHTML = '';
                        data.forEach(r => {
                            const tr = document.createElement('tr');
                            const last = r.last_price;
                            const m = r.momentum_return;
                            const mr = r.mean_rev_return;
                            
                            const lastStr = last !== null && last !== undefined ? last.toFixed(2) : '-';
                            const mStr = m !== null && m !== undefined ? m.toFixed(2) : '-';
                            const mrStr = mr !== null && mr !== undefined ? mr.toFixed(2) : '-';
                            
                            const mClass = getColorClass(m);
                            const mrClass = getColorClass(mr);

                            tr.innerHTML = `
                                <td>${r.index || ''}</td>
                                <td>${r.symbol}</td>
                                <td data-value="${last || ''}">${lastStr}</td>
                                <td data-value="${m || ''}" class="${mClass}">${mStr}</td>
                                <td data-value="${mr || ''}" class="${mrClass}">${mrStr}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                    }

                    function exportCSV(filename = 'scan.csv') {
                        const table = document.getElementById('resultsTable');
                        const rows = Array.from(table.querySelectorAll('tr'));
                        const csvRows = rows.map(r => Array.from(r.cells).map(c => '"' + c.textContent.replace(/"/g, '""') + '"').join(',')).join('\\n');
                        const blob = new Blob([csvRows], { type: 'text/csv' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url);
                    }

                    async function loadScanResults(live=false) {
                        const progressEl = document.getElementById('progressInfo');
                        const tbody = document.getElementById('resultsTable').tBodies[0];
                        tbody.innerHTML = '';
                        
                        const indexSelect = document.getElementById('indexSelect');
                        const selectedIndex = indexSelect.value;
                        const minReturn = document.getElementById('minReturnInput').value;
                        
                        if (!selectedIndex) return;

                        let names = [];
                        if (selectedIndex === 'ALL') {
                            names = Object.keys(INDEXES || {});
                        } else {
                            names = [selectedIndex];
                        }
                        
                        if (!names.length) { progressEl.textContent = 'No indexes defined'; return; }
                        
                        progressEl.textContent = 'Scanning ' + names.length + ' index(es)...';
                        loadingCount++;
                        updateSpinner();
                        
                        try {
                            const promises = names.map(async name => {
                                try {
                                    let url = '/api/scan?index=' + encodeURIComponent(name) + '&live=' + (live ? '1' : '0');
                                    if (minReturn !== '') {
                                        url += '&min_return=' + encodeURIComponent(minReturn);
                                    }
                                    const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
                                    if (!res.ok) throw new Error('Network response was not ok');
                                    const data = await res.json();
                                    return { name, results: data };
                                } catch (e) {
                                    console.error('Error scanning ' + name, e);
                                    return { name, results: [] };
                                }
                            });
                            
                            const all = await Promise.all(promises);
                            const rows = [];
                            all.forEach(a => { (a.results || []).forEach(r => rows.push(Object.assign({ index: a.name }, r))); });
                            
                            renderTable(rows);
                            progressEl.textContent = 'Loaded ' + rows.length + ' rows.';
                        } catch (e) {
                            progressEl.textContent = 'Error during scan.';
                            console.error(e);
                        } finally {
                            loadingCount--;
                            updateSpinner();
                        }
                    }

                    function sortTable(tableId, colIndex) {
                        const table = document.getElementById(tableId);
                        const tbody = table.tBodies[0];
                        const rows = Array.from(tbody.rows);
                        const th = table.tHead.rows[0].cells[colIndex];
                        const indicator = th.querySelector('.sort-indicator');
                        const current = th.dataset.order === 'asc' ? 'asc' : (th.dataset.order === 'desc' ? 'desc' : null);
                        const newOrder = current === 'asc' ? 'desc' : 'asc';
                        
                        Array.from(table.tHead.rows[0].cells).forEach(cell => { 
                            cell.dataset.order = ''; 
                            const ind = cell.querySelector('.sort-indicator'); 
                            if (ind) ind.textContent = ''; 
                        });
                        
                        th.dataset.order = newOrder;
                        if (indicator) indicator.textContent = newOrder === 'asc' ? '▲' : '▼';
                        
                        rows.sort((a, b) => {
                            const aCell = a.cells[colIndex];
                            const bCell = b.cells[colIndex];
                            const aVal = aCell.dataset.value !== undefined && aCell.dataset.value !== '' ? parseFloat(aCell.dataset.value) : null;
                            const bVal = bCell.dataset.value !== undefined && bCell.dataset.value !== '' ? parseFloat(bCell.dataset.value) : null;
                            
                            if (aVal !== null && bVal !== null && !isNaN(aVal) && !isNaN(bVal)) {
                                return newOrder === 'asc' ? aVal - bVal : bVal - aVal;
                            }
                            const aText = aCell.textContent.trim();
                            const bText = bCell.textContent.trim();
                            return newOrder === 'asc' ? aText.localeCompare(bText) : bText.localeCompare(aText);
                        });
                        
                        rows.forEach(r => tbody.appendChild(r));
                    }

                    // wire controls
                    try { if (window.DEFAULT_LIVE) document.getElementById('liveCheck').checked = true; } catch (e) {}
                    
                    document.getElementById('indexSelect').addEventListener('change', () => {
                        const live = document.getElementById('liveCheck').checked; loadScanResults(live);
                    });
                    document.getElementById('refreshBtn').addEventListener('click', () => {
                        const live = document.getElementById('liveCheck').checked; loadScanResults(live);
                    });
                    document.getElementById('exportBtn').addEventListener('click', () => exportCSV());

                    // Initial load
                    fetchIndexes();
                })();
            </script>

        </body>
        </html>
        """

    html = html.replace("__DEFAULT_LIVE_PLACEHOLDER__", default_live_js)
    return HTMLResponse(content=html)


@app.get("/scan", response_class=HTMLResponse)
def scan():
    response = _render_scan_page(default_live=False)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get("/scan-live", response_class=HTMLResponse)
def scan_live():
    # Render the same interactive page but default to live mode
    response = _render_scan_page(default_live=True)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.get('/api/scan')
def api_scan(
    request: Request,
    index: Optional[str] = Query(None),
    live: Optional[int] = Query(0),
    format: Optional[str] = Query(None),
    min_return: Optional[float] = Query(None)
):
    # Auto-detect browser request to serve HTML by default
    if format is None:
        accept = request.headers.get('accept', '')
        if 'text/html' in accept and 'application/json' not in accept:
            format = 'html'

    if not INDEXES:
        return [] if format != 'html' else HTMLResponse("No indexes configured.")

    # index: display name from INDEXES keys
    if index is None:
        # default to first index
        index = next(iter(INDEXES.keys()))

    symbols = INDEXES.get(index)
    if symbols is None:
        return [] if format != 'html' else HTMLResponse(f"Index '{index}' not found.")

    results = scan_market(symbols=symbols, live=bool(live))

    if min_return is not None:
        results = [
            r for r in results
            if (r.get('momentum_return') is not None and r['momentum_return'] >= min_return) or
               (r.get('mean_rev_return') is not None and r['mean_rev_return'] >= min_return)
        ]

    if format == 'html':
        html_content = f"""
        <html>
        <head>
            <title>Scan Results - {index}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f4f4f4; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h2>Scan Results for {index}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Last Price</th>
                        <th>Momentum Return</th>
                        <th>Mean Rev Return</th>
                    </tr>
                </thead>
                <tbody>
        """
        for row in results:
            last = row.get('last_price')
            mom = row.get('momentum_return')
            mr = row.get('mean_rev_return')
            html_content += f"""
                    <tr>
                        <td>{row.get('symbol')}</td>
                        <td>{f"{last:.2f}" if last is not None else "-"}</td>
                        <td>{f"{mom:.2f}" if mom is not None else "-"}</td>
                        <td>{f"{mr:.2f}" if mr is not None else "-"}</td>
                    </tr>
            """
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    return results


@app.get('/api/analyze')
def api_analyze(
    request: Request,
    index: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    live: Optional[int] = Query(0),
    format: Optional[str] = Query(None),
    recommendation: Optional[str] = Query(None)
):
    # Auto-detect browser request to serve HTML by default
    if format is None:
        accept = request.headers.get('accept', '')
        if 'text/html' in accept and 'application/json' not in accept:
            format = 'html'

    symbols = []
    title = "Analysis"
    if symbol:
        symbols = [symbol]
        title = f"Analysis - {symbol}"
    else:
        if index is None and INDEXES:
            index = next(iter(INDEXES.keys()))
        if index and index in INDEXES:
            symbols = INDEXES[index]
            title = f"Analysis - {index}"
        else:
            return [] if format != 'html' else HTMLResponse("No symbols found.")

    results = scan_analysis(symbols=symbols, live=bool(live))

    if recommendation:
        rec_lower = recommendation.lower()
        results = [r for r in results if rec_lower in r.get('recommendation', '').lower()]

    if format == 'html':
        html_content = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #f4f4f9; }}
                h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }}
                th {{ background-color: #f8f9fa; font-weight: 600; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .rec-Strong {{ color: green; font-weight: bold; }}
                .rec-Avoid {{ color: red; }}
            </style>
        </head>
        <body>
            <h2>{title}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>Recommendation</th>
                        <th>Mom Signal</th>
                        <th>Mom Return %</th>
                        <th>Mom Sharpe</th>
                        <th>Rev Signal</th>
                        <th>Rev Return %</th>
                        <th>Rev Win Rate %</th>
                    </tr>
                </thead>
                <tbody>
        """
        for r in results:
            mom = r.get('momentum', {})
            rev = r.get('mean_reversion', {})
            rec = r.get('recommendation', '')
            rec_class = 'rec-Strong' if 'Strong' in rec else ('rec-Avoid' if 'Avoid' in rec else '')
            
            html_content += f"""
                    <tr>
                        <td>{r.get('symbol')}</td>
                        <td>{r.get('last_price', 0):.2f}</td>
                        <td class="{rec_class}">{rec}</td>
                        <td>{mom.get('signal')}</td>
                        <td>{mom.get('metrics', {}).get('return_pct', 0):.2f}</td>
                        <td>{mom.get('metrics', {}).get('sharpe', 0):.2f}</td>
                        <td>{rev.get('signal')}</td>
                        <td>{rev.get('metrics', {}).get('return_pct', 0):.2f}</td>
                        <td>{rev.get('metrics', {}).get('win_rate_pct', 0):.2f}</td>
                    </tr>
            """
        html_content += "</tbody></table></body></html>"
        return HTMLResponse(content=html_content)

    return results


@app.get('/api/indexes')
def api_indexes():
    # Return available index definitions (display name -> list of symbols)
    return INDEXES


def _start_background_scan_blocking(index_name, symbols, live, max_workers=5):
    key = index_name
    with CACHE_LOCK:
        SCAN_CACHE[key] = {
            'running': True,
            'progress': 0,
            'total': len(symbols),
            'results': [],
            'last_updated': None,
        }

    def worker(sym):
        try:
            if live:
                data = __import__('app.data', fromlist=['']).fetch_data(sym, period='1d', interval='5m')
            else:
                data = __import__('app.data', fromlist=['']).fetch_data(sym)
            if data is None or data.empty:
                return {'symbol': sym, 'last_price': None, 'momentum_return': None, 'mean_rev_return': None}
            metrics = __import__('app.backtest', fromlist=['']).run_backtest(data)
            arr = data['Close'].to_numpy()
            last_price = float(arr[-1]) if arr.size else None
            return { 'symbol': sym, 'last_price': last_price, **metrics }
        except Exception as e:
            return { 'symbol': sym, 'last_price': None, 'momentum_return': None, 'mean_rev_return': None }

    # use ThreadPoolExecutor to limit parallelism
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = { ex.submit(worker, s): s for s in symbols }
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            with CACHE_LOCK:
                entry = SCAN_CACHE.get(key)
                if entry is not None:
                    entry['results'].append(res)
                    entry['progress'] = entry.get('progress', 0) + 1
                    entry['last_updated'] = datetime.now(timezone.utc).astimezone().isoformat()

    with CACHE_LOCK:
        entry = SCAN_CACHE.get(key)
        if entry is not None:
            entry['running'] = False


@app.get('/api/scan-start')
def api_scan_start(index: Optional[str] = Query(None), live: Optional[int] = Query(0), max_workers: Optional[int] = Query(5)):
    if index is None:
        index = next(iter(INDEXES.keys()))
    symbols = INDEXES.get(index)
    if symbols is None:
        return JSONResponse([], status_code=400)

    key = index
    with CACHE_LOCK:
        existing = SCAN_CACHE.get(key)
        if existing and existing.get('running'):
            return {'started': False, 'message': 'Scan already running'}

    loop = asyncio.get_event_loop()
    # run blocking scan in default executor so it doesn't block event loop
    loop.run_in_executor(None, _start_background_scan_blocking, index, symbols, bool(live), int(max_workers)) # type: ignore
    return {'started': True}


@app.get('/api/scan-status')
def api_scan_status(index: Optional[str] = Query(None)):
    if index is None:
        index = next(iter(INDEXES.keys()))
    with CACHE_LOCK:
        entry = SCAN_CACHE.get(index)
        if not entry:
            return {'running': False, 'progress': 0, 'total': 0, 'last_updated': None}
        return {'running': bool(entry.get('running')), 'progress': int(entry.get('progress', 0)), 'total': int(entry.get('total', 0)), 'last_updated': entry.get('last_updated')}


@app.get('/api/scan-results')
def api_scan_results(index: Optional[str] = Query(None)):
    if index is None:
        index = next(iter(INDEXES.keys()))
    with CACHE_LOCK:
        entry = SCAN_CACHE.get(index)
        if not entry:
            return {'results': [], 'last_updated': None}
        return {'results': entry.get('results', []), 'last_updated': entry.get('last_updated')}
