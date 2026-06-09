from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "senha_secreta_master"

def conectar():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    if "usuario" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = conectar()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE usuario=?",
            (usuario,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["senha"], senha):
            session["usuario"] = user["usuario"]
            session["perfil"] = user["perfil"]
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/usuarios")
def usuarios():
    if session.get("perfil") != "MASTER":
        return "Acesso negado"

    conn = conectar()
    lista = conn.execute("SELECT * FROM usuarios").fetchall()
    conn.close()

    return render_template("usuarios.html", usuarios=lista)

@app.route("/novo_usuario", methods=["GET", "POST"])
def novo_usuario():
    if session.get("perfil") != "MASTER":
        return "Acesso negado"

    if request.method == "POST":
        nome = request.form["nome"]
        usuario = request.form["usuario"]
        senha = generate_password_hash(request.form["senha"])
        perfil = request.form["perfil"]

        conn = conectar()
        conn.execute(
            "INSERT INTO usuarios(nome,usuario,senha,perfil) VALUES(?,?,?,?)",
            (nome, usuario, senha, perfil)
        )
        conn.commit()
        conn.close()

        return redirect("/usuarios")

    return render_template("novo_usuario.html")

@app.route("/notas")
def notas():
    conn = conectar()
    dados = conn.execute(
        "SELECT * FROM notas ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("notas.html", notas=dados)

@app.route("/nova_nota", methods=["GET", "POST"])
def nova_nota():
    if request.method == "POST":
        numero = request.form["numero"]
        fornecedor = request.form["fornecedor"]
        produto = request.form["produto"]
        quantidade = request.form["quantidade"]

        conn = conectar()
        conn.execute(
            """
            INSERT INTO notas
            (numero, fornecedor, produto, quantidade)
            VALUES (?, ?, ?, ?)
            """,
            (numero, fornecedor, produto, quantidade)
        )
        conn.commit()
        conn.close()

        return redirect("/notas")

    return render_template("nova_nota.html")

if __name__ == "__main__":
    app.run(debug=True)
