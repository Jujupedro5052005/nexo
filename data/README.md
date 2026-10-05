# Data

Esta pasta contém dados locais necessários ao desenvolvimento ou à execução.
O incremento 01 resolve `data/nexo.db` a partir da raiz do checkout, sem
depender da pasta de execução. O `.env.example` mantém apenas um exemplo de
URL, ainda não consumido. O banco gerado não deve ser versionado nem conter
dados sensíveis; testes usam bancos temporários fora deste diretório.

Subpastas como `sample/` ou `seeds/` só devem ser documentadas e criadas quando
existirem dados de exemplo ou sementes com finalidade definida. Não há dataset
incluído por este documento.
