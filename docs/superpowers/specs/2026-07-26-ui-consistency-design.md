# NovaGear Lightweight UI Consistency Design

Date: 2026-07-26
Status: Approved for implementation

## 1. Goal

Create a consistent visual system across NovaGear customer and
administration pages without changing routes, database behaviour,
authentication, order processing, product management, logging, or
load-balancing functionality.

The update should make the application feel like one cohesive product
while preserving the existing page content and workflows.

## 2. Scope

This is a lightweight visual update.

Included:

- Consistent page spacing and content widths
- Consistent page headers and subtitles
- Shared white-card presentation
- Shared form presentation
- Shared empty-state presentation
- Consistent buttons, tables, status labels, and messages
- Responsive behaviour for existing layouts
- Reuse of existing HTML classes wherever practical

Excluded:

- Route changes
- Database or model changes
- JavaScript interactions
- New application features
- Major content restructuring
- New authentication behaviour
- Major load balancer page redesign

## 3. Shared UI Components

### 3.1 Page shell

A `page-shell` class will provide consistent vertical spacing for
non-homepage screens.

### 3.2 Page header

The existing `page-header` pattern will become the primary title area.

It may contain:

- Page title
- Supporting description
- Optional action button or navigation link

Existing specialised headers such as `admin-hero` may retain their
current class while also using the shared page-header presentation.

### 3.3 Content cards

A `content-card` class will provide:

- White background
- Consistent border
- Consistent corner radius
- Consistent internal padding
- Subtle shadow
- Responsive width behaviour

Existing classes such as `order-card`, `product-form-card`, and
`cart-summary` will remain available and may be combined with the
shared class.

### 3.4 Form cards

A `form-card` class will standardise:

- Administrator login
- Checkout
- Product creation
- Product editing

It will not change field names, validation, submission methods, or
route destinations.

### 3.5 Empty states

An `empty-state` class will standardise screens that contain no data,
including:

- Empty product catalogue
- Empty shopping cart
- Empty orders list
- Empty log section where applicable

### 3.6 Status messages

Existing success, error, warning, availability, and order-status
elements will receive consistent spacing, borders, and typography.
Their meanings and backend conditions will not change.

## 4. Page Groups

### 4.1 Customer pages

The following pages will receive consistent spacing and cards:

- Product detail
- Shopping cart
- Checkout
- Order confirmation

The homepage hero and product card system will remain unchanged except
for small compatibility adjustments where needed.

### 4.2 Administration pages

The following pages will share a consistent administration layout:

- Administrator login
- Product management
- Product create/edit form
- Order management
- Order detail
- Application monitoring
- Admin logs

Existing page-specific data and controls will remain in their current
logical order.

### 4.3 Load balancer status

The load balancer status page will keep its specialised operational
appearance. Only its typography, maximum width, spacing, controls, and
responsive behaviour will be aligned with the main application.

## 5. Implementation Approach

The implementation will:

1. Add shared CSS classes to `static/style.css`.
2. Apply those classes to existing templates.
3. Preserve existing template classes to avoid regressions.
4. Avoid changing Flask route logic.
5. Avoid changing database models and migrations.
6. Add template-structure tests before production changes.
7. Run the focused UI tests and then the complete test suite.

## 6. Testing Strategy

Automated tests will verify that:

- Main customer pages use the shared page shell
- Main administration pages use the shared page shell
- Shared page headers are present
- Forms use the shared form-card presentation
- Major content sections use shared card classes
- Empty-state styling exists
- Responsive shared-card CSS exists
- Existing navigation, order, product, cart, checkout, logging, and
  monitoring tests continue to pass

Browser checks will cover:

- Desktop layout
- Mobile layout below 760px
- Customer pages
- Administrator pages
- Form readability
- Tables and long log content
- No horizontal overflow

## 7. Acceptance Criteria

The work is complete when:

- Major customer and administration pages share the same visual system
- Existing workflows remain unchanged
- No major page has inconsistent outer spacing
- Forms and content cards use consistent borders, padding, and radius
- Mobile pages remain readable without horizontal scrolling
- All automated tests pass
- Browser checks show no visible layout regression
