import os
import sqlite3
from dataclasses import dataclass,field,asdict
from abc import ABC,abstractmethod
from argparse import ArgumentParser
from json import dumps

CONFIGS = {
        "WIN":
        {
                "USER_PATH":"\\Users\\" + os.getlogin()
        },    
        "CHROME":{
            "PASSW":"",
            "HISTORY":""
        },
        "EDIGE":{
            
            "PASSW":"",
            "HISTORY":""}
}
@dataclass
class SearchConfigs:
    passw:str
    history:str
    def export(self):
        return asdict(self)
@dataclass
class Configurations:
    win:dict[str,str] = field(default_factory=dict())
    Chrome:dict[str,str]|SearchConfigs = field(default_factory=lambda :SearchConfigs("",""))
    Edige:dict[str,str]|SearchConfigs= field(default_factory=lambda :SearchConfigs("",""))
    def renderizer(self):
        # renderizer
        renderizery = lambda y,os: SearchConfigs(os["USER_PATH"] + y.passw, os["USER_PATH"] + y.history)
        [setattr(self,x,renderizery(y,self.win)) for x,y in dict(vars(self)).items() if x not in ["win"] and isinstance(y,SearchConfigs)]
        return self


    
class DAOBased(ABC):
    @property
    @abstractmethod
    def _SELECT(self):
        ...
    

class ChromeBasedDAO(DAOBased):
    _SELECT = "SELECT title,last_visit_time,url FROM urls"

class EdigeBasedDao(DAOBased):
    _SELECT = "SELECT title,last_visit_time,url FROM urls"
    _SELECT_N = "SELECT title,last_visit_time,url FROM urls ORDER BY title LIMIT %s"


class Entity(ABC):
    
    def export(self):
        return asdict(self)

@dataclass
class Chrome(Entity):
    title:str
    last_visit_time:str
    url:str
@dataclass
class Edige(Entity):
    title:str
    last_visit_time:str
    url:str

class Connection(ABC):
    @abstractmethod
    def loadRegisters(self,path):
        ...

class ConnectionSqlite(Connection):
    # XXX: NEED OPTIMIZATION!
    # THE CURSOR NEED OR A POOL OR AN ENTITY TO ALLOW LAZY LOAD
    def __init__(self,type:DAOBased,daoType:Chrome|Edige) -> None:
        self.type = type
        self.entity = daoType# like chrome edige etc entity
        super().__init__()
    
    def loadRegisters(self,path) -> list[Chrome|Edige]:
        with sqlite3.connect(path) as db:
            cursor = db.cursor()
            cursor.execute(self.type._SELECT)
            req = [None]
            req = [self.entity(*registrer) for registrer in cursor.fetchall()]
                
            #req = self.entity(*cursor.fetchall())
            cursor.close()
        return req
    def loadRegistersN(self,path,n:int):
        with sqlite3.connect(path) as db:
            cursor = db.cursor()
            cursor.execute(self.type._SELECT,n)
            req = [None]
            req = [self.entity(*registrer) for registrer in cursor.fetchall()]
                
            #req = self.entity(*cursor.fetchall())
            cursor.close()
        return req



            
        
class Merger:
    def __init__(self,filename) -> None:
        self.filename = filename +'.json'
    def __enter__(self):
        print(f"[+] Writting JSON Inform on {self.filename}")
        self.io = open(self.filename,'w')
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print(f"[-] Errors: {exc_type} \n {exc_value}")
        self.io.close()
        
    
        
        


CONFIGS = Configurations(
        win={
            "USER_PATH":"\\Users\\" + os.getlogin()
        },
        Chrome= SearchConfigs(
            "",
            r"\AppData\Local\Google\Chrome\User Data\Default\History"
        ),
        Edige= SearchConfigs(
            "",
            r"\AppData\Local\Microsoft\Edige\User Data\Default\History"
        )
    ).renderizer()





def extract_chrome_data(path):
    # Aquí iría el código para extraer datos de Chrome
    conn = ConnectionSqlite(
        ChromeBasedDAO,Chrome
    )
    if path:
        CONFIGS.Chrome.history = path
    req = conn.loadRegisters(CONFIGS.Chrome.history)
    return dumps([x.export() for x in req],indent=4)

def extract_edge_data(path):
    # Aquí iría el código para extraer datos de Edge
    conn = ConnectionSqlite(
        EdigeBasedDao,Edige
    )
    if path:
        CONFIGS.Edige.history = path
        #conn.loadRegisters(path=CONFIGS)
    req = conn.loadRegisters(CONFIGS.Edige.history)
    return dumps([x.export() for x in req],indent=4)
    
def main():
    parser = ArgumentParser(description="Herramienta de extracción de datos del historial de navegación con fines forenses.")
    parser.add_argument("OsName", type=str, help="Nombre del sistema operativo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--Chrome", action="store_true", help="Extraer datos del historial de Chrome")
    group.add_argument("-e", "--Edge", action="store_true", help="Extraer datos del historial de Edge")
    #parser.add_argument("-t","--top",type=int,help="establecer un limite de elementos a desplegar")
    # ! REALIZAR OPCION -T 
    parser.add_argument("-p", "--path", type=str, default=os.path.expanduser("~"), help="Ruta del directorio donde buscar los datos del historial (use en datos previamente extraidos)")
    parser.add_argument("-o","--output",type=str,help="escribir cambios en un archivo")
    args = parser.parse_args()
    stdout:str|None = None
    if args.Chrome:
        stdout = extract_chrome_data(args.path)
    elif args.Edge:
        stdout =  extract_edge_data(args.path)
    else:
        print("Debe especificar al menos una opción de navegador: -c (--Chrome) o -e (--Edge)")
    if args.output and stdout:
        with Merger(args.output) as rds:
            rds.io.write(stdout)
    
if __name__ == "__main__":
    main()
    