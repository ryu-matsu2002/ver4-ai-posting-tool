#!/bin/bash

# DBマイグレーションを実行
flask db upgrade

# アプリを起動（create_app() を使って生成）
gunicorn 'app:create_app()'
