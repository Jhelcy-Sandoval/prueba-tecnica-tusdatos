class ProxyManager:
    '''
    Gestiona la selección de proxies disponibles para
    la ejecución del scraper.
    '''

    def __init__(
        self,
        proxies: list[str],
    ):
        self.proxies = proxies
        self.current_index = 0

    def current(self) -> str | None:
        if not self.proxies:
            return None

        return self.proxies[self.current_index]

    def next(self) -> str | None:
        if not self.proxies:
            return None

        self.current_index = (
            self.current_index + 1
        ) % len(self.proxies)

        return self.current()