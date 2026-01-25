# ============================================================
# CLARISSA Colab Setup
# Run this cell at the beginning of any notebook in Colab
# ============================================================

"""
Usage in Colab:
    
    !wget -q https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa/-/raw/main/docs/tutorials/colab_setup.py
    exec(open('colab_setup.py').read())
    
Or copy-paste the COLAB_SETUP_CELL below into your first cell.
"""

COLAB_SETUP_CELL = '''
# ============================================================
# 🚀 CLARISSA Colab Setup - Run this first!
# ============================================================

import os
import subprocess
import sys

def setup_clarissa_colab(
    gitlab_repo="https://gitlab.com/wolfram_laube/blauweiss_llc/clarissa.git",
    branch="main",
    tutorials_path="docs/tutorials",
    use_gpu=True
):
    """
    Set up CLARISSA environment in Google Colab.
    
    Args:
        gitlab_repo: GitLab repository URL
        branch: Branch to clone
        tutorials_path: Path to tutorials within repo
        use_gpu: Whether to check for GPU availability
    """
    
    print("🔧 Setting up CLARISSA environment...")
    print("=" * 50)
    
    # 1. Check if we're in Colab
    IN_COLAB = 'google.colab' in sys.modules
    if not IN_COLAB:
        print("⚠️  Not running in Colab - skipping Colab-specific setup")
        return
    
    # 2. Check GPU
    if use_gpu:
        gpu_info = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if gpu_info.returncode == 0:
            print("✅ GPU available")
            # Extract GPU name
            for line in gpu_info.stdout.split('\n'):
                if 'Tesla' in line or 'A100' in line or 'V100' in line or 'T4' in line:
                    print(f"   {line.strip()}")
                    break
        else:
            print("⚠️  No GPU detected - go to Runtime → Change runtime type → GPU")
    
    # 3. Clone repository
    repo_name = "clarissa"
    if not os.path.exists(repo_name):
        print(f"\n📥 Cloning repository...")
        subprocess.run([
            'git', 'clone', '--depth', '1', '--branch', branch, gitlab_repo
        ], check=True)
        print(f"✅ Repository cloned")
    else:
        print(f"✅ Repository already exists")
    
    # 4. Change to tutorials directory
    tutorials_full_path = os.path.join(repo_name, tutorials_path)
    if os.path.exists(tutorials_full_path):
        os.chdir(tutorials_full_path)
        print(f"✅ Working directory: {os.getcwd()}")
    
    # 5. Install Python dependencies
    print(f"\n📦 Installing dependencies...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-q',
        'numpy', 'pandas', 'matplotlib', 'seaborn',
        'sentence-transformers',
        'openai', 'anthropic',
        'fastapi', 'httpx',
        'pyyaml', 'tqdm'
    ], check=True)
    
    # Optional: heavier dependencies
    print("📦 Installing optional dependencies (this may take a minute)...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-q',
        'langchain', 'langchain-community',
        'z3-solver'
    ], check=False)  # Don't fail if these don't install
    
    print("\n" + "=" * 50)
    print("✅ CLARISSA setup complete!")
    print("=" * 50)
    
    # 6. Print available notebooks
    print("\n📚 Available notebooks:")
    notebooks = sorted([f for f in os.listdir('notebooks') if f.endswith('.ipynb')])
    for nb in notebooks:
        print(f"   • {nb}")
    
    print("\n💡 Tip: Use the file browser (📁) to open notebooks")
    print("💡 Tip: For GPU tasks, ensure Runtime → GPU is selected")
    
    return True

# Run setup
setup_clarissa_colab()
'''

# ============================================================
# Colab Limitations & Workarounds
# ============================================================

COLAB_LIMITATIONS = """
## Colab Limitations for CLARISSA

| Feature | GitPod | Colab | Workaround |
|---------|--------|-------|------------|
| PostgreSQL + pgvector | ✅ | ❌ | Use SQLite + in-memory vectors |
| OPM Flow | ✅ Docker | ❌ | Mock simulator or API call |
| Persistent storage | ✅ Git | ⚠️ Google Drive | Mount Drive |
| GPU | ❌ | ✅ | Use Colab for training |
| Full environment | ✅ | ❌ | Subset of features |

### Recommended Workflow:
1. **Development**: Use GitPod (full features)
2. **GPU Training**: Use Colab (RL agent, embeddings)
3. **Production**: Deploy to cloud (GCP/AWS)
"""

# ============================================================
# SQLite Vector Search (Colab alternative to pgvector)
# ============================================================

