import os
import streamlit as st
from itertools import product
from periodic_finite_type import PeriodicFiniteType

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
    phase = st.sidebar.slider('周期', value=2, step=1, min_value=2, max_value=10)
    f_len = st.sidebar.slider('禁止語長', value=2, step=1, min_value=1, max_value=10)

    # --- 禁止語の入力 ---
    fword_all = [''.join(p) for p in product(alphabet, repeat=f_len)] if alphabet else []
    fword_init = [alphabet[0] * f_len] if alphabet else []
    fwords = st.multiselect('禁止語', fword_all, default=fword_init)

    # --- PFTの構築と禁止語の更新 ---
    try:
        PFT = PeriodicFiniteType(phase, f_len, fwords, True, OUTPUT_DIR)
        PFT.set_adj_list(alphabet)
        img = PFT.export_to_png()
        if img:
            st.image(img, caption="Generated Graph", use_column_width=True)
        else:
            st.write("画像の生成に失敗しました")
    except ValueError as e:
        st.error(f"エラー: {e}")
    except Exception as e:
        st.error(f"予期せぬエラー: {e}")

# ----------------------------------------
# 実行
# ----------------------------------------
if __name__ == "__main__":
    create_directory()
    main()
