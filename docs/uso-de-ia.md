# Uso de IA no projeto Casa das Letras

Registro de onde e como usei IA no teste técnico Elite Dev da Verzel, e do que revisei ou ajustei em cada etapa. Atualizado ao longo do projeto, não só no fim.

## Ferramentas

- **Hermes AI (agente de pesquisa):** usei na pesquisa de APIs públicas para o tema do leilão. Foi nessa pesquisa que encontrei a Open Library Search API.
- **Claude (Anthropic), pelo claude.ai:** meu auxiliar ao longo do projeto inteiro. Revisou a especificação, explicou cada parte (bibliotecas, padrões, comandos) e propôs o código, passo a passo.
- **Notion integrado ao Claude:** a especificação técnica ficou no Notion, e eu conectei o Notion ao Claude. A IA lia a especificação direto da fonte e conferia cada parte do projeto contra as regras escritas lá.
- **Claude Code, integrado ao VS Code:** usei na tela da sala ao vivo, a partir de um resumo técnico com as rotas, os eventos e os padrões do projeto.

## Como trabalhei

- Escrevi muito código eu mesmo: digitei, adaptei e corrigi os arquivos seguindo as explicações, em vez de só colar o que era gerado.
- Nada entrou no repositório sem eu ler, testar e entender. Antes de cada commit: testes automáticos (`pytest`, `npm run lint`, `npm run build`), teste manual no navegador ou na API navegável do DRF, e revisão do `git diff --staged`.
- As decisões de arquitetura e de escopo foram minhas (lista abaixo). Quando a IA sugeriu um caminho e eu escolhi outro, anotei aqui.
- Nos prompts para os agentes, usei o que aprendi no curso **Desenvolvimento e Orquestração com IA Generativa** (ONE AI for Tech, Alura): dar o contexto do projeto antes da tarefa, mandar o agente ler os arquivos e seguir os padrões que já existem, dizer exatamente o que entra e o que não pode mudar, pedir os testes e os comandos de verificação, e exigir que ele pare e explique antes de qualquer mudança fora do combinado.

## Registro

