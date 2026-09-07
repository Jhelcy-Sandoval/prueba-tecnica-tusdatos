class GoogleSelectors:
    '''
    Centraliza los selectores utilizados para interactuar
    y extraer información desde Google.
    '''

    SEARCH_INPUT = [
        'textarea[name="q"]',
        'input[name="q"]',
    ]

    CONSENT_BUTTON = [
        'button:has-text("Aceptar todo")',
        'button:has-text("Accept all")',
    ]

    SEARCH_RESULTS = [
        'cite.tjvcx.GvPZzd.cHaqb',
    ]

    RESULT_TITLE = [
        "h3",
    ]