# Publishing the Al-Qari Odoo Module

This guide covers how to distribute the module to customers and list it on the Odoo Apps Store.

## 1. Build the release zip

```powershell
powershell -ExecutionPolicy Bypass -File integrations/odoo-alqari/package.ps1
```

Output:

- `integrations/odoo-alqari/dist/alqari_integration-1.0.5.zip`
- `integrations/odoo-alqari/dist/CUSTOMER_INSTALL.md`

The zip root folder is **`alqari_integration/`** — ready for Odoo's *Install from zip* or manual addons copy.

## 2. GitHub release (direct download)

1. Tag the release, for example `odoo-integration-v1.0.5`.
2. Create a GitHub release and attach:
   - `alqari_integration-1.0.5.zip`
   - `CUSTOMER_INSTALL.md`
3. Point customers to the release page and [CUSTOMER_INSTALL.md](./CUSTOMER_INSTALL.md).

## 3. Odoo Apps Store — [apps.odoo.com/apps/upload](https://apps.odoo.com/apps/upload)

Official Odoo submission page: **[Submit your Apps & Themes](https://apps.odoo.com/apps/upload)**

### Before you start

| Requirement | Our module |
|-------------|------------|
| Odoo vendor account (sign in on apps.odoo.com) | Create / use Al-Qari vendor account |
| Odoo **17** target | Yes (`depends`: base, mail) |
| Icon PNG at `static/description/icon.png` | Yes |
| Listing HTML at `static/description/index.html` | Yes |
| Cover image in manifest `images` key | Yes (`banner.png`, `icon.png`) |
| License in manifest | `LGPL-3` + `LICENSE` file |
| Free module (no Odoo commission on module price) | No `price` key — module is free; Al-Qari API is billed separately |

Odoo store rules ([vendor guidelines](https://apps.odoo.com/apps/upload)): no hidden code download, no undocumented data collection, provide support for buyers. This module only calls `https://api.alqari.sa` with the customer’s own API key.

### Option A — Upload zip (fastest first submission)

1. Build the zip: `powershell -ExecutionPolicy Bypass -File integrations/odoo-alqari/package.ps1`
2. Open **[apps.odoo.com/apps/upload](https://apps.odoo.com/apps/upload)** and sign in.
3. Upload **`dist/alqari_integration-1.0.5.zip`** (root folder inside must be `alqari_integration/`).
4. Wait for Odoo to parse the module and show **Al-Qari Document AI**.
5. Complete the listing (summary, category **Productivity**, support URL `https://alqari.sa`).
6. Submit for review.

### Option B — Register Git repository (Odoo Apps Store — required path)

Odoo Apps Store does **not** accept zip uploads. Use the dedicated public repo:

```
ssh://git@github.com/PhantomsX/alqari-odoo#17.0
```

**Repo layout (one module folder at root):**

```
alqari-odoo/
└── alqari_integration/
```

**Sync from monorepo after each release:**

```powershell
powershell -ExecutionPolicy Bypass -File integrations/odoo-alqari/publish-odoo-repo.ps1
cd D:\alqari-odoo
git push origin 17.0
```

1. Open **[apps.odoo.com/apps/upload](https://apps.odoo.com/apps/upload)** → **Register your Git repository**.
2. Paste: `ssh://git@github.com/PhantomsX/alqari-odoo#17.0`
3. If the repo is **private**, authorize Odoo GitHub user **`online-odoo`** (Settings → Collaborators).
4. Click **Publish** on **Al-Qari Document AI**.

### Submission checklist

- [ ] Module installs on a fresh Odoo 17 database
- [ ] **Apps → Update Apps List** → install **Al-Qari Document AI**
- [ ] **Settings → Al-Qari → Test Connection** succeeds with `https://api.alqari.sa`
- [ ] Listing states: **Requires Al-Qari API key (`qari_...`) from [alqari.sa](https://alqari.sa)**
- [ ] Add 2–3 PNG screenshots to `static/description/` and reference them in `index.html` (Odoo recommends the [official description template](https://apps.odoo.com/apps/upload))
- [ ] Support contact: **apps@odoo.com** questions → reply via **apps@odoo.com** or your support email

### Listing copy (paste into store description if needed)

**Summary:** OCR, extract fields, classify, validate, and route documents to human review via Al-Qari.

**Important:** This free connector requires an Al-Qari cloud account and API key. Sign up at https://alqari.sa — API Base URL: `https://api.alqari.sa`.

### After submission

- Review usually takes a few business days.
- Questions from Odoo: **apps@odoo.com**
- To sell a paid module later, add to `__manifest__.py`: `'price': 49.99, 'currency': 'EUR'` (see [Odoo Apps pricing docs](https://apps.odoo.com/apps/upload)).

## 4. Odoo.sh / self-hosted Git install

Customers can also add the folder to their Git repo:

```
integrations/odoo-alqari/alqari_integration/
```

Then add that path to `addons_path` and install from Apps.

## 5. Version bumps

1. Update `"version"` in `alqari_integration/__manifest__.py`
2. Add entry to [CHANGELOG.md](./CHANGELOG.md)
3. Re-run `package.ps1`
4. Tag and publish a new GitHub release + Odoo Apps update
