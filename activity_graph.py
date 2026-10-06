"""Generate an activity graph SVG (last 31 days of contributions) for a GitHub profile README."""
import datetime as dt
import json
import math
import os
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = os.environ.get("OUT_FILE", "dist/activity-graph.svg")
DAYS = 31

# Colors (match README theme)
BG, LINE, POINT, AREA, TEXT, GRID = "#0d1117", "#1f6feb", "#e6edf3", "#1f6feb", "#58a6ff", "#21262d"


def fetch_days():
    query = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return [(d["date"], d["contributionCount"]) for d in days][-DAYS:]


def build_svg(days):
    W, H = 1200, 420
    L, R, T, B = 80, 40, 70, 70
    pw, ph = W - L - R, H - T - B
    counts = [c for _, c in days]
    step = max(1, math.ceil(max(counts + [1]) / 5))
    top = step * 5

    def x(i):
        return L + pw * i / (len(days) - 1)

    def y(v):
        return T + ph - ph * v / top

    pts = [(x(i), y(c)) for i, c in enumerate(counts)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"M{L},{T + ph} L" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + f" L{L + pw},{T + ph} Z"

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         "<style>"
         ".t{font:600 22px 'Segoe UI',Ubuntu,sans-serif;fill:" + TEXT + "}"
         ".l{font:12px 'Segoe UI',Ubuntu,sans-serif;fill:" + POINT + ";opacity:.75}"
         ".ln{stroke-dasharray:4000;stroke-dashoffset:4000;animation:d 2.5s ease forwards}"
         ".ar{opacity:0;animation:f 1s ease 1.5s forwards}"
         ".pt{opacity:0;animation:f .6s ease 2s forwards}"
         "@keyframes d{to{stroke-dashoffset:0}}@keyframes f{to{opacity:1}}"
         "</style>",
         f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{AREA}" stop-opacity=".45"/>'
         f'<stop offset="1" stop-color="{AREA}" stop-opacity="0"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>',
         f'<text x="{W/2}" y="40" text-anchor="middle" class="t">{USER}\'s Contribution Graph</text>']

    for k in range(6):
        v = step * k
        s.append(f'<line x1="{L}" x2="{L+pw}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="{GRID}"/>')
        s.append(f'<text x="{L-12}" y="{y(v)+4:.1f}" text-anchor="end" class="l">{v}</text>')
    for i, (date, _) in enumerate(days):
        s.append(f'<text x="{x(i):.1f}" y="{T+ph+22}" text-anchor="middle" class="l">{int(date[-2:])}</text>')
    s.append(f'<text x="{W/2}" y="{H-14}" text-anchor="middle" class="l">Days</text>')
    s.append(f'<text x="22" y="{T+ph/2}" text-anchor="middle" class="l" transform="rotate(-90 22 {T+ph/2})">Contributions</text>')

    s.append(f'<path d="{area}" fill="url(#g)" class="ar"/>')
    s.append(f'<polyline points="{line}" fill="none" stroke="{LINE}" stroke-width="3" stroke-linejoin="round" class="ln"/>')
    for (px, py), (date, c) in zip(pts, days):
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{POINT}" class="pt"><title>{date}: {c}</title></circle>')
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_svg(fetch_days()))
    print(f"Wrote {OUT}")
