# Design System Mosaic — Guia de Marca e Identidade Visual

## Como o Mosaic se relaciona com o Carbon

O Carbon Design System é a base **funcional** do produto — componentes,
comportamento, acessibilidade. O Design System Mosaic é a camada de
**identidade** por cima disso: cor de marca, tipografia de destaque,
iconografia e voz visual que fazem a Mosaic Labs parecer a Mosaic Labs,
e não um produto genérico feito com Carbon puro.

**Regra prática:** telas de produto (o que o colaborador usa no dia a
dia) seguem o Carbon quase que integralmente, com toques pontuais de
marca (cor primária em botões de destaque, por exemplo). Landing pages,
apresentações e materiais de marketing usam o Mosaic com mais liberdade.

## Princípios de marca

**Modular.** Assim como um mosaico é feito de peças pequenas que
formam um todo coerente, nossa marca é construída em componentes
reutilizáveis — nunca em telas desenhadas do zero.

**Precisa, não fria.** Somos uma ferramenta de precisão (auditoria,
consistência, padrão), mas a comunicação evita soar como fiscal. Tom
de colega experiente, não de sistema policiando.

**Acessível por padrão, não como extra.** Contraste, foco visível e
leitura por voz não são "revisão de acessibilidade no final" — são
parte da definição de pronto de qualquer peça visual.

**Expressiva com moderação.** Usamos cor de marca pra guiar atenção
(ação principal, destaque, novidade), nunca para decorar uma tela
inteira.

## Paleta de marca

### Primária (Índigo)

| Token | Hex | Uso |
|---|---|---|
| `$mosaic-brand-100` | `#E0E7FF` | Fundo de badges e superfícies leves de marca |
| `$mosaic-brand-200` | `#C7D2FE` | Hover de fundos claros |
| `$mosaic-brand-300` | `#A5B4FC` | Bordas de destaque |
| `$mosaic-brand-400` | `#818CF8` | Ícones de marca |
| `$mosaic-brand-500` | `#4F46E5` | **Cor primária da marca** — CTAs de marketing, ponto de destaque |
| `$mosaic-brand-600` | `#4338CA` | Hover de botão de marca |
| `$mosaic-brand-700` | `#3730A3` | Texto de marca sobre fundo claro |
| `$mosaic-brand-800` | `#312E81` | Texto em fundo escuro |
| `$mosaic-brand-900` | `#1E1B4B` | Uso reservado — fundos muito escuros, raramente usado |

### Secundária (Âmbar)

| Token | Hex | Uso |
|---|---|---|
| `$mosaic-accent-100` | `#FEF3C7` | Fundos suaves de destaque secundário |
| `$mosaic-accent-500` | `#F59E0B` | Elementos de atenção que não sejam erro (ex: "novidade") |
| `$mosaic-accent-700` | `#B45309` | Texto sobre fundo âmbar claro |

## Tokens semânticos

### Superfície

| Token | Valor | Uso |
|---|---|---|
| `$mosaic-surface-default` | `#FFFFFF` | Fundo padrão, tema claro |
| `$mosaic-surface-elevated` | `#FFFFFF` + `shadow-md` | Cards, modais, popovers |
| `$mosaic-surface-overlay` | `rgba(17, 24, 39, 0.5)` | Backdrop de modal |
| `$mosaic-surface-inverse` | `#0F172A` | Fundo de tema escuro |

### Texto

| Token | Valor | Uso |
|---|---|---|
| `$mosaic-text-primary` | `#111827` | Títulos, corpo de texto principal |
| `$mosaic-text-secondary` | `#4B5563` | Descrição, metadado, texto de apoio |
| `$mosaic-text-tertiary` | `#9CA3AF` | Placeholder, estado desabilitado |
| `$mosaic-text-inverse` | `#F9FAFB` | Texto sobre fundo escuro/de marca |

### Borda

| Token | Valor | Uso |
|---|---|---|
| `$mosaic-border-default` | `#E5E7EB` | Divisor, borda de tabela |
| `$mosaic-border-focus` | `$mosaic-brand-500` | Anel de foco em elementos de marca |
| `$mosaic-border-error` | `#DC2626` | Estado de erro, quando não estiver usando o token de erro do Carbon |

## Tipografia

Usamos **Manrope** como fonte de destaque em peças de marca (landing,
apresentações). Telas de produto continuam com a IBM Plex Sans do
Carbon — não trocamos a fonte de produto por questão de legibilidade
em densidade alta de informação.

| Token | Fonte | Tamanho | Peso | Uso |
|---|---|---|---|---|
| `$mosaic-type-hero` | Manrope | 3rem / 48px | 800 | Título principal de landing |
| `$mosaic-type-heading` | Manrope | 2rem / 32px | 700 | Título de seção |
| `$mosaic-type-subheading` | Manrope | 1.25rem / 20px | 600 | Subtítulo |
| `$mosaic-type-body` | Manrope | 1rem / 16px | 400 | Texto corrido de marketing |

## Espaçamento de peças de marca

| Token | Valor | Uso |
|---|---|---|
| `$mosaic-space-hero` | 80px | Entre seções de landing page |
| `$mosaic-space-section` | 64px | Entre blocos de conteúdo |
| `$mosaic-space-component` | 32px | Entre componentes numa landing |
| `$mosaic-space-tight` | 16px | Dentro de cards de marketing |

## Logo

- **Espaço de respiro mínimo:** deixe ao redor do logo um espaço vazio
  equivalente à altura do símbolo (o losango do "M"). Nunca encoste
  texto, borda ou outro elemento gráfico dentro dessa área.
- **Tamanho mínimo:** 24px de altura em digital, 15mm em impresso.
  Abaixo disso o símbolo perde legibilidade.
- **Uso incorreto:** não distorcer proporção, não aplicar sombra ou
  contorno, não colocar sobre fundo com baixo contraste, não recolorir
  fora da versão em `$mosaic-brand-500` (colorida), branca (fundo
  escuro/de marca) ou `$mosaic-text-primary` (monocromática).

## Iconografia

- Ícones de linha (não preenchidos), espessura de traço consistente de
  1.5px, grid de 24x24px.
- Reaproveitamos o conjunto de ícones do Carbon como base — só criamos
  ícone customizado quando o Carbon genuinamente não tem um equivalente.
- Ícone de marca (usado em pontos de destaque/novidade, como no
  Onboarding Tooltip) usa a cor `$mosaic-brand-500`.

## Movimento (Motion)

| Token | Valor | Uso |
|---|---|---|
| `$mosaic-motion-rapido` | 120ms, ease-out | Hover, foco |
| `$mosaic-motion-padrao` | 200ms, ease-in-out | Abertura de modal, dropdown |
| `$mosaic-motion-lento` | 320ms, ease-in-out | Transição de página, ilustração de Empty State |

**Regra de acessibilidade:** toda animação acima de 120ms precisa ter
uma versão reduzida quando `prefers-reduced-motion` estiver ativo —
troque a transição por um corte direto (opacidade instantânea), nunca
remova a mudança de estado em si.

## Modo escuro

| Token (claro) | Token (escuro) | Valor escuro |
|---|---|---|
| `$mosaic-surface-default` | `$mosaic-surface-dark` | `#0F172A` |
| `$mosaic-text-primary` | `$mosaic-text-primary-dark` | `#F8FAFC` |
| `$mosaic-border-default` | `$mosaic-border-dark` | `#334155` |

**Regra:** todo token de marca precisa ter equivalente escuro definido
antes do componente ser aprovado — nunca lançar um componente que só
funciona no tema claro.
