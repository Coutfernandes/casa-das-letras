# Casa das Letras

Casa de leilões online de livros raros, com o catálogo vindo da [Open Library](https://openlibrary.org/developers/api). Leiloeiros publicam lotes, licitantes dão lances ao vivo, e qualquer pessoa, mesmo sem login, pode auditar o histórico de lances de um lote e confirmar que ninguém o adulterou.

Projeto feito para o teste técnico **Elite Dev** da Verzel.

| | |
| --- | --- |
| **Site** | https://casa-das-letras.vercel.app |
| **API (vitrine)** | https://casa-das-letras.onrender.com/api/lots/ |
| **Como funciona a auditoria** | https://casa-das-letras.vercel.app/auditoria |

## Sumário

1. [O projeto, o link e as contas de teste](#1-o-projeto-o-link-e-as-contas-de-teste)
2. [Como rodar com Docker](#2-como-rodar-com-docker)
3. [Como rodar sem Docker (Windows)](#3-como-rodar-sem-docker-windows)
4. [Variáveis de ambiente](#4-variáveis-de-ambiente)
5. [Decisões técnicas](#5-decisões-técnicas)
6. [Como verificar a auditoria](#6-como-verificar-a-auditoria)
7. [Limitações conhecidas](#7-limitações-conhecidas)
8. [Como rodar os testes](#8-como-rodar-os-testes)
9. [Como usei IA](#9-como-usei-ia)

---

## 1. O projeto, o link e as contas de teste

### Contas de teste

Todas usam a senha **`SenhaSegura123!`**. São contas só de demonstração, criadas pelo comando `seed_data`.

| Conta | Papel | O que dá para testar |
| --- | --- | --- |
| `leiloeiro@casadasletras.com` | Leiloeiro | Buscar livros na Open Library, criar e cancelar lotes, ver os resultados e o total recebido |
| `licitante1@casadasletras.com` | Licitante (Ana Souza) | Lidera o *Dom Casmurro* e já arrematou *Memórias Póstumas de Brás Cubas* |
| `licitante2@casadasletras.com` | Licitante (Bruno Lima) | Lidera *O Guarani* e foi superado no *Dom Casmurro* |

Também dá para **criar uma conta nova** na tela de entrar, escolhendo o papel.

### O que o seed cria

| Lote | Situação |
| --- | --- |
| *Memórias Póstumas de Brás Cubas* | Encerrado, com vencedor e comprovante |
| *Dom Casmurro* | Ao vivo, com 3 lances alternados entre os dois licitantes |
| *O Guarani* | Ao vivo, com 1 lance |
| *O Cortiço* | Ao vivo, sem lances (bom para testar o primeiro lance) |
| *Os Sertões* | Agendado |

Cada licitante começa com R$ 5.000,00 de depósito. As datas são relativas ao momento em que o seed roda: os lotes ao vivo terminam 10 dias depois.

### Um roteiro rápido

1. Sem login, abra a vitrine e clique em **Auditar histórico** em qualquer lote.
2. Entre com `licitante1` numa janela e com `licitante2` numa janela anônima, e abra a sala do *Dom Casmurro* nas duas.
3. Dê um lance com o `licitante2` (o botão **Usar mínimo** preenche o valor). A outra janela mostra **"Você foi superado"** na hora, sem recarregar, e o valor volta ao disponível da carteira.
4. Com o `licitante1`, abra **Meus arremates → Vencidos → Ver comprovante**.
5. Com o `leiloeiro`, abra o **Painel**.

### Funcionalidades

- **Papéis:** leiloeiro e licitante, com permissões por papel em cada rota.
- **Vitrine:** lotes ao vivo, agendados e encerrados, com busca por título ou autor e filtro por faixa de valor. Os cancelados não aparecem.
- **Painel do leiloeiro:** busca na Open Library, criação de lote (com descrição do exemplar), cancelamento de lote sem lances, resultados e total recebido.
- **Sala ao vivo (WebSocket):** lance atual, histórico, contagem regressiva sincronizada com o relógio do servidor, aviso de "ganhando" ou "superado" e reconexão automática.
- **Carteira:** saldo total, comprometido e disponível, depósito simulado e extrato.
- **Meus arremates:** lotes com lance e lotes vencidos, com comprovante.
- **Comprovante público:** abre por link, sem login, com o pseudônimo do vencedor e o hash do último lance.
- **Auditoria pública:** recalcula a cadeia de hashes, confere a âncora assinada e a cópia externa, e diz exatamente o que foi adulterado e em qual lance.
- **Tema claro e escuro.**

### Stack

| Camada | Tecnologia |
| --- | --- |
| Frontend | React + Vite + TypeScript + Tailwind, na Vercel |
| Backend | Django 5.2 + Django REST Framework + Django Channels (Daphne, ASGI), no Render |
| Banco | PostgreSQL (Neon em produção; PostgreSQL 18 local no desenvolvimento) |
| Redis | Upstash, para a cópia externa das âncoras da auditoria |
| Agendador | cron-job.org, chamando a rota protegida `POST /api/internal/tick/` a cada minuto |

## 2. Como rodar com Docker

O projeto **não tem Docker Compose**. O Docker não funcionou no computador de desenvolvimento (o WSL 2 não conseguia criar a máquina virtual), então o projeto foi feito e testado rodando direto no Windows, e a produção usa serviços gerenciados. O Docker Compose era um opcional da especificação e ficou de fora para garantir o núcleo obrigatório no prazo.

## 3. Como rodar sem Docker (Windows)

Pré-requisitos: **Python 3.12**, **Node.js 20 ou mais novo** e **PostgreSQL** (testado com o 18). O Redis é opcional no desenvolvimento.

### Backend

No PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Crie um banco vazio no PostgreSQL e edite o `backend/.env`:

- `DATABASE_URL`: o endereço do seu banco local, por exemplo `postgres://usuario:senha@localhost:5432/casa_das_letras`;
- `DJANGO_SECRET_KEY` e `ALIAS_SECRET`: gere cada um com `python -c "import secrets; print(secrets.token_urlsafe(50))"`;
- `AUDIT_SIGNING_KEY`: gere com `python manage.py generate_signing_key` e cole a linha impressa.

Depois:

```powershell
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

O backend sobe em `http://localhost:8000`, já com o WebSocket (o Daphne entra no lugar do servidor padrão do Django).

### Frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`. O Vite repassa `/api`, `/ws`, `/media` e `/static` para o backend, então o navegador vê um site só.

### Comandos úteis

| Comando | O que faz |
| --- | --- |
| `python manage.py seed_data --reset` | Apaga lotes, lances, carteiras e comprovantes e recria os dados de exemplo |
| `python manage.py close_due_lots` | Liquida os lotes que já terminaram (em produção, o cron faz isso a cada minuto) |
| `python manage.py generate_signing_key` | Gera uma chave Ed25519 nova para a `AUDIT_SIGNING_KEY` |
| `python manage.py sign_missing_anchors` | Assina a âncora de lotes antigos que ainda não tinham assinatura (só se a cadeia estiver íntegra) |

## 4. Variáveis de ambiente

Os modelos ficam em `backend/.env.example` e `frontend/.env.example`. Nenhum valor real vai para o repositório.

### Backend

| Variável | Obrigatória | O que é |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Sim | Chave do Django (sessões e cookies) |
| `ALIAS_SECRET` | Sim | Segredo do HMAC que gera os pseudônimos. Não troque depois de ter usuários |
| `DATABASE_URL` | Sim | Endereço do PostgreSQL. No Neon, a conexão direta (sem `-pooler`) com `?sslmode=require` |
| `AUDIT_SIGNING_KEY` | Sim | Chave privada Ed25519 que assina as âncoras. Trocar invalida as assinaturas existentes |
| `DJANGO_DEBUG` | Não | `True` no desenvolvimento. O padrão é `False` (o lado seguro) |
| `DJANGO_ALLOWED_HOSTS` | Não | Domínios aceitos. No Render, o domínio entra sozinho pelo `RENDER_EXTERNAL_HOSTNAME` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Sim em produção | O endereço do frontend (ex.: `https://casa-das-letras.vercel.app`). Também libera a origem do WebSocket |
| `REDIS_URL` | Não | Redis da cópia externa das âncoras (`rediss://` no Upstash). Vazio desliga a cópia, e a auditoria mostra um aviso |
| `CRON_SECRET` | Não | Senha da rota `POST /api/internal/tick/`. Vazio desliga a rota |
| `COVER_DOWNLOAD` | Não | `True` baixa a capa para `media/`. `False` (produção) usa o endereço da Open Library |
| `DRF_NUM_PROXIES` | Não | Quantos proxies ficam na frente do Django, para o limite da auditoria contar o IP certo |
| `DJANGO_CONN_MAX_AGE` | Não | Reaproveitamento de conexões com o banco. O padrão é `0`, como o Django recomenda sob ASGI |

### Frontend

| Variável | O que é |
| --- | --- |
| `VITE_WS_URL` | Endereço do WebSocket em produção (ex.: `wss://casa-das-letras.onrender.com`). Vazio no desenvolvimento |

## 5. Decisões técnicas

### Mesma origem para os cookies

O frontend fica na Vercel, que repassa `/api/*` para o backend no Render (`frontend/vercel.json`). Para o navegador, o site e a API são do mesmo domínio, então o login por **sessão do Django** (cookie HttpOnly, SameSite Lax, Secure em produção, com proteção CSRF) funciona sem configurar CORS. Escolhi sessão em vez de JWT porque há um único frontend no mesmo domínio: o logout encerra o acesso na hora e não precisa de biblioteca extra.

A Vercel não repassa WebSocket, então a sala conecta direto no backend (`wss://...onrender.com`). Para identificar quem está conectado sem cookie entre domínios, o frontend pede um **ticket** curto em `POST /api/auth/ws-ticket/` (30 segundos, uso único) e o envia na conexão. Sem ticket, a conexão é aceita como visitante.

### Dinheiro em centavos

Todo valor é um inteiro em centavos, no banco, na API e nos cálculos. A formatação para "R$ 1.234,56" só acontece na tela.

### Saldo calculado, nunca gravado

- **Total** = soma do extrato da carteira (só recebe lançamentos, nunca edita).
- **Comprometido** = soma dos lances atuais dos lotes em que a pessoa lidera e que ainda não foram liquidados.
- **Disponível** = total − comprometido.

Como o comprometido é calculado, quando alguém é superado o valor volta ao disponível no mesmo instante em que o novo líder é gravado, sem nenhum passo extra.

### O motor de lances e a concorrência

Todo lance passa por um único serviço, `place_bid()`, numa transação que trava **primeiro o lote e depois o licitante** (`select_for_update()`). A ordem fixa evita deadlock. Dois lances no mesmo lote esperam um pelo outro, e o segundo é revalidado contra o novo preço. Dois lances do mesmo licitante em lotes diferentes não conseguem gastar o mesmo saldo. Os testes de concorrência usam threads de verdade contra o PostgreSQL.

Os lances recusados respondem 422 com um código e uma mensagem clara: `BELOW_MINIMUM`, `INSUFFICIENT_BALANCE`, `ALREADY_WINNING`, `LOT_NOT_STARTED` e `LOT_CLOSED`.

### Anti-sniping

Se um lance é aceito quando faltam 2 minutos ou menos, o novo fim passa a ser **o horário do lance + 2 minutos**. O enunciado admite outra leitura (o fim atual + 2 minutos). Escolhi esta porque ela garante sempre os mesmos 2 minutos para os outros responderem, sem que lances seguidos empurrem o fim cada vez mais longe.

### Liquidação

Não há um processo separado. A liquidação acontece de dois jeitos, e os dois usam o mesmo serviço, que é idempotente (liquidar duas vezes não tem efeito):

1. **Preguiçosa:** um lance, a abertura da sala, os arremates ou o painel liquidam na hora um lote que já terminou.
2. **Agendada:** o cron-job.org chama `POST /api/internal/tick/` a cada minuto, para os lotes que ninguém abriu. A mesma chamada mantém o servidor gratuito acordado.

Numa única transação, o vencedor é debitado, o leiloeiro é creditado e o comprovante é emitido. O débito nunca falha por falta de saldo, porque o valor já estava comprometido.

### Histórico à prova de adulteração

São três camadas, e cada uma pega um tipo de fraude:

1. **Cadeia de hashes:** cada lance guarda o SHA-256 de `lot_id|sequence|bidder_alias|amount_cents|created_at_utc_iso|prev_hash`. O primeiro aponta para `GENESIS`. Alterar, apagar ou inserir um lance no meio quebra a cadeia dali em diante.
2. **Âncora assinada:** a cada lance, na mesma transação, o lote guarda o número de lances e o último hash, assinados com **Ed25519**. Isso pega a remoção dos últimos lances (que deixaria uma cadeia perfeita, só que menor). Sem a chave privada, quem mexe no banco não consegue recalcular uma âncora válida. A chave pública fica em `GET /api/audit/public-key/`.
3. **Cópia externa da âncora:** depois do commit de cada lance, a âncora também é gravada no Redis, fora do banco, numa lista que só recebe inserções. Isso pega o caso que a assinatura sozinha não pega: restaurar um estado antigo inteiro do banco (lances, âncora e assinatura antigos, todos válidos).

A verificação (`GET /api/audit/lots/{id}/`) roda sete checagens e devolve o motivo da primeira falha:

| Adulteração direta no banco | Motivo |
| --- | --- |
| Alterar o valor ou o horário de um lance | `hash_mismatch` |
| Apagar um lance do meio | `sequence_gap` |
| Inserir um lance no meio e recalcular os hashes | `chain_broken` |
| Apagar os últimos lances | `anchor_mismatch` |
| Recalcular a cadeia e a âncora sem a chave | `bad_signature` |
| Restaurar um estado antigo inteiro | `anchor_rollback` |
| Alterar o comprovante | `receipt_mismatch` |

**Modelo de ameaça:** a defesa cobre quem tem acesso total ao banco de dados, mas não ao servidor do backend, onde ficam a chave privada e o acesso ao Redis. Quem controlar ao mesmo tempo o banco, o servidor e a chave pode forjar qualquer histórico. Num sistema real, as âncoras seriam publicadas também num registro externo de só escrita.

### Privacidade

Cada usuário recebe um pseudônimo (`Licitante #a3f9c1`), gerado por HMAC-SHA256 do id com o `ALIAS_SECRET`. A sala, a auditoria e o comprovante mostram só o pseudônimo, o valor, o horário e o hash. Nome e e-mail só aparecem para a própria pessoa, e os lances dela aparecem como "Você".

### Resiliência da Open Library

A Open Library só é chamada na busca do painel do leiloeiro. Ao criar um lote, o livro é copiado para o banco (um retrato do item), então a vitrine, a sala, a auditoria e o comprovante continuam funcionando com a API fora do ar. A busca tem timeout de 5 segundos, uma nova tentativa e cache de 10 minutos. Sem API e sem cache, o painel avisa que a busca está indisponível e que os lotes já criados não são afetados.

## 6. Como verificar a auditoria

### No site

Abra qualquer lote e clique em **Auditar histórico** (ou **Auditar este lote**, na sala). A página mostra as sete verificações, a chave pública e o histórico completo de lances. Não precisa de login.

### Adulterando um lance de propósito

Com o projeto rodando localmente e o seed criado (seção 3):

1. Abra a auditoria do *Dom Casmurro* e copie o id do lote, que fica no endereço depois de `/auditoria/`. O resultado deve ser **Histórico íntegro**.
2. Na pasta `backend`, abra o shell do Django:

   ```powershell
   python manage.py shell
   ```

3. Altere o valor do primeiro lance direto no banco, com SQL, como faria alguém com acesso ao banco (troque `ID_DO_LOTE`):

   ```python
   from django.db import connection; LOT = "ID_DO_LOTE"
   with connection.cursor() as c: c.execute("UPDATE bids_bid SET amount = amount + 100 WHERE lot_id = %s AND sequence = 1", [LOT])
   ```

4. Clique em **Verificar novamente**. A página fica vermelha: **"A cadeia quebra no lance #1: o hash recalculado não confere com o gravado (hash_mismatch)."** A linha do lance #1 fica destacada como "Com problema".
5. Desfaça a alteração e verifique de novo. O resultado volta a **Histórico íntegro**:

   ```python
   with connection.cursor() as c: c.execute("UPDATE bids_bid SET amount = amount - 100 WHERE lot_id = %s AND sequence = 1", [LOT])
   ```

Os testes automáticos (`apps/audit/test_verification.py`) cobrem cada linha da tabela da seção 5, inclusive o retrocesso de um estado antigo inteiro.

## 7. Limitações conhecidas

- **Plano gratuito do Render:** o servidor tem 0,1 de CPU, então a primeira resposta depois de um deploy pode demorar alguns segundos. O cron a cada minuto evita que ele durma. Se ele dormir mesmo assim, o primeiro acesso pode levar cerca de um minuto.
- **Um processo só:** as salas ao vivo usam o `InMemoryChannelLayer` do Channels, que só funciona com um processo do servidor. Para escalar, seria preciso trocar por um channel layer com Redis.
- **Reconexão em deploy:** a cada deploy o backend reinicia, e quem estiver numa sala perde a conexão por alguns segundos. A sala reconecta sozinha e busca o estado de novo.
- **Datas do seed:** os lotes ao vivo terminam 10 dias depois do seed. Para recomeçar a demonstração, rode `seed_data --reset`.
- **Capas:** em produção, as capas vêm direto da Open Library (o servidor gratuito não tem disco permanente). Se uma imagem falhar, a capa é desenhada com o título e o autor.
- **Obras, não edições:** a busca da Open Library devolve obras. O ano e o número de edições são os da obra, e nenhum lote afirma ser primeira edição ou exemplar autografado.
- **Sem Docker Compose** (seção 2).

## 8. Como rodar os testes

### Backend (pytest)

Os testes rodam contra o PostgreSQL, porque o SQLite ignora o `select_for_update()` e os testes de concorrência não valeriam nada nele. O Redis é trocado pelo `fakeredis`, e cada teste recebe uma chave de assinatura nova.

```powershell
cd backend
pytest
```

São **205 testes**, entre eles:

- todas as regras de lance e os cinco códigos de recusa;
- lances simultâneos com threads (só um é aceito);
- o anti-sniping;
- o saldo comprometido e a volta ao disponível quando alguém é superado;
- a liquidação com e sem lances, e liquidar duas vezes;
- uma adulteração direta no banco para cada motivo da auditoria;
- as rotas públicas sem login e o limite de 30 verificações por minuto (429);
- o WebSocket (eventos, ticket e visitante);
- a Open Library fora do ar.

### Frontend

```powershell
cd frontend
npm run lint
npm run build
```

## 9. Como usei IA

O registro completo está em [`docs/uso-de-ia.md`](docs/uso-de-ia.md). Em resumo:

- Encontrei a Open Library pesquisando APIs com o agente **Hermes AI**.
- Usei o **Claude** como auxiliar ao longo do projeto: ele revisou a especificação, explicou cada parte (bibliotecas, padrões e comandos) e propôs o código. Em várias partes, usei o **Claude Code** no VS Code a partir de prompts técnicos.
- Nos prompts, apliquei o que aprendi no curso **Desenvolvimento e Orquestração com IA Generativa** (ONE AI for Tech, Alura): contexto do projeto antes da tarefa, ler os arquivos e seguir os padrões existentes, dizer o que entra e o que não pode mudar, pedir os testes e parar antes de qualquer mudança fora do combinado.
- Escrevi, testei e revisei cada parte: nada entrou no repositório sem eu rodar os testes, testar no navegador e revisar o diff. As decisões de arquitetura e de escopo foram minhas, como a hospedagem, o ticket do WebSocket e a ordem das partes.
