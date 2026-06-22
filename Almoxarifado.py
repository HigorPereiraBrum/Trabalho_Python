import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

class Almoxarifado:
    def __init__(self, caminho_arquivo="almoxarifado_dados.csv"):
        self.caminho_arquivo = caminho_arquivo
        self.colunas_base = ["ID", "Produto", "Categoria", "Qtd_Atual", "Qtd_Minima", "Preco_Unitario", "Cor_Hex"]
        self.carregar_dados()

    def carregar_dados(self):
        if os.path.exists(self.caminho_arquivo):
            try:
                self.df = pd.read_csv(self.caminho_arquivo)
                for col in self.colunas_base:
                    if col not in self.df.columns:
                        self.df[col] = ""
            except Exception as e:
                print(f"Erro ao carregar CSV: {e}")
                self.df = pd.DataFrame(columns=self.colunas_base)
        else:
            self.df = pd.DataFrame(columns=self.colunas_base)

    def salvar_dados(self):
        self.df.to_csv(self.caminho_arquivo, index=False)

    def adicionar_item(self, dados):
        novo_df = pd.DataFrame([dados])
        self.df = pd.concat([self.df, novo_df], ignore_index=True)
        self.salvar_dados()

    def excluir_item(self, item_id):
        self.df = self.df[self.df['ID'].astype(str) != str(item_id)].copy()
        self.salvar_dados()

    def editar_item(self, item_id, novos_dados):
        idx = self.df[self.df['ID'].astype(str) == str(item_id)].index
        if not idx.empty:
            for key, value in novos_dados.items():
                if key in self.df.columns:
                    self.df.loc[idx, key] = value
            self.salvar_dados()
            return True
        return False

