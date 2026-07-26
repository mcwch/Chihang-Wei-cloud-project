# NovaGear UI Consistency Implementation Plan

**Goal:** Unify customer, administration, and load-balancer page styling
without changing application behaviour.

**Approach:** Preserve all existing routes, form fields, template
variables, and page-specific classes. Add shared layout classes to the
templates, then append a shared CSS consistency layer.

**Tech Stack:** Flask, Jinja2, HTML, CSS, pytest, PowerShell, Git.

## Constraints

- Do not change Flask routes.
- Do not change database models.
- Do not add JavaScript.
- Preserve all form methods, actions, names, and values.
- Preserve existing business logic.
- Add tests before changing production templates.
- Run the complete pytest suite before committing.

## Files

Create:

- `ecommerce_app/tests/test_ui_consistency.py`

Modify:

- `ecommerce_app/templates/admin_login.html`
- `ecommerce_app/templates/admin_products.html`
- `ecommerce_app/templates/admin_product_form.html`
- `ecommerce_app/templates/orders.html`
- `ecommerce_app/templates/order_detail.html`
- `ecommerce_app/templates/admin_monitor.html`
- `ecommerce_app/templates/admin_logs.html`
- `ecommerce_app/templates/cart.html`
- `ecommerce_app/templates/checkout.html`
- `ecommerce_app/templates/order_success.html`
- `ecommerce_app/templates/product_detail.html`
- `ecommerce_app/templates/load_balancer_status.html`
- `ecommerce_app/static/style.css`

## Task 1: Define the shared UI contract

1. Create `tests/test_ui_consistency.py`.
2. Test that customer pages use `page-shell`.
3. Test that administration pages use `page-shell`.
4. Test that login, checkout, and product forms use `form-card`.
5. Test that major content sections use `content-card`.
6. Test that empty order and log states use `empty-state`.
7. Test that checkout and order-success symbols are not corrupted.
8. Test that shared responsive CSS selectors exist.
9. Test that the standalone load-balancer page uses equivalent classes.
10. Run the new test file and verify that it fails for the expected
    missing markup and CSS.

## Task 2: Update customer pages

### Shopping cart

- Add `page-shell` to `cart-page`.
- Add `content-card` to cart items.
- Add shared card classes to the cart summary.
- Preserve quantity, remove, clear-cart, and checkout actions.

### Checkout

- Add `page-shell` to `checkout-page`.
- Change the corrupted back link to:

  `&larr; Back to Shopping Cart`

- Add `form-card` to the checkout form.
- Add `content-card` to the order summary.
- Add shared error-message classes.

### Order confirmation

- Add `page-shell` to `success-page`.
- Add `content-card` to `success-card`.
- Replace the corrupted success icon with:

  `&#10003;`

### Product detail

- Add a `page-shell product-detail-page` wrapper.
- Add `content-card` to the product information panel.
- Preserve the existing product visual and cart form.

Run customer, cart, checkout, route, and product-visual tests.

## Task 3: Update administration pages

### Administrator login

- Add `page-shell narrow-page`.
- Add `form-card` to the login card.
- Add shared error-message classes.
- Preserve the hidden redirect field and password input.

### Product management

- Add a `page-shell` wrapper.
- Combine `admin-hero` with `page-header`.
- Add `content-card` around the product table area.
- Preserve archive, restore, and edit actions.

### Product form

- Add a `page-shell` wrapper.
- Combine `admin-hero` with `page-header`.
- Add `form-card` to `product-form-card`.
- Preserve all input names and validation attributes.

### Orders

- Add a `page-shell` wrapper.
- Add `content-card` to filters and order cards.
- Replace the plain no-results paragraph with an `empty-state`.

### Order detail

- Add a `page-shell` wrapper.
- Add `content-card` to customer and item sections.
- Add `status-update-form` to the existing status form.

### Monitoring

- Add a `page-shell` wrapper.
- Add shared card classes to statistic cards and summary content.

### Admin logs

- Add a `page-shell` wrapper.
- Add `content-card` to each log section.
- Use `empty-state` for unavailable log content.
- Preserve persistent log scrolling and audit event data.

Run all administration, monitoring, product-management, order, audit,
and logging tests.

## Task 4: Add shared CSS

Append a shared CSS layer defining:

- `.page-shell`
- `.narrow-page`
- `.content-card`
- `.form-card`
- `.data-card`
- `.content-card-inverse`
- `.status-message`
- `.status-message-error`
- `.page-header-actions`
- responsive table overflow
- responsive form widths
- `overflow-wrap: anywhere`

Keep existing CSS rules intact and use the new rules as the final
consistency layer.

Run the UI, homepage, navigation, and product-visual tests.

## Task 5: Update the load-balancer page

Keep `load_balancer_status.html` standalone.

- Add `page-shell` to the main container.
- Place the title and summary inside `page-header`.
- Add shared status-message classes to configuration errors.
- Add `content-card` to backend target sections.
- Use a shared empty card when no targets exist.
- Align inline spacing, border radius, typography, and mobile behaviour.
- Preserve all state keys and health conditions.

Run `tests/test_ui_consistency.py`.

## Task 6: Final verification

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Browser-check desktop and mobile versions of:

- Product detail
- Cart
- Checkout
- Order confirmation
- Administrator login
- Product management
- Orders
- Monitoring
- Admin logs
- Load-balancer status

Verify:

- No horizontal page overflow
- Forms remain usable
- Tables scroll inside their wrapper
- Logs retain internal scrolling
- Checkout displays a left arrow
- Confirmation displays a check mark
- Existing workflows remain unchanged

Commit message:

```text
style: unify customer and admin page layouts
```

