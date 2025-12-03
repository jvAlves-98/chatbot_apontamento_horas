import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import os

class GerenciadorFuncionarios:
    def __init__(self):
        """Inicializa conexão com banco de dados PostgreSQL"""
        self.conn = None
        self.conectar()
    
    def conectar(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        
        load_dotenv(dotenv_path)
        """Estabelece conexão com PostgreSQL"""
        
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('HOST_DW'),
                database=os.getenv('DBNAME_DW'),
                user=os.getenv('USER_DW'),
                password=os.getenv('PASS_DW'),
                port=os.getenv('PORT_DW'),
                options='-c search_path=apontador_horas,public'
            )
            print("✅ Conectado ao banco de dados com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco: {e}")
            exit(1)
    
    def hash_senha(self, senha):
        """Gera hash SHA-256 da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def inserir_funcionario(self):
        """Insere novo funcionário"""
        print("\n" + "="*60)
        print("📝 CADASTRAR NOVO FUNCIONÁRIO")
        print("="*60)
        
        try:
            # Coleta dados
            usuario = input("Usuário (login): ").strip()
            senha = input("Senha: ").strip()
            email = input("E-mail: ").strip()
            nome_completo = input("Nome Completo: ").strip()
            departamento = input("Departamento: ").strip()
            
            print("\nNíveis disponíveis:")
            print("1 - funcionario")
            print("2 - coordenador")
            print("3 - supervisor")
            print("4 - socio")
            print("5 - prestador de servico")
            print("6 - admin")
            nivel_opcao = input("Escolha o nível (1-6): ").strip()
            niveis = {
                '1': 'funcionario', 
                '2': 'coordenador', 
                '3': 'supervisor', 
                '4': 'socio',
                '5': 'prestador de servico',
                '6': 'admin'
            }
            nivel = niveis.get(nivel_opcao, 'funcionario')
            
            # Gestor
            gestor = input("Nome do Gestor: ").strip()
            
            # Gestor ID (opcional)
            gestor_input = input("ID do Gestor (deixe vazio se não souber): ").strip()
            gestor_id = int(gestor_input) if gestor_input else None
            
            # Hash da senha
            senha_hash = self.hash_senha(senha)
            
            # Inserir no banco
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO apontador_horas.funcionarios 
                (usuario, senha_hash, email, nome_completo, departamento, nivel, gestor, gestor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (usuario, senha_hash, email, nome_completo, departamento, nivel, gestor, gestor_id))
            
            id_novo = cursor.fetchone()[0]
            self.conn.commit()
            
            print(f"\n✅ Funcionário cadastrado com sucesso! ID: {id_novo}")
            
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            print(f"\n❌ Erro: Usuário ou e-mail já existe no sistema")
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Erro ao cadastrar: {e}")
    
    def listar_funcionarios(self):
        """Lista todos os funcionários"""
        print("\n" + "="*60)
        print("👥 LISTA DE FUNCIONÁRIOS")
        print("="*60)
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    id, usuario, nome_completo, email, 
                    departamento, nivel, ativo, gestor
                FROM apontador_horas.funcionarios
                ORDER BY nome_completo
            """)
            
            funcionarios = cursor.fetchall()
            
            if not funcionarios:
                print("\n⚠️ Nenhum funcionário cadastrado")
                return
            
            print(f"\n{'ID':<5} {'Usuário':<15} {'Nome':<25} {'Depto':<15} {'Nível':<12} {'Ativo':<6} {'Gestor':<20}")
            print("-" * 120)
            
            for func in funcionarios:
                ativo = "✓" if func['ativo'] else "✗"
                gestor = func['gestor'] if func['gestor'] else "-"
                print(f"{func['id']:<5} {func['usuario']:<15} {func['nome_completo']:<25} "
                      f"{func['departamento']:<15} {func['nivel']:<12} {ativo:<6} {gestor:<20}")
            
            print(f"\nTotal: {len(funcionarios)} funcionários")
            
        except Exception as e:
            print(f"\n❌ Erro ao listar: {e}")
    
    def alterar_senha(self):
        """Altera senha de um funcionário"""
        print("\n" + "="*60)
        print("🔑 ALTERAR SENHA")
        print("="*60)
        
        try:
            usuario = input("Usuário: ").strip()
            nova_senha = input("Nova senha: ").strip()
            
            senha_hash = self.hash_senha(nova_senha)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE apontador_horas.funcionarios 
                SET senha_hash = %s
                WHERE usuario = %s
            """, (senha_hash, usuario))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                print("\n✅ Senha alterada com sucesso!")
            else:
                print("\n⚠️ Usuário não encontrado")
            
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Erro ao alterar senha: {e}")
    
    def alterar_status(self):
        """Ativa ou desativa um funcionário"""
        print("\n" + "="*60)
        print("🔄 ALTERAR STATUS (ATIVO/INATIVO)")
        print("="*60)
        
        try:
            usuario = input("Usuário: ").strip()
            
            # Busca status atual
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT ativo, nome_completo FROM apontador_horas.funcionarios WHERE usuario = %s", (usuario,))
            func = cursor.fetchone()
            
            if not func:
                print("\n⚠️ Usuário não encontrado")
                return
            
            status_atual = "ATIVO" if func['ativo'] else "INATIVO"
            print(f"\nFuncionário: {func['nome_completo']}")
            print(f"Status atual: {status_atual}")
            
            novo_status = not func['ativo']
            confirma = input(f"\nDeseja {'ATIVAR' if novo_status else 'DESATIVAR'}? (s/n): ").strip().lower()
            
            if confirma == 's':
                cursor.execute("""
                    UPDATE apontador_horas.funcionarios 
                    SET ativo = %s
                    WHERE usuario = %s
                """, (novo_status, usuario))
                self.conn.commit()
                print(f"\n✅ Funcionário {'ATIVADO' if novo_status else 'DESATIVADO'} com sucesso!")
            else:
                print("\n❌ Operação cancelada")
            
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Erro ao alterar status: {e}")
    
    def alterar_departamento(self):
        """Altera departamento de um funcionário"""
        print("\n" + "="*60)
        print("🏢 ALTERAR DEPARTAMENTO")
        print("="*60)
        
        try:
            usuario = input("Usuário: ").strip()
            novo_depto = input("Novo Departamento: ").strip()
            
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE apontador_horas.funcionarios 
                SET departamento = %s
                WHERE usuario = %s
            """, (novo_depto, usuario))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                print("\n✅ Departamento alterado com sucesso!")
            else:
                print("\n⚠️ Usuário não encontrado")
            
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Erro ao alterar departamento: {e}")
    
    def alterar_nivel(self):
        """Altera nível de acesso de um funcionário"""
        print("\n" + "="*60)
        print("⭐ ALTERAR NÍVEL DE ACESSO")
        print("="*60)
        
        try:
            usuario = input("Usuário: ").strip()
            
            print("\nNíveis disponíveis:")
            print("1 - funcionario")
            print("2 - coordenador")
            print("3 - supervisor")
            print("4 - socio")
            print("5 - prestador de servico")
            print("6 - admin")
            nivel_opcao = input("Escolha o novo nível (1-6): ").strip()
            niveis = {
                '1': 'funcionario', 
                '2': 'coordenador', 
                '3': 'supervisor', 
                '4': 'socio',
                '5': 'prestador de servico',
                '6': 'admin'
            }
            novo_nivel = niveis.get(nivel_opcao)
            
            if not novo_nivel:
                print("\n❌ Nível inválido")
                return
            
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE apontador_horas.funcionarios 
                SET nivel = %s
                WHERE usuario = %s
            """, (novo_nivel, usuario))
            
            if cursor.rowcount > 0:
                self.conn.commit()
                print(f"\n✅ Nível alterado para '{novo_nivel}' com sucesso!")
            else:
                print("\n⚠️ Usuário não encontrado")
            
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Erro ao alterar nível: {e}")
    
    def buscar_funcionario(self):
        """Busca detalhes de um funcionário"""
        print("\n" + "="*60)
        print("🔍 BUSCAR FUNCIONÁRIO")
        print("="*60)
        
        try:
            usuario = input("Usuário: ").strip()
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    id, usuario, nome_completo, email, 
                    departamento, nivel, ativo, gestor
                FROM apontador_horas.funcionarios
                WHERE usuario = %s
            """, (usuario,))
            
            func = cursor.fetchone()
            
            if not func:
                print("\n⚠️ Usuário não encontrado")
                return
            
            print("\n" + "-"*60)
            print(f"ID: {func['id']}")
            print(f"Usuário: {func['usuario']}")
            print(f"Nome Completo: {func['nome_completo']}")
            print(f"E-mail: {func['email']}")
            print(f"Departamento: {func['departamento']}")
            print(f"Nível: {func['nivel']}")
            print(f"Status: {'ATIVO' if func['ativo'] else 'INATIVO'}")
            print(f"Gestor: {func['gestor']}")
            print("-"*60)
            
        except Exception as e:
            print(f"\n❌ Erro ao buscar: {e}")
    
    def menu_principal(self):
        """Exibe menu principal"""
        while True:
            print("\n" + "="*60)
            print("⏱️  SISTEMA DE GERENCIAMENTO DE FUNCIONÁRIOS - BOOKER")
            print("="*60)
            print("1 - Cadastrar novo funcionário")
            print("2 - Listar todos os funcionários")
            print("3 - Buscar funcionário")
            print("4 - Alterar senha")
            print("5 - Alterar status (ativar/desativar)")
            print("6 - Alterar departamento")
            print("7 - Alterar nível de acesso")
            print("0 - Sair")
            print("="*60)
            
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == '1':
                self.inserir_funcionario()
            elif opcao == '2':
                self.listar_funcionarios()
            elif opcao == '3':
                self.buscar_funcionario()
            elif opcao == '4':
                self.alterar_senha()
            elif opcao == '5':
                self.alterar_status()
            elif opcao == '6':
                self.alterar_departamento()
            elif opcao == '7':
                self.alterar_nivel()
            elif opcao == '0':
                print("\n👋 Encerrando sistema...")
                break
            else:
                print("\n❌ Opção inválida!")
            
            input("\nPressione ENTER para continuar...")
    
    def __del__(self):
        """Fecha conexão ao destruir objeto"""
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    # Configurar variáveis de ambiente ou editar aqui:
    # os.environ['DB_HOST'] = 'seu_host_oracle'
    # os.environ['DB_NAME'] = 'seu_banco'
    # os.environ['DB_USER'] = 'seu_usuario'
    # os.environ['DB_PASSWORD'] = 'sua_senha'
    
    sistema = GerenciadorFuncionarios()
    sistema.menu_principal()