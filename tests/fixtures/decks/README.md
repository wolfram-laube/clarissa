# Test Fixture Decks

Reference simulation input decks for integration and contract testing.

## Provenance

| Deck | Source | License | Grid | Description |
|------|--------|---------|------|-------------|
| `spe1/SPE1CASE1.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 Case 1 — basic three-phase black-oil |
| `spe1/SPE1CASE2.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 Case 2 — dissolved gas, primary reference |
| `spe1/SPE1CASE2_2P.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 two-phase (oil-water only) |
| `spe9/SPE9_CP.DATA` | OPM/opm-data | ODbL | 24×25×15 (9000) | SPE9 corner-point, 26 wells |
| `spe9/SPE9_CP_SHORT.DATA` | OPM/opm-data | ODbL | 24×25×15 (9000) | SPE9 short run (fewer timesteps) |
| `watershed/WATERSHED.DATA` | Doug (pm-flow) | Internal | 20×20×3 (1200) | Groundwater recharge demo |

## Large Models (via Git Submodule)

Available in `data/opm-data/` (not copied into fixtures due to size or because the canonical version lives in the submodule):

| Model | Path | Grid | Size | Use Case |
|-------|------|------|------|----------|
| SPE3 | `spe3/SPE3CASE1.DATA` | 9×9×4 (324) | 36KB | Gas condensate with VAPOIL/DISGAS |
| SPE5 | `spe5/SPE5CASE1.DATA` | 7×7×3 (147) | 24KB | Miscible flood with solvent — WAG injection, 21 half-cycles |
| SPE10 M1 | `spe10model1/SPE10_MODEL1.DATA` | 100×1×20 (2K) | 204KB | 2D cross-section upscaling benchmark |
| SPE10 M2 | `spe10model2/SPE10_MODEL2.DATA` | 60×220×85 (1.1M) | 74MB | Large heterogeneous stress test |
| Norne | `norne/NORNE_ATW2013.DATA` | 46×112×22 (113K) | 31MB | Real North Sea field validation |
| Sleipner | `sleipner/SLEIPNER_ORG.DATA` | 64×118×263 (2M) | 59MB | CO₂ storage benchmark |

Access: `git submodule update --init data/opm-data`

## Verifying Deck Authenticity

Reservoir-simulation benchmark decks circulate widely (papers, forks, internal mailing lists, colleagues' laptops), and modified variants are easy to mistake for the original. **Before trusting a deck someone hands you, verify its SHA256 against this manifest.**

### Canonical reference

All hashes in this section refer to the OPM/opm-data submodule pin:

```
Repository:  https://github.com/OPM/opm-data.git
Branch:      master
Commit:      eaa2261683a97027e057c2bc49612ad1c86390b3  (2023-05-05)
```

The CLARISSA submodule `data/opm-data` is pinned to this commit. The vendored fixtures under `tests/fixtures/decks/` and `tests/voice/spe_models/` are byte-identical copies of the corresponding files in the submodule at this pin.

### How to verify

```bash
sha256sum path/to/some/SPE5CASE1.DATA
# compare the output against the manifest below
# match → canonical opm-data version (the right thing)
# no match → a modified variant; do NOT silently replace canonical files
```

### Manifest — vendored fixtures

| Path | Size | SHA256 |
|------|-----:|--------|
| `tests/fixtures/decks/spe1/SPE1CASE1.DATA`     | 11,927 | `e26f11a6438ecd97fc56ccd456a463c74680a912e3d9f71b33682bd7c0531b3f` |
| `tests/fixtures/decks/spe1/SPE1CASE2.DATA`     | 11,907 | `29d9c02659031026ffbab9f62d6400642a61bf2bfaf8c0ac0c7b82f147f4bd29` |
| `tests/fixtures/decks/spe1/SPE1CASE2_2P.DATA`  |  9,292 | `f0d65321174f40c3bc9d47f8218df9003f15a47121049b4912f78c859c90d511` |
| `tests/fixtures/decks/spe9/SPE9_CP.DATA`       | 15,580 | `cbfaf7adccf562a2e368160589ef1c3250795120fd3de0dd6af48c4e2e7d823a` |
| `tests/fixtures/decks/spe9/SPE9_CP_SHORT.DATA` | 15,588 | `76f782c829a9e70a0aebf06075b52368b094b4a63ea5b923d4dbb6dc40a0be92` |
| `tests/voice/spe_models/SPE1CASE1.DATA`        | 11,927 | `e26f11a6438ecd97fc56ccd456a463c74680a912e3d9f71b33682bd7c0531b3f` |
| `tests/voice/spe_models/SPE9.DATA`             | 15,927 | `358bbc47699a857c939eab48700018e3deeeb8478c5c0bc85c1eb5842e361f45` |

### Manifest — submodule decks (most frequently used)

| Path (under `data/opm-data/`) | Size | SHA256 |
|------|-----:|--------|
| `spe1/SPE1CASE1.DATA`        | 11,927 | `e26f11a6438ecd97fc56ccd456a463c74680a912e3d9f71b33682bd7c0531b3f` |
| `spe1/SPE1CASE2.DATA`        | 11,907 | `29d9c02659031026ffbab9f62d6400642a61bf2bfaf8c0ac0c7b82f147f4bd29` |
| `spe1/SPE1CASE2_2P.DATA`     |  9,292 | `f0d65321174f40c3bc9d47f8218df9003f15a47121049b4912f78c859c90d511` |
| `spe3/SPE3CASE1.DATA`        | — | `601cc21ff148e96ab7c6023eead283530f05f3678cfa862fcddf56f3e8d479af` |
| `spe3/SPE3CASE2.DATA`        | — | `0f31fa4751458c2dbbbe3a954b9d6b543e86ff63c241ec888e541c0881dce415` |
| `spe5/SPE5.BASE`             |  9,106 | `ab60ca7fef525d4957f524a1b1ed2d32f614492553f03ce9f55dec95eebc75f4` |
| `spe5/SPE5CASE1.DATA`        |  4,217 | `91dacb0d796b94c917c88566dd35e3e5e58557af4190b6e71621ab591e346241` |
| `spe9/SPE9.DATA`             | 15,927 | `358bbc47699a857c939eab48700018e3deeeb8478c5c0bc85c1eb5842e361f45` |
| `spe9/SPE9_CP.DATA`          | 15,580 | `cbfaf7adccf562a2e368160589ef1c3250795120fd3de0dd6af48c4e2e7d823a` |
| `spe9/SPE9_CP_SHORT.DATA`    | 15,588 | `76f782c829a9e70a0aebf06075b52368b094b4a63ea5b923d4dbb6dc40a0be92` |
| `spe10model1/SPE10_MODEL1.DATA` | — | `77741b9674e7fa809b736449fa4684f0d28456c92874b06311aaf0ac0edee93e` |
| `spe10model1/SPE10_MODEL1_CP.DATA` | — | `a321465eeab18830c35d4f97eeb8d53ee3d84c203c7bce18bf4bc9239af929de` |
| `spe10model2/SPE10_MODEL2.DATA` | — | `74723a59446bdcae34e2b4f86c98216c03b1cf67286d1a6e45dc3134b2a96c63` |
| `norne/NORNE_ATW2013.DATA`   | — | `f346c910f68a80b41ee54606bd434dc9e2993fffa7a2469235f396c2c0a9e080` |
| `sleipner/SLEIPNER_ORG.DATA` | — | `cf766afbe3f3960a594d421ec25f0870375cd230467f5c31612ca1aa3d32c126` |

The full manifest (all 49 `.DATA`/`.BASE`/`.INC`/`.GRDECL` files in the submodule, including include-files for Norne and Sleipner) can be regenerated at any time with:

```bash
cd data/opm-data
find . -type f \( -name "*.DATA" -o -name "*.BASE" -o -name "*.INC" -o -name "*.GRDECL" \) \
  -not -path "./.git/*" | sort | xargs sha256sum
```

### Policy for received decks

When a colleague hands you a deck file:

1. **Verify SHA256.** If it matches the manifest, treat as canonical. Done.
2. **If it does not match,** do **not** silently overwrite the canonical version under `data/opm-data/` (submodule) or `tests/fixtures/decks/`. Instead:
   - File it as `<name>_VARIANT.DATA` (or `_SHORT.DATA`, `_<purpose>.DATA`) in an appropriate location.
   - Add a row to this README's Provenance table documenting the source, the modification, and the use case.
   - If the modification is intentional and reusable, fold it into a proper fixture with its own SHA256 entry.
3. **If the submodule pin needs to advance** (i.e., upstream has new commits we want), update `.gitmodules`/`git submodule update --remote` in a dedicated MR that also refreshes this manifest. Do not mix submodule bumps with unrelated changes.

## Licensing

OPM reference data: Open Database License (ODbL 1.0)
http://opendatacommons.org/licenses/odbl/1.0/

Individual contents: Database Contents License (DbCL 1.0)
http://opendatacommons.org/licenses/dbcl/1.0/
