class G2Selectors:
    '''
    Centraliza los selectores utilizados para extraer
    información de productos desde G2.
    '''
    
    SEARCH_INPUT = [
        'input[name="query"]',
        'input[type="search"]',
        'input[placeholder*="Search"]',
    ]

    SEARCH_BUTTON = [
        'button.submit-search-btn[type="submit"]',
        'button[type="submit"]',
    ]

    PRODUCT = [
        'a[href*="/products/"][href$="/reviews"]',
        '/html/body/div[5]/div/div[1]/div/div[6]/div/div[2]/div[4]/div[1]/section/div/div/div/div[1]/div[2]/a[1]',
        
    ]

    RATING = [
        '.elv-star-wrapper__desc__rating',
        '//*[@id="product-header"]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/span[1]'
    ]

    REVIEWS = [
        '.elv-star-wrapper__desc__count',
        '//*[@id="product-header"]/div[1]/div[1]/div[2]/div[2]/div[1]/div[2]/span[2]'
    ]
    
    CAPTCHA_SELECTOR = [
        'iframe[title="DataDome CAPTCHA"]'
        ]
    
    SLIDER_CONTAINER_SELECTOR = [
        ".sliderContainer"
    ]
    
    SLIDER_SELECTOR = [
        ".slider"
    ]
    
    HARD_BLOCK_SELECTOR = [
        '[data-dd-response-page="hard-block"]'
    ]