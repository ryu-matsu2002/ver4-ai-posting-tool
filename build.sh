#!/usr/bin/env bash

# Pythonライブラリをインストール
pip install -r requirements.txt

# DBマイグレーションを実行（app.dbがなければ作成される）
flask db upgrade
