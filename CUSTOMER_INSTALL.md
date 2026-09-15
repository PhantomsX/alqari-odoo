# Al-Qari Odoo Module — Customer Install Guide

Install the **Al-Qari Document AI** module on your Odoo 17 server and connect it to the Al-Qari cloud API.

---

## What you need

| Item | Details |
|------|---------|
| **Odoo** | Version 17 (Community or Enterprise) |
| **Al-Qari account** | Provided by Al-Qari — includes API key |
| **Network** | Odoo server must reach `https://api.alqari.sa` over HTTPS |
| **Python** | `requests` library on the Odoo Python environment |

---

## Step 1 — Get credentials from Al-Qari

Al-Qari will provide:

- **API Base URL:** `https://api.alqari.sa`
- **API Key:** starts with `qari_...` (from your Al-Qari dashboard)

Keep the API key secret. Only Odoo administrators should configure it.

---

## Step 2 — Install the module

### Option A — Copy the module folder

1. Download the latest `alqari_integration-*.zip` from [GitHub Releases](https://github.com/PhantomsX/docutalk-be/releases) (search for **odoo-integration** tags) or from Al-Qari.
2. Extract the folder `alqari_integration/` into your Odoo addons directory, for example:
   ```
   /opt/odoo/custom-addons/alqari_integration/
   ```
3. Ensure the addons path is listed in `odoo.conf`:
   ```
   addons_path = /usr/lib/python3/dist-packages/odoo/addons,/opt/odoo/custom-addons
   ```
4. Install Python dependency (if missing):
   ```bash
   pip install requests
   ```
5. Restart Odoo.

### Option B — Odoo.sh

1. Add `alqari_integration/` to your Odoo.sh Git repository.
2. Push to the linked branch.
3. Odoo.sh builds and deploys automatically.

---

## Step 3 — Activate in Odoo

1. Log in as administrator.
2. Go to **Apps**.
3. Click **Update Apps List**.
4. Search **Al-Qari Document AI**.
5. Click **Install** (or **Activate**).

---

## Step 4 — Configure

1. Open **Al-Qari → Configuration** (administrators only).
2. Set:
   - **API Base URL:** `https://api.alqari.sa`
   - **API Key:** your `qari_...` key
3. Click **Test Connection**.
4. Configure defaults:
   - **Extract Fields** — e.g. `invoice_number, total, date, vendor_name`
   - **Categories** — document types for classification
   - **Required Fields** — fields that must exist when validating
5. Click **Save**.

### Field validation rules (recommended)

For precise checks like **total > 10000**:

1. Go to **Al-Qari → Field Validation Rules**.
2. Create rules, for example:
   - Field: `total`, Operator: **Greater than**, Value: `10000`
3. Enable **Validate by Default** in Configuration, or check **Validate** when processing each document.

---

## Step 5 — Use

**Al-Qari → Process Document**

1. Enter a document name.
2. Upload a PDF or image (PNG/JPG receipt photo).
3. Click **Process Document**.
4. Review results on the document record:
   - **Extracted Summary** — key invoice fields
   - **Validation** — PASS/FAIL if validation was enabled

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Module not in Apps | Enable developer mode → Update Apps List |
| Test Connection fails | Check URL, API key, firewall/proxy to `api.alqari.sa` |
| Invalid API key | Verify key with Al-Qari; regenerate if needed |
| Insufficient credits | Contact Al-Qari to top up your account |
| `requests` not found | Run `pip install requests` in Odoo's Python env and restart |

---

## Support

- Website: [https://alqari.sa](https://alqari.sa)
- API documentation: Swagger at `https://api.alqari.sa/docs`

---

## Architecture

```
Your Odoo Server                    Al-Qari Cloud
┌─────────────────┐                ┌──────────────────┐
│  Al-Qari Module │  ── HTTPS ──▶  │  Integration API │
│  (this plugin)  │  ◀── JSON ───  │  OCR / AI nodes  │
└─────────────────┘                └──────────────────┘
```

Your documents are sent to Al-Qari for processing. Results are stored back in Odoo.
