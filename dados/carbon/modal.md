# Modal — Carbon Design System v11

## Quando usar

Use modais para apresentar informações críticas ou solicitar input necessário para completar o fluxo do usuário. Modais interrompem o workflow — use com parcimônia.

## Quando NÃO usar

Se o usuário precisar executar a tarefa repetidamente, faça-a na página principal em vez de um modal.

## Variantes

| Variante | Uso |
|---|---|
| Passive | Apenas informação, sem ações. |
| Transactional | Requer uma ação para fechar. Tem botões Cancelar + Ação. |
| Danger | Variante transactional para ações destrutivas/irreversíveis. |
| Acknowledgment | Sistema requer confirmação do usuário. Um único botão (OK). |
| Progress | Vários passos antes de fechar. Tem Cancelar, Anterior, Próximo/Concluir. |

## Anatomia

1. **Header:** título, label opcional, ícone de fechar (x).
2. **Body:** informação e controles necessários para a tarefa.
3. **Footer:** botões de ação principal e cancelar.
4. **Overlay:** fundo escuro que bloqueia o conteúdo da página.

## Tamanhos

Extra small, Small, Medium, Large. Escolha conforme a quantidade de conteúdo.

## Regras de conteúdo

- O título deve ser um verbo que descreve a tarefa: "Adicionar domínio", "Excluir usuário".
- Se o modal é aberto por um botão, o título deve corresponder ao label do botão.
- Use label opcional para contexto (ex: caminho do objeto sendo editado).
- O texto do body deve ter no máximo 80% da largura do modal.
- Nunca use scroll horizontal no modal — use um tamanho maior.