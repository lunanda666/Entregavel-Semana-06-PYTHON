
import math
import re
from abc import ABC, abstractmethod
from datetime import datetime

# =====================================================================
# EXCECOES PERSONALIZADAS
# =====================================================================


class BancoError(Exception):
    """Classe base de todos os erros de regra de negocio do banco."""


class DadoInvalidoError(BancoError, ValueError):
    """Dado de entrada invalido (e-mail, CPF, valor negativo, tipo errado...).

    Tambem herda de ValueError: quem ja captura ValueError continua
    funcionando, e quem quiser pode capturar o erro especifico do dominio.
    """


class SaldoInsuficienteError(BancoError):
    """Lancada quando a operacao exige mais dinheiro do que a conta possui."""

    def __init__(self, saldo, valor_necessario):
        # guarda os numeros como atributos para uso posterior (ex.: relatorios)
        self.saldo = saldo
        self.valor_necessario = valor_necessario
        super().__init__(
            f"Saldo insuficiente: disponivel R$ {saldo:.2f}, "
            f"necessario R$ {valor_necessario:.2f}"
        )


class LimiteSaquesExcedidoError(BancoError):
    """Lancada quando a poupanca ultrapassa o limite de saques do mes."""

    def __init__(self, limite):
        self.limite = limite
        super().__init__(f"Limite de {limite} saques mensais ja atingido")


# =====================================================================
# VALIDACAO DE VALORES MONETARIOS
# =====================================================================


def validar_valor_monetario(valor, nome="valor", permitir_zero=False):
    """Valida um valor em dinheiro e devolve-o arredondado a 2 casas.

    Args:
        valor: numero a validar (int ou float).
        nome: nome do campo, usado na mensagem de erro.
        permitir_zero: se True, aceita 0 (ex.: saldo inicial); se False,
            exige valor estritamente positivo (ex.: deposito).

    Raises:
        DadoInvalidoError: se nao for numero, for NaN/infinito ou negativo.
    """
    # bool e subclasse de int em Python (True == 1): rejeitamos explicitamente
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DadoInvalidoError(f"{nome} deve ser numerico, recebido: {valor!r}")

    # NaN e infinito passam nas comparacoes de forma enganosa
    if math.isnan(valor) or math.isinf(valor):
        raise DadoInvalidoError(f"{nome} deve ser um numero finito")

    # com permitir_zero=True, so o negativo e invalido; senao, zero tambem e
    invalido = valor < 0 if permitir_zero else valor <= 0
    if invalido:
        regra = "deve ser maior ou igual a zero" if permitir_zero else "deve ser maior que zero"
        raise DadoInvalidoError(f"{nome} {regra}, recebido: {valor}")

    return round(float(valor), 2)


# =====================================================================
# TRANSACAO (registro de movimentacao)
# =====================================================================


