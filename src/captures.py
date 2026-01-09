from typing import Any, List, Tuple, Dict, Callable, Optional
from tree_sitter import Parser, Language, QueryCursor, Query
import importlib

# Definiamo un tipo per l'handler per chiarezza
HandlerFunc = Callable[[Any, Any, Any], Any]

class CapturesManager:
    def __init__(self, language_name: str):
        """
        :param language_name: es. "python", "javascript"
        :param queries_config: Dizionario opzionale delle query. Se None, prova a importarlo.
        """
        self.language_name = language_name
        self.LANGUAGE = self._load_language()
        
        # Carichiamo la configurazione grezza
        raw_queries = self._load_default_queries()
        
        # Compiliamo Query e Mappa una volta sola all'avvio
        self.query_obj, self.dispatch_map = self._compile_queries(raw_queries)

    def _load_language(self) -> Language:
        """Carica dinamicamente la libreria del linguaggio."""
        try:
            if self.language_name == "python":
                import tree_sitter_python as tspython
                return Language(tspython.language())
            # Aggiungi qui altri linguaggi (es. java, go, etc.)
            else:
                raise ValueError(f"Language {self.language_name} not supported yet.")
        except ImportError as e:
            raise RuntimeError(f"Failed to load tree-sitter language: {e}")

    def _load_default_queries(self) -> Dict:
        """Tenta di importare il file queries.py basandosi sul nome lingua."""
        try:
            if self.language_name == "python":
                from .languages.python.queries import PYTHON_QUERIES
                return PYTHON_QUERIES
        except (ImportError, AttributeError):
            print(f"Warning: No default queries found for {self.language_name}")
            return {}

    def _compile_queries(self, queries_dict: Dict) -> Tuple[Query, Dict[str, HandlerFunc]]:
        """
        Trasforma il dizionario di config (formato 'Query String' -> 'Lista di Dict Handler') in:
        1. Un singolo oggetto Query ottimizzato.
        2. Una Dispatch Map piatta { 'capture_name': handler_function }.
        """
        query_strings = []
        dispatch_map = {}

        # Iteriamo sulla struttura dati fornita (chiave = query string, valore = lista di mapping)
        for query_str, handlers_list in queries_dict.items():
            
            # 1. Aggiungiamo la stringa della query alla lista per Tree-sitter
            # Tree-sitter compilerà tutte queste stringhe in un unico oggetto Query efficiente
            query_strings.append(query_str)

            # 2. Popoliamo la mappa di dispatch appiattendo la lista
            # handlers_list è tipo: [ { "module": handle_module } ] 
            # oppure: [ {"class_definition": h_def}, {"class_name": h_name}, ... ]
            if isinstance(handlers_list, list):
                for handler_mapping in handlers_list:
                    # handler_mapping è un dict { "nome_cattura": funzione_handler }
                    for capture_name, handler_func in handler_mapping.items():
                        # Controllo di sicurezza: verifichiamo che handler_func sia chiamabile
                        if not callable(handler_func):
                            print(f"Warning: Handler for '{capture_name}' is not a function/callable.")
                        
                        # Inseriamo nella mappa piatta: "module" -> handle_module
                        dispatch_map[capture_name] = handler_func
            else:
                print(f"Error: Expected a list of dicts for query '{query_str}', got {type(handlers_list)}")

        # Uniamo tutte le stringhe in una sola query gigante separata da newline
        full_query_str = "\n".join(query_strings)
        
        try:
            # Compiliamo la query una volta sola
            query_obj = Query(self.LANGUAGE, full_query_str)
        except Exception as e:
            # Utile per il debug: stampa quale query ha fallito
            print(f"Error compiling combined query. First 100 chars: {full_query_str[:100]}...")
            raise e

        return query_obj, dispatch_map
   
    def get_handler(self, capture_name: str) -> Optional[HandlerFunc]:
        """Recupera la funzione handler associata al nome della cattura."""
        return self.dispatch_map.get(capture_name)
    
    def get_handlers(self) -> Dict[str, HandlerFunc]:
        """Recupera la funzione handler associata al nome della cattura."""
        return self.dispatch_map

    def execute(self, root_node) -> List[Tuple[Any, str]]:
        """
        Esegue la query pre-compilata.
        Ritorna una lista ORDINATA di (node, capture_name).
        """
        captures = QueryCursor(self.query_obj).captures(root_node)

        flat_captures = []

        for name, nodes in captures.items():
            for node in nodes:
                flat_captures.append((node, name))

        # Ordinamento fondamentale: Start Byte ASC, End Byte DESC (Parent before Child)
        flat_captures.sort(key=lambda x: (x[0].start_byte, -x[0].end_byte))
        
        return flat_captures