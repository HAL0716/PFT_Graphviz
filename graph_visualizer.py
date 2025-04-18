import io
import math
import tempfile
import subprocess
from typing import Optional
from pathlib import Path
from itertools import cycle
from collections import defaultdict
# 外部ライブラリ
from pdf2image import convert_from_bytes
from dot2tex import dot2tex
# 自作モジュール
from periodic_finite_type import PeriodicFiniteType
from Node import Node


class GraphVisualizer:
    def __init__(self, PFT: PeriodicFiniteType, x_scale: float = 1.0, y_scale: float = 1.0) -> None:
        self.PFT = PFT
        self.x_scale = x_scale
        self.y_scale = y_scale

    @property
    def dot(self) -> str:
        try:
            def build_node_layers() -> dict[int, list[Node]]:
                """ラベルの長さごとにノードを整理し、各層をソート"""
                layers = defaultdict(list)
                for node in self.PFT.nodes:
                    layers[len(node.label)].append(node)
                for nodes in layers.values():
                    nodes.sort(key=lambda n: n.phase)
                return dict(sorted(layers.items()))

            def calc_pos(idx: int, N: int, r: float) -> tuple[float, float]:
                """ノードの位置を計算"""
                angle = (math.pi / 2) - (idx * (2 * math.pi / N))
                return round(r * math.cos(angle) * self.x_scale, 2), round(r * math.sin(angle) * self.y_scale, 2)
            
            def set_N() -> int:
                """配置の調整"""
                return self.PFT.phase if self.PFT.phase > 3 else 6
            
            def build_pos_map() -> dict[Node, tuple[float, float]]:
                """ノードの配置"""
                N = set_N()
                used_cnt = [0] * N
                idx_iter = cycle(range(N))

                pos_map = {}
                for layer_len, nodes in build_node_layers().items():
                    if layer_len == 0:
                        nodes.reverse()
                    for node in nodes:
                        if layer_len == 0:
                            idx = next(idx_iter)
                        x, y = calc_pos(idx+1, N, used_cnt[idx] + 1)
                        pos_map[node] = (x, y)
                        used_cnt[idx] += 1
                    idx = next(idx_iter)

                return pos_map

            def build_idx_map() -> dict[Node, int]:
                """ノードの番号"""
                sorted_nodes = sorted(self.PFT.nodes, key=lambda n: (n.label, n.phase))
                return {node: i for i, node in enumerate(sorted_nodes)}

            pos_map = build_pos_map()
            idx_map = build_idx_map()

            lines = [
                "digraph G {",
                "\tlayout=neato;",
                "\tsplines=true;",
                "\tnode [shape=ellipse, width=0.6, height=0.4, fixedsize=true];"
            ]
            lines.append("")

            for node, idx in idx_map.items():
                x, y = pos_map[node]
                lines.append(f'\t{idx} [texlbl="${node.texlbl}$", pos="{x},{y}!"];')
            lines.append("")

            for src, dsts in self.PFT.adj_list.items():
                for label, dst in dsts.items():
                    lines.append(f'\t{idx_map[src]} -> {idx_map[dst]} [label="{label}", texlbl="${label}$"];')
            lines.append("}")

            return "\n".join(lines)
        
        except Exception as e:
            print(f"[DOT Error] {e}")
            return ""

    @property
    def tex(self) -> str:
        try:
            def process_tex(tex: str) -> str:
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
            
            dot_src = self.dot
            if not dot_src:
                print("[Error] Failed to generate DOT source.")
                return ""
            tex_src = dot2tex(dot_src, format="tikz", crop=True)
            return process_tex(tex_src)
        
        except Exception as e:
            print(f"[Tex Error] {e}")
            return ""

    @property
    def pdf(self) -> Optional[io.BytesIO]:
        try:
            tex_src = self.tex
            if not tex_src:
                return None

            with tempfile.TemporaryDirectory() as tmpdir:
                tex_path = Path(tmpdir) / "graph.tex"
                tex_path.write_text(tex_src)

                subprocess.run(
                    ["pdflatex", "-output-directory", tmpdir, str(tex_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

                pdf_path = tex_path.with_suffix(".pdf")
                pdf_bytes = pdf_path.read_bytes()

                return io.BytesIO(pdf_bytes)
        
        except subprocess.CalledProcessError as e:
            print(f"[PDF Generation Error] Failed to run pdflatex: {e}")
            return None
        except Exception as e:
            print(f"[PDF Error] {e}")
            return None

    @property
    def png(self) -> Optional[io.BytesIO]:
        try:
            pdf_io = self.pdf
            if not pdf_io:
                return None
            pdf_io.seek(0)
            image = convert_from_bytes(pdf_io.read())[0]
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            return img_byte_arr
        except Exception as e:
            print(f"[PNG Error] {e}")
            return None