| Data | Etapa | Como a IA ajudou | O que eu fiz, revisei ou alterei |
| --- | --- | --- | --- |
| 24/10/2026 | Escolha da API | O Hermes AI me ajudou na pesquisa de APIs. O Claude avaliou a Open Library: campos úteis, capas, ausência de chave e cuidados (livros sem capa, instabilidade) | Pesquisei e encontrei a Open Library Search API; escolhi o tema de livros raros |
| 24/10/2026 | Leitura do enunciado | O Claude resumiu o PDF e apontou os pontos críticos: concorrência nos lances, saldo comprometido, histórico à prova de adulteração e resiliência da API | Conferi o resumo com o PDF |
| 24/10/2026 | Especificação | O Claude revisou a minha especificação v1 e apontou problemas: escopo grande para 7 dias, remoção dos últimos lances não detectada pela hash chain, cookies entre domínios diferentes, falta de modelo de dados e de máquina de estados | Escrevi a v1; aceitei as correções que faziam sentido |
| 24/10/2026 | Especificação v2 | O Claude escreveu a versão revisada: modelo de dados, estados do lote, motor de lances, auditoria com âncora assinada, API, eventos WebSocket, testes e plano | Revisei e mantive a especificação oficial no Notion |
| 24/10/2026 | Telas | O Claude gerou os protótipos navegáveis das telas, com os tokens visuais que eu defini | Defini a identidade visual e usei os protótipos como referência em todas as telas |
| 24/10/2026 | Conferência com o PDF | O Claude comparou a especificação e as telas com cada item do enunciado e apontou lacunas: retrocesso do histórico, "outros campos relevantes" e itens do envio | Pedi a auditoria pública sem login como requisito explícito |
| 25 e 26/10/2026 | Ambiente de desenvolvimento | O Claude guiou a instalação do WSL e do Docker, o diagnóstico do erro `CreateVm/ERROR_TIMEOUT` e, quando o Docker não funcionou, a instalação do Python 3.12, do PostgreSQL e o ajuste do PATH | Fiz as instalações e os diagnósticos no meu computador |
| 26/10/2026 | Infraestrutura | O Claude ajustou a especificação para a infraestrutura que escolhi | Decidi: back na Oracle Cloud, banco no Neon e front na Vercel |
| 26/10/2026 | Repositório, backend e autenticação (partes 1 a 4) | O Claude explicou e propôs o `.gitignore`, o README inicial, o projeto Django, os modelos, o usuário com papel e pseudônimo e o login por sessão | Escrevi e testei cada parte; corrigi um `LOCAL_APPS` duplicado no `settings.py` e o CSRF entre o Vite e o Django |
| 26/10/2026 | Base do frontend e login (parte 5) | O Claude explicou e propôs os tokens do Tailwind, as rotas, o contexto de autenticação e a tela de login | Encontrei e corrigi o erro de regra de hooks (`useSeedAccount` → `fillSeedAccount`); pedi o botão de mostrar a senha e a remoção de uma mensagem repetida no cadastro |
| 26/10/2026 | Catálogo, lotes, vitrine e painel (parte 6) | O Claude explicou e propôs o adaptador da Open Library, as rotas, os testes e as telas | Testei cada rota no DRF e cada tela no navegador; encontrei as margens dobradas, o prazo quebrado no cartão e as edições faltando na vitrine; a revisão do diff pegou uma linha duplicada e 70 arquivos sem quebra de linha final |
| 26 e 27/10/2026 | Carteira, motor de lances e concorrência (parte 8) | O Claude explicou e propôs o saldo calculado, o hash de cada lance, o `place_bid()` com as travas e os testes de lances simultâneos | Rodei os testes de concorrência várias vezes; testei um lance de verdade pela API; corrigi uma fixture duplicada e imports fora do lugar |
| 27/10/2026 | WebSocket (parte 9, backend) | O Claude explicou e propôs o Channels, o Daphne, os eventos ao vivo e o ticket do WebSocket | Escolhi o ticket (a opção da especificação) em vez da alternativa mais simples; corrigi código depois de um `return` e testes que usavam a versão antiga de uma função |
| 27/10/2026 | Tela da sala (parte 9, frontend) | O Claude Code no VS Code escreveu a tela a partir de um resumo técnico preparado com o Claude | Revisei os diffs com o Claude, fiz os 12 testes manuais (lances ao vivo em duas janelas, superado sem recarregar, visitante, agendado, reconexão, lote inexistente) e fiz o commit |
| 27/10/2026 | Liquidação, comprovante e meus arremates (parte 10) | O Claude escreveu a liquidação e os prompts com as regras e o layout do protótipo; o Claude Code no VS Code corrigiu a trava (`select_for_update` com junção externa) e escreveu as rotas, as telas e os testes | Rodei os testes (142 no backend), testei com dois licitantes até o fim do lote, abri o comprovante sem login, revisei cada diff e separei os commits; anotei quatro ajustes para a parte 12 |
| 27/10/2026 | Auditoria (parte 11) | O Claude releu a seção 7 da especificação e o protótipo e preparou os prompts; o Claude Code no VS Code escreveu a assinatura Ed25519, a cópia da âncora no Redis, a verificação com as 7 checagens, a tela Auditoria e o selo do comprovante | Gerei a minha chave de assinatura, assinei os lotes antigos, adulterei um lance direto no banco pelo shell do Django e vi a auditoria acusar `hash_mismatch` no lance #1, e desfiz; testei a tela sem login e o lote inexistente; revisei os diffs e conferi que o `.env` não entrou no Git |
| 27/10/2026 | Dados de exemplo (parte 13a) | O Claude preparou o prompt a partir da seção 13 da especificação; o Claude Code no VS Code escreveu o comando `seed_data`, montou o JSON dos livros com uma consulta à Open Library e escreveu os testes | Pedi para corrigir os dados dos livros (o tradutor listado como autor, o ano de *O Cortiço* e os títulos), rodei o `--reset` e conferi a vitrine, os arremates das duas contas e a sala |

## Decisões que tomei

- Seguir sem Docker no computador de desenvolvimento e hospedar o back na Oracle Cloud, o banco no Neon e o front na Vercel.
- Usar o Python 3.12 em vez do 3.14 que já tinha instalado, para usar a mesma versão da VM de produção.
- Terminar o projeto inteiro localmente e deixar o deploy para o fim.
- Usar o ticket do WebSocket, como na especificação, para o servidor avisar só quem foi superado.
- Deixar o selo "Histórico íntegro" do comprovante para depois da auditoria existir, para ele nunca afirmar algo que o sistema não verificou.
- Criar a página `/auditoria`, explicando a verificação, no lugar de um link que levava a "Lote não encontrado".
- Trocar a hospedagem do backend da Oracle Cloud para o Render, porque o cadastro na Oracle não foi liberado a tempo. Comparei Oracle, AWS, Render e o backend na própria Vercel (que ganhou WebSocket para Python em julho de 2026) e escolhi o Render, por rodar o Daphne como um servidor comum, igual ao do desenvolvimento.
- [preencher: outras decisões, como a regra de anti-sniping "horário do lance + 2 min"]

## Resumo para o formulário de envio

[Encontrei a Open Library pesquisando com o agente Hermes AI. Usei o Claude como auxiliar no projeto inteiro: ele explicava cada parte e propunha o código, e eu escrevia, testava, revisava cada diff antes do commit e tomava as decisões de arquitetura. Na tela da sala ao vivo, usei o Claude Code no VS Code.]
