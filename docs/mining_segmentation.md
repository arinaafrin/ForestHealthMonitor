# Mining-area segmentation baseline (Sentinel-2 + U-Net)

An optional extension of Forest Health Monitor. It reuses the Earth Engine
connection and CI of this project, but lives in `src/mining/` and has its own
requirements, so the API image does not need PyTorch.

**Goal.** Train a small U-Net that marks mining areas (open pits, waste rock
dumps, tailings dams, processing areas) in Sentinel-2 imagery, and measure it
honestly on regions it has never seen.

**Status.** Baseline with results from real runs (26 and 27 October 2026). The
score is modest. Read the limits below before using any number.

## Summary

| Method | Test IoU |
|---|---|
| All-mine guess (every pixel is "mine") | 0.149 |
| Random Forest, one pixel at a time | 0.275 |
| U-Net, mean of 3 training runs | 0.336 (95% interval 0.268 to 0.408) |

The U-Net is better than both simple methods, but the gap to the Random Forest
is small compared with the uncertainty, and I did not test it formally.

## Data

| Part | Source |
|---|---|
| Images | Sentinel-2 L2A (`COPERNICUS/S2_SR_HARMONIZED`), median composite of 2019, cloud masked with the SCL band. Bands B2, B3, B4, B8, B11, B12 at 10 m |
| Labels | Maus et al. (2022), *Global-scale mining polygons (Version 2)*, PANGAEA, https://doi.org/10.1594/PANGAEA.942325, licence CC BY-SA 4.0 |

The polygons were drawn by visual interpretation of 2019 Sentinel-2 imagery.
That is why the image year is 2019.

## Known limits of the labels (read before trusting any score)

- The label is one class, "mining area". Open pits, waste rock dumps, tailings
  dams, water ponds and processing plants are **not** separated in the polygons.
- The authors report 88.3% overall accuracy against 1,000 control points, with
  producer's accuracy for the mine class of 78.9%. So some mine pixels are
  missing from the labels (label noise).
- Only a 10 km buffer around known mine coordinates was inspected. The data
  does not cover every mine. A patch chosen as "no mine" can still contain an
  unmapped mine. Negative patches are therefore **approximately** negative.
- Labels are one year (2019). Mines change over time.

## Design choices

- **Spatial split.** Patches are grouped into lon/lat blocks (default 1 degree).
  A whole block goes to one split. This stops near-identical neighbouring
  patches from appearing in both train and test. `check_no_block_leak` raises if
  this ever fails, and a test covers it.
- **Normalisation from train only.** Channel mean and std never see val or test.
- **Test set used once per run**, with the checkpoint chosen on validation IoU.
- **Metrics from pixel counts over the whole split**, not averages of per-image
  scores. Reported: IoU, F1, precision, recall.
- **Fixed seeds** and a config file saved in every run folder. The training seed
  changes initialisation and batch order only. The data split is the same for
  all seeds.

## Results

### Setup

- 500 patches: 400 centred on a mapped mine, 100 "negative" patches placed
  away from any mapped polygon (about 15 km, approximate).
- Patch size 256 x 256 pixels (2.56 km).
- Split by 1-degree blocks: 352 train, 74 validation, 74 test patches.
- The test set has 62 patches with a mapped mine, 12 negative patches and 56
  spatial blocks.
- U-Net with 483,169 parameters, trained on a CPU. AdamW, learning rate 0.0005,
  up to 40 epochs, early stopping after 15 epochs without improvement, loss =
  binary cross-entropy + Dice, threshold 0.5.

### U-Net, three training seeds

| Seed | Val IoU | Test IoU | Test precision | Test recall |
|---|---|---|---|---|
| 1 | 0.405 | 0.332 | 0.542 | 0.461 |
| 2 | 0.411 | 0.340 | 0.581 | 0.450 |
| 3 | 0.410 | 0.338 | 0.586 | 0.445 |
| Mean (counts averaged) | | 0.336 | | |

Validation is higher than test because the checkpoint was chosen on validation.
Only the test numbers should be quoted.

**Uncertainty.** Resampling the 56 test blocks 2,000 times gives a 95% interval
of 0.268 to 0.408 for the mean IoU. The three seeds agree closely because they
share one split, so they show training noise only. The interval covers the
choice of test patches, not the choice of split or training data.

### Comparison with simple methods (test set)

| Method | IoU | Precision | Recall |
|---|---|---|---|
| All-mine guess | 0.149 | 0.149 | 1.000 |
| Random Forest, per pixel, threshold 0.5 | 0.275 | 0.328 | 0.634 |
| U-Net seed 1, threshold 0.5 | 0.332 | 0.542 | 0.461 |
| U-Net seed 1, threshold 0.40 (chosen on validation) | 0.344 | 0.505 | 0.519 |

- Random Forest: 100 trees, depth 12, 400,000 training pixels from the 352 train
  patches, features are the 6 bands plus NDVI and NBR. Its validation-chosen
  threshold (0.70) gave a worse test IoU (0.223), so its validation and test
  results disagree. The 0.5 result is shown.
- Threshold: validation IoU is almost flat between 0.30 and 0.55, and the test
  gain at 0.40 (+0.012) is small. The main number uses 0.5.
- No paired test between the U-Net and the Random Forest was run.

### First, smaller run

