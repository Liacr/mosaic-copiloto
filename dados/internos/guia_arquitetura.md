# Guia de Arquitetura de Design System — Mosaic Labs

## Por que escolhemos o Carbon Design System?

A Mosaic Labs adotou o **Carbon Design System (IBM)** como padrão oficial de design e front-end em 2026. A decisão foi tomada pelos seguintes motivos:

1. **Maturidade:** o Carbon existe há anos, é mantido ativamente pela IBM e tem documentação extensa.
2. **Acessibilidade:** segue rigorosamente as diretrizes WCAG 2.1 AA, o que reduz o risco legal e melhora a experiência de todos os usuários.
3. **Comunidade:** é open source, com comunidade ativa e atualizações frequentes.
4. **Consistência:** usar um design system consolidado evita que cada time reinvente componentes básicos.

## Escopo de adoção

Não vamos cobrir os 100+ componentes do Carbon de uma vez. A fase 1 (este trimestre) foca em:

- Button
- Input / Text Field
- Modal
- Tooltip
- Tag

## Responsabilidades

- **Design Ops:** mantém os tokens de design sincronizados entre Figma e código.
- **Tech Lead:** garante que o padrão de código interno esteja alinhado com as diretrizes do Carbon.
- **QA:** valida que novas telas não introduzem componentes fora do padrão sem aprovação.

## Versão adotada

Carbon v11 (última estável). Não mantemos histórico de versões antigas no nosso ambiente.