class AppAlmoxarifado(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sistema = Almoxarifado()
        self.title("Sistema de Almoxarifado - Desktop")
        self.geometry("1200x800")
        self.configure(bg="#f0f2f5")
        
        self.cor_selecionada = "#3498db"
        
        self.setup_ui()
        self.atualizar_visualizacao()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=30, font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        
        main_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- LADO ESQUERDO: FORMULÁRIO ---
        left_frame = tk.Frame(main_container, bg="#ffffff", bd=1, relief=tk.RIDGE)
        main_container.add(left_frame, weight=1)

        tk.Label(left_frame, text="📝 GESTÃO DE ITEM", font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#2c3e50").pack(pady=20)
        
        self.form_frame = tk.Frame(left_frame, bg="#ffffff")
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.entries = {}
        campos = [
            ("ID", "ID do Item"),
            ("Produto", "Nome do Produto"),
            ("Categoria", "Categoria"),
            ("Qtd_Atual", "Quantidade Atual"),
            ("Qtd_Minima", "Quantidade Mínima"),
            ("Preco_Unitario", "Preço Unitário (R$)")
        ]

        for key, label in campos:
            frame = tk.Frame(self.form_frame, bg="#ffffff")
            frame.pack(fill=tk.X, pady=5)
            tk.Label(frame, text=label, bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w")
            entry = ttk.Entry(frame)
            entry.pack(fill=tk.X, ipady=5)
            self.entries[key] = entry

        tk.Label(self.form_frame, text="Cor de Destaque", bg="#ffffff", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10,0))
        self.btn_cor = tk.Button(self.form_frame, text="Selecionar Cor", bg=self.cor_selecionada, fg="white", 
                                 command=self.escolher_cor, relief=tk.FLAT, font=("Segoe UI", 9, "bold"))
        self.btn_cor.pack(fill=tk.X, pady=10, ipady=8)

        # Botões de Ação
        btn_frame = tk.Frame(left_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X, pady=20, padx=20)
        
        ttk.Button(btn_frame, text="💾 SALVAR / ATUALIZAR", command=self.salvar_item).pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(btn_frame, text="✏️ EDITAR SELECIONADO", command=self.carregar_para_edicao_btn).pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(btn_frame, text="🗑️ DELETAR SELECIONADO", command=self.deletar_item).pack(fill=tk.X, pady=5, ipady=5)
        ttk.Button(btn_frame, text="🧹 LIMPAR CAMPOS", command=self.limpar_campos).pack(fill=tk.X, pady=5, ipady=5)

        # --- LADO DIREITO: TABELA E GRÁFICO ---
        right_frame = tk.Frame(main_container, bg="#f0f2f5")
        main_container.add(right_frame, weight=3)

        # Filtro e Exportação
        top_bar = tk.Frame(right_frame, bg="#f0f2f5")
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_bar, text="🔍 Pesquisar:", bg="#f0f2f5", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.entry_filtro = ttk.Entry(top_bar)
        self.entry_filtro.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True, ipady=3)
        self.entry_filtro.bind("<KeyRelease>", lambda e: self.atualizar_tabela())
        
        ttk.Button(top_bar, text="📸 EXPORTAR TABELA (IMG)", command=self.exportar_tabela_imagem).pack(side=tk.RIGHT, padx=5)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Aba Tabela
        self.tab_tabela = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_tabela, text=" 📋 Lista de Itens ")
        
        columns = ("ID", "Produto", "Categoria", "Qtd", "Mínimo", "Preço")
        self.tree = ttk.Treeview(self.tab_tabela, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        tree_scroll = ttk.Scrollbar(self.tab_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self.carregar_para_edicao_btn())

        # Aba Gráfico
        self.tab_grafico = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_grafico, text=" 📊 Visualização Gráfica ")
        self.fig_canvas = None

    def escolher_cor(self):
        cor = colorchooser.askcolor(title="Escolha a cor do item")[1]
        if cor:
            self.cor_selecionada = cor
            self.btn_cor.config(bg=cor)

    def salvar_item(self):
        try:
            dados = {k: v.get() for k, v in self.entries.items()}
            if not dados["ID"] or not dados["Produto"]:
                messagebox.showwarning("Aviso", "ID e Produto são obrigatórios!")
                return
            
            dados["Cor_Hex"] = self.cor_selecionada
            
            if any(self.sistema.df['ID'].astype(str) == str(dados["ID"])):
                self.sistema.editar_item(dados["ID"], dados)
                messagebox.showinfo("Sucesso", "Item atualizado!")
            else:
                self.sistema.adicionar_item(dados)
                messagebox.showinfo("Sucesso", "Item cadastrado!")
            
            self.atualizar_visualizacao()
            self.limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def carregar_para_edicao_btn(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um item na tabela primeiro!")
            return
        
        item_id = str(self.tree.item(selected[0])['values'][0])
        item_data = self.sistema.df[self.sistema.df['ID'].astype(str) == item_id].iloc[0].to_dict()
        
        self.limpar_campos()
        for key, entry in self.entries.items():
            if key in item_data:
                entry.insert(0, str(item_data[key]))
        
        self.cor_selecionada = item_data.get("Cor_Hex", "#3498db")
        self.btn_cor.config(bg=self.cor_selecionada)

    def deletar_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um item para deletar!")
            return
        
        item_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirmar", f"Deseja excluir o item ID {item_id}?"):
            self.sistema.excluir_item(item_id)
            self.atualizar_visualizacao()

    def limpar_campos(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.cor_selecionada = "#3498db"
        self.btn_cor.config(bg=self.cor_selecionada)

    def atualizar_tabela(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        filtro = self.entry_filtro.get().lower()
        df_view = self.sistema.df
        
        if filtro:
            mask = (
                df_view['Produto'].astype(str).str.contains(filtro, case=False, na=False) |
                df_view['Categoria'].astype(str).str.contains(filtro, case=False, na=False)
            )
            df_view = df_view[mask]

        for _, row in df_view.iterrows():
            self.tree.insert("", tk.END, values=(
                row.get("ID", ""),
                row.get("Produto", ""),
                row.get("Categoria", ""),
                row.get("Qtd_Atual", ""),
                row.get("Qtd_Minima", ""),
                row.get("Preco_Unitario", "")
            ))

    def atualizar_grafico(self):
        if self.fig_canvas:
            self.fig_canvas.get_tk_widget().destroy()
            
        if self.sistema.df.empty:
            return

        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        df_plot = self.sistema.df.copy()
        df_plot["Qtd_Atual"] = pd.to_numeric(df_plot["Qtd_Atual"], errors='coerce').fillna(0)
        cores = df_plot.set_index('Produto')['Cor_Hex'].to_dict()
        
        sns.barplot(x="Qtd_Atual", y="Produto", data=df_plot, palette=cores, ax=ax)
        ax.set_title("📦 Nível de Estoque por Item", fontsize=12, fontweight='bold')
        plt.tight_layout()

        self.fig_canvas = FigureCanvasTkAgg(fig, master=self.tab_grafico)
        self.fig_canvas.draw()
        self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def atualizar_visualizacao(self):
        self.atualizar_tabela()
        self.atualizar_grafico()

    def exportar_tabela_imagem(self):
        if self.sistema.df.empty:
            messagebox.showwarning("Aviso", "Não há dados para exportar!")
            return

        caminho = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not caminho:
            return

        try:
            # Criar uma figura do Matplotlib para a tabela
            fig, ax = plt.subplots(figsize=(10, len(self.sistema.df) * 0.5 + 1))
            ax.axis('off')
            
            df_export = self.sistema.df.drop(columns=['Cor_Hex'])
            tabela = ax.table(cellText=df_export.values, colLabels=df_export.columns, loc='center', cellLoc='center')
            
            tabela.auto_set_font_size(False)
            tabela.set_fontsize(10)
            tabela.scale(1.2, 1.2)
            
            plt.title("Relatório de Almoxarifado", fontsize=14, pad=20)
            plt.savefig(caminho, bbox_inches='tight', dpi=300)
            plt.close()
            messagebox.showinfo("Sucesso", f"Imagem salva em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar imagem: {e}")

if __name__ == "__main__":
    app = AppAlmoxarifado()
    app.mainloop()