class Transacao:
    """Registro de uma movimentacao financeira (deposito, saque, tarifa...).

    A Transacao existe DENTRO de uma Conta (composicao: "a conta tem
    transacoes"). Tipo e valor sao validados por @property, e a data so
    tem getter, pois o historico nao deve ser reescrito.
    """

    # tuplas (imutaveis) com os tipos aceitos e se somam ou subtraem do saldo
    TIPOS_CREDITO = ("DEPOSITO", "RENDIMENTO")
    TIPOS_DEBITO = ("SAQUE", "TARIFA")

    def __init__(self, tipo, valor, data=None):
        """Cria a transacao validando tipo e valor.

        Args:
            tipo: um de DEPOSITO, RENDIMENTO, SAQUE ou TARIFA.
            valor: valor positivo em reais.
            data: datetime opcional; se None, usa o momento atual.
                (None no lugar de datetime.now() como padrao: um padrao
                avaliado na definicao seria o mesmo para todos os objetos.)
        """
        self.tipo = tipo      # passa pelo setter (validacao)
        self.valor = valor    # passa pelo setter (validacao)
        self._data = data if data is not None else datetime.now()

    @property
    def tipo(self):
        """Tipo da transacao (sempre em maiusculas)."""
        return self._tipo

    @tipo.setter
    def tipo(self, valor):
        """Aceita apenas os tipos conhecidos."""
        if not isinstance(valor, str):
            raise DadoInvalidoError(f"tipo deve ser texto, recebido: {valor!r}")
        valor = valor.strip().upper()
        if valor not in self.TIPOS_CREDITO + self.TIPOS_DEBITO:
            raise DadoInvalidoError(f"tipo de transacao desconhecido: {valor!r}")
        self._tipo = valor

    @property
    def valor(self):
        """Valor da transacao em reais (sempre positivo)."""
        return self._valor

    @valor.setter
    def valor(self, novo_valor):
        """Aceita apenas valores positivos."""
        self._valor = validar_valor_monetario(novo_valor, "valor da transacao")

    @property
    def data(self):
        """Data e hora da transacao (somente leitura)."""
        return self._data

    def __str__(self):
        """Linha amigavel para o extrato."""
        sinal = "+" if self._tipo in self.TIPOS_CREDITO else "-"
        return (f"{self._data:%d/%m/%Y %H:%M} | {self._tipo:<10} | "
                f"{sinal} R$ {self._valor:>9.2f}")

    def __repr__(self):
        """Representacao tecnica para debug."""
        return f"Transacao({self._tipo!r}, {self._valor!r}, {self._data!r})"


# =====================================================================
# CLIENTE (titular das contas)
# =====================================================================


class Cliente:
    """Cliente do banco.

    Relacao com Conta: o cliente TEM contas (agregacao). Nao usamos
    heranca aqui, pois "Cliente e uma Conta" nao faz sentido.
    """

    # padroes compilados uma unica vez (raw strings, como na aula 5)
    PADRAO_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    PADRAO_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")

    def __init__(self, nome, email, cpf):
        """Cria o cliente; dados invalidos impedem a criacao do objeto.

        Raises:
            DadoInvalidoError: nome vazio, e-mail ou CPF fora do formato.
        """
        self.nome = nome      # passa pelo setter
        self.email = email    # passa pelo setter
        # o CPF identifica o cliente (e usado em __eq__ e __hash__), por isso
        # so e definido aqui e nao tem setter
        if not isinstance(cpf, str) or not self.PADRAO_CPF.match(cpf.strip()):
            raise DadoInvalidoError(
                f"CPF invalido (use 000.000.000-00): {cpf!r}"
            )
        self._cpf = cpf.strip()
        self._contas = []     # lista nova para CADA cliente

    # ------------------------------------------------------------------
    # propriedades (encapsulamento)
    # ------------------------------------------------------------------
    @property
    def nome(self):
        """Nome completo do cliente."""
        return self._nome

    @nome.setter
    def nome(self, valor):
        """Exige texto com pelo menos 2 caracteres."""
        if not isinstance(valor, str) or len(valor.strip()) < 2:
            raise DadoInvalidoError(
                f"nome deve ter ao menos 2 caracteres, recebido: {valor!r}"
            )
        self._nome = valor.strip()

    @property
    def email(self):
        """E-mail de contato."""
        return self._email

    @email.setter
    def email(self, valor):
        """Exige o formato nome@dominio.ext (regex)."""
        if not isinstance(valor, str) or not self.PADRAO_EMAIL.match(valor.strip()):
            raise DadoInvalidoError(f"e-mail invalido: {valor!r}")
        self._email = valor.strip()

    @property
    def cpf(self):
        """CPF do cliente (somente leitura)."""
        return self._cpf

    @property
    def contas(self):
        """Contas do cliente, como tupla (a lista interna fica protegida)."""
        return tuple(self._contas)

    @property
    def saldo_total(self):
        """Soma dos saldos de todas as contas do cliente."""
        return round(sum(conta.saldo for conta in self._contas), 2)

    # ------------------------------------------------------------------
    # comportamentos
    # ------------------------------------------------------------------
    def adicionar_conta(self, conta):
        """Vincula uma conta a este cliente.

        Raises:
            DadoInvalidoError: se nao for uma Conta, se pertencer a outro
                titular ou se ja estiver vinculada.
        """
        if not isinstance(conta, Conta):
            raise DadoInvalidoError(f"esperava uma Conta, recebido: {conta!r}")
        if conta.titular != self:
            raise DadoInvalidoError("a conta pertence a outro titular")
        if conta in self._contas:
            raise DadoInvalidoError(f"conta #{conta.numero} ja esta vinculada")
        self._contas.append(conta)

    # ------------------------------------------------------------------
    # metodos especiais (dunder)
    # ------------------------------------------------------------------
    def __str__(self):
        """Texto amigavel para o usuario."""
        return f"{self._nome} <{self._email}>"

    def __repr__(self):
        """Representacao tecnica: parece o codigo que recria o objeto."""
        return f"Cliente({self._nome!r}, {self._email!r}, {self._cpf!r})"

    def __eq__(self, outro):
        """Dois clientes sao iguais se tiverem o mesmo CPF."""
        if not isinstance(outro, Cliente):
            return NotImplemented
        return self._cpf == outro._cpf

    def __hash__(self):
        """Obrigatorio ao definir __eq__: o hash usa o mesmo campo (CPF)."""
        return hash(self._cpf)

    def __lt__(self, outro):
        """Ordena clientes por nome (usado por sorted())."""
        if not isinstance(outro, Cliente):
            return NotImplemented
        return self._nome < outro._nome


