# Componentes Internos — Mosaic Labs

Estes componentes **não fazem parte do Carbon Design System**. São
extensões próprias, construídas e mantidas pela Engenharia Front-end,
porque cobrem casos de uso que o Carbon não resolve nativamente. Antes
de propor um componente novo, verifique se um destes cinco já resolve
o problema.

---

## Data Table (avançada)

**O que é:** tabela de dados com paginação, ordenação por coluna,
filtro embutido no cabeçalho e seleção múltipla de linhas. O
`DataTable` do Carbon cobre casos simples; este componente existe para
volumes grandes de dado (200+ linhas) com necessidade de ações em
massa.

**Quando usar:** telas de listagem administrativa (ex: lista de
usuários, lista de pedidos, relatórios). Não use para tabelas
pequenas e estáticas — nesse caso, o `DataTable` padrão do Carbon é
suficiente e mais leve.

**Estados:** carregando (skeleton), vazio (ver componente Empty State),
erro de carregamento, com filtro ativo, com linhas selecionadas.

**Tokens usados:** cores e espaçamento do Carbon (`--cds-layer-01`,
`--cds-spacing-05`); cor de destaque de linha selecionada usa
`$mosaic-brand-100` como fundo.

**Acessibilidade:** cabeçalho de coluna ordenável precisa de
`aria-sort`; seleção de linha precisa de `aria-label` descrevendo qual
linha está sendo selecionada, não apenas um checkbox mudo.

---

## Status Badge

**O que é:** indicador visual compacto de estado (ex: "Ativo",
"Pendente", "Cancelado", "Em análise"). O `Tag` do Carbon é genérico;
o Status Badge tem uma paleta fixa de 5 estados com significado
semântico consistente em todo o produto.

**Quando usar:** sempre que for representar o status de um registro
(pedido, usuário, tarefa). Não use `Tag` do Carbon pra esse fim — isso
gera inconsistência de cor entre telas diferentes pro mesmo tipo de
status.

**Variantes fixas:**

| Status | Cor de fundo | Cor de texto |
|---|---|---|
| Ativo | verde (Carbon `--cds-support-success`) | escuro |
| Pendente | amarelo (Carbon `--cds-support-warning`) | escuro |
| Cancelado | vermelho (Carbon `--cds-support-error`) | escuro |
| Em análise | `$mosaic-brand-100` | `$mosaic-brand-700` |
| Rascunho | cinza (Carbon `--cds-layer-accent-01`) | `$mosaic-text-secondary` |

**Regra importante:** não criar uma sexta variante sem aprovação do
Design Ops — a força do componente está em ter um vocabulário visual
fechado e previsível.

**Acessibilidade:** a cor nunca é a única informação — o texto do
status sempre aparece por escrito dentro do badge, nunca só a cor.

---

## Filter Bar

**O que é:** barra horizontal de filtros combináveis (busca por texto +
múltiplos dropdowns + botão de limpar filtros), usada acima de listas
e tabelas.

**Quando usar:** qualquer tela de listagem com mais de um critério de
filtro. Para um único campo de busca, use o `Search` padrão do Carbon
diretamente — não precisa do Filter Bar completo.

**Anatomia:** campo de busca (Carbon `Search`) + até 4 dropdowns
(Carbon `Dropdown`) + contador de filtros ativos + botão "Limpar
filtros" que só aparece quando há pelo menos um filtro ativo.

**Tokens usados:** 100% tokens do Carbon — este componente não
introduz nenhum token novo, é uma composição de componentes Carbon já
existentes.

**Acessibilidade:** o contador de filtros ativos deve ser anunciado via
`aria-live="polite"` quando o número mudar, pra leitor de tela
perceber a mudança sem precisar navegar até lá.

---

## Empty State

**O que é:** tela ou bloco exibido quando uma lista/tabela não tem
nenhum resultado — seja porque não há dados ainda, ou porque um filtro
zerou os resultados.

**Quando usar:** todo Data Table, Filter Bar ou lista precisa ter um
Empty State definido antes de ir pra produção. Não é opcional.

**Duas variantes obrigatórias:**
1. **Vazio genuíno** (nunca houve dado): ilustração + título + texto
   explicando o que fazer + botão de ação principal (ex: "Criar
   primeiro pedido").
2. **Vazio por filtro** (havia dado, filtro não achou nada): título
   mais curto + botão "Limpar filtros", sem ilustração grande.

**Tokens usados:** tipografia e espaçamento do Carbon; ilustração usa a
paleta `$mosaic-brand-*` para manter identidade visual.

---

## Onboarding Tooltip

**O que é:** variação do `Tooltip` do Carbon usada especificamente em
fluxos de introdução de funcionalidade nova (ex: "essa é a nova aba de
relatórios"), com um ponto pulsante indicando novidade e um botão
"Entendi" que marca o tooltip como visto permanentemente.

**Diferença do Tooltip padrão do Carbon:** o Tooltip padrão aparece só
no hover/focus e nunca é "lembrado". O Onboarding Tooltip aparece
automaticamente na primeira visita à tela, persiste até ser descartado
pelo usuário, e nunca mais aparece pra aquele colaborador depois disso.

**Quando usar:** exclusivamente para apresentar funcionalidade nova —
nunca para conteúdo de ajuda permanente (isso continua sendo o
Tooltip padrão do Carbon).

**Tokens usados:** cor de destaque do ponto pulsante usa
`$mosaic-brand-500`; todo o resto (balão, texto, sombra) usa tokens do
Carbon.

**Acessibilidade:** o ponto pulsante não pode ser a única forma de
indicar novidade — o texto do tooltip também precisa deixar claro que
é uma funcionalidade nova, pra quem usa leitor de tela ou tem
sensibilidade a movimento (`prefers-reduced-motion` deve desativar a
pulsação, mantendo só o balão estático).
