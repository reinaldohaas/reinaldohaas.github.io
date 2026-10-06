# reinaldohaas.github.io

Portal acadêmico e científico aberto do **Prof. Dr. Reinaldo Haas** (Departamento de Física / UFSC).

Disponível publicamente em: **[https://reinaldohaas.github.io/](https://reinaldohaas.github.io/)**

---

### 🚀 Atualização Automática Contínua

Este portal é mantido sincronizado automaticamente com os repositórios públicos de [@reinaldohaas](https://github.com/reinaldohaas) no GitHub:

- **Script:** [`sync_portal.py`](sync_portal.py) consulta a API pública do GitHub, categoriza os projetos, detecta páginas do GitHub Pages e reconstrói o `index.html`.
- **Automação:** O fluxo de trabalho [`.github/workflows/sync_portal.yml`](.github/workflows/sync_portal.yml) roda diariamente via GitHub Actions (e também pode ser acionado manualmente via `workflow_dispatch`).
- **Execução manual local:**
  ```bash
  python sync_portal.py
  ```
