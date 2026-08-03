# Tag — Carbon Design System v11

## O que é

Tags são usadas para rotular, categorizar ou organizar itens usando palavras-chave.

## Variantes

| Variante | Propósito |
|---|---|
| Read-only | Sem interatividade. Para categorização e rotulação. |
| Dismissible | Pode ser fechada/removida. Usada em filtros e conteúdo gerado pelo usuário. |
| Selectable | Pode ser selecionada/desselecionada. Usada para filtrar dados. |
| Operational | Ao interagir, revela tags adicionais em popover, modal ou breadcrumb. |

## Anatomia

- Container
- Título (texto)
- Ícone decorativo (opcional)
- Ícone de fechar (apenas dismissible)

## Tamanhos

Small, Medium (padrão), Large.

Use small em espaços condensados. Medium é o mais comum. Large quando a tag é ponto focal da página.

## Regras de conteúdo

- Títulos devem ser concisos, preferencialmente até 20 caracteres.
- Não quebre o título em múltiplas linhas.
- Quando o título é muito longo, use ellipsis com tooltip mostrando o texto completo.

## Estados

- Read-only: enabled, disabled, skeleton
- Dismissible/Operational: enabled, hover, focus, on click, disabled, skeleton
- Selectable: enabled, hover, focus, selected, disabled, skeleton

## Espaçamento entre tags

Quando em grupo, mantenha 8px ($spacing-03) entre as tags em todas as direções.