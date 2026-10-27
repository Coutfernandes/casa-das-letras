# Casa das Letras

Casa de leilões online de livros raros, com lances em tempo real e histórico de lances auditável e à prova de adulteração.

Projeto desenvolvido para o teste técnico **Elite Dev** da Verzel.

> 🚧 Em desenvolvimento. Este README será completado ao longo do projeto.

## Stack

- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Backend:** Django + Django REST Framework + Django Channels
- **Banco de dados:** PostgreSQL
- **Tempo real:** WebSocket com Redis
- **Catálogo de livros:** [Open Library API](https://openlibrary.org/dev/docs/api/search)

## Estrutura

- `backend/`: API em Django
- `frontend/`: aplicação React
- `docs/`: documentação do projeto

## Deploy

- **Backend:** Render, descrito em `render.yaml` (build em `backend/build.sh`).
- **Frontend:** Vercel, configurado em `frontend/vercel.json`.

> O `frontend/vercel.json` repassa `/api/*` para `https://casa-das-letras.onrender.com`, um endereço de exemplo.
> Troque pelo endereço real do serviço no Render antes do primeiro deploy na Vercel.
> A regra de `/api` vem antes da regra que manda o resto para o `index.html`.
