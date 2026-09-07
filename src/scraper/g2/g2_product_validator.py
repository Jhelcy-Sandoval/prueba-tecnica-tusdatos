class G2ProductValidator:
    '''
    Valida que la página actual corresponda al producto
    esperado de G2.
    '''

    @staticmethod
    def validate_url(
        expected_url: str,
        current_url: str,
        product_name: str,
    ) -> bool:
        '''
        Comprueba que la URL actual corresponda al producto
        que se intentó abrir.
        '''

        current_url = current_url.lower()

        if "/products/" not in current_url:
            print(
                f"Página inesperada para '{product_name}'. "
                f"URL actual: {current_url}"
            )
            return False

        expected_slug = (
            expected_url.rstrip("/")
            .split("/")[-2]
            .lower()
        )

        if expected_slug not in current_url:
            print(
                f"Advertencia: la URL no corresponde "
                f"al producto '{product_name}'."
            )
            print(
                f"Esperada: {expected_url}"
            )
            print(
                f"Actual: {current_url}"
            )
            return False

        return True