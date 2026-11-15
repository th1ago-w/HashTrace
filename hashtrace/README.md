# HashTrace

Monitor de integridade de arquivos em Python. Cria uma referência com hashes SHA-256 e compara o conteúdo de uma pasta para encontrar arquivos **criados, alterados e excluídos**.

Projeto de estudo de segurança defensiva, desenvolvido com auxílio de IA. Usa somente a biblioteca padrão do Python, sem instalar pacotes.

## Como executar

Requer Python 3.10 ou superior. Baixe os arquivos, abra o terminal na pasta do projeto e execute:

```bash
python hashtrace.py registrar exemplo --base referencia.json
python hashtrace.py verificar exemplo --base referencia.json
```

Na primeira verificação, o resultado será `Nenhuma mudança detectada.`

Agora edite `exemplo/config.txt`, crie um arquivo na pasta `exemplo` e exclua `exemplo/notas.txt`. Execute novamente:

```bash
python hashtrace.py verificar exemplo --base referencia.json --json relatorio.json
```

Exemplo de saída, supondo que o arquivo criado se chame `novo.txt`:

```text
CRIADOS: 1
  novo.txt

ALTERADOS: 1
  config.txt

EXCLUÍDOS: 1
  notas.txt

Mudanças detectadas.
```

O JSON inclui as listas de mudanças, o caminho da pasta e a data de verificação em UTC. Salve o relatório fora da pasta monitorada para evitar que ele próprio apareça na próxima comparação.

No Windows, se `python` não for reconhecido, tente `py`.

## Como funciona

1. `registrar` percorre a pasta e suas subpastas, lendo os arquivos em blocos de 1 MB para calcular SHA-256.
2. A referência armazena o caminho absoluto da pasta e os hashes associados aos caminhos relativos.
3. `verificar` calcula os hashes atuais e compara com a referência. A ordem dos arquivos não interfere no resultado.

O programa não altera os arquivos monitorados. Uma referência existente só é substituída quando você informa `--sobrescrever`:

```bash
python hashtrace.py registrar exemplo --base referencia.json --sobrescrever
```

Faça isso apenas quando quiser aceitar o estado atual como nova referência.

## Códigos de saída

| Código | Significado |
| --- | --- |
| 0 | Referência criada ou nenhuma mudança detectada |
| 1 | Mudanças detectadas |
| 2 | Erro de leitura, argumentos ou referência inválida |

## Testes

```bash
python -m unittest -v
```

Os testes usam pastas temporárias e cobrem criação, alteração, exclusão, arquivos binários, referência inválida e proteções contra sobrescrita.

## Limitações

- A verificação acontece quando você executa o comando; não é monitoramento contínuo.
- Mudanças de nome aparecem como exclusão e criação.
- Compara conteúdo, não permissões, proprietário ou data de modificação.
- Links simbólicos são ignorados. Evite pastas com junções ou outros redirecionamentos do sistema de arquivos.
- A pasta deve permanecer estável durante a leitura. Alterações simultâneas podem gerar uma visão inconsistente.
- Erros de acesso interrompem a análise em vez de apresentar uma comparação incompleta.
- A referência é um JSON sem assinatura. Guarde-a em um local confiável: quem conseguir alterá-la pode esconder mudanças.
- Detectar uma alteração não significa detectar malware, e ausência de alteração não garante segurança.

## Estrutura

```text
hashtrace.py          Comandos, cálculo de hashes e comparação
test_hashtrace.py     Testes automatizados
exemplo/          Arquivos fictícios para experimentar
```

## Demonstração

<img width="1650" height="1323" alt="hashtrace" src="https://github.com/user-attachments/assets/f1d9b13e-1eb5-4043-ba8a-49c2c4ddaa2d" />
