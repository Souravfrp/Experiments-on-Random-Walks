# Run the optimized study on my Mac

I have already created a Conda environment named `random-walks-viz`. I can reuse it for this new version.

1. Download and extract `Random_Walks_Optimized_Research_v2.zip` to `~/Downloads/`.
2. Open Terminal and run:

```bash
cd ~/Downloads/Random_Walks_Optimized_Research_v2
conda activate random-walks-viz
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

3. For the full n=20 run in **one command**:

```bash
python run_all.py --dimensions 20 --steps 2560 --chains 3000 --seed 2026 --repeats 1 --threads 4
```

4. To open all stages within Jupyter, use:

```bash
python -m notebook
```

Open `notebooks/01_full_python_cpp_study.ipynb`, choose the settings in its **one parameter cell**, and run the notebook. This uses the Python kernel to invoke a native C++17 executable; the C++ random walk is genuinely compiled, not simulated with Python.

5. Outputs appear in a **new UTC-timestamped** `runs/<id>/` folder, containing numerical CSV files, plots, comparison matrices, run metadata and completion status. Each new execution gets its own folder.

For a small pilot, replace `20` with `2,3,5`, and use `--steps 128 --chains 300 --threads 1`.

**If the C++ compiler command cannot be found**, install Apple Command Line Tools via Terminal `xcode-select --install`, then retry. If Matplotlib or NumPy versions disagree, install compatible packages **in the dedicated `random-walks-viz` environment**, not in Anaconda `base`.

**Interpretation note:** A common seed does not imply Python and C++ coordinate-for-coordinate identical outputs. A checkpoint below the chosen empirical threshold does not certify that total-variation distance is small. Preserve `parameters.json` with every set of results.
