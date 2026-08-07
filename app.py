from datetime import datetime
import sqlite3
import pandas as pd
import flet as ft

def conectar_bd():
    conn = sqlite3.connect("dados_financeiros.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            data TEXT,
            descricao TEXT,
            tipo TEXT,
            categoria TEXT,
            valor REAL
        )
    """)
    conn.commit()
    return conn, cursor

conn, cursor = conectar_bd()

USUARIOS_PERMITIDOS = {
    "rita": "1234",
    "cliente1": "senha2026",
    "cliente2": "gastos10",
    "hotmart": "teste2026"
}

# Categorias aprimoradas solicitadas
CATEGORIAS_ENTRADA = ["Salário", "Renda Extra", "Pagamento", "Trabalho", "Outros"]
CATEGORIAS_SAIDA = ["Mercado", "Contas de casa", "Combustível", "Alimentação", "Supérfluo", "Passeio", "Outros"]

# Cores distintas e impactantes para cada categoria
CORES_CATEGORIAS = {
    # Saídas (tons quentes e marcantes)
    "Mercado": "#E53935",          # Vermelho forte
    "Contas de casa": "#FB8C00",   # Laranja escuro
    "Combustível": "#8E24AA",      # Roxo forte
    "Alimentação": "#FF7043",      # Laranja suave
    "Supérfluo": "#EC407A",        # Rosa choque
    "Passeio": "#42A5F5",          # Azul claro
    "Outros": "#78909C",           # Cinza azulado
    
    # Entradas (tons esverdeados)
    "Salário": "#2E7D32",          # Verde escuro forte
    "Renda Extra": "#43A047",      # Verde vibrante
    "Pagamento": "#66BB6A",        # Verde claro
    "Trabalho": "#26A69A"          # Verde água
}

def main(page: ft.Page):
    page.title = "Gestor de Gastos Mensais"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO
    page.fonts = {
        "Inter": "https://fonts.gstatic.com/s/inter/v13/UcC73FwrK3iLTeHuS_fvQtMwCp50KnMa1ZL7W0Q5nw.woff2"
    }
    page.theme = ft.Theme(font_family="Inter")
    page.icon = "icon-512.png"

    session = {"autenticado": False, "usuario_atual": ""}

    def carregar_dados_usuario():
        query = "SELECT id, data as Data, descricao as Descrição, tipo as Tipo, categoria as Categoria, valor as Valor FROM transacoes WHERE usuario = ? ORDER BY id DESC"
        return pd.read_sql_query(query, conn, params=(session["usuario_atual"],))

    def mudar_tela(route):
        page.clean()
        
        if not session["autenticado"]:
            logo = ft.Image(src="icon-512.png", width=90, height=90)
            titulo = ft.Text("Gestor de Gastos", size=20, weight=ft.FontWeight.W_600, color="pink")
            subtitulo = ft.Text("Faça login para continuar", size=13, color="#AAAAAA")
            
            txt_usuario = ft.TextField(label="Usuário", border_radius=10, text_size=14, height=50)
            txt_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, border_radius=10, text_size=14, height=50)
            lbl_erro = ft.Text(color="red", size=12)

            def fazer_login(e):
                u = txt_usuario.value.strip().lower()
                s = txt_senha.value.strip()
                if u in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[u] == s:
                    session["autenticado"] = True
                    session["usuario_atual"] = u
                    mudar_tela("/")
                else:
                    lbl_erro.value = "⚠️ Usuário ou senha incorretos."
                    page.update()

            btn_entrar = ft.ElevatedButton(
                content=ft.Text("ENTRAR NO APP", color="white", size=13, weight=ft.FontWeight.W_600),
                on_click=fazer_login,
                bgcolor="pink",
                width=300,
                height=45
            )

            page.add(
                ft.Column([
                    logo,
                    ft.Container(height=10),
                    titulo,
                    subtitulo,
                    ft.Container(height=15),
                    txt_usuario,
                    txt_senha,
                    lbl_erro,
                    ft.Container(height=10),
                    btn_entrar
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=320)
            )
        else:
            df = carregar_dados_usuario()

            def fazer_logout(e):
                session["autenticado"] = False
                session["usuario_atual"] = ""
                mudar_tela("/")

            logo_topo = ft.Image(src="icon-512.png", width=36, height=36)

            header = ft.Row([
                ft.Row([
                    logo_topo,
                    ft.Column([
                        ft.Text("Gestor de Gastos", size=14, weight=ft.FontWeight.BOLD, color="pink"),
                        ft.Text(f"👤 {session['usuario_atual'].upper()}", size=11, color="#AAAAAA")
                    ], spacing=1)
                ], alignment=ft.MainAxisAlignment.START),
                ft.TextButton(content=ft.Text("Sair", color="pink", size=13), on_click=fazer_logout)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            editando_id = ft.Ref[int]()
            editando_id.current = None

            txt_desc = ft.TextField(label="Descrição (Ex: Compras do mês)", border_radius=10, text_size=14, height=50)
            
            dd_cat = ft.Dropdown(
                label="Categoria", 
                options=[ft.dropdown.Option(c) for c in CATEGORIAS_SAIDA], 
                value="Mercado", 
                border_radius=10,
                text_size=14
            )

            dd_tipo = ft.Dropdown(
                label="Tipo", 
                options=[ft.dropdown.Option("Saída"), ft.dropdown.Option("Entrada")], 
                value="Saída", 
                border_radius=10,
                text_size=14
            )

            def ajustar_cats_tipo(e):
                if dd_tipo.value == "Entrada":
                    dd_cat.options = [ft.dropdown.Option(c) for c in CATEGORIAS_ENTRADA]
                    dd_cat.value = "Salário"
                else:
                    dd_cat.options = [ft.dropdown.Option(c) for c in CATEGORIAS_SAIDA]
                    dd_cat.value = "Mercado"
                page.update()

            btn_tipo_filtro = ft.TextButton(content=ft.Text("🔄 Atualizar Categorias pelo Tipo", size=11, color="pink"), on_click=ajustar_cats_tipo)

            txt_valor = ft.TextField(label="Valor (R$)", value="0.00", border_radius=10, text_size=14, height=50)
            
            data_atual_str = datetime.now().strftime("%d/%m/%Y")
            txt_data = ft.TextField(label="Data (DD/MM/AAAA)", value=data_atual_str, border_radius=10, text_size=14, height=50)
            lbl_msg_lancamento = ft.Text(size=12)

            btn_salvar_texto = ft.Text("SALVAR LANÇAMENTO", color="white", size=13, weight=ft.FontWeight.W_600)

            def salvar_lancamento(e):
                try:
                    val = float(txt_valor.value.replace(",", "."))
                    desc = txt_desc.value.strip()
                    if not desc or val <= 0:
                        lbl_msg_lancamento.value = "⚠️ Preencha a descrição e um valor válido."
                        lbl_msg_lancamento.color = "red"
                        page.update()
                        return

                    if editando_id.current is None:
                        cursor.execute(
                            "INSERT INTO transacoes (usuario, data, descricao, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?, ?)",
                            (session["usuario_atual"], txt_data.value, desc, dd_tipo.value, dd_cat.value, val)
                        )
                        lbl_msg_lancamento.value = "✅ Lançamento salvo com sucesso!"
                    else:
                        cursor.execute(
                            "UPDATE transacoes SET data=?, descricao=?, tipo=?, categoria=?, valor=? WHERE id=?",
                            (txt_data.value, desc, dd_tipo.value, dd_cat.value, val, editando_id.current)
                        )
                        lbl_msg_lancamento.value = "✅ Lançamento corrigido com sucesso!"
                        editando_id.current = None
                        btn_salvar_texto.value = "SALVAR LANÇAMENTO"

                    conn.commit()
                    txt_desc.value = ""
                    txt_valor.value = "0.00"
                    txt_data.value = datetime.now().strftime("%d/%m/%Y")
                    lbl_msg_lancamento.color = "green"
                    page.update()
                    mudar_tela("/")
                except Exception as ex:
                    lbl_msg_lancamento.value = f"⚠️ Erro ao salvar: {ex}"
                    lbl_msg_lancamento.color = "red"
                    page.update()

            btn_salvar = ft.ElevatedButton(
                content=btn_salvar_texto,
                on_click=salvar_lancamento,
                bgcolor="pink",
                width=400,
                height=45
            )

            # Função para abrir detalhes completos ao clicar em uma categoria (Ex: Mercado, Combustível)
            def abrir_detalhes_categoria(tipo_cat, nome_cat):
                df_filtrado = df[(df["Tipo"] == tipo_cat) & (df["Categoria"] == nome_cat)]
                
                itens_lista = []
                for _, r in df_filtrado.iterrows():
                    cor_val = "green" if tipo_cat == "Entrada" else "#E53935"
                    itens_lista.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"📅 {r['Data']} (ID #{r['id']})", size=11, color="#AAAAAA"),
                                    ft.Text(f"{r['Descrição']}", size=13, weight=ft.FontWeight.W_500, color="white")
                                ], spacing=2),
                                ft.Text(f"R$ {r['Valor']:.2f}", size=13, weight=ft.FontWeight.BOLD, color=cor_val)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=10,
                            bgcolor="#222222",
                            border_radius=8,
                            margin=ft.margin.only(bottom=6)
                        )
                    )

                total_cat = df_filtrado["Valor"].sum()

                dlg = ft.AlertDialog(
                    title=ft.Text(f"{nome_cat} ({tipo_cat})", size=16, weight=ft.FontWeight.BOLD, color="pink"),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Total gasto/recebido: R$ {total_cat:.2f}", size=13, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Divider(height=10),
                            ft.Column(itens_lista, scroll=ft.ScrollMode.AUTO, tight=True)
                        ], tight=True),
                        width=340,
                        height=350
                    ),
                    actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(dlg))]
                )
                page.open(dlg)

            componentes_resumo = []
            if not df.empty:
                total_entradas = df[df["Tipo"] == "Entrada"]["Valor"].sum()
                total_saidas = df[df["Tipo"] == "Saída"]["Valor"].sum()
                saldo = total_entradas - total_saidas

                cards_row = ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("GANHOS", size=10, color="#AAAAAA", weight=ft.FontWeight.BOLD),
                            ft.Text(f"R$ {total_entradas:.2f}", size=12, color="green", weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#222222", padding=8, border_radius=10, expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("GASTOS", size=10, color="#AAAAAA", weight=ft.FontWeight.BOLD),
                            ft.Text(f"R$ {total_saidas:.2f}", size=12, color="#E53935", weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#222222", padding=8, border_radius=10, expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("SALDO", size=10, color="#AAAAAA", weight=ft.FontWeight.BOLD),
                            ft.Text(f"R$ {saldo:.2f}", size=12, color="#42A5F5", weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#222222", padding=8, border_radius=10, expand=True
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                componentes_resumo.append(cards_row)

                componentes_resumo.append(ft.Container(height=5))
                componentes_resumo.append(ft.Text("📋 Toque em uma categoria para ver o extrato detalhado", size=12, color="#AAAAAA"))
                
                df_agrupado = df.groupby(["Tipo", "Categoria"])["Valor"].sum().reset_index()
                for _, row in df_agrupado.iterrows():
                    t_cat = row["Tipo"]
                    n_cat = row["Categoria"]
                    val_cat = row["Valor"]
                    cor_badge = CORES_CATEGORIAS.get(n_cat, "pink")
                    
                    item_agrupado = ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Container(width=12, height=12, bgcolor=cor_badge, border_radius=6),
                                ft.Text(f"[{t_cat}] {n_cat}", size=13, weight=ft.FontWeight.W_500)
                            ], spacing=8),
                            ft.Text(f"R$ {val_cat:.2f}", size=13, weight=ft.FontWeight.BOLD, color=cor_badge)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=12,
                        bgcolor="#1E1E1E",
                        border_radius=8,
                        margin=ft.margin.only(bottom=4),
                        ink=True,
                        on_click=lambda e, tc=t_cat, nc=n_cat: abrir_detalhes_categoria(tc, nc)
                    )
                    componentes_resumo.append(item_agrupado)

            lista_transacoes_dropdown = []
            if not df.empty:
                for _, r in df.iterrows():
                    lbl = f"ID {r['id']} - [{r['Data']}] {r['Categoria']}: {r['Descrição']} (R$ {r['Valor']:.2f})"
                    lista_transacoes_dropdown.append(ft.dropdown.Option(text=lbl, key=str(r['id'])))

            dd_transacao_escolhida = ft.Dropdown(label="Selecionar Lançamento para Corrigir / Apagar", options=lista_transacoes_dropdown, border_radius=10, text_size=13)

            def carregar_para_correcao(e):
                if dd_transacao_escolhida.value:
                    id_alvo = int(dd_transacao_escolhida.value)
                    transacao_selecionada = df[df["id"] == id_alvo]
                    if not transacao_selecionada.empty:
                        t = transacao_selecionada.iloc[0]
                        editando_id.current = t["id"]
                        txt_desc.value = t["Descrição"]
                        dd_tipo.value = t["Tipo"]
                        ajustar_cats_tipo(None)
                        dd_cat.value = t["Categoria"]
                        txt_valor.value = str(t["Valor"])
                        txt_data.value = t["Data"]
                        btn_salvar_texto.value = f"ATUALIZAR LANÇAMENTO #{t['id']}"
                        lbl_msg_lancamento.value = f"✏️ Editando ID {t['id']}. Altere e clique em Salvar."
                        lbl_msg_lancamento.color = "orange"
                        page.update()

            def apagar_lancamento(e):
                if dd_transacao_escolhida.value:
                    id_alvo = int(dd_transacao_escolhida.value)
                    cursor.execute("DELETE FROM transacoes WHERE id=?", (id_alvo,))
                    conn.commit()
                    mudar_tela("/")

            def apagar_mes_inteiro(e):
                cursor.execute("DELETE FROM transacoes WHERE usuario=?", (session["usuario_atual"],))
                conn.commit()
                mudar_tela("/")

            btn_corrigir = ft.ElevatedButton(
                content=ft.Text("CORRIGIR SELECIONADO", color="white", size=12),
                on_click=carregar_para_correcao,
                bgcolor="orange",
                height=40
            )

            btn_apagar = ft.ElevatedButton(
                content=ft.Text("EXCLUIR SELECIONADO", color="white", size=12),
                on_click=apagar_lancamento,
                bgcolor="red",
                height=40
            )

            btn_apagar_mes = ft.ElevatedButton(
                content=ft.Text("DELETAR TUDO DO MÊS", color="white", size=12, weight=ft.FontWeight.W_600),
                on_click=apagar_mes_inteiro,
                bgcolor="darkred",
                width=400,
                height=40
            )

            page.add(
                header,
                ft.Divider(height=15),
                ft.Text("➕ Novo Lançamento / Edição", size=14, weight=ft.FontWeight.BOLD),
                txt_desc,
                ft.Row([dd_tipo, dd_cat]),
                btn_tipo_filtro,
                ft.Row([txt_valor, txt_data]),
                btn_salvar,
                lbl_msg_lancamento,
                ft.Divider(height=15),
                ft.Text("📊 Resumo do Mês", size=14, weight=ft.FontWeight.BOLD),
                *componentes_resumo,
                ft.Container(height=5),
                ft.Text("✏️ Gerenciar Lançamentos", size=14, weight=ft.FontWeight.BOLD),
                dd_transacao_escolhida,
                ft.Row([btn_corrigir, btn_apagar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=5),
                btn_apagar_mes,
                ft.Container(height=20)
            )

    mudar_tela("/")

if __name__ == "__main__":
    ft.app(target=main, port=8550, host="0.0.0.0")



   


    