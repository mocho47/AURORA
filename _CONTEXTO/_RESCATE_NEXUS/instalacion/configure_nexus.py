import os
import json
import sys
from pathlib import Path

def fingerprint() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
            v, _ = winreg.QueryValueEx(k, "MachineGuid")
            return str(v)
    except Exception:
        return str(os.getpid())

def main():
    home = Path.home()
    app = home / "nexus"
    app.mkdir(exist_ok=True)
    p = app / "config.json"
    cfg = {}
    if p.exists():
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    lic = cfg.get("license") or {}
    brands = cfg.get("brands") or {}
    fp = fingerprint()
    allowed = lic.get("allowed_devices") or []
    if fp and fp not in allowed:
        allowed.append(fp)
    lic["allowed_devices"] = allowed
    lic["enabled"] = lic.get("enabled", True)
    lic["dev_mode"] = True
    lic["expires"] = lic.get("expires", "")
    cfg["license"] = lic
    # Ensure default brands
    def ensure_brand(n: str):
        b = brands.get(n) or {}
        b.setdefault("email", "")
        b.setdefault("fb_page_id", "")
        b.setdefault("ig_account_id", "")
        b.setdefault("fb_token", "")
        b.setdefault("ig_token", "")
        b.setdefault("status", "pendiente")
        brands[n] = b
    ensure_brand("actualiza tus faros")
    ensure_brand("creaciones milens")
    # Optional CLI token update: brand, fb_token, ig_token
    if len(sys.argv) >= 3:
        brand = sys.argv[1].strip().lower()
        fb_t = sys.argv[2].strip()
        ig_t = sys.argv[3].strip() if len(sys.argv) >= 4 else None
        ensure_brand(brand)
        brands[brand]["fb_token"] = fb_t
        if ig_t:
            brands[brand]["ig_token"] = ig_t
        print("UPDATED TOKEN FOR", brand)
    cfg["brands"] = brands
    p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("CONFIGURED", str(p))
    print("FINGERPRINT", fp)

if __name__ == "__main__":
    main()
