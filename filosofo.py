import threading
import time
import random
import pygame
import sys
import math

# Definindo as dimensões da tela e cores
# DEFININDO AS DIMENSÕES DA INTERFACE E AS CORES
LARGURA, ALTURA = 800, 600
COR_FUNDO = (240, 240, 240) 
COR_MESA = (200, 150, 100)
COR_PENSANDO = (255, 215, 0)    # Amarelo mostarda
COR_FAMINTO = (255, 0, 0)       # Vermelho
COR_COMENDO = (0, 255, 0)       # Verde
COR_GARFO = (100, 100, 100)
COR_TEXTO = (0, 0, 0)

class JantarDosFilosofos:
    def __init__(self, num_filosofos=5):
        self.num_filosofos = num_filosofos
        # Criamos um Lock para cada garfo
        # CRIAMOS UM LOCK PARA CADA GARFO 
        self.garfos = [threading.Lock() for _ in range(num_filosofos)]
        # Mutex para garantir exclusão na seção crítica
        # MUTEX PARA GARANTIR EXCLUSÃO NA SEÇÃO CRÍTICA
        self.mutex = threading.Lock()
        # Estados iniciais: todos pensando
        # ESTADOS INICIAIS: TODOS PENSANDO
        self.estados = ['pensando'] * num_filosofos
        # Cada filósofo tem sua Condition para controlar espera e notificação
        # CADA FILÓSOFO TEM UMA CONDIÇÃO PARA CONTROLAR A ESPERA E A NOTIFICAÇÃO
        self.condicoes = [threading.Condition(self.mutex) for _ in range(num_filosofos)]
        # Lock para proteger a atualização dos status para exibição
        # LOCK PARA PROTEGER A ATUALIZAÇÃO DOS STATUS PARA EXIBIÇÃO
        self.status_lock = threading.Lock()
        self.status_messages = ["Pensando"] * num_filosofos
    
    def pegar_garfos(self, filosofo_id):
        # O filósofo tenta pegar os dois garfos (à esquerda e à direita)
        # O FILÓSOFO TENTA PEGAR OS DOIS GARFOS (À ESQUERDA E À DIREITA)
        with self.mutex:
            self.estados[filosofo_id] = 'faminto'
            self._atualizar_status(filosofo_id, "Faminto")
            # Depois de mudar o estado para faminto, tentamos testar se pode comer
            # DEPOIS DE MUDAR O ESTADO PARA FAMINTO, É FEITO O TESTE PARA VER SE O FILÓSOFO PODE COMER
            self._verificar_vizinhos(filosofo_id)
            # Se não pode comer, fica esperando até receber um notify
            # SE NÃO PUDER COMER, O PRÓXIMO FILÓSOFO FICA ESPERANDO ATÉ RECEBER UMA NOTIFICAÇÃO
            while self.estados[filosofo_id] != 'comendo':
                self.condicoes[filosofo_id].wait()
    
    def largar_garfos(self, filosofo_id):
        # O filósofo acabou de comer e vai largar os garfos para os outros usarem
        # O FILÓSOFO ACABOU DE COMER E VAI LARGAR OS GARFOS PARA OS OUTROS PODEREM USAR
        with self.mutex:
            self.estados[filosofo_id] = 'pensando'
            self._atualizar_status(filosofo_id, "Pensando")
            # Após largar, verificar se os vizinhos famintos podem passar a comer
            # APÓS LARGAR OS GARFOS, É FEITA UMA VERIFICAÇÃO PARA VER SE OS VIZINHOS FAMINTOS PODEM COMER
            self._verificar_vizinhos((filosofo_id - 1) % self.num_filosofos)
            self._verificar_vizinhos((filosofo_id + 1) % self.num_filosofos)
    
    def _verificar_vizinhos(self, filosofo_id):
        # Só pode comer se os dois vizinhos não estiverem comendo
        # SÓ PODE COMER SE OS DOIS FILÓSOFOS VIZINHOS NÃO ESTIVEREM COMENDO
        esquerda = (filosofo_id - 1) % self.num_filosofos
        direita = (filosofo_id + 1) % self.num_filosofos
        
        # Se ele estiver faminto e os vizinhos não comerem, ele pode comer
        # SE O FILÓSOFO ESTIVER FAMINTO E OS FILÓSOFOS VIZINHOS NÃO ESTIVEREM COMENDO, ELE PODE COMER
        if (self.estados[filosofo_id] == 'faminto' and
            self.estados[esquerda] != 'comendo' and
            self.estados[direita] != 'comendo'):
            
            self.estados[filosofo_id] = 'comendo'
            self._atualizar_status(filosofo_id, "Comendo")
            # Notifica o filósofo que estava esperando para comer
            # NOTIFICA O FILÓSOFO QUE ESTAVA ESPERANDO PARA PODER COMER
            self.condicoes[filosofo_id].notify()
    
    def _atualizar_status(self, filosofo_id, mensagem):
        # Atualiza a mensagem exibida para o filósofo atual
        # ATUALIZA A MENSAGEM EXIBIDA PARA O FILÓSOFO ATUAL
        with self.status_lock:
            self.status_messages[filosofo_id] = mensagem
    
    def get_status(self, filosofo_id):
        # Retorna o status atual para exibição
        # RETORNA O STATUS ATUAL PARA EXIBIÇÃO
        with self.status_lock:
            return self.status_messages[filosofo_id]