# =====================================================================
# CONTA (classe abstrata)
# =====================================================================


class Conta(ABC):
    """Conta bancaria generica (classe ABSTRATA: nao pode ser instanciada).

    Concentra o que e comum a todas as contas (numero, titular, saldo,
    deposito, saque, extrato) e OBRIGA as filhas a implementar
    `fechar_mes()`, que cada tipo de conta executa do seu jeito.

    Invariantes (sempre verdadeiras): o saldo nunca e negativo e so muda
    por operacoes que deixam rastro no historico.
    """

    # atributo de CLASSE: compartilhado por todas as contas (gera numeros)
    _proximo_numero = 1001
    # nome do tipo de conta; cada filha sobrescreve
    TIPO = "Generica"

    def __init__(self, titular, saldo_inicial=0.0):
        """Cria a conta validando tudo ANTES de gerar o numero.

        Args:
            titular: Cliente dono da conta.
            saldo_inicial: valor inicial (>= 0), registrado como deposito.

        Raises:
            DadoInvalidoError: titular nao e Cliente ou saldo invalido.
        """
        if not isinstance(titular, Cliente):
            raise DadoInvalidoError(f"titular deve ser um Cliente, recebido: {titular!r}")
        saldo_inicial = validar_valor_monetario(
            saldo_inicial, "saldo inicial", permitir_zero=True
        )

        self._titular = titular
        # usa Conta._proximo_numero (e nao self.) para o contador ser unico
        # entre todas as subclasses
        self._numero = Conta._proximo_numero
        Conta._proximo_numero += 1
        self._saldo = 0.0
        self._historico = []        # lista nova para CADA conta

        if saldo_inicial > 0:
            self.depositar(saldo_inicial)

    # ------------------------------------------------------------------
    # propriedades (somente leitura): o estado so muda por metodos
    # ------------------------------------------------------------------
    @property
    def titular(self):
        """Cliente dono da conta."""
        return self._titular

    @property
    def numero(self):
        """Numero unico da conta."""
        return self._numero

    @property
    def saldo(self):
        """Saldo atual. Sem setter: so depositar/sacar o alteram."""
        return self._saldo

    @property
    def historico(self):
        """Transacoes realizadas, como tupla (a lista interna fica protegida)."""
        return tuple(self._historico)

    # ------------------------------------------------------------------
    # operacoes
    # ------------------------------------------------------------------
    def depositar(self, valor):
        """Adiciona dinheiro a conta e devolve o novo saldo."""
        valor = validar_valor_monetario(valor, "valor do deposito")
        self._creditar(valor, "DEPOSITO")
        return self._saldo

    def sacar(self, valor):
        """Retira dinheiro da conta e devolve o novo saldo.

        Raises:
            DadoInvalidoError: valor nao positivo.
            SaldoInsuficienteError: valor maior que o saldo.
        """
        valor = validar_valor_monetario(valor, "valor do saque")
        self._debitar(valor, "SAQUE")
        return self._saldo

    def extrato(self):
        """Devolve o extrato completo como texto."""
        linhas = [f"Extrato - {self}"]
        linhas += [f"  {transacao}" for transacao in self._historico]
        linhas.append(f"  Saldo atual: R$ {self._saldo:.2f}")
        return "\n".join(linhas)

    @abstractmethod
    def fechar_mes(self):
        """Rotina mensal da conta (CONTRATO: toda filha deve implementar).

        Returns:
            float: variacao do saldo causada pelo fechamento
            (positiva = ganho, negativa = cobranca).
        """

    # ------------------------------------------------------------------
    # auxiliares protegidos (uso interno e das subclasses)
    # ------------------------------------------------------------------
    def _creditar(self, valor, tipo):
        """Soma ao saldo e registra a transacao."""
        self._saldo = round(self._saldo + valor, 2)
        self._historico.append(Transacao(tipo, valor))

    def _debitar(self, valor, tipo):
        """Subtrai do saldo e registra; e AQUI que o saldo negativo e barrado."""
        if valor > self._saldo:
            raise SaldoInsuficienteError(self._saldo, valor)
        self._saldo = round(self._saldo - valor, 2)
        self._historico.append(Transacao(tipo, valor))

    # ------------------------------------------------------------------
    # metodos especiais (dunder)
    # ------------------------------------------------------------------
    def __str__(self):
        """Texto amigavel para o usuario."""
        return (f"Conta {self.TIPO} #{self._numero} | "
                f"{self._titular.nome} | Saldo: R$ {self._saldo:.2f}")

    def __repr__(self):
        """Representacao tecnica (type(self) mostra a classe real do objeto)."""
        return (f"{type(self).__name__}(numero={self._numero}, "
                f"titular={self._titular.nome!r}, saldo={self._saldo})")

    def __eq__(self, outro):
        """Duas contas sao iguais se tiverem o mesmo numero."""
        if not isinstance(outro, Conta):
            return NotImplemented
        return self._numero == outro._numero

    def __hash__(self):
        """Acompanha __eq__: o hash usa o numero da conta."""
        return hash(self._numero)

    def __lt__(self, outro):
        """Compara pelo SALDO, para ordenar contas com sorted()/max().

        Atencao: __eq__ compara numeros e __lt__ compara saldos; por isso
        nao definimos os demais operadores de ordem.
        """
        if not isinstance(outro, Conta):
            return NotImplemented
        return self._saldo < outro._saldo


