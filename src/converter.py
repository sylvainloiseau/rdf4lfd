from abc import abstractmethod
from rdflib import Graph

class Converter():

    @abstractmethod
    def get_graph(self) -> Graph:
        pass

    @abstractmethod
    def convert(self) -> None:
        pass