#!/usr/bin/env python3
"""
sync_portal.py - Atualizador Automático do Portal Científico de Reinaldo Haas
Gera o index.html de https://reinaldohaas.github.io/ com base na API pública do GitHub.

Características:
- Apresenta Reinaldo Haas como um pesquisador curioso e multitarefa na física e computação.
- Todos os repositórios em pé de igualdade (sem destaque exclusivo ou favorecimento artificial).
- Coleta automática dos metadados de todos os repositórios públicos de @reinaldohaas.
- Classificação por temas (Aplicações Online, Modelos & Convecção, Hidrologia, Clima & Sol, Ferramentas).
- Busca instantânea e filtros reativos no navegador sem dependências pesadas.
- Pode ser executado localmente ou de tempos em tempos via GitHub Actions.
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Metadados enriquecidos para repositórios (curadoria científica dos projetos de Haas)
CURATED_METADATA = {
    "tarefa-meso": {
        "desc": "Tutorial interativo e diagnóstico físico-termodinâmico de mesoescala comparando regimes convectivos (Kerry Emanuel 1994, Siphon/MetPy e sondagens SBPA).",
        "category": "pages",
        "topics": ["mesoescala", "termodinamica", "metpy", "skew-t", "conveccao"]
    },
    "demos": {
        "desc": "Demonstrações didáticas e visualizações interativas em dinâmica atmosférica, convecção e termodinâmica de fluidos.",
        "category": "pages",
        "topics": ["interativo", "fisica", "fluidos", "educacao"]
    },
    "solar": {
        "desc": "Modelagem de radiação solar em superfície, parametrizações de céu claro, irradiância global/direta e avaliação de potencial fotovoltaico.",
        "category": "pages",
        "topics": ["energia-solar", "radiacao", "fotovoltaico", "clima"]
    },
    "granizo": {
        "desc": "Diagnóstico de tempestades severas granizíferas, microfísica de gelo e índices preditivos com suporte a dados de radar e modelos numéricos.",
        "category": "pages",
        "topics": ["granizo", "tempestades-severas", "radar", "microfisica"]
    },
    "anima_cptec": {
        "desc": "Visualizador e animador automatizado de imagens de satélite meteorológico GOES e produtos operacionais de previsão de tempo.",
        "category": "pages",
        "topics": ["satelites", "goes", "cptec", "previsao-tempo"]
    },
    "hecras_vale": {
        "desc": "Modelagem hidrodinâmica e simulação computacional de inundações na bacia do Rio Itajaí com HEC-RAS 1D/2D.",
        "category": "pages",
        "topics": ["hidrologia", "hec-ras", "inundacoes", "itajai"]
    },
    "itajaim_hecras": {
        "desc": "Aplicação web interativa para visualização de cotas, tempos de trânsito e mapas de inundação da bacia do Itajaí-Mirim.",
        "category": "pages",
        "topics": ["hidrologia", "hec-ras", "inundacoes", "web-map"]
    },
    "indices_climaticos": {
        "desc": "Monitoramento e análise estatística de índices climáticos globais e teleconexões (ENSO, SAM, MJO, Dipolo do Atlântico).",
        "category": "pages",
        "topics": ["clima", "enso", "teleconexoes", "estatistica"]
    },
    "Himalaia_2026": {
        "desc": "Estudos e visualizações de processos meteorológicos orográficos de grande altitude e dinâmica de montanhas nos Himalaias.",
        "category": "pages",
        "topics": ["orografia", "himalaia", "alta-altitude", "meteorologia"]
    },
    "toro-model": {
        "desc": "Modelo de nuvem anelástico 3D θ_ρ investigando a Hipótese de Haas: produção explosiva de gelo secundário (SIP / Hallett-Mossop) e precipitação extrema.",
        "category": "convection",
        "topics": ["microfisica", "sip", "nuvens", "conveccao-profunda", "modelo-3d"]
    },
    "eoce-model": {
        "desc": "Extreme Orographic Convective Events (EOCE) — Simulação 3D com microfísica detalhada para eventos convectivos na Serra Geral (Haas 2024, arXiv:2411.08219).",
        "category": "convection",
        "topics": ["orografia", "microfisica", "serra-geral", "arxiv", "conveccao"]
    },
    "CM1": {
        "desc": "Cloud Model 1 (George Bryan, NCAR): modelo atmosférico não-hidrostático de alta resolução para pesquisas fundamentais de convecção e tempestades.",
        "category": "convection",
        "topics": ["cm1", "modelo-atmosferico", "ncar", "conveccao"]
    },
    "toro-CM1": {
        "desc": "Acoplamento e configurações de casos do modelo CM1 com parametrizações e testes da Hipótese Toró de gelo secundário.",
        "category": "convection",
        "topics": ["cm1", "toro", "gelo-secundario", "simulacao"]
    },
    "era5_to_cm1": {
        "desc": "Conversor e gerador de sondagens e condições iniciais e de contorno a partir da reanálise ERA5 (ECMWF) para o modelo CM1.",
        "category": "convection",
        "topics": ["era5", "cm1", "reanalise", "ecmwf", "fortran"]
    },
    "VCAN": {
        "desc": "Análise dinâmica e termodinâmica de Vórtices Ciclônicos de Altos Níveis (VCAN) e impactos na convecção no Nordeste e América do Sul.",
        "category": "convection",
        "topics": ["vcan", "altos-niveis", "sinotica", "conveccao"]
    },
    "meteorologia-montanhas": {
        "desc": "Caderno interativo e scripts baseados no livro texto didático cobrindo brisas, ondas orográficas, ventos catabáticos e convecção forçada.",
        "category": "tools",
        "topics": ["livro-didatico", "montanhas", "orografia", "ensino"]
    },
    "clima_espacial_amas": {
        "desc": "Pesquisa e processamento de dados sobre clima espacial, ventos solares e monitoramento da Anomalia Magnética do Atlântico Sul (AMAS).",
        "category": "climate",
        "topics": ["clima-espacial", "sol", "amas", "geomagnetismo"]
    },
    "elnino": {
        "desc": "Diagnósticos de anomalias de TSM do Pacífico Equatorial e impactos de episódios de El Niño / La Niña na precipitação do Sul do Brasil.",
        "category": "climate",
        "topics": ["el-nino", "la-nina", "tsm", "clima"]
    },
    "sondagens": {
        "desc": "Ferramentas computacionais e scripts em Python para leitura, controle de qualidade e plotagem de dados de radiossondagens atmosféricas.",
        "category": "convection",
        "topics": ["radiossondagens", "skew-t", "metpy", "qualidade-dados"]
    },
    "como-encontrar-seu-dragao": {
        "desc": "Modelagem computacional e simulação exploratória de fenômenos físicos complexos inspirada em dinâmicas não-lineares.",
        "category": "tools",
        "topics": ["computacao-cientifica", "fisica", "simulacao", "exploracao"]
    },
    "ARPS": {
        "desc": "Advanced Regional Prediction System (ARPS, CAPS/University of Oklahoma): modelo regional não-hidrostático para previsão de tempestades.",
        "category": "convection",
        "topics": ["arps", "modelo-numerico", "fortran", "tempestades"]
    },
    "WRF-IBM_UFSC": {
        "desc": "Adaptações e implementações do modelo Weather Research and Forecasting (WRF) com método de fronteira imersa (IBM) na UFSC.",
        "category": "convection",
        "topics": ["wrf", "ibm", "fronteira-imersa", "ufsc"]
    },
    "scripts_previsao_UFSC": {
        "desc": "Scripts operacionais de download, integração e geração de cartas sinóticas e de mesoescala da previsão de tempo WRF-ICON da UFSC.",
        "category": "tools",
        "topics": ["previsao-operacional", "wrf", "icon", "ufsc"]
    },
    "wrfplot": {
        "desc": "Ferramenta de linha de comando em Python para visualização rápida e geração automatizada de produtos gráficos do modelo WRF.",
        "category": "tools",
        "topics": ["wrf", "python", "cli", "visualizacao"]
    },
    "gis4wrf": {
        "desc": "Extensão para QGIS para pré-processamento, configuração de grades e pós-processamento de simulações do modelo WRF.",
        "category": "tools",
        "topics": ["qgis", "wrf", "gis", "pre-processamento"]
    },
    "era5wrf": {
        "desc": "Rotinas de extração de dados do ERA5 para inicialização de domínios meteorológicos no WRF Preprocessing System (WPS).",
        "category": "tools",
        "topics": ["era5", "wrf", "wps", "automacao"]
    },
    "QCD": {
        "desc": "Cadernos e estudos computacionais em cromodinâmica quântica, teoria de campos e física matemática computacional.",
        "category": "tools",
        "topics": ["fisica-computacional", "qcd", "matematica", "campos"]
    },
    "infraLABMIT": {
        "desc": "Sistemas e infraestrutura computacional do Laboratório de Meteorologia e Instrumentação Térmica (LABMIT - UFSC).",
        "category": "tools",
        "topics": ["labmit", "ufsc", "infraestrutura", "instrumentacao"]
    },
    "Instrumentacao": {
        "desc": "Material didático e scripts de apoio para Instrumentação Meteorológica e Técnicas de Observação Atmosférica.",
        "category": "tools",
        "topics": ["instrumentacao", "sensores", "ensino", "observacao"]
    },
    "wrf_tutorial": {
        "desc": "Tutoriais práticos e cadernos passo a passo para compilação, configuração de namelist e execução do WRF e WPS.",
        "category": "tools",
        "topics": ["wrf", "tutorial", "namelist", "ensino"]
    },
    "regrid": {
        "desc": "Conjunto de rotinas e contêiner Docker para interpolação e regridding de dados da grade triangular/icosaédrica do ICON para lat/lon.",
        "category": "tools",
        "topics": ["icon", "regrid", "docker", "dwd"]
    },
    "drone_lidar": {
        "desc": "Processamento de nuvens de pontos LiDAR e fotogrametria aérea por drones para mapeamento topográfico e modelagem orográfica.",
        "category": "tools",
        "topics": ["lidar", "drones", "topografia", "sensoriamento-remoto"]
    },
    "Awesome-Physics-aware-Generation": {
        "desc": "Curadoria de métodos de inteligência artificial informados por leis físicas (PINNs, modelos generativos guiados por física).",
        "category": "tools",
        "topics": ["ia-fisica", "pinns", "generative-ai", "machine-learning"]
    },
    "cmip6-temperature-demo": {
        "desc": "Demonstração e análise de modelos climáticos globais do CMIP6 em ambiente de computação em nuvem.",
        "category": "climate",
        "topics": ["cmip6", "clima-global", "cloud", "ipcc"]
    },
    "opsd": {
        "desc": "Tratamento de séries temporais de dados abertos de sistemas de energia e geração renovável.",
        "category": "climate",
        "topics": ["energia-renovavel", "series-temporais", "dados-abertos"]
    },
    "view-georeferenced-jpg": {
        "desc": "Visualizador web leve para imagens JPG georreferenciadas com suporte a projeções geográficas.",
        "category": "tools",
        "topics": ["georreferenciamento", "web-viewer", "gis"]
    }
}

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "Jupyter Notebook": "#DA5B0B",
    "Fortran": "#4d41b1",
    "HTML": "#e34c26",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "TeX": "#3D6117",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Outro": "#8b949e"
}

CATEGORY_INFO = {
    "all": {"label": "Todos os Repositórios", "icon": "📦"},
    "pages": {"label": "Páginas & Apps Online", "icon": "🌐"},
    "convection": {"label": "Modelos & Convecção", "icon": "🌪️"},
    "hydrology": {"label": "Hidrologia & HEC-RAS", "icon": "🌊"},
    "climate": {"label": "Clima, Sol & Satélites", "icon": "☀️"},
    "tools": {"label": "Ferramentas & Ensino", "icon": "💻"}
}


def fetch_repos_via_gh():
    """Tenta obter os repositórios via gh CLI."""
    try:
        cmd = [
            "gh", "repo", "list", "reinaldohaas", "--limit", "100",
            "--json", "name,description,pushedAt,updatedAt,homepageUrl,primaryLanguage,isFork,stargazerCount,forkCount,repositoryTopics,url,visibility"
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except Exception:
        return None


def fetch_repos_via_api():
    """Fallback: obtém os repositórios diretamente via API HTTP do GitHub."""
    url = "https://api.github.com/users/reinaldohaas/repos?per_page=100&sort=pushed"
    req = urllib.request.Request(url, headers={"User-Agent": "reinaldohaas-portal-updater"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # Normalizar campos
            normalized = []
            for r in data:
                normalized.append({
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "pushedAt": r.get("pushed_at"),
                    "updatedAt": r.get("updated_at"),
                    "homepageUrl": r.get("homepage"),
                    "primaryLanguage": {"name": r.get("language")} if r.get("language") else None,
                    "isFork": r.get("fork", False),
                    "stargazerCount": r.get("stargazers_count", 0),
                    "forkCount": r.get("forks_count", 0),
                    "repositoryTopics": [{"name": t} for t in r.get("topics", [])] if r.get("topics") else None,
                    "url": r.get("html_url"),
                    "visibility": "PUBLIC" if not r.get("private") else "PRIVATE",
                    "has_pages": r.get("has_pages", False)
                })
            return normalized
    except Exception as e:
        print(f"Erro na requisição à API do GitHub: {e}", file=sys.stderr)
        return []


def determine_category(repo, has_pages):
    name = repo["name"].lower()
    curated = CURATED_METADATA.get(repo["name"], {})
    if "category" in curated:
        return curated["category"]

    if has_pages and repo["name"] != "reinaldohaas.github.io":
        return "pages"

    if any(k in name for k in ["hec", "ras", "hidro", "inund", "ita", "taquari"]):
        return "hydrology"

    if any(k in name for k in ["cm1", "toro", "eoce", "convec", "wrf", "arps", "granizo", "sondag", "vcan", "shear"]):
        return "convection"

    if any(k in name for k in ["solar", "clima", "nino", "satelit", "cptec", "goes", "cmip6", "opsd", "amas"]):
        return "climate"

    return "tools"


def format_iso_date(dt_str):
    if not dt_str:
        return "Data n/d"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return dt_str[:10]


def build_repo_cards(repos):
    cards_html = []
    
    # Repositórios com GitHub Pages conhecidos
    KNOWN_PAGES = {
        "tarefa-meso", "demos", "solar", "granizo", "anima_cptec",
        "hecras_vale", "itajaim_hecras", "indices_climaticos", "Himalaia_2026"
    }

    for r in repos:
        name = r["name"]
        if name in ["reinaldohaas.github.io", "reinaldohaas"]:
            # Não listar o próprio repositório de configuração nem o repositório raiz como card comum
            continue

        url = r.get("url") or f"https://github.com/reinaldohaas/{name}"
        lang_obj = r.get("primaryLanguage")
        lang = lang_obj["name"] if lang_obj else "Outro"
        lang_color = LANGUAGE_COLORS.get(lang, "#8b949e")

        has_pages = r.get("has_pages") or (name in KNOWN_PAGES)
        pages_url = f"https://reinaldohaas.github.io/{name}/" if has_pages else None
        homepage = r.get("homepageUrl")

        # Prioridade para descrição
        curated = CURATED_METADATA.get(name, {})
        desc = curated.get("desc") or r.get("description") or "Projeto e experimentos em física computacional e ciência de dados."
        
        # Categoria
        cat = determine_category(r, has_pages)
        cat_badge = CATEGORY_INFO.get(cat, CATEGORY_INFO["tools"])

        # Tópicos
        topics = []
        if r.get("repositoryTopics"):
            topics = [t["name"] for t in r["repositoryTopics"]]
        elif "topics" in curated:
            topics = curated["topics"]

        date_str = format_iso_date(r.get("pushedAt") or r.get("updatedAt"))
        stars = r.get("stargazerCount", 0)
        forks = r.get("forkCount", 0)

        # Ações do cartão (sem qualquer destaque artificial a um projeto isolado)
        action_buttons = []
        if pages_url:
            action_buttons.append(f"""
              <a href="{pages_url}" target="_blank" rel="noopener noreferrer" class="card-btn-action btn-online">
                <span>🌐 Aplicação Online</span>
              </a>
            """)
        elif homepage and homepage.startswith("http"):
            action_buttons.append(f"""
              <a href="{homepage}" target="_blank" rel="noopener noreferrer" class="card-btn-action btn-link">
                <span>🔗 Artigo / Site</span>
              </a>
            """)

        action_buttons.append(f"""
          <a href="{url}" target="_blank" rel="noopener noreferrer" class="card-btn-action btn-github">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
            <span>GitHub ↗</span>
          </a>
        """)

        actions_html = "".join(action_buttons)

        tags_html = "".join([f'<span class="repo-tag">#{t}</span>' for t in topics[:4]])

        stars_html = f'<span class="repo-meta-item" title="Estrelas">⭐ {stars}</span>' if stars > 0 else ""
        forks_html = f'<span class="repo-meta-item" title="Forks">🍴 {forks}</span>' if forks > 0 else ""

        cards_html.append(f"""
        <article class="repo-card" data-category="{cat}" data-name="{name.lower()}" data-lang="{lang.lower()}" data-desc="{desc.lower()}">
          <div class="card-inner">
            <div class="card-header">
              <div class="card-badge cat-{cat}">
                <span>{cat_badge['icon']}</span>
                <span>{cat_badge['label']}</span>
              </div>
              <span class="card-date" title="Último commit">Atualizado {date_str}</span>
            </div>
            
            <h3 class="card-title">
              <a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a>
            </h3>

            <p class="card-description">{desc}</p>

            <div class="card-tags">
              {tags_html}
            </div>

            <div class="card-footer">
              <div class="card-meta">
                <span class="lang-indicator">
                  <span class="lang-dot" style="background-color: {lang_color}"></span>
                  <span class="lang-name">{lang}</span>
                </span>
                {stars_html}
                {forks_html}
              </div>

              <div class="card-actions">
                {actions_html}
              </div>
            </div>
          </div>
        </article>
        """)

    return "\n".join(cards_html)


def generate_full_html(repos):
    now_utc = datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")
    total_repos = len([r for r in repos if r["name"] not in ["reinaldohaas.github.io", "reinaldohaas"]])
    pages_count = sum(1 for r in repos if r.get("has_pages") or r["name"] in [
        "tarefa-meso", "demos", "solar", "granizo", "anima_cptec",
        "hecras_vale", "itajaim_hecras", "indices_climaticos", "Himalaia_2026"
    ])
    
    cards_html = build_repo_cards(repos)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reinaldo Haas | Pesquisador Curioso & Multitarefa</title>
  <meta name="description" content="Portal científico e repositórios abertos do Prof. Dr. Reinaldo Haas (UFSC). Modelagem numérica da atmosfera, dinâmica de fluidos, convecção severa, microfísica, hidrologia e energia solar.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-page: #0a0d14;
      --bg-surface: #111622;
      --bg-card: rgba(18, 24, 38, 0.85);
      --bg-card-hover: rgba(26, 34, 52, 0.95);
      --border: rgba(255, 255, 255, 0.08);
      --border-hover: rgba(56, 189, 248, 0.35);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --accent-cyan: #38bdf8;
      --accent-blue: #3b82f6;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-purple: #a855f7;
      --accent-rose: #f43f5e;
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-sans);
      background-color: var(--bg-page);
      color: var(--text-main);
      min-height: 100vh;
      line-height: 1.6;
      background-image: 
        radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.12) 0px, transparent 55%),
        radial-gradient(at 100% 10%, rgba(99, 102, 241, 0.10) 0px, transparent 50%),
        radial-gradient(at 50% 60%, rgba(16, 185, 129, 0.06) 0px, transparent 60%);
      background-attachment: fixed;
    }}

    .container {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 3rem 1.5rem 5rem;
    }}

    /* HEADER DA APRESENTAÇÃO */
    header.hero {{
      text-align: center;
      padding: 3rem 1rem 3.5rem;
      max-width: 900px;
      margin: 0 auto;
    }}

    .badge-hero {{
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.45rem 1.1rem;
      border-radius: 9999px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      color: var(--accent-cyan);
      font-size: 0.85rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      margin-bottom: 1.5rem;
    }}

    .badge-hero::before {{
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-cyan);
      box-shadow: 0 0 10px var(--accent-cyan);
    }}

    h1.hero-title {{
      font-size: 3.1rem;
      font-weight: 800;
      letter-spacing: -0.035em;
      line-height: 1.12;
      margin-bottom: 0.85rem;
      background: linear-gradient(135deg, #ffffff 30%, #cbd5e1 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .hero-subtitle {{
      font-size: 1.35rem;
      font-weight: 600;
      color: var(--accent-cyan);
      margin-bottom: 1.25rem;
    }}

    .hero-affiliation {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      font-size: 0.96rem;
      color: #cbd5e1;
      margin-bottom: 1.5rem;
    }}

    .hero-bio {{
      font-size: 1.05rem;
      color: var(--text-muted);
      line-height: 1.7;
      margin: 0 auto 2rem;
      max-width: 820px;
    }}

    .hero-links {{
      display: flex;
      justify-content: center;
      gap: 0.85rem;
      flex-wrap: wrap;
    }}

    .btn-header {{
      display: inline-flex;
      align-items: center;
      gap: 0.55rem;
      padding: 0.65rem 1.35rem;
      border-radius: 8px;
      font-size: 0.92rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
      cursor: pointer;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.04);
      color: var(--text-main);
      backdrop-filter: blur(8px);
    }}

    .btn-header:hover {{
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.25);
      transform: translateY(-2px);
    }}

    .btn-header.github-btn {{
      background: #24292f;
      border-color: #3b4252;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }}

    .btn-header.github-btn:hover {{
      background: #2f363d;
      border-color: #4c566a;
    }}

    /* BARRA DE ESTATÍSTICAS */
    .stats-bar {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.25rem;
      margin: 2rem 0 3.5rem;
    }}

    .stat-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      transition: all 0.2s ease;
    }}

    .stat-card:hover {{
      border-color: var(--border-hover);
      transform: translateY(-2px);
    }}

    .stat-number {{
      font-size: 1.9rem;
      font-weight: 800;
      color: #ffffff;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .stat-label {{
      font-size: 0.84rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-weight: 600;
    }}

    /* SEÇÃO DE CONTROLES: BUSCA & FILTROS */
    .controls-wrapper {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.4rem;
      margin-bottom: 2.5rem;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}

    .search-row {{
      display: flex;
      gap: 1rem;
      margin-bottom: 1.2rem;
      flex-wrap: wrap;
    }}

    .search-input-box {{
      flex: 1;
      min-width: 280px;
      position: relative;
    }}

    .search-input-box input {{
      width: 100%;
      padding: 0.85rem 1rem 0.85rem 2.8rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(10, 13, 20, 0.7);
      color: #ffffff;
      font-size: 0.95rem;
      font-family: var(--font-sans);
      outline: none;
      transition: border-color 0.2s ease;
    }}

    .search-input-box input:focus {{
      border-color: var(--accent-cyan);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15);
    }}

    .search-icon {{
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-dim);
      font-size: 1.1rem;
      pointer-events: none;
    }}

    .sort-box select {{
      padding: 0.85rem 1.2rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(10, 13, 20, 0.7);
      color: var(--text-main);
      font-size: 0.92rem;
      font-family: var(--font-sans);
      outline: none;
      cursor: pointer;
    }}

    .filter-pills {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .filter-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.45rem 0.9rem;
      border-radius: 7px;
      font-size: 0.85rem;
      font-weight: 600;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .filter-pill:hover {{
      color: var(--text-main);
      border-color: rgba(255, 255, 255, 0.2);
    }}

    .filter-pill.active {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--accent-cyan);
      color: #ffffff;
    }}

    .results-info {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
      padding-top: 0.85rem;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      font-size: 0.84rem;
      color: var(--text-dim);
    }}

    /* GRID DE REPOSITÓRIOS - EQUIDADE TOTAL */
    .repo-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 1.5rem;
    }}

    .repo-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}

    .repo-card:hover {{
      background: var(--bg-card-hover);
      border-color: var(--border-hover);
      transform: translateY(-4px);
      box-shadow: 0 14px 30px rgba(0, 0, 0, 0.4);
    }}

    .card-inner {{
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      height: 100%;
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.85rem;
      gap: 0.5rem;
    }}

    .card-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .cat-pages {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
    .cat-convection {{ background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }}
    .cat-hydrology {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }}
    .cat-climate {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .cat-tools {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}

    .card-date {{
      font-size: 0.78rem;
      color: var(--text-dim);
      font-family: var(--font-mono);
    }}

    .card-title {{
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 0.6rem;
      line-height: 1.3;
    }}

    .card-title a {{
      color: #ffffff;
      text-decoration: none;
      transition: color 0.2s ease;
    }}

    .card-title a:hover {{
      color: var(--accent-cyan);
    }}

    .card-description {{
      color: var(--text-muted);
      font-size: 0.91rem;
      line-height: 1.6;
      margin-bottom: 1.2rem;
      flex-grow: 1;
    }}

    .card-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 1.25rem;
    }}

    .repo-tag {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.06);
      color: var(--text-dim);
      font-size: 0.74rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-family: var(--font-mono);
    }}

    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 1rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    .card-meta {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.82rem;
      color: var(--text-dim);
    }}

    .lang-indicator {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      color: var(--text-muted);
      font-weight: 600;
    }}

    .lang-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
    }}

    .card-actions {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-left: auto;
    }}

    .card-btn-action {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
    }}

    .btn-online {{
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    .btn-online:hover {{
      background: rgba(56, 189, 248, 0.25);
      border-color: var(--accent-cyan);
      color: #ffffff;
    }}

    .btn-link {{
      background: rgba(168, 85, 247, 0.15);
      color: var(--accent-purple);
      border: 1px solid rgba(168, 85, 247, 0.3);
    }}

    .btn-link:hover {{
      background: rgba(168, 85, 247, 0.25);
      color: #ffffff;
    }}

    .btn-github {{
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .btn-github:hover {{
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
      border-color: rgba(255, 255, 255, 0.25);
    }}

    /* RODAPÉ */
    footer {{
      margin-top: 5rem;
      padding-top: 2.5rem;
      border-top: 1px solid var(--border);
      text-align: center;
      color: var(--text-dim);
      font-size: 0.88rem;
    }}

    footer a {{
      color: var(--accent-cyan);
      text-decoration: none;
    }}

    footer a:hover {{
      text-decoration: underline;
    }}

    .auto-sync-notice {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      margin-top: 0.75rem;
      font-size: 0.82rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.03);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      border: 1px solid var(--border);
    }}

    @media (max-width: 768px) {{
      h1.hero-title {{ font-size: 2.2rem; }}
      .hero-subtitle {{ font-size: 1.15rem; }}
      .container {{ padding: 1.5rem 1rem; }}
      .repo-grid {{ grid-template-columns: 1fr; }}
      .search-row {{ flex-direction: column; }}
      .sort-box select {{ width: 100%; }}
    }}
  </style>
</head>
<body>

  <div class="container">
    
    <!-- APRESENTAÇÃO PESSOAL & PERFIL DO PESQUISADOR -->
    <header class="hero">
      <div class="badge-hero">Física da Terra & Computação Científica</div>
      <h1 class="hero-title">Reinaldo Haas</h1>
      <div class="hero-subtitle">Pesquisador Curioso & Multitarefa</div>
      
      <div class="hero-affiliation">
        <span>📍 Departamento de Física — UFSC (Florianópolis, Brasil)</span>
        <span>•</span>
        <span>🌪️ Meteorologia Teórica, Modelagem & Ciências Ambientais</span>
      </div>

      <p class="hero-bio">
        Atuo na interface entre física atmosférica, convecção profunda severa, microfísica de nuvens, modelagem hidrodinâmica fluvial, estimativa de radiação solar e ferramentas computacionais abertas. Movido por curiosidade científica constante e postura multitarefa, compartilho abaixo o ecossistema ativo de códigos, modelos numéricos, visualizadores e cadernos de pesquisa desenvolvidos no GitHub.
      </p>

      <div class="hero-links">
        <a href="https://github.com/reinaldohaas" target="_blank" rel="noopener noreferrer" class="btn-header github-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          <span>Perfil no GitHub (@reinaldohaas)</span>
        </a>
        <a href="http://lattes.cnpq.br/4422247184297121" target="_blank" rel="noopener noreferrer" class="btn-header">
          <span>📜 Currículo Lattes</span>
        </a>
        <a href="mailto:reinaldo.haas@ufsc.br" class="btn-header">
          <span>✉️ Contato Institucional</span>
        </a>
      </div>
    </header>

    <!-- BARRA DE ESTATÍSTICAS AO VIVO -->
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-number">{total_repos}</div>
        <div class="stat-label">Repositórios Públicos</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{pages_count}</div>
        <div class="stat-label">Páginas & Aplicações Online</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">5+</div>
        <div class="stat-label">Modelos Numéricos & Física 3D</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">100%</div>
        <div class="stat-label">Código Aberto & Reprodutível</div>
      </div>
    </div>

    <!-- CONTROLES INTERATIVOS: BUSCA E FILTROS -->
    <section class="controls-wrapper">
      <div class="search-row">
        <div class="search-input-box">
          <span class="search-icon">🔍</span>
          <input type="text" id="searchInput" placeholder="Pesquisar projetos, modelos, ferramentas ou temas..." oninput="filterAndRender()">
        </div>
        <div class="sort-box">
          <select id="sortSelect" onchange="filterAndRender()">
            <option value="recent">Ordenar por: Mais Recentes (Commit)</option>
            <option value="name">Ordenar por: Nome (A-Z)</option>
          </select>
        </div>
      </div>

      <div class="filter-pills" id="filterPills">
        <button class="filter-pill active" data-filter="all" onclick="setCategory('all')">📦 Todos ({total_repos})</button>
        <button class="filter-pill" data-filter="pages" onclick="setCategory('pages')">🌐 Páginas & Apps Online ({pages_count})</button>
        <button class="filter-pill" data-filter="convection" onclick="setCategory('convection')">🌪️ Modelos & Convecção</button>
        <button class="filter-pill" data-filter="hydrology" onclick="setCategory('hydrology')">🌊 Hidrologia & HEC-RAS</button>
        <button class="filter-pill" data-filter="climate" onclick="setCategory('climate')">☀️ Clima, Sol & Satélites</button>
        <button class="filter-pill" data-filter="tools" onclick="setCategory('tools')">💻 Ferramentas & Ensino</button>
      </div>

      <div class="results-info">
        <span id="resultsCount">Exibindo todos os repositórios</span>
        <span>Repositórios sincronizados diretamente do GitHub</span>
      </div>
    </section>

    <!-- GRID DE REPOSITÓRIOS CIENTÍFICOS (TODOS EM IGUALDADE) -->
    <main class="repo-grid" id="repoGrid">
      {cards_html}
    </main>

    <!-- RODAPÉ E SINCRONIZAÇÃO AUTOMÁTICA -->
    <footer>
      <p>© {datetime.now().year} Reinaldo Haas • Departamento de Física / CFM — UFSC</p>
      <div class="auto-sync-notice">
        <span>🔄 Atualizado automaticamente em <strong>{now_utc}</strong></span>
        <span>•</span>
        <span>Gerado via <code>sync_portal.py</code></span>
      </div>
      <p style="margin-top: 0.75rem; font-size: 0.82rem;">
        Hospedado no <a href="https://pages.github.com/" target="_blank" rel="noopener noreferrer">GitHub Pages</a> via repositório <a href="https://github.com/reinaldohaas/reinaldohaas.github.io" target="_blank" rel="noopener noreferrer">reinaldohaas.github.io</a>.
      </p>
    </footer>

  </div>

  <script>
    let currentCategory = 'all';

    function setCategory(cat) {{
      currentCategory = cat;
      document.querySelectorAll('.filter-pill').forEach(btn => {{
        if (btn.dataset.filter === cat) {{
          btn.classList.add('active');
        }} else {{
          btn.classList.remove('active');
        }}
      }});
      filterAndRender();
    }}

    function filterAndRender() {{
      const query = document.getElementById('searchInput').value.trim().toLowerCase();
      const sortMode = document.getElementById('sortSelect').value;
      const grid = document.getElementById('repoGrid');
      const cards = Array.from(grid.querySelectorAll('.repo-card'));

      let visibleCount = 0;

      cards.forEach(card => {{
        const cat = card.dataset.category;
        const name = card.dataset.name;
        const lang = card.dataset.lang;
        const desc = card.dataset.desc;

        const matchCat = (currentCategory === 'all') || (cat === currentCategory);
        const matchQuery = !query || name.includes(query) || desc.includes(query) || lang.includes(query);

        if (matchCat && matchQuery) {{
          card.style.display = 'flex';
          visibleCount++;
        }} else {{
          card.style.display = 'none';
        }}
      }});

      // Ordenação
      if (sortMode === 'name') {{
        cards.sort((a, b) => a.dataset.name.localeCompare(b.dataset.name));
        cards.forEach(c => grid.appendChild(c));
      }}

      // Contador de resultados
      const countEl = document.getElementById('resultsCount');
      if (countEl) {{
        countEl.textContent = `Exibindo ${{visibleCount}} de ${{cards.length}} repositórios`;
      }}
    }}
  </script>
</body>
</html>
"""
    return html_content


def main():
    print("=== Sincronizador Automático do Portal GitHub (@reinaldohaas) ===")
    repos = fetch_repos_via_gh()
    if not repos:
        print("gh CLI indisponível ou falhou. Tentando API HTTP pública...")
        repos = fetch_repos_via_api()

    if not repos:
        print("Falha ao obter repositórios. Abortando sem alterar index.html.", file=sys.stderr)
        sys.exit(1)

    print(f"Repositórios coletados com sucesso: {len(repos)}")

    # Filtrar apenas repositórios públicos
    public_repos = [r for r in repos if r.get("visibility") != "PRIVATE"]
    print(f"Repositórios públicos a exibir: {len(public_repos)}")

    html = generate_full_html(public_repos)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Arquivo index.html gerado com sucesso!")


if __name__ == "__main__":
    main()
