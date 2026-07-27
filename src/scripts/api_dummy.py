from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Phenobase")


@app.get("/", response_class=HTMLResponse)
async def homepage():
    return (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        "<title>Phenobase</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        "display:flex;justify-content:center;align-items:center;height:100vh;"
        "margin:0;background:#f5f5f5;color:#333}"
        ".container{text-align:center;padding:3rem;background:#fff;"
        "border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.1);max-width:500px}"
        "h1{margin-bottom:.5rem;color:#1a1a1a}"
        ".status{display:inline-block;padding:.3rem .8rem;background:#28a745;"
        "color:#fff;border-radius:20px;font-size:.85rem;font-weight:600}"
        ".info{color:#666;font-size:.9rem;margin-top:1.5rem}"
        "a{color:#0366d6;text-decoration:none}"
        "a:hover{text-decoration:underline}"
        "</style>"
        "</head>"
        "<body>"
        '<div class="container">'
        "<h1>Phenobase</h1>"
        '<span class="status">online</span>'
        '<p style="margin-top:1.5rem;color:#555">'
        "Hello from Phenobase — proxy is working</p>"
        '<div class="info">'
        "<p>Traefik routing verified &#10003;</p>"
        '<p><a href="https://github.com/EOA-team/035_phenobase">'
        "View on GitHub</a></p>"
        "</div>"
        "</div>"
        "</body>"
        "</html>"
    )
