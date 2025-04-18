import os
import streamlit as st
from itertools import product
from periodic_finite_type import PeriodicFiniteType
from graph_visualizer import GraphVisualizer

# ----------------------------------------
# 定数
# ----------------------------------------
SYMBOLS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
OUTPUT_DIR = "output"

# ----------------------------------------
# 関数
# ----------------------------------------
def create_directory() -> None:
    """
    プログラム開始時にoutputディレクトリを自動で作成します。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------
# メインUI
# ----------------------------------------
def main():
    st.title('PFTのグラフを生成')

    # --- サイドバー（パラメータ入力） ---
    st.sidebar.header('パラメータの入力')
    alphabet = st.sidebar.multiselect('シンボル', list(SYMBOLS), default=['0', '1'])
    phase    = st.sidebar.slider('周期', value=2, step=1, min_value=2, max_value=10)
    f_len    = st.sidebar.slider('禁止語長', value=2, step=1, min_value=1, max_value=10)
    st.sidebar.header('描画の設定')
    x_scale  = st.sidebar.slider('縮尺: x', value=1.0, step=0.1, min_value=0.2, max_value=2.0)
    y_scale  = st.sidebar.slider('縮尺: y', value=0.5, step=0.1, min_value=0.2, max_value=2.0)

    # --- 禁止語の入力 ---
    fword_all = [''.join(p) for p in product(alphabet, repeat=f_len)] if alphabet else []
    fword_init = [alphabet[0] * f_len] if alphabet else []
    fwords = st.multiselect('禁止語', fword_all, default=fword_init)

    # --- PFTの構築と禁止語の更新 ---
    try:
        PFT = PeriodicFiniteType(phase, f_len, fwords, True)
        PFT.set_adj_list(alphabet)

        Graph = GraphVisualizer(PFT, x_scale, y_scale)

        img = Graph.png
        pdf = Graph.pdf

        if img:
            st.header("画像データ")
            st.image(img, use_container_width=True)

            st.subheader("⬇ ダウンロード")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="PNG を保存",
                    data=img,
                    file_name="graph.png",
                    mime="image/png",
                    key="png_dl",
                    use_container_width=True
                )
            with col2:
                if pdf:
                    st.download_button(
                        label="PDF を保存",
                        data=pdf,
                        file_name="graph.pdf",
                        mime="application/pdf",
                        key="pdf_dl",
                        use_container_width=True
                    )
        else:
            st.error("PNG の出力に失敗しました。")

        dot = Graph.dot
        if dot:
            st.header("DOT ファイル")
            st.code(dot, language='dot')

            st.subheader("⬇ ダウンロード")
            st.download_button(
                label="DOT を保存",
                data=dot,
                file_name="graph.dot",
                mime="text/plain",
                key="dot_dl",
                use_container_width=True
            )
        else:
            st.write("Error: DOT の出力")

    except ValueError as e:
        st.error(f"エラー: {e}")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

# ----------------------------------------
# 実行
# ----------------------------------------
if __name__ == "__main__":
    main()
