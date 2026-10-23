# Testes por cenário — CLARA multiagente

Cenários da seção 6.2 da apostila, enviados ao chat da CLARA com um `sessionId` por cenário (3, 4 e 5 na mesma sessão). O sub-agente vem do registro da execução (nós executados), equivalente ao painel Logs.

| # | Mensagem(ns) | Resposta obtida | Sub-agente (registro) | Esperado | OK? |
| --- | --- | --- | --- | --- | --- |
| 1 | oi | Olá! Eu sou a CLARA, assistente virtual do Núcleo de Convênios. Como posso ajudar você hoje? | nenhum | Nenhum sub-agente; apresenta-se como CLARA | sim |
| 2 | Qual o horário de atendimento e o e-mail de vocês? | O Núcleo de Convênios funciona de segunda a sexta, das 08 h às 17 h, tanto presencialmente quanto por telefone.  <br><br>Para contato por e‑mail, utilize: atendimento@nucleo-convenios.example.  <br><br>Qualquer outra dúvida, estou à disposição! | INFO | INFO; segunda a sexta, das 8h às 17h, e o e-mail do Núcleo | sim |
| 3 | Quero saber sobre um convênio. | Claro! Para poder consultar os detalhes do convênio, preciso que você me informe o número dele no formato **NNN/AAAA** (por exemplo, 047/2026). Assim poderei buscar as informações corretas para você. | nenhum | Nenhum sub-agente; pede o número no formato NNN/AAAA | sim |
| 4 | É o 047/2026. Qual o objeto e o valor? | O convênio **047/2026** tem como objeto **“Pesquisa Aplicada em Tecnologias Sustentáveis”** e possui o valor de **R$ 250.000,00**. | CONVENIOS | CONVENIOS; "Pesquisa Aplicada em Tecnologias Sustentáveis" e R$ 250.000,00 | sim |
| 5 | Quem assina pela fundação? | Pela Fundação **Pesquisa & Inovação**, o convênio 047/2026 é assinado por **Fernanda Lopes Azevedo**. | CONVENIOS | CONVENIOS ou nenhum; Fernanda Lopes Azevedo, sem pedir o número de novo | sim |
| 6 | E o convênio 099/2026, qual o valor? | Não encontrei nenhum registro para o convênio 099/2026 na nossa base de dados. Caso o número esteja correto, pode ser que ainda não tenha sido inserido ou que tenha ocorrido algum erro de digitação. Se precisar de ajuda adicional ou quiser verificar outro convênio, estou à disposição! | CONVENIOS | CONVENIOS; não há registro desse número; não cita outros convênios | sim |
| 7a | Preciso falar com uma pessoa: meu pedido de aditivo do convênio 021/2026 está parado há um mês. | Entendo, vamos registrar sua solicitação para que a equipe do Núcleo de Convênios possa entrar em contato. Por favor, informe seu nome completo e o e‑mail que podemos usar para o atendimento. | nenhum | Nenhum sub-agente; pede só nome e e-mail | sim |
| 7b | Sou Carlos Mendes, carlos.mendes@exemplo.example | Chamado registrado com sucesso!  <br>**Protocolo:** CH-20261023-104132  <br><br>A equipe do Núcleo de Convênios analisará seu pedido e retornará no próximo dia útil. Qualquer dúvida adicional, estamos à disposição. | ATENDIMENTO | ATENDIMENTO; protocolo CH-…; nova linha na tabela chamados | sim |
| 8a | Meu nome é Maria. | Olá, Maria! Eu sou a CLARA, assistente virtual do Núcleo de Convênios. Como posso ajudar você hoje? | nenhum | Nenhum sub-agente | sim |
| 8b | Você lembra meu nome? | Sim, Maria, eu lembro do seu nome. Como posso ajudar você hoje? | nenhum | Nenhum sub-agente; responde Maria, pela memória da sessão | sim |

## Ajustes de prompt

| Cenário | Instrução anterior | Instrução nova | Resultado do novo teste |
| --- | --- | --- | --- |
| — | Nenhum ajuste necessário | — | — |

## Observações da revisão

A coluna OK? combina duas checagens: o caminho (sub-agente no registro da execução) e palavras-chave na resposta. Três respostas corretas falharam só na comparação literal, porque o modelo escreveu caracteres Unicode tipográficos; a revisão humana, pelo critério da seção 6.2, as considerou aprovadas:

- **2**: "08 h" e "17 h" com espaço fino inseparável (U+202F); horário e e-mail do Núcleo estão na resposta, via INFO.
- **5**: "Fernanda Lopes Azevedo" com U+202F entre os nomes; a CLARA não pediu o número de novo.
- **7a**: "e‑mail" com hífen inseparável (U+2011); a CLARA pediu só nome e e-mail, sem pedir de novo a descrição.

No cenário 7, a tabela `chamados` recebeu a linha com protocolo `CH-20261023-104132`, nome `Carlos Mendes`, e-mail `carlos.mendes@exemplo.example` e a descrição tirada da primeira mensagem. Nenhum cenário exigiu ajuste de prompt.
