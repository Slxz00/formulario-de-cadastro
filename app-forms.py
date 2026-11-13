"""
Cadastro de Clientes
Interface gráfica (Tkinter) + banco de dados (SQLite).
"""

import re
import sqlite3
import tkinter as tk
from contextlib import closing
from tkinter import messagebox, ttk

DB_NAME = "clientes.db"
EMAIL_REGEX = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


# ---------------------------------------------------------------------------
# Camada de banco de dados
# ---------------------------------------------------------------------------
def conectar():
    return sqlite3.connect(DB_NAME)


def criar_tabela():
    """Cria a tabela de clientes caso ainda não exista."""
    with closing(conectar()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nome     TEXT NOT NULL,
                email    TEXT NOT NULL UNIQUE,
                telefone TEXT NOT NULL
            )
            """
        )


def inserir_cliente(nome, email, telefone):
    """Insere um cliente e devolve o ID gerado."""
    with closing(conectar()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
            (nome, email, telefone),
        )
        return cursor.lastrowid


def listar_clientes():
    """Devolve todos os clientes cadastrados, do mais recente ao mais antigo."""
    with closing(conectar()) as conn:
        return conn.execute(
            "SELECT id, nome, email, telefone FROM clientes ORDER BY id DESC"
        ).fetchall()


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def formatar_telefone(digitos):
    """Formata 10 ou 11 dígitos como (00) 0000-0000 / (00) 00000-0000."""
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"


# ---------------------------------------------------------------------------
# Interface gráfica
# ---------------------------------------------------------------------------
class CadastroClientesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cadastro de Clientes")
        self.root.geometry("640x460")
        self.root.minsize(560, 420)

        self.var_nome = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_telefone = tk.StringVar()

        # Janela "Visualizar Clientes" (criada sob demanda)
        self.janela_clientes = None
        self.tree_clientes = None
        self.lbl_total = None

        self._montar_formulario()
        self._montar_lista()
        self.atualizar_lista()
        self.entry_nome.focus()

    # ----- construção da tela ------------------------------------------------
    def _montar_formulario(self):
        frame = ttk.LabelFrame(self.root, text="Dados do cliente", padding=12)
        frame.pack(fill="x", padx=12, pady=(12, 6))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_nome = ttk.Entry(frame, textvariable=self.var_nome)
        self.entry_nome.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(frame, text="E-mail:").grid(row=1, column=0, sticky="w", pady=4)
        self.entry_email = ttk.Entry(frame, textvariable=self.var_email)
        self.entry_email.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(frame, text="Telefone:").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_telefone = ttk.Entry(frame, textvariable=self.var_telefone)
        self.entry_telefone.grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        botoes = ttk.Frame(frame)
        botoes.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(botoes, text="Salvar", command=self.salvar).pack(side="left", padx=4)
        ttk.Button(botoes, text="Limpar", command=self.limpar).pack(side="left", padx=4)
        ttk.Button(
            botoes, text="Visualizar Clientes", command=self.visualizar_clientes
        ).pack(side="left", padx=4)

        # Enter salva o cadastro
        self.root.bind("<Return>", lambda _event: self.salvar())

    def _montar_lista(self):
        frame = ttk.LabelFrame(self.root, text="Clientes cadastrados", padding=8)
        frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))
        self.tree = self._criar_treeview(frame, altura=8)

    def _criar_treeview(self, parent, altura=8):
        """Cria uma tabela (Treeview + barra de rolagem) de clientes dentro de 'parent'."""
        colunas = ("id", "nome", "email", "telefone")
        tree = ttk.Treeview(parent, columns=colunas, show="headings", height=altura)
        for col, titulo, largura in (
            ("id", "ID", 50),
            ("nome", "Nome", 180),
            ("email", "E-mail", 200),
            ("telefone", "Telefone", 120),
        ):
            tree.heading(col, text=titulo)
            tree.column(col, width=largura, anchor="w" if col != "id" else "center")

        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    # ----- validação ------------------------------------------------------------
    def _validar(self):
        """Valida os campos. Devolve (dados, None) ou (None, mensagem_de_erro, campo)."""
        nome = self.var_nome.get().strip()
        email = self.var_email.get().strip().lower()
        telefone = self.var_telefone.get().strip()

        if not nome or not email or not telefone:
            return None, "Preencha todos os campos antes de salvar.", self._primeiro_vazio()

        if not EMAIL_REGEX.match(email):
            return None, "Informe um e-mail válido (ex.: nome@dominio.com).", self.entry_email

        digitos = re.sub(r"\D", "", telefone)
        if len(digitos) not in (10, 11):
            return (
                None,
                "Informe um telefone válido com DDD (10 ou 11 dígitos).",
                self.entry_telefone,
            )

        return (nome, email, formatar_telefone(digitos)), None, None

    def _primeiro_vazio(self):
        if not self.var_nome.get().strip():
            return self.entry_nome
        if not self.var_email.get().strip():
            return self.entry_email
        return self.entry_telefone

    # ----- ações ----------------------------------------------------------------
    def salvar(self):
        dados, erro, campo = self._validar()
        if erro:
            messagebox.showwarning("Atenção", erro)
            campo.focus()
            return

        try:
            novo_id = inserir_cliente(*dados)
        except sqlite3.IntegrityError:
            messagebox.showwarning("Atenção", "Já existe um cliente cadastrado com esse e-mail.")
            self.entry_email.focus()
            return
        except sqlite3.Error as exc:
            messagebox.showerror("Erro", f"Não foi possível salvar o cliente:\n{exc}")
            return

        messagebox.showinfo("Sucesso", f"Cliente cadastrado com sucesso (ID {novo_id}).")
        self.limpar()

    def limpar(self):
        """Limpa o formulário e recarrega a lista com os dados atuais do banco."""
        self.var_nome.set("")
        self.var_email.set("")
        self.var_telefone.set("")
        self.tree.selection_remove(self.tree.selection())
        self.atualizar_lista()
        self.entry_nome.focus()

    def visualizar_clientes(self):
        """Abre uma nova janela com todos os clientes cadastrados no banco de dados."""
        # Se a janela já estiver aberta, apenas a traz para frente e atualiza os dados
        if self._janela_clientes_aberta():
            self.janela_clientes.lift()
            self.janela_clientes.focus_force()
            self.atualizar_lista()
            return

        janela = tk.Toplevel(self.root)
        janela.title("Visualizar Clientes")
        janela.geometry("620x380")
        janela.minsize(480, 280)
        janela.transient(self.root)
        self.janela_clientes = janela

        frame = ttk.Frame(janela, padding=12)
        frame.pack(fill="both", expand=True)

        frame_tabela = ttk.Frame(frame)
        frame_tabela.pack(fill="both", expand=True)
        self.tree_clientes = self._criar_treeview(frame_tabela, altura=12)

        rodape = ttk.Frame(frame)
        rodape.pack(fill="x", pady=(10, 0))
        self.lbl_total = ttk.Label(rodape, text="")
        self.lbl_total.pack(side="left")
        ttk.Button(rodape, text="Fechar", command=janela.destroy).pack(side="right")
        ttk.Button(rodape, text="Atualizar", command=self.atualizar_lista).pack(
            side="right", padx=4
        )

        self.atualizar_lista()

    def _janela_clientes_aberta(self):
        return self.janela_clientes is not None and self.janela_clientes.winfo_exists()

    @staticmethod
    def _preencher_tree(tree, clientes):
        tree.delete(*tree.get_children())
        for cliente in clientes:
            tree.insert("", "end", values=cliente)

    def atualizar_lista(self):
        """Recarrega os dados do banco na lista principal e na janela de visualização (se aberta)."""
        try:
            clientes = listar_clientes()
        except sqlite3.Error as exc:
            messagebox.showerror("Erro", f"Não foi possível carregar os clientes:\n{exc}")
            return

        self._preencher_tree(self.tree, clientes)

        if self._janela_clientes_aberta():
            self._preencher_tree(self.tree_clientes, clientes)
            total = len(clientes)
            if total == 0:
                self.lbl_total.config(text="Nenhum cliente cadastrado.")
            else:
                self.lbl_total.config(text=f"Total de clientes: {total}")


def main():
    criar_tabela()
    root = tk.Tk()
    CadastroClientesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
