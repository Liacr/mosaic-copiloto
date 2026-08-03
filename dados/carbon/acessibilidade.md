# Acessibilidade — Carbon Design System v11

## Compromisso

O Carbon segue o IBM Accessibility Checklist, baseado em WCAG 2.1 AA, Section 508 e padrões europeus.

## Princípios para designers

- Informação visual deve ser traduzível em texto.
- Teste designs com screen reader quando possível.
- Maximize legibilidade e clareza visual.
- Siga as diretrizes de teclado.

## Deficiências contempladas

### Cegueira

- Usam screen readers ou Braille.
- Não usam mouse.
- **Aplicação para todos:** interfaces de voz (assistents de IA) dependem de representação audio.

### Baixa visão

- Usam screen magnifiers, alto contraste, fontes grandes.
- Afeta ~4% da população mundial.
- **Aplicação para todos:** telas em ambientes claros (exterior) e visão que piora após os 40 anos.

### Daltonismo

- Afeta 8% dos homens e 0.4% das mulheres.
- Não diferenciam algumas cores.
- **Regra:** nunca use apenas cor para transmitir informação. Use também texto, ícones ou padrões.

### Surdez

- Dependem de legendas e transcrições.
- **Aplicação para todos:** ambientes barulhentos ou silenciosos onde não se pode ligar o som.

### Deficiências motoras

- Podem usar teclado, trackball, reconhecimento de voz.
- **Regra:** todo componente deve ser operável por teclado.

### Deficiências cognitivas

- Dificuldades com memória, atenção, leitura.
- **Regras:** evite linguagem complexa, autoplay, animações piscantes. Design linear e baixa carga cognitiva.

## Contraste de cores

- Black text é acessível (WCAG AA) em cores 10-50.
- White text é acessível em cores 60-100.
- Diferença de 50+ entre valores = combinação acessível.