SQLITE_VECTOR_SETUP = '''
# SQLite-based vector search for Colab (no PostgreSQL needed)

import sqlite3
import numpy as np
import json
from typing import List, Tuple

class SimpleVectorStore:
    """
    Lightweight vector store using SQLite.
    For Colab environments where PostgreSQL isn't available.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                content TEXT NOT NULL,
                source_type TEXT,
                metadata TEXT,
                embedding BLOB
            )
        """)
        self.conn.commit()
    
    def add(self, content: str, embedding: np.ndarray, 
            source_type: str = None, metadata: dict = None):
        """Add a document with its embedding."""
        self.conn.execute(
            "INSERT INTO documents (content, source_type, metadata, embedding) VALUES (?, ?, ?, ?)",
            (content, source_type, json.dumps(metadata or {}), embedding.tobytes())
        )
        self.conn.commit()
    
    def search(self, query_embedding: np.ndarray, limit: int = 5) -> List[Tuple[str, float]]:
        """Find most similar documents using cosine similarity."""
        cursor = self.conn.execute("SELECT content, embedding FROM documents")
        
        results = []
        for content, emb_bytes in cursor:
            stored_emb = np.frombuffer(emb_bytes, dtype=np.float32)
            similarity = np.dot(query_embedding, stored_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_emb)
            )
            results.append((content, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

# Usage:
# store = SimpleVectorStore()
# store.add("WELSPECS defines wells", embedding_vector)
# results = store.search(query_vector, limit=3)
'''

# ============================================================
# Mock OPM Flow for Colab
# ============================================================

MOCK_OPM_FLOW = '''
# Mock OPM Flow simulator for Colab environments

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
import time

@dataclass
class MockSimulationResult:
    """Simulated result for demo purposes."""
    success: bool
    runtime_seconds: float
    timesteps: int
    
    # Production data (synthetic)
    times: np.ndarray          # days
    oil_rate: np.ndarray       # STB/day
    water_rate: np.ndarray     # STB/day
    pressure: np.ndarray       # psia
    
    water_breakthrough_days: Optional[float] = None
    cumulative_oil: float = 0.0
    cumulative_water: float = 0.0

class MockOPMFlow:
    """
    Mock simulator that generates realistic-looking results.
    For demonstration when OPM Flow isn't available.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
    
    def run(self, deck_content: str, duration_days: int = 365) -> MockSimulationResult:
        """
        Generate synthetic simulation results.
        
        The mock uses simple decline curve analysis to generate
        plausible-looking production profiles.
        """
        print("🛢️ Running mock simulation (OPM Flow not available in Colab)...")
        time.sleep(1)  # Simulate some processing time
        
        # Parse some basic info from deck (simplified)
        has_injector = 'WCONINJE' in deck_content
        
        # Time array
        dt = 30  # monthly timesteps
        times = np.arange(0, duration_days + dt, dt)
        n_steps = len(times)
        
        # Initial conditions
        q_oil_initial = 500 + self.rng.uniform(-100, 100)  # STB/day
        p_initial = 4000 + self.rng.uniform(-200, 200)     # psia
        
        # Decline parameters
        if has_injector:
            # Waterflood: slower decline, water breakthrough
            decline_rate = 0.1 / 365  # 10% per year
            breakthrough_time = 180 + self.rng.uniform(-30, 60)
        else:
            # Primary: faster decline
            decline_rate = 0.3 / 365  # 30% per year
            breakthrough_time = None
        
        # Generate profiles
        oil_rate = q_oil_initial * np.exp(-decline_rate * times)
        
        # Water rate (zero until breakthrough, then increasing)
        water_rate = np.zeros_like(times)
        if breakthrough_time:
            bt_idx = np.searchsorted(times, breakthrough_time)
            if bt_idx < n_steps:
                water_rate[bt_idx:] = 100 * (1 - np.exp(-0.005 * (times[bt_idx:] - breakthrough_time)))
        
        # Pressure decline
        pressure = p_initial - 0.5 * times + self.rng.normal(0, 20, n_steps)
        pressure = np.maximum(pressure, 500)  # Min BHP
        
        # Cumulative
        cum_oil = np.trapz(oil_rate, times)
        cum_water = np.trapz(water_rate, times)
        
        print(f"✅ Mock simulation complete: {n_steps} timesteps")
        
        return MockSimulationResult(
            success=True,
            runtime_seconds=1.0,
            timesteps=n_steps,
            times=times,
            oil_rate=oil_rate,
            water_rate=water_rate,
            pressure=pressure,
            water_breakthrough_days=breakthrough_time,
            cumulative_oil=cum_oil,
            cumulative_water=cum_water
        )

# Usage:
# simulator = MockOPMFlow()
# result = simulator.run(deck_content, duration_days=1825)
# plt.plot(result.times, result.oil_rate)
'''

if __name__ == "__main__":
    print("CLARISSA Colab Setup Module")
    print("=" * 40)
    print("
Copy the COLAB_SETUP_CELL into your first Colab cell:")
    print(COLAB_SETUP_CELL[:500] + "...")
