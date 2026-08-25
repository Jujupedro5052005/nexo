# Observações do professor

Este arquivo registra orientações fornecidas pelo professor fora dos documentos
oficiais. Elas não devem ser reescritas como se fossem decisões originalmente
do projeto.

## Professor sugeriu

- evitar herança artificial;
- uma classe base sem uso concreto pode indicar herança sem justificativa;
- polimorfismo pode fazer sentido, mas deve surgir de necessidade real;
- associação não é adequada ao modelo proposto;
- focar em composição.

## Decisão adotada pelo projeto

Com base nessas orientações, `Asset` não terá subclasses apenas para demonstrar
POO; composição é o relacionamento interno enfatizado; herança e polimorfismo
só serão utilizados em necessidades concretas. O modelo não usa associação
como conceito arquitetural a ser demonstrado.

## Pendente de confirmação

O PDF oficial enumera associação e composição no requisito A-008. Deve-se
confirmar com o professor como registrar a orientação posterior em relação à
redação do documento oficial, sem introduzir uma relação artificial.