150 patches (105 train, 25 validation, 20 test), different sites and a different
split. Test IoU 0.252 against an all-mine guess of 0.098. It stopped after 12
epochs with the best epoch at 4. The two runs are not directly comparable, but
the larger dataset gave a steadier training curve and a higher score.

### Per-patch results (seed 1, threshold 0.5)

- 62 patches with a mapped mine: median IoU 0.286, range 0.000 to 0.817.
- 10 of these 62 were almost missed (predicted area under 20% of the label).
- 3 of the 12 negative patches have more than 1% of pixels marked as mine.

## Failure analysis

Worst patches from `test_per_patch.csv`. For negative patches the IoU is 0 if
even one pixel is marked, so check the predicted percentage as well.

| Patch | Country | Type | Label % | Predicted % | IoU | What the picture shows |
|---|---|---|---|---|---|---|
| pos_00069 | MWI | mine | 0.8 | 0.0 | 0.000 | (add after checking) |
| pos_00107 | MEX | mine | 8.9 | 0.0 | 0.000 | (add after checking) |
| pos_00134 | MAR | mine | 5.8 | 0.0 | 0.000 | (add after checking) |
| pos_00197 | SLV | mine | 1.3 | 0.0 | 0.000 | (add after checking) |
| pos_00227 | AFG | mine | 2.3 | 2.5 | 0.000 | (add after checking) |
| neg_00008 | IRN | negative | 0.0 | 13.0 | 0.000 | (add after checking) |
| neg_00041 | IND | negative | 0.0 | 0.4 | 0.000 | (add after checking) |
| neg_00051 | BFA | negative | 0.0 | 60.7 | 0.000 | (add after checking) |

Facts from the table: three of the five worst mapped-mine patches have labels
covering less than 3% of the patch. In `pos_00227` the model marked about the
right amount (2.5% against 2.3%) but in the wrong place. Two negative patches
have large marked areas (13% and 60.7%); each is either an unmapped mine or a
real false alarm, and the picture has to decide which.

## What these results support

- A small U-Net, trained on 352 patches, finds mining areas on unseen regions
  clearly better than an all-mine guess (about 0.34 against 0.15).
- It is somewhat better than a per-pixel Random Forest, mainly through fewer
  false alarms (precision 0.54 against 0.33).

## What they do not support

- Any claim of high accuracy. Precision and recall are both about 0.5.
- Any claim about specific mine types, countries or years.
- Small differences between runs, thresholds or methods. The interval is wide.

## Folder layout

```
src/mining/
  config.py         settings (dataclasses)
  geo.py            UTM zone and pixel grid helpers
  labels.py         read polygons, polygons -> mask
  sampling.py       choose sites, spatial blocks, splits, leak check
  gee_export.py     download one Sentinel-2 patch (Earth Engine)
  build_dataset.py  export all patches + manifest.csv
  dataset.py        PyTorch dataset, train-only normalisation
  model.py          small U-Net
  losses.py         BCE + Dice
  metrics.py        IoU, F1, precision, recall from counts
  train.py          training loop, early stopping, final test
  evaluate.py       re-evaluate a saved run
  visualise.py      image | label | prediction pictures
  synthetic.py      fake data for smoke tests ONLY
  cli.py            command line
scripts/mining/
  analyse_run.py    per-patch summary of a run
  bootstrap_ci.py   95% interval by resampling spatial blocks
  threshold_sweep.py  threshold chosen on validation, applied to test
  rf_baseline.py    per-pixel Random Forest comparison
tests/unit/mining/  unit tests (no internet, no Earth Engine)
```

## Commands

```bash
# setup
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-mining.txt
pytest tests/unit/mining -v

# smoke run on fake data (checks the code runs; says nothing about accuracy)
python -m src.mining.cli synthetic --out data/synthetic
python -m src.mining.cli train --data-dir data/synthetic --run-dir runs/smoke --epochs 15 --lr 0.003 --base-channels 8

# real data: download the GeoPackage from the PANGAEA record and save it as
# data/raw/global_mining_polygons_v2.gpkg, then set GEE_SERVICE_ACCOUNT_EMAIL
# and GOOGLE_APPLICATION_CREDENTIALS
python -m src.mining.cli build-dataset --limit 3 --out-dir data/mining_probe
python -m src.mining.cli build-dataset --n-sites 400 --out-dir data/mining_500

# the runs reported above
python -m src.mining.cli train --data-dir data/mining_500 --run-dir runs/m500_seed1 --epochs 40 --patience 15 --lr 0.0005
python -m src.mining.cli train --data-dir data/mining_500 --run-dir runs/m500_seed2 --epochs 40 --patience 15 --lr 0.0005 --seed 2
python -m src.mining.cli train --data-dir data/mining_500 --run-dir runs/m500_seed3 --epochs 40 --patience 15 --lr 0.0005 --seed 3

# analysis
python scripts/mining/analyse_run.py runs/m500_seed1 data/mining_500
python scripts/mining/bootstrap_ci.py data/mining_500 runs/m500_seed1 runs/m500_seed2 runs/m500_seed3
python scripts/mining/threshold_sweep.py runs/m500_seed1 data/mining_500
python scripts/mining/rf_baseline.py data/mining_500
```

## Next steps (not done)

- Test sensitivity to label noise (for example, drop 20% of mine pixels in the
  training masks).
- Test on countries that are not in training.
- Export more patches (about 1,000) and train on a GPU.
- Add Sentinel-1 backscatter as extra channels.
- Run a paired test between the U-Net and the Random Forest.