# =====================================================================
# CONTA CORRENTE (herda de Conta)
# =====================================================================


class ContaCorrente(Conta):
    """Conta corrente (relacao "e uma Conta").

    Especializa a Conta com duas regras:
      - cada saque custa uma taxa fixa (sobrescreve `sacar`);
      - todo mes cobra uma tarifa de manutencao (implementa `fechar_mes`).
    """

    TIPO = "Corrente"
    TAXA_SAQUE = 2.50   # constante de classe: igual para todas as contas

    def __init__(self, titular, saldo_inicial=0.0, tarifa_manutencao=15.0):
        """Cria a conta corrente.

        Args:
            titular: Cliente dono da conta.
            saldo_inicial: saldo de abertura (>= 0).
            tarifa_manutencao: tarifa mensal (>= 0).
        """
        # o setter so guarda o valor validado e nao depende da classe mae;
        # chamar antes evita gastar um numero de conta se a tarifa for invalida
        self.tarifa_manutencao = tarifa_manutencao
        super().__init__(titular, saldo_inicial)   # reaproveita o construtor da mae

    @property
    def tarifa_manutencao(self):
        """Tarifa cobrada a cada fechamento de mes."""
        return self._tarifa_manutencao

    @tarifa_manutencao.setter
    def tarifa_manutencao(self, valor):
        """Aceita zero ou mais; negativo seria um 'bonus' disfarcado."""
        self._tarifa_manutencao = validar_valor_monetario(
            valor, "tarifa de manutencao", permitir_zero=True
        )

    def sacar(self, valor):
        """POLIMORFISMO: sobrescreve sacar() cobrando a taxa por saque."""
        valor = validar_valor_monetario(valor, "valor do saque")
        total = round(valor + self.TAXA_SAQUE, 2)
        # confere o TOTAL antes de mexer no saldo, para nao sacar so metade
        if total > self.saldo:
            raise SaldoInsuficienteError(self.saldo, total)
        super().sacar(valor)                           # saque normal da mae
        self._debitar(self.TAXA_SAQUE, "TARIFA")       # mais a taxa
        return self.saldo

    def fechar_mes(self):
        """Cobra a tarifa de manutencao (ate o limite do saldo disponivel)."""
        cobrado = min(self._tarifa_manutencao, self.saldo)   # nunca deixa negativo
        if cobrado > 0:
            self._debitar(cobrado, "TARIFA")
            return -cobrado
        return 0.0

    def __str__(self):
        """Estende o texto da mae com a tarifa (reuso via super())."""
        return f"{super().__str__()} | Tarifa mensal: R$ {self._tarifa_manutencao:.2f}"


