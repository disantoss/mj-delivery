#!/bin/bash
pip install -r requirements.txt --quiet
python -m streamlit run app_delivery.py \
  --server.port 8000 \
  --server.address 0.0.0.0 \
  --server.headless true
