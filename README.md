# Al-Qari Odoo Integration

Production-ready **Odoo 17** module for the [Al-Qari](https://alqari.sa) document AI platform.

## Download

| Resource | Link |
|----------|------|
| **Install guide** | [CUSTOMER_INSTALL.md](./CUSTOMER_INSTALL.md) |
| **Odoo-only Git repo** | [github.com/PhantomsX/alqari-odoo](https://github.com/PhantomsX/alqari-odoo) (branch `17.0`) |
| **Release zip** | Run `package.ps1` → `dist/alqari_integration-*.zip` |
| **Odoo Apps Store** | Register repo URL — see [PUBLISH.md](./PUBLISH.md) |

## For customers

1. Download `alqari_integration-*.zip` from GitHub Releases.
2. Follow **[CUSTOMER_INSTALL.md](./CUSTOMER_INSTALL.md)**.
3. Configure **API Base URL** `https://api.alqari.sa` and your `qari_...` API key.

## For maintainers

### Release packaging

```powershell
powershell -ExecutionPolicy Bypass -File integrations/odoo-alqari/package.ps1
```

Creates `dist/alqari_integration-<version>.zip` ready for GitHub Releases or Odoo Apps Store.

### Local testing (Docker)

```powershell
powershell -ExecutionPolicy Bypass -File integrations/odoo-alqari/start.ps1
```

Open http://localhost:8069 → install **Al-Qari Document AI**.

### Module path

```
integrations/odoo-alqari/alqari_integration/   ← ship this folder
```

### Architecture

```
Odoo UI  →  alqari_client.py  →  POST /services/integration/upload-ocr
                               →  POST /services/integration/extract-fields
                               →  POST /services/integration/classify
                               →  POST /services/integration/validate
```

## Version

See [CHANGELOG.md](./CHANGELOG.md).
