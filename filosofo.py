import time
import random
import socket
from threading import Thread, RLock, Semaphore
from config import IPS_FILOSOFOS, PORTA_INICIO, PORTA_JANTA
import threading
import os
from datetime import datetime, timedelta

# Variáveis globais
lock = RLock()
semaphore = Semaphore(4)  # Permite que no máximo 4 filósofos tentem comer simultaneamente
idFilosofo = 2  # 1,2,3,4 ou 5 (deve corresponder ao índice no array de IPs)
ipsFilosofosReal = ["200.239.138.232", "200.239.138.237",
                   "200.239.138.92", "200.239.138.205",
                   "200.239.138.234"]

situacaoFilosofo = 0  # 1 para comendo, 0 para pensando
meuGarfo = 2
garfoAmigo = 0  # 0 indica que não tem garfo do amigo
comecou = 0


class Filosofo(Thread):
    def __init__(self, cond):
        Thread.__init__(self)
        self.op = cond

    def comer(self):
        global situacaoFilosofo
        print(f"Filósofo {idFilosofo} comendo")
        situacaoFilosofo = 1
        time.sleep(random.random())  # Tempo aleatório para comer
        situacaoFilosofo = 0
        
        # Notifica outros filósofos que está comendo
        for ip in IPS_FILOSOFOS:
            msg = f"Filosofo {ipsFilosofosReal[idFilosofo-1]} comendo com garfos {meuGarfo} e {garfoAmigo}"
            self.enviaDado(ip, PORTA_JANTA, msg)

    def pegarGarfoAmigo(self):
        global garfoAmigo
        
        # Adquire o semáforo para evitar deadlock
        semaphore.acquire()
        print(f"Filósofo {idFilosofo} tentando pegar garfo do amigo")
        
        try:
            if garfoAmigo != 0:
                return True
                
            # Envia requisição para pegar o garfo
            self.enviaDado(IPS_FILOSOFOS[idFilosofo % len(IPS_FILOSOFOS)], 5060, "1|-1")
            
            try:
                # Espera resposta com timeout
                msg, ipFilosofoAmigo = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5061, 1)
                print(f"Filósofo {idFilosofo} recebeu resposta: {msg}")
                
                with lock:
                    garfoAmigo = int(msg[2])
                
                # Confirmação
                self.enviaDado(IPS_FILOSOFOS[idFilosofo % len(IPS_FILOSOFOS)], 5060, "ok")
                print(f"Filósofo {idFilosofo} pegou garfo {garfoAmigo}")
                
                return garfoAmigo != 0
                
            except socket.timeout:
                print(f"Filósofo {idFilosofo} timeout ao pegar garfo")
                return False
                
        finally:
            semaphore.release()

    def devolverGarfoAmigo(self):
        global garfoAmigo
        print(f"Filósofo {idFilosofo} devolvendo garfo {garfoAmigo}")
        
        with lock:
            if garfoAmigo == 0:
                return True
                
            # Envia mensagem para devolver o garfo
            self.enviaDado(IPS_FILOSOFOS[idFilosofo % len(IPS_FILOSOFOS)], 5060, f"2|{garfoAmigo}")
            
            try:
                # Espera confirmação
                msg, ipFilosofoComFome = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5001, 1)
                if msg == "ok":
                    self.enviaDado(ipFilosofoComFome[0], 5060, "ok")
                    msg, ipFilosofoComFome = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5001, 1)
                    if msg == "ok":
                        garfoAmigo = 0
                        print(f"Filósofo {idFilosofo} devolveu garfo com sucesso")
                        return True
            except socket.timeout:
                print(f"Filósofo {idFilosofo} timeout ao devolver garfo")
                return False

    def dormir(self):
        print(f"Filósofo {idFilosofo} pensando")
        time.sleep(random.uniform(0.1, 0.5))  # Tempo aleatório para pensar

    def viver(self):
        print(f"Filósofo {idFilosofo} começou a viver")
        
        while True:
            self.dormir()
            
            # Tenta comer
            if self.pegarGarfoAmigo() and meuGarfo:
                self.comer()
                if garfoAmigo != 0:
                    self.devolverGarfoAmigo()
            else:
                # Espera um tempo antes de tentar novamente
                time.sleep(random.uniform(0.1, 0.3))

    def atendeFilosofoAmigo(self):
        global meuGarfo
        print(f"Filósofo {idFilosofo} aguardando requisições")
        
        msg, ipFilosofoComFome = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5060, 0)
        print(f"Filósofo {idFilosofo} recebeu mensagem: {msg}")
        
        if situacaoFilosofo == 0 and msg[0] == "1" and meuGarfo != 0:
            # Pode emprestar o garfo
            self.enviaDado(ipFilosofoComFome[0], 5061, f"2|{meuGarfo}")
            
            try:
                msg, ipFilosofoComFome = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5060, 1)
                if msg == "ok":
                    with lock:
                        meuGarfo = 0
                    print(f"Filósofo {idFilosofo} emprestou seu garfo")
                    return True
            except socket.timeout:
                return False
                
        elif msg[0] == "2":
            # Recebeu devolução de garfo
            print(f"Filósofo {idFilosofo} recebendo garfo de volta")
            self.enviaDado(ipFilosofoComFome[0], 5001, "ok")
            
            try:
                msg, ipFilosofoComFome = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], 5060, 1)
                if msg == "ok":
                    with lock:
                        meuGarfo = idFilosofo
                        self.enviaDado(ipFilosofoComFome[0], 5001, "ok")
                    print(f"Filósofo {idFilosofo} recuperou seu garfo")
                    return True
            except socket.timeout:
                return False

    def imprimeJantar(self):
        msg, ipFilosofo = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], PORTA_JANTA, 0)
        print(f"Mensagem do jantar: {msg}")

    def enviaDado(self, ipFilosofoDestino, portaRequisicao, dado):
        for i in range(3):  # Tenta 3 vezes
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
                    dest = (str(ipFilosofoDestino), int(portaRequisicao))
                    tcp.connect(dest)
                    tcp.send(dado.encode())
                return True
            except Exception as e:
                print(f"Erro ao enviar dados (tentativa {i+1}): {e}")
                time.sleep(0.1)
        return False

    def recebeDado(self, ipFilosofo, portaAtendimento, cond):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            orig = (str(ipFilosofo), int(portaAtendimento))
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if cond:
                tcp.settimeout(0.5)
            tcp.bind(orig)
            tcp.listen(1)
            objSocket, ipFilosofoComFome = tcp.accept()
            msg = objSocket.recv(1024).decode()
            return msg, ipFilosofoComFome

    def inicio(self):
        global comecou
        cond = int(input("1 para ouvir e 2 para executar: "))
        
        if cond == 1:
            msg, ipFilosofoAmigo = self.recebeDado(IPS_FILOSOFOS[idFilosofo-1], PORTA_INICIO, 0)
            if msg == "inicio":
                print("Começou!!")
                comecou = 1
        elif cond == 2:
            msg = input("Digite 'inicio' para começar: ")
            for ip in IPS_FILOSOFOS:
                if ip != IPS_FILOSOFOS[idFilosofo-1]:
                    self.enviaDado(ip, PORTA_INICIO, msg)
            comecou = 1

    def run(self):
        while True:
            if self.op == 0 and comecou == 0:
                self.inicio()
            elif self.op == 1 and comecou == 1:
                self.atendeFilosofoAmigo()
            elif self.op == 2 and comecou == 1:
                self.viver()
            elif self.op == 3 and comecou == 1:
                self.imprimeJantar()
            time.sleep(0.1)  # Evita uso excessivo da CPU

    def __init__(self, cond):
        Thread.__init__(self)
        self.op = cond
        self.tempo_inicio = datetime.now()
        self.tempo_maximo = timedelta(seconds = 120)  # 2 minutos = 120 segundos
        self.executando = True

    def verificar_tempo(self):
        while self.executando:
            if datetime.now() > self.tempo_inicio + self.tempo_maximo:
                print(f"\nFilósofo {idFilosofo} terminou por tempo")
                self.executando = False
                os._exit(0)
            time.sleep(1)

    def viver(self):
        # Inicia verificador de tempo
        threading.Thread(target=self.verificar_tempo, daemon=True).start()
        
        while self.executando:
            self.dormir()
            
            if self.pegarGarfoAmigo() and meuGarfo:
                self.comer()
                if garfoAmigo != 0:
                    self.devolverGarfoAmigo()
            else:
                time.sleep(random.uniform(0.1, 0.3))


# Inicia as threads
for i in range(4):
    Filosofo(i).start()
    time.sleep(0.1)  # Espaçamento entre inícios de threads

print("Sistema dos filósofos iniciado")