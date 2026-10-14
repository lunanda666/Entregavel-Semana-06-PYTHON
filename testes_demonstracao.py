from modelagem_classes import (
    BancoError,
    Cliente,
    Conta,
    ContaCorrente,
    ContaPoupanca,
    Transacao,
)


def secao(titulo):
    """Imprime um cabecalho para separar as secoes da demonstracao."""
    print(f"\n{'=' * 64}\n{titulo}\n{'=' * 64}")


def tentar(descricao, acao):
    """Executa `acao` (funcao sem argumentos) e mostra o resultado ou o erro.

    Captura apenas as excecoes esperadas neste sistema: os erros de regra
    de negocio (BancoError), TypeError (classe abstrata) e AttributeError
    (atributo sem setter). Qualquer outro erro continua quebrando o
    programa, o que e o certo: seria um bug de verdade.
    """
    try:
        resultado = acao()
    except (BancoError, TypeError, AttributeError) as erro:
        print(f"  [ERRO capturado] {descricao}\n      -> {type(erro).__name__}: {erro}")
    else:
        print(f"  [OK] {descricao} -> {resultado}")


def main():
    """Executa todas as demonstracoes na ordem."""
    # ------------------------------------------------------------------
    secao("1. CRIACAO DOS OBJETOS (4 clientes + 7 contas = 11 instancias)")
    # ------------------------------------------------------------------
    ana = Cliente("Ana Silva", "ana@email.com", "123.456.789-00")
    bruno = Cliente("Bruno Costa", "bruno@empresa.com", "987.654.321-00")
    carla = Cliente("Carla Souza", "carla@email.com", "111.222.333-44")
    diego = Cliente("Diego Melo", "diego@email.com", "222.333.444-55")
    clientes = [ana, bruno, carla, diego]

    # lista com classes DIFERENTES (CC e CP), tratadas de forma uniforme
    ana_cc = ContaCorrente(ana, 1000.0)
    ana_cp = ContaPoupanca(ana, 5000.0, taxa_rendimento=0.006)
    bruno_cc = ContaCorrente(bruno, 300.0, tarifa_manutencao=20.0)
    carla_cp1 = ContaPoupanca(carla, 2000.0)
    carla_cp2 = ContaPoupanca(carla, 150.0, taxa_rendimento=0.007)
    diego_cc = ContaCorrente(diego, 80.0)
    diego_cp = ContaPoupanca(diego)          # saldo inicial zero
    contas = [ana_cc, ana_cp, bruno_cc, carla_cp1, carla_cp2, diego_cc, diego_cp]

    # vincula cada conta ao seu titular (Cliente TEM contas)
    for conta in contas:
        conta.titular.adicionar_conta(conta)

    for cliente in clientes:
        print(f"{cliente} | contas: {len(cliente.contas)}")
    for conta in contas:
        print(f"  {conta}")
    print(f"Total de objetos criados: {len(clientes) + len(contas)}")

    # ------------------------------------------------------------------
    secao("2. OPERACOES BASICAS E EXTRATO")
    # ------------------------------------------------------------------
    ana_cc.depositar(500)
    ana_cc.sacar(200)       # na corrente, cobra tambem a taxa de saque
    print(ana_cc.extrato())

    # ------------------------------------------------------------------
    secao("3. POLIMORFISMO")
    # ------------------------------------------------------------------
    print("3.1 Mesmo comando sacar(100) em todas as contas:")
    for conta in contas:
        # a chamada e a mesma; o resultado depende da classe do objeto
        tentar(f"{type(conta).__name__} #{conta.numero} sacar(100)",
               lambda conta=conta: f"saldo R$ {conta.sacar(100):.2f}")

    print("\n3.2 Mesmo comando fechar_mes() em todas as contas:")
    for conta in contas:
        variacao = conta.fechar_mes()
        print(f"  {type(conta).__name__:<14} #{conta.numero} -> "
              f"{variacao:+8.2f} | saldo R$ {conta.saldo:.2f}")

    # ------------------------------------------------------------------
    secao("4. METODOS ESPECIAIS (__repr__, __eq__, __lt__)")
    # ------------------------------------------------------------------
    print("repr(conta):  ", repr(ana_cc))
    print("repr(cliente):", repr(ana))
    print("mesma conta ==        :", ana_cc == ana_cc)
    print("contas diferentes ==  :", ana_cc == ana_cp)
    copia_ana = Cliente("Ana S.", "outro@email.com", "123.456.789-00")
    print("mesmo CPF, outro obj ==:", ana == copia_ana)
    print("\nContas ordenadas por saldo (sorted usa __lt__):")
    for conta in sorted(contas):
        print(f"  {conta.saldo:>9.2f}  {type(conta).__name__} #{conta.numero}")
    print("Conta de maior saldo:", max(contas))

    # ------------------------------------------------------------------
    secao("5. ENTRADAS INVALIDAS (try/except)")
    # ------------------------------------------------------------------
    print("5.1 Validacoes de Cliente (@property / construtor):")
    tentar("e-mail sem @", lambda: Cliente("Eli", "eli.email.com", "123.456.789-00"))
    tentar("CPF sem pontuacao", lambda: Cliente("Eli", "eli@email.com", "12345678900"))
    tentar("nome vazio", lambda: Cliente("", "eli@email.com", "123.456.789-00"))
    tentar("trocar e-mail por valor invalido",
           lambda: setattr(ana, "email", "sem-arroba"))

    print("\n5.2 Validacoes de valores e contas:")
    tentar("depositar valor negativo", lambda: ana_cc.depositar(-50))
    tentar("depositar texto", lambda: ana_cc.depositar("abc"))
    tentar("sacar mais que o saldo", lambda: ana_cc.sacar(999999))
    tentar("alterar saldo direto (sem setter)",
           lambda: setattr(ana_cc, "saldo", 1_000_000))
    tentar("saldo inicial negativo", lambda: ContaCorrente(ana, -10))
    tentar("tarifa negativa", lambda: ContaCorrente(ana, tarifa_manutencao=-5))
    tentar("taxa de rendimento de 90%", lambda: ContaPoupanca(ana, taxa_rendimento=0.9))
    tentar("titular que nao e Cliente", lambda: ContaCorrente("Ana", 100))
    tentar("instanciar classe abstrata", lambda: Conta(ana))
    tentar("transacao de tipo desconhecido", lambda: Transacao("PIX", 10))
    tentar("sacar de poupanca vazia", lambda: diego_cp.sacar(1))
    tentar("vincular conta de outro titular", lambda: ana.adicionar_conta(bruno_cc))

    print("\n5.3 Limite de saques da poupanca (3 por mes):")
    for tentativa in range(1, 5):
        tentar(f"saque {tentativa} de R$ 10 na poupanca da Ana",
               lambda: f"saldo R$ {ana_cp.sacar(10):.2f}")

    # ------------------------------------------------------------------
    secao("6. RESUMO POR CLIENTE")
    # ------------------------------------------------------------------
    for cliente in sorted(clientes):       # usa Cliente.__lt__ (por nome)
        print(f"{cliente.nome:<12} saldo total: R$ {cliente.saldo_total:>9.2f}")


# executa main() apenas quando o arquivo e rodado diretamente
if __name__ == "__main__":
    main()