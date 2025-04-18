from Node import Node

class PeriodicFiniteType:
    def __init__(self, phase: int, f_len: int, fwords: list[str], is_beal: bool = True) -> None:
        self.__phase = phase
        self.__f_len = f_len
        self.__nodes: set[Node] = set()
        self.__adj_list: dict[Node, dict[str, Node]] = {}

        if is_beal:
            self.__init_beal_nodes(fwords)
    
    @property
    def phase(self) -> int:
        return self.__phase
    
    @property
    def f_len(self) -> int:
        return self.__f_len
    
    @property
    def nodes(self) -> set[Node]:
        return self.__nodes
    
    @property
    def adj_list(self) -> dict[Node, dict[str, Node]]:
        return self.__adj_list
    
    def __init_beal_nodes(self, fwords: list[str]) -> None:
        self.__nodes.update(Node('', t) for t in range(self.__phase))
        for fword in fwords:
            self.__nodes.update(Node(fword[:i+1], 0) for i, _ in enumerate(fword))

    def set_adj_list(self, alphabet: list[str]) -> None:
        def find_dst(base_label: str, base_phase: int) -> Node:
            for i in range(len(base_label)):
                dst = Node(base_label[i:], (base_phase + i) % self.__phase)
                if dst in self.__nodes:
                    return dst
            return Node("", (base_phase + len(base_label)) % self.__phase)

        def set_dsts(src: Node) -> dict[str, Node]:
            return {
                label: find_dst(src.label + label, src.phase)
                for label in alphabet
            }
        
        # [src][label] = dst
        self.__adj_list = {
            src: set_dsts(src)
            for src in self.__nodes if len(src.label) < self.__f_len
        }

    def __str__(self) -> str:
        if self.__adj_list:
            return "\n".join(f"{src} -> {', '.join(f'{label} : {dst}' for label, dst in dsts.items())}" for src, dsts in self.__adj_list.items())
        else:
            return "\n".join(str(node) for node in sorted(self.__nodes, key=lambda n: (n.phase, n.label)))