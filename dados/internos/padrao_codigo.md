# Padrão de Código Front-end — Mosaic Labs

## Regra de ouro

> Se o Carbon já tem um componente para isso, use o componente do Carbon. Não escreva do zero.

## Tokens obrigatórios

- **Cores:** sempre use os tokens do Carbon (`$button-primary`, `$text-error`), nunca cores hexadecimais literais.
- **Espaçamento:** use os tokens de spacing (`$spacing-01` a `$spacing-13`).
- **Tipografia:** use as famílias e tamanhos definidos nos tokens de tipo do Carbon.

## Exemplo correto vs. incorreto

```css
/* INCORRETO — cor literal, fora do padrão */
.botao-primario {
    background-color: #2979FF;
}

/* CORRETO — token do Carbon */
.botao-primario {
    background-color: $button-primary;
}
```

## Validação antes do commit

Antes de abrir um Pull Request, o desenvolvedor deve:

1. Verificar se o componente já existe no Carbon (consultar o Mosaic, nosso agente de IA).
2. Garantir que nenhum valor hexadecimal ou pixel fixo foi usado onde existe um token equivalente.
3. Confirmar que estados de foco e erro estão visíveis e acessíveis.

## Dúvidas?

Pergunte ao Mosaic, nosso copiloto de qualidade de produto. Ele consulta a documentação oficial do Carbon e nossos padrões internos.