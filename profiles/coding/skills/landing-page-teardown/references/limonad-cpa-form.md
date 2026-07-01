# Limonad CPA Form Pattern

Verified working structure for POST to `./lemon.php` on Limonad-affiliate landers. Replace offer/geo-specific values per campaign.

## Hidden Field Stack

### 1. UTM capture (from URL $_GET / JS)
```html
<input type="hidden" name="utm_source"    value="<?= $_GET['utm_source'];?>" />
<input type="hidden" name="utm_content"   value="<?= $_GET['utm_content'];?>" />
<input type="hidden" name="utm_campaign"  value="<?= $_GET['utm_campaign'];?>" />
<input type="hidden" name="utm_term"      value="<?= $_GET['utm_term'];?>" />
<input type="hidden" name="utm_medium"    value="<?= $_GET['utm_medium'];?>" />
<input type="hidden" name="pixel"         value="<?= $_GET['pixel'];?>" />
```
For static HTML landers, auto-fill via JS:
```javascript
const params = new URLSearchParams(window.location.search);
['utm_source','utm_content','utm_campaign','utm_term','utm_medium','pixel']
  .forEach(k => { const el = document.querySelector('input[name="'+k+'"]'); if(el) el.value = params.get(k)||''; });
```

### 2. Click / sub ID
```html
<input type="hidden" name="clickid" value="{subid}" />
```

### 3. Required offer fields
| Field | Typical value | Notes |
|---|---|---|
| `validate_phone_enable` | `0` | Disable server-side phone validation |
| `offer_id` | `39711` | Campaign offer ID |
| `esub` | `-7EBR...` | Sub-parameter hash from flow |
| `template_name` | `IDD8PaZc5GuuVmH` | Creative / lander template ID |
| `country_code` | `MX` / `ZA` / etc. | Uppercase ISO-3166 alpha-2 |
| `payment_redirect` | `0` | |
| `broker_redirect` | `0` | |
| `shipment_price` | `0` | |
| `total_price` | `890` | Final price (int) |
| `price_vat` | `0.0` | |
| `shipment_vat` | `0.0` | |
| `total_price_wo_shipping` | `890` | Same as total_price when shipment=0 |
| `price` | `890` | Displayed current price |
| `old_price` | `1780` | Crossed-out original price |
| `currency` | `MXN` / `ZAR` / etc. | Uppercase ISO code |
| `package_id` | `0` | |
| `package_prices` | `{}` | Empty JSON object literal |

### 4. Security / hash fields
```html
<input type="hidden" name="l" value="b3da38ba282de3b543e52e6750d001b6d8aee007" />
<input type="hidden" name="7a36e0448c7ca442dfc186d46d1c1ef228890ffe" value="YzQ5NjJkYmM2NTg2MGQ3Yzk3MDI4N2ZiOWZjMTZlNjk2MDU=" />
```

### 5. User-visible inputs
```html
<input name="name"  type="text"  required minlength="2" placeholder="Enter your name" class="main-input" />
<input name="phone" type="tel"   required class="only_number main-input" placeholder="Phone number" />
<button type="submit" class="js_submit order-button">ORDER WITH DISCOUNT</button>
```
- `only_number` class is required for client-side phone digit filtering.
- `js_submit` class is required on the submit button for Limonad script hooks.

## Migration Checklist (from generic `order.php` form)

- [ ] Change `action` from `order.php` → `./lemon.php`
- [ ] Remove `sub1`, `sub2`, `sub3`, `tax` hidden fields (Limonad uses `clickid` + UTM stack)
- [ ] Add full UTM hidden field stack
- [ ] Add offer fields (`offer_id`, `esub`, `template_name`, `country_code`, `currency`, prices)
- [ ] Add security hash fields (`l`, `7a36e0448c7ca442dfc186d46d1c1ef228890ffe`)
- [ ] Ensure button has `js_submit` class
- [ ] Ensure phone input has `only_number` class
- [ ] Add `minlength="2"` to name input
- [ ] Preserve all visual CSS classes and wrapper structure (`formFb`, `formFb__container`, etc.)
