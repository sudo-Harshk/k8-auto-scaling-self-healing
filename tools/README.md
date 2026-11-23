# tools/

External binaries are not committed. Download them into this folder:

| Tool | Version | Download |
|---|---|---|
| TLA+ tools (TLC model checker) | 1.8.0 | `curl -L -o tools/tla2tools.jar https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar` |

TLC needs Java 11 or newer. To run the safety model check:

```bash
cd specs
java -cp ../tools/tla2tools.jar tlc2.TLC -config SafetyShieldV2_safety.cfg SafetyShieldV2.tla
```
