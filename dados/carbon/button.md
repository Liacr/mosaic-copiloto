# Button — Carbon Design System v11

## Quando usar

Use botões para comunicar ações que o usuário pode executar. Cada página deve ter apenas um botão primário. Demais ações devem usar variantes de menor ênfase.

## Quando NÃO usar

Não use botões como elementos de navegação. Para isso, use links.

## Variantes

| Variante | Propósito |
|---|---|
| Primary | Ação principal da página. Aparece uma vez por tela. |
| Secondary | Ação secundária, usada em par com o primário (ex: Cancelar). Nunca use isolado. |
| Tertiary | Ação menos proeminente. Pode ser usado isolado ou com o primário. |
| Ghost | Ação de menor ênfase. Usado em conjunto com primário/secundário. |
| Danger | Ações destrutivas (excluir, remover). Tem três estilos: primary, tertiary e ghost. |

## Tamanhos

Extra small, Small, Medium, Large (productive), Large (expressive), Extra large, 2XL.

O tamanho mais comum em produtos de software é o **Large (productive)**.

## Alinhamento

- **Esquerda:** formulários em página, banners, botões aninhados em tiles.
- **Direita:** notificações inline, tabelas de dados, wizards, modais.
- **Full-span:** modais, side panels, tiles pequenos (máx. 320px no Carbon atual).

## Regras de conteúdo

- O label do botão deve ser uma ação (verbo): "Salvar", "Cancelar", "Excluir".
- Não use "OK" ou "Done" — são vagos.
- O label é sempre alinhado à esquerda dentro do botão.
- Ícones ficam à direita do label (ou centralizados em icon-only buttons).

## Estados

Enabled, Hover, Focus, Active, Disabled.