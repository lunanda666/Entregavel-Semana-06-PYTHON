import unittest

from modelagem_classes import (
    BancoError,
    Cliente,
    Conta,
    ContaCorrente,
    ContaPoupanca,
    DadoInvalidoError,
    LimiteSaquesExcedidoError,
    SaldoInsuficienteError,
    Transacao,
)


class TestBanco(unittest.TestCase):
    """Cobre validacoes, encapsulamento, heranca e polimorfismo."""

    def setUp(self):
        """Roda antes de CADA teste: objetos novos, sem estado compartilhado."""
        self.ana = Cliente("Ana Silva", "ana@email.com", "123.456.789-00")
        self.corrente = ContaCorrente(self.ana, 1000.0)
        self.poupanca = ContaPoupanca(self.ana, 1000.0, taxa_rendimento=0.01)

    # ---------------- Cliente ----------------
    def test_cliente_valido(self):
        self.assertEqual(str(self.ana), "Ana Silva <ana@email.com>")

    def test_email_invalido_impede_criacao(self):
        with self.assertRaises(DadoInvalidoError):
            Cliente("Eli", "sem-arroba", "123.456.789-00")

    def test_cpf_invalido_impede_criacao(self):
        with self.assertRaises(DadoInvalidoError):
            Cliente("Eli", "eli@email.com", "12345678900")

    def test_setter_de_email_valida(self):
        with self.assertRaises(DadoInvalidoError):
            self.ana.email = "invalido"
        self.assertEqual(self.ana.email, "ana@email.com")   # nao foi alterado

    def test_clientes_com_mesmo_cpf_sao_iguais(self):
        outra = Cliente("Outra", "outra@email.com", "123.456.789-00")
        self.assertEqual(self.ana, outra)
        self.assertEqual(hash(self.ana), hash(outra))

    # ---------------- Conta (abstrata) ----------------
    def test_conta_abstrata_nao_instancia(self):
        with self.assertRaises(TypeError):
            Conta(self.ana)

    def test_deposito_e_saque(self):
        self.poupanca.depositar(500)
        self.poupanca.sacar(200)
        self.assertEqual(self.poupanca.saldo, 1300.0)

    def test_valor_invalido(self):
        for invalido in (-1, 0, "abc", None, True, float("nan")):
            with self.subTest(valor=invalido):
                with self.assertRaises(DadoInvalidoError):
                    self.poupanca.depositar(invalido)

    def test_saldo_nunca_fica_negativo(self):
        with self.assertRaises(SaldoInsuficienteError):
            self.poupanca.sacar(1000.01)
        self.assertEqual(self.poupanca.saldo, 1000.0)

    def test_saldo_nao_tem_setter(self):
        with self.assertRaises(AttributeError):
            self.corrente.saldo = 5

    def test_historico_e_protegido(self):
        self.assertIsInstance(self.corrente.historico, tuple)
        self.assertIsInstance(self.corrente.historico[0], Transacao)

    def test_numeros_de_conta_sao_unicos(self):
        self.assertNotEqual(self.corrente.numero, self.poupanca.numero)

    # ---------------- Heranca e polimorfismo ----------------
    def test_heranca(self):
        self.assertIsInstance(self.corrente, Conta)
        self.assertIsInstance(self.poupanca, Conta)

    def test_saque_corrente_cobra_taxa(self):
        self.corrente.sacar(100)
        self.assertEqual(self.corrente.saldo, 1000 - 100 - ContaCorrente.TAXA_SAQUE)

    def test_saque_corrente_exige_valor_mais_taxa(self):
        conta = ContaCorrente(self.ana, 101.0)       # 101 < 100 + 2,50
        with self.assertRaises(SaldoInsuficienteError):
            conta.sacar(100)
        self.assertEqual(conta.saldo, 101.0)         # nada foi debitado

    def test_poupanca_limita_saques(self):
        for _ in range(ContaPoupanca.LIMITE_SAQUES_MES):
            self.poupanca.sacar(10)
        with self.assertRaises(LimiteSaquesExcedidoError):
            self.poupanca.sacar(10)

    def test_fechar_mes_polimorfico(self):
        # mesma chamada, resultados diferentes conforme a classe
        self.assertEqual(self.corrente.fechar_mes(), -15.0)    # tarifa
        self.assertEqual(self.poupanca.fechar_mes(), 10.0)     # 1% de 1000

    def test_fechar_mes_corrente_nao_deixa_saldo_negativo(self):
        conta = ContaCorrente(self.ana, 5.0)
        self.assertEqual(conta.fechar_mes(), -5.0)
        self.assertEqual(conta.saldo, 0.0)

    def test_excecoes_herdam_de_banco_error_e_value_error(self):
        self.assertTrue(issubclass(DadoInvalidoError, BancoError))
        self.assertTrue(issubclass(DadoInvalidoError, ValueError))

    # ---------------- Dunder ----------------
    def test_igualdade_e_ordem_de_contas(self):
        self.assertEqual(self.corrente, self.corrente)
        self.assertNotEqual(self.corrente, self.poupanca)
        self.assertEqual(max([self.corrente, ContaPoupanca(self.ana, 5000.0)]).saldo, 5000.0)

    def test_vinculo_cliente_conta(self):
        self.ana.adicionar_conta(self.corrente)
        self.assertEqual(self.ana.contas, (self.corrente,))
        outro = Cliente("Bruno", "bruno@email.com", "987.654.321-00")
        with self.assertRaises(DadoInvalidoError):
            outro.adicionar_conta(self.corrente)     # conta de outro titular

    def test_transacao_valida_tipo_e_valor(self):
        with self.assertRaises(DadoInvalidoError):
            Transacao("PIX", 10)
        with self.assertRaises(DadoInvalidoError):
            Transacao("SAQUE", -1)


if __name__ == "__main__":
    unittest.main()