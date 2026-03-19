# e2ectl

kubectl-style CLI for Axis Communications edge-to-edge device pairing.

Replace multi-step web GUI configuration with declarative YAML manifests. Discover devices, plan pairings, apply them in one command, verify state, and tear down cleanly.

## Install

```bash
pip install e2ectl
# or
pipx install e2ectl
```

**From source:**

```bash
git clone https://github.com/oneshot2001/e2ectl.git
cd e2ectl
pip install -e ".[dev]"
```

## Quick Start

```bash
# 1. Discover Axis devices on your network
e2ectl discover --range 10.1.1.0/24 -u root -p $E2ECTL_DEFAULT_PASS

# 2. Bootstrap a manifest from discovered devices
e2ectl discover --range 10.1.1.0/24 -u root -p $PASS -o yaml > site.yaml
# Edit site.yaml to add your pairings

# 3. Validate your manifest
e2ectl plan -f site.yaml

# 4. Apply pairings
e2ectl apply -f site.yaml

# 5. Verify pairing state
e2ectl verify -f site.yaml

# 6. Tear down when needed
e2ectl teardown -f site.yaml
```

## Commands

| Command | Description |
|---------|-------------|
| `e2ectl discover` | Scan a subnet for Axis devices |
| `e2ectl plan` | Validate a manifest and preview planned pairings |
| `e2ectl apply` | Execute pairings from a manifest |
| `e2ectl verify` | Check live state of declared pairings |
| `e2ectl teardown` | Remove all pairings in a manifest |

### Global Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--user` | `-u` | `root` | Default username for device auth |
| `--password` | `-p` | | Default password for device auth |
| `--timeout` | `-t` | `10` | Timeout per API call (seconds) |
| `--output` | `-o` | `table` | Output format: table, json, yaml, csv |
| `--verbose` | `-v` | | Show debug output |
| `--dry-run` | | | Preview changes without executing |

## Manifest Format

Manifests are declarative YAML files that describe your site's devices and pairings.

```yaml
apiVersion: e2ectl/v1
kind: SitePairing
metadata:
  name: my-site
  site: "Site Name — City, ST"
  project: "PROJECT-ID"
  integrator: "Company Name"

defaults:
  credentials:
    username: root
    password: ${E2ECTL_DEFAULT_PASS}  # Environment variable
  timeout: 15

devices:
  - name: parking-radar
    ip: 10.1.1.10
    type: radar
    model: AXIS D2210-VE

  - name: parking-ptz
    ip: 10.1.1.20
    type: camera
    model: AXIS Q6135-LE

pairings:
  - name: parking-autotrack
    type: radar-ptz
    primary: parking-radar
    secondary: parking-ptz
    config:
      mountingHeight: 4.5
      panOffset: 0
      tracking: true
    labels:
      zone: parking
      purpose: autotracking
```

### Credential Security

Manifests support `${ENV_VAR}` interpolation. **Never commit plaintext passwords.**

```bash
export E2ECTL_DEFAULT_PASS='your-camera-password'
e2ectl apply -f site.yaml
```

Per-device credential overrides:

```yaml
devices:
  - name: special-cam
    ip: 10.1.1.99
    type: camera
    credentials:
      username: admin
      password: ${SPECIAL_CAM_PASS}
```

## Supported Pairing Types

| Type | Status | Description |
|------|--------|-------------|
| `radar-ptz` | Supported | Radar autotracking with PTZ cameras |
| `audio` | Planned (v0.2) | Camera-to-speaker/mic pairing |
| `camera` | Planned (v0.3) | Intercom-to-camera pairing |

### Radar-PTZ Config Options

| Key | Type | Description |
|-----|------|-------------|
| `mountingHeight` | float | Camera mounting height in meters |
| `panOffset` | float | Pan offset in degrees |
| `tracking` | bool | Enable/disable autotracking |

## Examples

See the [`examples/`](examples/) directory for ready-to-use manifests:

- **retail-store.yaml** — Camera + speaker pairs for retail deterrence
- **radar-campus.yaml** — Radar-PTZ autotracking for campus security
- **school-deterrence.yaml** — Perimeter deterrence with strobes
- **warehouse-radar.yaml** — Full-perimeter radar autotracking (4 zones)

## Output Formats

All commands support `--output` (`-o`) with four formats:

```bash
e2ectl discover -r 10.1.1.0/24 -o table   # Rich terminal table (default)
e2ectl discover -r 10.1.1.0/24 -o json    # JSON array
e2ectl discover -r 10.1.1.0/24 -o yaml    # YAML manifest skeleton
e2ectl discover -r 10.1.1.0/24 -o csv     # CSV for spreadsheets
```

The `yaml` format generates a manifest skeleton from discovered devices — edit it to add your pairings.

## Device Classification

e2ectl automatically classifies Axis devices by model number:

| Series | Type | Examples |
|--------|------|---------|
| P, Q, M, FA, F | Camera | P3268-LVE, Q6135-LE, M3106 |
| C | Speaker | C1410, C1310-E, C8210 |
| D2xxx | Radar | D2210-VE, D2110-VE |
| A8xxx | Intercom | A8105-E, A8207-VE |
| D4100 | Strobe | D4100-E |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — all operations completed |
| 1 | Partial failure — some pairings failed |
| 2 | Total failure — all pairings failed |
| 3 | Validation error — manifest is invalid |

## Development

```bash
git clone https://github.com/oneshot2001/e2ectl.git
cd e2ectl
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check .

# Type check
mypy e2ectl/
```

## License

MIT
