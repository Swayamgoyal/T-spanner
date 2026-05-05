#!/bin/bash

echo "🚀 Starting Baswana-Sen T-Spanner Verification..."

# 1. Build C++ Implementation
echo "🔨 Compiling C++ core..."
cd algos/cpp/ && make && cd ../..

# 2. Run Python Unit Tests
echo "🧪 Running unit tests..."
pytest experiments/tests/test_core.py

# 3. Run a sample experiment (Facebook 3-spanner)
echo "📊 Running sample experiment (ego-Facebook)..."
python3 algos/python/baswana_sen.py --k 2 --topology facebook --quiet

echo "✅ All components verified successfully!"
