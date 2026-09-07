from weasyprint import HTML
from jinja2 import Template

_TEMPLATE = Template("""
<html><body style="font-family: sans-serif;">
  <h1>Forest Health Report</h1>
  <h2>{{ region_name }}</h2>
  <p>Assessed: {{ checked_on }}</p>
  <table border="1" cellpadding="6">
    <tr><th>Index</th><th>Score</th></tr>
    <tr><td>Greenness (NDVI)</td><td>{{ greenness }}</td></tr>
    <tr><td>Burn severity (NBR)</td><td>{{ burn_severity }}</td></tr>
    <tr><td>Moisture stress (NDMI)</td><td>{{ moisture_stress }}</td></tr>
    <tr><td>Canopy density (EVI)</td><td>{{ canopy_density }}</td></tr>
  </table>
  <p><b>Status:</b> {{ status }}</p>
</body></html>
""")

def build_report_pdf(region_name: str, result: dict) -> bytes:
    html = _TEMPLATE.render(region_name=region_name, **result)
    return HTML(string=html).write_pdf()