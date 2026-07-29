# Installation

## Install from PyPI (Linux/Mac)

```bash
pip install propongo
propongo
```

Opens at [http://localhost:5000](http://localhost:5000)

## Windows Installation

**Recommended:** Use a virtual environment to avoid conflicts with system Python.

1. **Create virtual environment with Anaconda/Miniconda** (recommended)
   ```powershell
   # Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
   conda create -n propongo python=3.13
   conda activate propongo
   ```
   
!!! note "Warning"
      Installing to base Python can cause package conflicts. Learn about [Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for better Python environment management or use [this](http://3point.xyz/geo2/appendix1/) mini guide to install a virtual environment on your machine. For even simpler management, install using uv (please see 'Install using uv' section).

2. **Install GTK3 Runtime** (Required for PDF export and any Windows OS users) <br>
   a. Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/
   <br>
   b. Run installer, choose "Full installation"
   <br>
   c. Restart your computer

3. **Install Propongo**
   ```powershell
   pip install propongo
   ```

4. **Run the application**
   ```powershell
   propongo
   ```
   
5. **Open browser** to http://localhost:5000 or control click on the link to the localhost browser in your terminal.

!!! note "Troubleshooting"
    If PDF export fails, ensure GTK3 is in your PATH. If Excel import doesn't work, run: `pip install pandas openpyxl tabulate`

## Install using uv
Installing propongo using uv is faster and simpler than using conda and keeps everything in the same folder for easier project and software management and not having to look in obscure files layers deep in your OS. The package also handles virtual environments automatically. If you're using windows, make sure to install GTK3 first, as described above.

1. Install uv. Go to https://docs.astral.sh/uv and click on installation in the left panel. For linux and mac:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Install git by following the instructions at https://git-scm.com/install/windows. Or if you don't want to do that go to https://github.com/VRConservation/propongo, click on the green code button and select download zip, unzip, and save the file where you want it.
3. After installing git, go to the folder where you want the propongo files, right click and select open in terminal.
4. Go to https://github.com/VRConservation/propongo, click the green code button and copy the url under clone.
5. Run git clone https://github.com/VRConservation/propongo.git in your terminal
6. In the same open terminal run:
```bash
uv sync
uv run propongo
```
7. Open propongo at http://localhost:5000 or ctrl + click in the server link in the terminal
8. Start using the app.

## Install from source

```bash
git clone https://github.com/VRConservation/propongo.git
cd propongo
pip install -e .
propongo
```

## Development setup

```bash
git clone https://github.com/VRConservation/propongo.git
cd propongo
pip install -e ".[dev]"
python run.py
```
