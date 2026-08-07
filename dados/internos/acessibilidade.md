# Guia de Acessibilidade — Mosaic Labs

## Por que isso não é opcional

Acessibilidade não é uma etapa de revisão no final — é parte da
definição de pronto de qualquer tela ou componente. Um componente que
funciona visualmente mas não funciona por teclado ou leitor de tela
está **incompleto**, não "quase pronto". Esse guia existe pra dar ao
time um padrão objetivo do que verificar, em vez de depender de
julgamento individual sobre o que "parece acessível".

## Navegação por teclado

Todo elemento interativo (botão, link, campo, item de menu) precisa
ser alcançável usando só a tecla `Tab`, na mesma ordem em que aparece
visualmente na tela — de cima pra baixo, esquerda pra direita. Isso
importa porque nem todo colaborador usa mouse ou toque; alguns navegam
o produto inteiro por teclado, seja por preferência, seja por
necessidade.

- Elemento desabilitado nunca deve receber foco.
- O indicador de foco precisa ser visível — não confie no estilo
  padrão do navegador, defina explicitamente com o token
  `$mosaic-border-focus`.
- Um Modal ou dropdown aberto deve prender o foco dentro dele (foco
  não pode "escapar" para o conteúdo por trás) até ser fechado.

## Leitores de tela

Leitores de tela (NVDA, VoiceOver, JAWS) convertem a interface em
áudio ou braille. Pra isso funcionar direito:

- Imagem informativa precisa de `alt` descrevendo o que ela transmite.
  Imagem puramente decorativa usa `alt=""` vazio, pra ser ignorada.
- Botão que só tem ícone (sem texto visível) precisa de `aria-label`
  descrevendo a ação — "Fechar", não "Botão X".
- Mensagem de erro de formulário precisa estar associada ao campo via
  `aria-describedby`, não só posicionada visualmente perto dele.
- Conteúdo que muda dinamicamente sem recarregar a página (contador de
  filtro ativo, por exemplo) precisa de `aria-live="polite"` pra ser
  anunciado.

## Contraste de cor

Contraste insuficiente é o problema de acessibilidade mais comum e
mais fácil de evitar — é só uma questão de escolher o par certo de
token.

- Texto normal (até 18px) precisa de contraste mínimo de **4.5:1**
  contra o fundo.
- Texto grande (acima de 18px em negrito, ou acima de 24px normal)
  precisa de no mínimo **3:1**.
- Informação nunca pode depender só da cor — todo Status Badge, por
  exemplo, tem o texto do status escrito, não só a cor de fundo.

## Formulários

- Todo campo tem um `<label>` associado (via atributo `for` ou
  envolvendo o campo) — nunca use só `placeholder` como rótulo, ele
  desaparece assim que a pessoa começa a digitar.
- Campo obrigatório é indicado visualmente **e** via `aria-required`,
  não só por um asterisco que um leitor de tela pode ignorar.
- Erro de validação precisa ser visível e anunciado, não só uma borda
  vermelha silenciosa.

## Semântica HTML

Usar a tag certa importa mais do que parece, porque é isso que dá
significado à estrutura pra quem não está vendo a tela:

- `<header>`, `<main>`, `<footer>`, `<nav>` no lugar de `<div>` genérica
  sempre que fizer sentido estrutural.
- Hierarquia de título (`<h1>` a `<h6>`) sem pular nível — não vá de
  `<h2>` direto pra `<h4>` só porque o `<h4>` "parece do tamanho certo".
- Lista de itens usa `<ul>`/`<ol>`, nunca uma pilha de `<div>` com
  bullet desenhado via CSS.
- Tabela de dado usa `<table>`, `<th>`, `<td>` de verdade — o Data
  Table interno é construído em cima dessa base semântica, não em
  `<div>`s estilizadas como tabela.

## Zoom e área de toque

- A interface precisa continuar funcional com zoom de até 200%, sem
  cortar conteúdo ou gerar scroll horizontal.
- Em telas de 320px de largura, não pode haver scroll horizontal.
- Alvo de toque (botão, ícone clicável) tem no mínimo 44x44px — abaixo
  disso, fica difícil de acionar com precisão em tela sensível ao
  toque.

## O que ainda não cobrimos

Compatibilidade com Internet Explorer 11 não é suportada. Suporte a
`prefers-reduced-motion` está em implementação parcial (já vale pra
componentes de marca, conforme o guia de Design System Mosaic, mas
ainda não foi auditado em todos os componentes do Carbon usados no
produto) — está no roadmap, não é considerado bloqueador de PR ainda.

## Ferramentas de verificação

| Ferramenta | O que verifica | Quando usar |
|---|---|---|
| axe DevTools | Contraste, semântica, ARIA | Durante o desenvolvimento |
| Lighthouse (aba Acessibilidade) | Nota geral da página | Antes de abrir o Pull Request |
| NVDA / VoiceOver | Leitura real com leitor de tela | Fluxos críticos (checkout, cadastro, ações destrutivas) |
| WAVE | Visão geral rápida de problemas | Checagem inicial, sanity check |

## Responsabilidade

QA revalida antes de ir pra produção, mas a responsabilidade primária
é de quem desenvolveu a tela — acessibilidade não é trabalho de uma
pessoa só no final do processo.
