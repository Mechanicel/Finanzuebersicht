from tkcalendar import DateEntry

DEFAULT_DATE_ENTRY_CONFIG = {
    "date_pattern": "yyyy-mm-dd",
    "width": 20,
    "font": ("Arial", 16),
}


def create_date_entry(parent, **kwargs):
    config = DEFAULT_DATE_ENTRY_CONFIG.copy()
    config.update(kwargs)
    return DateEntry(parent, **config)
