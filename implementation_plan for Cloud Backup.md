# Cloud Backup User Interface Plan

We will expand the recently created `cloud_backup` backend functionality by exposing it through the main Barkat POS user interface. 

## Proposed Changes

### 1. Navigation Updates
#### [MODIFY] `barkat/templates/base.html`
- A new **Cloud Backup** section containing a cloud icon will be added to the primary sidebar.
- It will be positioned near the bottom of the active menus (e.g., right under "Staff" or "Finance").

### 2. URL Routes and Views
#### [MODIFY] `barkat_wholesale/urls.py`
- We will link a new `cloud_backup.urls` file to manage all endpoints strictly relating to the Cloud Backup application under `/backup/`.

#### [NEW] `cloud_backup/urls.py`
- `/` -> Displays the main Cloud Backup dashboard.
- `/keys/` -> Displays the Keys/Authentication page.
- `/trigger-manual/` -> A hidden POST endpoint purely to trigger the manual backup logic.

#### [NEW] `cloud_backup/views.py` & `cloud_backup/forms.py`
We will create views handling the user flows for:
1. **The Dashboard**: A page featuring a large status card denoting the `last_backup_date`, along with options (like Radio Buttons or styled tiles) to select either "Auto Backup" or "Manual Backup". When Auto Backup is selected, an input field for `backup_interval_minutes` will appear to denote the schedule timing.
2. **Key Configuration**: A discrete page containing standard forms for `key_id`, `application_key` (masked as password input for security), `bucket_name`, and `endpoint_url`.
3. **Manual Trigger**: A function that manually executes the `perform_cloud_backup` utility and returns the user to the dashboard with an updated timestamp and a success pop-up.

### 3. Tailwind Templates
#### [NEW] `cloud_backup/templates/cloud_backup/dashboard.html`
- Will extend your beautiful `base.html` design.
- Uses premium glassmorphism/cards and high-visibility status tags ("Active", "Never Backed Up", etc).
- Will feature a button labeled "Configure Cloud Keys" redirecting to the keys page.

#### [NEW] `cloud_backup/templates/cloud_backup/keys.html`
- Professional form layout explicitly tailored for securely inputting Backblaze integration endpoints. 
- Includes a "Back to Dashboard" navigation prompt.

## Open Questions 

> [!IMPORTANT]
> 1. Should we add the Cloud Backup menu in the main sidebar directly or embed it within an existing dropdown menu like "Setup" or "System"? (I am assuming main sidebar for now).
> 2. Do you have a specific style in mind for the radio buttons, or shall I adhere strictly to your modern Barkat POS styling (e.g., matching the blue/slate gradient accents)?

## Verification Plan

1. Clicking "Cloud Backup" on the sidebar loads the Dashboard correctly.
2. Saving the interval as "Auto" correctly links to the ORM and reschedules the `django-q2` timer.
3. Accessing the Cloud Keys page allows smooth credentials input.
4. Attempting a manual backup successfully uploads to the destination and updates the `last_backup_date` in the dashboard UI in real-time.
