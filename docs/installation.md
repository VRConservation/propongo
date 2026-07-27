# Installation

## Install from PyPI (Linux/Mac)

```bash
pip install propongo2
propongo2
```

Opens at [http://localhost:5000](http://localhost:5000)

## Windows Installation

**Recommended:** Use a virtual environment to avoid conflicts with system Python.

1. **Create virtual environment with Anaconda/Miniconda** (recommended)
   ```powershell
   # Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
   conda create -n propongo python=3.10
   conda activate propongo
   ```
   
   !!! warning
       Installing to base Python can cause package conflicts. [Learn about Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for better Python environment management.

2. **Install GTK3 Runtime** (required for PDF export)
   - Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Run installer, choose "Full installation"
   - Restart your computer

3. **Install Propongo2**
   ```powershell
   pip install propongo2
   ```

4. **Run the application**
   ```powershell
   propongo2
   ```
   
5. **Open browser** to http://localhost:5000

!!! note "Troubleshooting"
    If PDF export fails, ensure GTK3 is in your PATH. If Excel import doesn't work, run: `pip install pandas openpyxl tabulate`

## Install from source

```bash
git clone https://github.com/VRConservation/propongo2.git
cd propongo2
pip install -e .
propongo2
```

## Development setup

```bash
git clone https://github.com/VRConservation/propongo2.git
cd propongo2
pip install -e ".[dev]"
python run.py
```
