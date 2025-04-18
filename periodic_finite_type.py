import io
import math
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from graphviz import Source
from dot2tex import dot2tex
from pdf2image import convert_from_path

from Node import Node  # あなたのローカル定義クラス

class PeriodicFiniteType:
    def __init__(self, phase: int, f_len: int, fwords: list[str], is_beal: bool = True, output_dir: str = "output") -> None:
        self._phase = phase
        self._f_len = f_len
        self.dir_path = Path(output_dir)
        self.__nodes: set[Node] = set()
        self.__adj_list: dict[Node, dict[str, Node]] = {}

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
    
    def export_to_dot(self, use_latex: bool = False) -> str:
        def calc_pos(idx: int, N: int, r: float) -> tuple[float, float]:
            angle = (math.pi / 2) - (idx * (2 * math.pi / N))
            return round(r * math.cos(angle), 2), round(r * math.sin(angle), 2)

        def build_pos_map() -> dict:
            node_layers = [[] for _ in range(self._f_len + 1)]
            for node in self.__nodes:
                node_layers[len(node.label)].append(node)
            for layer in node_layers:
                layer.sort(key=lambda n: n.phase)

            N = max(self._phase, 6)
            idx, used_cnt = -1, [0] * N

            def next_idx():
                nonlocal idx
                idx = (idx + 1) % N
                return idx

            pos_map = {}
            for i, nodes in enumerate(node_layers):
                if i == 0:
                    nodes.reverse()
                for node in nodes:
                    if i == 0:
                        next_idx()
                    x, y = calc_pos(idx + 1, N, used_cnt[idx] + 1)
                    pos_map[node] = (x, y)
                    used_cnt[idx] += 1
                next_idx()
            return pos_map

        sorted_nodes = sorted(self.__nodes, key=lambda n: (n.label, n.phase))
        idx_map = {node: i for i, node in enumerate(sorted_nodes)}
        pos_map = build_pos_map()

        lines = ["digraph G {", "\tlayout=neato;", "\tsplines=true;"]
        if use_latex:
            lines.append("\tnode [shape=ellipse, width=0.6, height=0.4, fixedsize=true];")
        lines.append("")

        for node, idx in idx_map.items():
            x, y = pos_map[node]
            if use_latex:
                lines.append(f'\t{idx} [texlbl="${node.texlbl}$", pos="{x},{y}!" ];')
            else:
                lines.append(f'\t{idx} [label="{node}", pos="{x},{y}!" ];')

        lines.append("")

        for src, dsts in self.__adj_list.items():
            for label, dst in dsts.items():
                if use_latex:
                    lines.append(f'\t{idx_map[src]} -> {idx_map[dst]} [texlbl="${label}$"];')
                else:
                    lines.append(f'\t{idx_map[src]} -> {idx_map[dst]} [label="{label}"];')

        lines.append("}")

        return "\n".join(lines)


    def export_to_png(self, use_latex: bool = False) -> Optional[io.BytesIO]:
        try:
            if not use_latex:
                dot_content = self.export_to_dot()
                src = Source(dot_content)
                img_data = src.pipe(format='png')
                return io.BytesIO(img_data)

            dot_tex = dot2tex(self.export_to_dot(use_latex=True), format="tikz", crop=True)
            tex_src = self._patch_tex_source(dot_tex)

            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = Path(tmpdir) / "graph.tex"
                pdf_path = tex_path.with_suffix(".pdf")

                tex_path.write_text(tex_src)

                subprocess.run(
                    ["pdflatex", "-output-directory", tmpdir, str(tex_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

                image = convert_from_path(str(pdf_path))[0]
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                img_byte_arr.seek(0)
                return img_byte_arr
        except Exception as e:
            return None

    def _patch_tex_source(self, tex: str) -> str:
        lines = tex.splitlines()
        result = []
        for line in lines:
            if r"\documentclass{article}" in line:
                result.append(r"\documentclass[border=5pt]{standalone}")
            elif r"\enlargethispage" in line:
                continue
            else:
                result.append(line)
        return "\n".join(result)

    def __str__(self) -> str:
        if self.__adj_list:
            return "\n".join(f"{src} -> {', '.join(f'{label} : {dst}' for label, dst in dsts.items())}" for src, dsts in self.__adj_list.items())
        else:
            return "\n".join(str(node) for node in sorted(self.__nodes, key=lambda n: (n.phase, n.label)))