def filosofo(filosofo_id, jantar):
    while True:
        # Aqui o filósofo está pensando, tempo maior para tornar visualização mais clara
        # AQUI O FILÓSOFO ESTÁ PENSANDO, TEMPO MAIOR PARA FACILITAR A VISUALIZAÇÃO
        
        jantar._atualizar_status(filosofo_id, "Pensando")
        time.sleep(random.uniform(3, 6))  # Tempo aleatório para pensar # TEMPO ALEATÓRIO PARA PENSAR
        
        # Ficou com fome, tenta pegar os garfos
        # FICOU COM FOME, TENTA PEGAR OS GARFOS
        jantar._atualizar_status(filosofo_id, "Faminto")
        jantar.pegar_garfos(filosofo_id)
        
        # Quando consegue comer, mantém esse estado um tempo
        # QUANDO CONSEGUE COMER, CONTINUA NESSE ESTADO POR UM TEMPO
        jantar._atualizar_status(filosofo_id, "Comendo")
        time.sleep(random.uniform(3, 4))  # Tempo aleatório para comer  # TEMPO ALEATÓRIO PARA COMER
        
        # Depois de comer, deixa os garfos para os vizinhos usarem
        # DEPOIS DE COMER, O FILÓSOFO LARGA OS GARFOS PARA OS FILÓSOFOS VIZINHOS USAREM
        jantar._atualizar_status(filosofo_id, "Largando garfos")
        jantar.largar_garfos(filosofo_id)

