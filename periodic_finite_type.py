import os
import io
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
    
    def export_to_dot(self) -> str:
        """.dot内容をファイルに保存せずに文字列で返す"""
        nodes = sorted(self.__nodes, key=lambda n: (n.label, n.phase))
        idx_map = {node: i for i, node in enumerate(nodes)}

        dot_content = "digraph G {\n"
        for node, idx in idx_map.items():
            dot_content += f'\t{idx} [label="{node}"];\n'
        dot_content += "\n"
        for src, dsts in self.__adj_list.items():
            for label, dst in dsts.items():
                dot_content += f'\t{idx_map[src]} -> {idx_map[dst]} [label="{label}"];\n'
        dot_content += "}\n"
        
        return dot_content

    def export_to_png(self) -> Optional[io.BytesIO]:
        """メモリ内でPNG画像を生成して返す"""
        try:
            # .dotファイル内容を生成
            dot_content = self.export_to_dot()

            # DOT内容をgraphvizのSourceに渡してPNGに変換
            src = Source(dot_content)

            # PNGデータをメモリに保持
            png_data = src.pipe(format='png')  # pipeメソッドでメモリ内に画像データを直接取得

            # バイナリデータをBytesIOに格納して返す
            img_io = io.BytesIO(png_data)
            return img_io

        except Exception as e:
            return None

    def __str__(self) -> str:
        if self.__adj_list:
            return "\n".join(f"{src} -> {', '.join(f'{label} : {dst}' for label, dst in dsts.items())}" for src, dsts in self.__adj_list.items())
        else:
            return "\n".join(str(node) for node in sorted(self.__nodes, key=lambda n: (n.phase, n.label)))