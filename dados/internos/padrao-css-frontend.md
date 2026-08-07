# Padrão de CSS e Arquitetura Front-end — Mosaic Labs

## Como os dois sistemas de token coexistem

A Mosaic Labs usa **dois níveis de token** no CSS, e é comum confundir
quando usar cada um:

- **Tokens do Carbon** — chegam como CSS custom properties (ex:
  `var(--cds-button-primary)`). Usados em **qualquer** componente de
  produto (telas internas, dashboards, formulários).
- **Tokens customizados Mosaic** — chegam como variáveis Sass
  (ex: `$mosaic-brand-500`), compiladas em tempo de build. Usados
  **apenas** em landing pages de marketing, dashboards com identidade
  visual própria, e modo escuro.

**Regra de decisão simples:** se a tela faz parte do produto (o que o
colaborador usa no dia a dia), use tokens do Carbon. Se é uma peça de
marketing ou uma superfície com identidade visual própria da marca,
use tokens Mosaic. Nunca misture os dois no mesmo componente sem
justificativa documentada em comentário no código.

## Nomenclatura de classes CSS

Seguimos uma convenção próxima de BEM, com prefixo `mosaic-` pra evitar
colisão com classes de bibliotecas externas:

```
.mosaic-[componente]
.mosaic-[componente]__[elemento]
.mosaic-[componente]--[modificador]
```

Exemplo:
```css
.mosaic-status-badge { }
.mosaic-status-badge__icone { }
.mosaic-status-badge--erro { }
```

Não usamos nomes de classe baseados em aparência (ex: `.texto-azul`,
`.margem-grande`) — o nome deve descrever o papel do elemento, nunca o
valor visual bruto. Isso é a mesma lógica por trás dos tokens: nomear
pela função, não pelo valor.

## Regra de ouro: nenhum valor solto no CSS

Nenhum valor de cor, espaçamento, tipografia ou sombra pode ser escrito
diretamente no CSS. Sempre referencie um token — do Carbon ou da Mosaic,
conforme a regra de decisão acima.

```css
/* Errado */
.mosaic-card {
  background-color: #ffffff;
  padding: 24px;
}

/* Certo */
.mosaic-card {
  background-color: var(--cds-layer-01);
  padding: var(--cds-spacing-07);
}
```

Essa regra é validada automaticamente pelo Stylelint no CI (plugin
`declaration-property-value-disallowed-list` bloqueia valores
hexadecimais e `px`/`rem` soltos fora dos arquivos de definição de
token).

## Proibido usar `!important`

Se você sente necessidade de `!important`, o problema é de
especificidade da regra anterior, não de força bruta. Pull Requests
com `!important` são bloqueados no lint automaticamente, exceto em
casos de sobrescrita de biblioteca de terceiros — e mesmo assim precisa
de comentário explicando o motivo.

## Estrutura de pastas de estilo

```
src/estilos/
  tokens/           -> apenas definição de token, nunca estilo de componente
  base/              -> reset, tipografia global
  componentes/        -> um arquivo .scss por componente interno
  temas/
    claro.scss
    escuro.scss
```

## Modo escuro

Todo componente novo precisa funcionar nos dois temas antes de ser
aprovado em code review. Siga a tabela de equivalência de tokens claro
→ escuro documentada no guia de Design Tokens Customizados. Não é
aceitável lançar um componente só com o tema claro implementado.

## Checklist rápido antes de abrir Pull Request de estilo

- [ ] Nenhum valor de cor/espaçamento/fonte escrito direto no CSS
- [ ] Classe segue a convenção `mosaic-[componente]__[elemento]--[modificador]`
- [ ] Sem uso de `!important`
- [ ] Funciona em tema claro e escuro
- [ ] Rodou o Stylelint localmente antes do commit (`npm run lint:css`)