class FilosofosAnimation:
    def __init__(self, jantar):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Jantar dos Filósofos")
        self.clock = pygame.time.Clock()
        self.jantar = jantar
        self.fonte = pygame.font.SysFont('Arial', 16)
        self.fonte_grande = pygame.font.SysFont('Arial', 24, bold=True)
        
        # Coordenadas centrais e tamanhos para desenhar elementos
        # COORDENADAS CENTRAIS E TAMANHOS PARA DESENHAR OS ELEMENTOS DA INTERFACE
        self.centro_x, self.centro_y = LARGURA // 2, ALTURA // 2
        self.raio_mesa = 150
        self.raio_filosofos = 30
        self.comprimento_garfo = 40
    
    def desenhar_mesa(self):
        # Desenha a mesa circular
        # DESENHA A MESA CIRCULAR
        pygame.draw.circle(self.tela, COR_MESA, 
                         (self.centro_x, self.centro_y), self.raio_mesa)
        
        # Percorre cada filósofo para desenhá-lo e desenhar o garfo ao lado
        # PERCORRE CADA FILÓSOFO PARA DESENHAR ELES E OS GARFOS AO LADO
        for i in range(self.jantar.num_filosofos):
            angulo = 2 * math.pi * i / self.jantar.num_filosofos
            self.desenhar_filosofos(i, angulo)
            self.desenhar_garfo(i, angulo)
    
    def desenhar_filosofos(self, id_filosofos, angulo):
        # Calcula a posição baseado em círculo (mesa)
        # CALCULA A POSIÇÃO BASEADA EM CÍRCULO (MESA)
        x = self.centro_x + (self.raio_mesa + 50) * math.cos(angulo)
        y = self.centro_y + (self.raio_mesa + 50) * math.sin(angulo)
        
        # Muda cor conforme estado
        estado = self.jantar.estados[id_filosofos]
        if estado == 'comendo':
            cor = COR_COMENDO
        elif estado == 'faminto':
            cor = COR_FAMINTO
        else:  # pensando
            cor = COR_PENSANDO
        
        # Desenha o círculo representando o filósofo
        # DESENHA O CÍRCULO QUE REPRESENTA O FILÓSOFO
        pygame.draw.circle(self.tela, cor, (int(x), int(y)), self.raio_filosofos)
        
        # Escreve o número do filósofo perto do círculo (começando em 1)
        # ESCREVE O NÚMERO DO FILÓSOFO PERTO DO CÍRCULO
        texto = self.fonte.render(f"Filósofo {id_filosofos + 1}", True, COR_TEXTO)
        rect_texto = texto.get_rect(center=(int(x), int(y)))
        self.tela.blit(texto, rect_texto)
        
        # Também exibe o status atual logo abaixo
        # TAMBÉM EXIBE O STATUS ATUAL EM BAIXO
        status = self.jantar.get_status(id_filosofos)
        texto_status = self.fonte.render(status, True, COR_TEXTO)
        rect_status = texto_status.get_rect(center=(int(x), int(y) + 40))
        self.tela.blit(texto_status, rect_status)
    
    def desenhar_garfo(self, id_garfo, angulo):
        # O garfo fica entre dois filósofos, então ajustamos ângulo
        # O GARFO FICA ENTRE DOIS FILÓSOFOS, ENTÃO O ÂNGULO É AJUSTADO
        angulo_offset = math.pi / self.jantar.num_filosofos
        x = self.centro_x + self.raio_mesa * math.cos(angulo + angulo_offset)
        y = self.centro_y + self.raio_mesa * math.sin(angulo + angulo_offset)
        
        # Linha representando o garfo
        # LINHA QUE REPRESENTA O GARFO
        fim_x = x + self.comprimento_garfo * math.cos(angulo + angulo_offset)
        fim_y = y + self.comprimento_garfo * math.sin(angulo + angulo_offset)
        pygame.draw.line(self.tela, COR_GARFO, (x, y), (fim_x, fim_y), 5)
        
        # Texto do garfo (no caso está vazio, mas pode ser usado para mostrar IDs)
        # TEXTO DO GARFO (NO CASO ESTÁ VAZIO, MAS PODE SER USADO PARA MOSTRAR OS IDS)
        texto_garfo = self.fonte.render(f"", True, COR_GARFO)
        rect_garfo = texto_garfo.get_rect(center=(int(x + 20), int(y + 20)))
        self.tela.blit(texto_garfo, rect_garfo)
    
    def executar(self):
        rodando = True
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False
            
            self.tela.fill(COR_FUNDO)
            
            # Chamada para desenhar mesa, filósofos e garfos
            # COMANDO PARA DESENHAR A MESA, OS FILÓSOFOS E OS GARFOS
            self.desenhar_mesa()
            
            # Exibe o título centralizado no topo
            # EXIBE O TÍTULO QUE APARECE NO TOPO
            titulo = self.fonte_grande.render("Jantar dos Filósofos", True, COR_TEXTO)
            self.tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 20))
            
            pygame.display.flip()
            self.clock.tick(30)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    num_filosofos = 5
    jantar = JantarDosFilosofos(num_filosofos)
    
    # Criando as threads de forma que cada filósofo opere em paralelo
    # CRIANDO AS THREADS FAZENDO COM QUE CADA FILÓSOFO ATUE AO MESMO TEMPO
    filosofos = []
    for i in range(num_filosofos):
        thread_filosofos = threading.Thread(target=filosofo, args=(i, jantar))
        thread_filosofos.daemon = True  # Permite sair do programa mesmo com threads rodando # PERMITE SAIR DO PROGRAMA MESMO COM AS THREADS RODANDO
        thread_filosofos.start()
        filosofos.append(thread_filosofos)
    
    # Cria e inicia a interface gráfica
    # CRIA E INICIA O PYGAME
    animacao = FilosofosAnimation(jantar)
    animacao.executar()