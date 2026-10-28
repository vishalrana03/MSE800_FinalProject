# Admin Guide — Tour Package

## Sign in
Use the local demo administrator account:

- Email: `admin@tour.local`
- Password: `Admin123!`

These credentials are for local coursework only and must not be used on a deployed system.

## Add a package
1. Sign in with the administrator account.
2. Open the admin dashboard and choose the add-package option.
3. Enter a title, description, available dates, price, rating, and optional main image URL.
4. Add at least one destination. Use one destination per line in this format:

```text
Place name | City | Description | Image URL
```

The image URL is optional. Do not put an image URL in the description field unless it is actually meant to be the description.

5. Save the form. Check that the package and destination are visible in the catalogue.

## Access rules
- Visitors must sign in before accessing admin pages.
- Customer accounts cannot create or manage packages.
- Only administrator accounts should be able to add packages.

## Validation checks
- End date must not be earlier than start date.
- Price cannot be negative.
- Rating must be between 0 and 5.
- At least one valid destination is required.
- If saving fails, check the displayed validation message and confirm no partial package was added.
