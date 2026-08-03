# Text Input — Carbon Design System v11

## Quando usar

Use para permitir que o usuário insira texto livre. Inclui variantes para texto simples, password e text area.

## Anatomia

- **Label:** identifica o campo. Deve ter no máximo 3 palavras.
- **Field text:** o texto digitado pelo usuário.
- **Helper text:** informação adicional abaixo do campo.
- **Placeholder:** texto de exemplo dentro do campo (não substitui o label).

## Tokens de tipografia aplicados

| Elemento | Tamanho | Peso | Token |
|---|---|---|---|
| Label | 12px / 0.75rem | Regular 400 | $label-01 |
| Field text | 14px / 0.875rem | Regular 400 | $body-compact-01 |
| Helper text | 12px / 0.75rem | Regular 400 | $helper-text-01 |

## Tokens de espaçamento aplicados

| Elemento | Propriedade | Valor | Token |
|---|---|---|---|
| Label | margin-bottom | 8px / 0.5rem | $spacing-03 |
| Helper text | margin-top | 4px / 0.25rem | $spacing-02 |
| Field text | padding-left, padding-right | 16px / 1rem | $spacing-05 |
| Field | border-bottom | 1px | — |
| Focus | border | 2px | — |
| Invalid | border | 2px | — |

## Tamanhos de input

| Tamanho | Altura |
|---|---|
| Small (sm) | 32px / 2rem |
| Medium (md) | 40px / 2.5rem |
| Large (lg) | 48px / 3rem |

## Estados

Enabled, Hover, Focus, Error, Warning, Disabled.