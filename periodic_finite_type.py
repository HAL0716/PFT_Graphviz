import os
import tempfile
from pathlib import Path
from typing import Optional
from graphviz import Source
from Node import Node

class PeriodicFiniteType:
    def __init__(self, phase: int, f_len: int, fwords: list[str], is_beal: bool = True, output_dir: str = "output") -> None:
        self._phase = phase
        self._f_len = f_len
        self.dir_path = Path(output_dir)
        self.__nodes: set[Node] = set()
        self.__adj_list: dict[Node, dict[str, Node]] = {}
        
        os.makedirs(self.dir_path, exist_ok=True)

        if is_beal:
            self.__init_beal_nodes(fwords)

    def __init_beal_nodes(self, fwords: list[str]) -> None:
        self.__nodes.update(Node('', t) for t in range(self._phase))
        for fword in fwords:
            self.__nodes.update(Node(fword[:i+1], 0) for i, _ in enumerate(fword))

    def set_adj_list(self, alphabet: list[str]) -> None:
        def find_dst(base_label: str, base_phase: int) -> Node:
            for i in range(len(base_label)):
                dst = Node(base_label[i:], (base_phase + i) % self._phase)
                if dst in self.__nodes:
                    return dst
            return Node("", (base_phase + len(base_label)) % self._phase)

        def set_dsts(src: Node) -> dict[str, Node]:
            return {
                label: find_dst(src.label + label, src.phase)
                for label in alphabet
            }
        
        # [src][label] = dst
        self.__adj_list = {
            src: set_dsts(src)
            for src in self.__nodes if len(src.label) < self._f_len
        }

    
    def _prepare_path(self, filename: str, suffix: str) -> Path:
        """一時ファイル用のフルパスを生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            return path.with_suffix(suffix)
    
    def export_to_dot(self, filename: str | Path = "graph") -> None:
        filepath = self._prepare_path(filename, ".dot")
        
        nodes = sorted(self.__nodes, key=lambda n: (n.label, n.phase))
        idx_map = {node: i for i, node in enumerate(nodes)}

        with filepath.open("w") as f:
            f.write("digraph G {\n")
            for node, idx in idx_map.items():
                f.write(f'\t{idx} [label="{node}"];\n')
            f.write("\n")
            for src, dsts in self.__adj_list.items():
                for label, dst in dsts.items():
                    f.write(f'\t{idx_map[src]} -> {idx_map[dst]} [label="{label}"];\n')
            f.write("}\n")

    def export_to_png(self, filename: str | Path = "graph") -> Optional[Path]:
        try:
            dot_path = self._prepare_path(filename, ".dot")
            png_path = self._prepare_path(filename, ".png")

            self.export_to_dot(dot_path.name)

            src = Source.from_file(dot_path)
            src.render(png_path.with_suffix(""), format="png", cleanup=True)

            return png_path
        except Exception as e:
            # print(f"Export failed: {e}")
            return None

    def __str__(self) -> str:
        if self.__adj_list:
            return "\n".join(f"{src} -> {', '.join(f'{label} : {dst}' for label, dst in dsts.items())}" for src, dsts in self.__adj_list.items())
        else:
            return "\n".join(str(node) for node in sorted(self.__nodes, key=lambda n: (n.phase, n.label)))