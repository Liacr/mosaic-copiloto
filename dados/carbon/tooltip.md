# Tooltip — Carbon Design System v11

## O que é

Tooltips exibem informação adicional ao passar o mouse (hover) ou focar (focus) em um elemento. São contextuais, úteis e não essenciais.

## Regra fundamental

Tooltips são **embutidos em outros componentes**, não são usados como componentes standalone. A única exceção é o **Definition Tooltip**.

## Quando usar

- Mostrar nomes de controles sem label visual (ex: icon buttons).
- Fornecer informação adicional para elementos focáveis.
- Definir termos ou dar detalhes sobre um item inline (definition tooltip).

## Quando NÃO usar

- NÃO coloque informação crítica para completar a tarefa — use helper text sempre visível.
- NÃO inclua elementos interativos (links, botões) dentro de tooltips. Para isso, use o componente Toggletip.

## Definition Tooltip

Usado para definir termos ou dar ajuda extra dentro de textos. Funciona bem em labels, parágrafos ou espaços compactos como tabelas de dados.

## Alinhamento do container

O container do tooltip pode ser alinhado a **start**, **center** ou **end** para evitar que saia da tela ou cubra informação importante.

## Tooltip vs Toggletip

| | Tooltip | Toggletip |
|---|---|---|
| Gatilho | Hover ou Focus | Click ou Enter |
| Conteúdo | Apenas texto, não interativo | Pode ter botões, links |
| Uso | Informação breve suplementar | Informação que requer interação |