# =====================================================================
# CONTA POUPANCA (herda de Conta)
# =====================================================================


class ContaPoupanca(Conta):
    """Conta poupanca (relacao "e uma Conta").

    Especializa a Conta com duas regras:
      - rende uma taxa mensal sobre o saldo (implementa `fechar_mes`);
      - permite poucos saques por mes (sobrescreve `sacar`).
    """

    TIPO = "Poupanca"
    LIMITE_SAQUES_MES = 3
    TAXA_MAXIMA = 0.05   # 5% ao mes: acima disso o dado esta quase certamente errado

    def __init__(self, titular, saldo_inicial=0.0, taxa_rendimento=0.005):
        """Cria a poupanca.

        Args:
            titular: Cliente dono da conta.
            saldo_inicial: saldo de abertura (>= 0).
            taxa_rendimento: taxa mensal entre 0 e 0.05 (padrao 0,5%).
        """
        self.taxa_rendimento = taxa_rendimento    # valida pelo setter
        self._saques_no_mes = 0
        super().__init__(titular, saldo_inicial)

    @property
    def taxa_rendimento(self):
        """Taxa de rendimento mensal (ex.: 0.005 = 0,5%)."""
        return self._taxa_rendimento

    @taxa_rendimento.setter
    def taxa_rendimento(self, valor):
        """Aceita numeros de 0 ate TAXA_MAXIMA."""
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise DadoInvalidoError(f"taxa deve ser numerica, recebido: {valor!r}")
        if not 0 <= valor <= self.TAXA_MAXIMA:
            raise DadoInvalidoError(
                f"taxa deve estar entre 0 e {self.TAXA_MAXIMA}, recebido: {valor}"
            )
        self._taxa_rendimento = float(valor)

    @property
    def saques_restantes(self):
        """Quantos saques ainda podem ser feitos neste mes."""
        return self.LIMITE_SAQUES_MES - self._saques_no_mes

    def sacar(self, valor):
        """POLIMORFISMO: sobrescreve sacar() limitando saques por mes."""
        if self._saques_no_mes >= self.LIMITE_SAQUES_MES:
            raise LimiteSaquesExcedidoError(self.LIMITE_SAQUES_MES)
        novo_saldo = super().sacar(valor)   # valida valor e saldo na mae
        self._saques_no_mes += 1            # so conta se o saque deu certo
        return novo_saldo

    def fechar_mes(self):
        """Credita o rendimento do mes e zera o contador de saques."""
        rendimento = round(self.saldo * self._taxa_rendimento, 2)
        if rendimento > 0:
            self._creditar(rendimento, "RENDIMENTO")
        self._saques_no_mes = 0
        return rendimento

    def __str__(self):
        """Estende o texto da mae com taxa e saques restantes."""
        return (f"{super().__str__()} | Rendimento: "
                f"{self._taxa_rendimento * 100:.2f}% a.m. | "
                f"Saques restantes: {self.saques_restantes}")