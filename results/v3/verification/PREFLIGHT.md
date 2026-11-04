# Version 3 Preflight

Date: 29 October 2026

No version-3 production code or experimental run existed when this preflight was performed.

## Environment

- Python: 3.13.1
- Java: Oracle Java 8, `1.8.0_471-b09`, 64-bit
- Working Java executable: `C:\Program Files\Java\jre1.8.0_471\bin\java.exe`
- The Windows `java` shim at `C:\Program Files (x86)\Common Files\Oracle\Java\java8path\java.exe` did not return during the preflight. The project Groovy wrapper correctly selects the working direct Java 8 installation.
- UnetStack launcher: `bin\unet.bat`

## Existing test baseline

Command:

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
```

Result: 18 tests passed.

Groovy tests executed through `scripts\run-groovy-tests.ps1`:

- `tests\protocol-test.groovy` - `PROTOCOL_TEST_PASS`
- `tests\state-test.groovy` - `STATE_TEST_PASS`
- `tests\agent-state-test.groovy` - `AGENT_STATE_TEST_PASS`
- `tests\controller-test.groovy` - `CONTROLLER_TEST_PASS`
- `tests\scenario-test.groovy` - `SCENARIO_TEST_PASS`
- `tests\smoke-test.groovy` - `SMOKE_TEST_PASS`

## Experimental-state guard

- Existing `results/v2/runs/evaluation/` completed manifest count: 0.
- Existing version-2 feasibility and partial calibration evidence remains untouched.
- Version-3 screening, calibration, and held-out evaluation have not started.
