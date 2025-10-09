#!/bin/bash
cd "$(dirname "$0")"
streamlit run showcase.py --server.port 8501
